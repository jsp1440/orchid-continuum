#!/usr/bin/env python3
"""
GBIF Orchidaceae Data Harvester
Harvests global occurrence records for Orchidaceae family
Following Darwin Core standards with quality filtering
"""

import os
import sys
import json
import requests
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrchidaceaeHarvester:
    """GBIF data harvester for Orchidaceae family"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.gbif_base_url = "https://api.gbif.org/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OrchidContinuum/1.0 (research@orchidcontinuum.org)'
        })
        
        # Quality filters as per specification
        self.quality_filters = {
            'hasCoordinate': True,
            'hasGeospatialIssue': False,
            'coordinateUncertaintyInMeters': '0,50000',
            'basisOfRecord': ['HUMAN_OBSERVATION', 'OBSERVATION', 'PRESERVED_SPECIMEN'],
            'license': ['CC0_1_0', 'CC_BY_4_0', 'CC_BY_NC_4_0']
        }
        
        # Issue flags to exclude
        self.exclude_issues = [
            'PRESUMED_NEGATED_LONGITUDE',
            'PRESUMED_NEGATED_LATITUDE', 
            'COUNTRY_COORDINATE_MISMATCH',
            'ZERO_COORDINATE'
        ]
        
        # Darwin Core fields to extract
        self.dwc_fields = [
            'occurrenceID', 'datasetKey', 'datasetName', 'license', 'rightsHolder',
            'institutionCode', 'collectionCode', 'scientificName', 'acceptedScientificName',
            'taxonRank', 'taxonKey', 'acceptedTaxonKey', 'kingdom', 'phylum', 'class',
            'order', 'family', 'genus', 'species', 'eventDate', 'year', 'month', 'day',
            'recordedBy', 'identifiedBy', 'decimalLatitude', 'decimalLongitude',
            'coordinateUncertaintyInMeters', 'geodeticDatum', 'elevation',
            'minimumElevationInMeters', 'maximumElevationInMeters', 'country',
            'countryCode', 'stateProvince', 'county', 'municipality', 'locality',
            'basisOfRecord', 'establishmentMeans', 'occurrenceStatus', 'individualCount',
            'lifeStage', 'sex', 'media', 'references', 'issue', 'modified',
            'lastInterpreted', 'gbifID', 'publishingOrgKey'
        ]
        
        self.datasets_catalog = {}
        self.taxa_catalog = {}
        
    def setup_directories(self):
        """Create output directory structure"""
        dirs = [
            self.output_dir / "gbif_orchidaceae" / "parquet",
            self.output_dir / "gbif_orchidaceae" / "jsonl", 
            self.output_dir / "catalog",
            self.output_dir / "reports"
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        logger.info("Output directories created")
        
    def get_orchidaceae_taxon_key(self) -> int:
        """Get GBIF taxon key for Orchidaceae family"""
        url = f"{self.gbif_base_url}/species/match"
        params = {'name': 'Orchidaceae', 'rank': 'FAMILY'}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('matchType') == 'EXACT' and data.get('family') == 'Orchidaceae':
            taxon_key = data['usageKey']
            logger.info(f"Found Orchidaceae taxon key: {taxon_key}")
            return taxon_key
        else:
            raise ValueError("Could not find exact match for Orchidaceae family")
            
    def search_occurrences(self, taxon_key: int, limit: int = 300, offset: int = 0) -> Dict:
        """Search GBIF occurrences for Orchidaceae"""
        url = f"{self.gbif_base_url}/occurrence/search"
        
        params = {
            'taxonKey': taxon_key,
            'limit': limit,
            'offset': offset,
            **self.quality_filters
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
        
    def filter_quality_issues(self, record: Dict) -> bool:
        """Filter out records with quality issues"""
        issues = record.get('issues', [])
        return not any(issue in self.exclude_issues for issue in issues)
        
    def normalize_coordinates(self, lat: float, lon: float) -> Tuple[float, float]:
        """Normalize coordinates to 5 decimal places"""
        return round(lat, 5), round(lon, 5)
        
    def extract_record_data(self, record: Dict) -> Dict:
        """Extract and normalize fields from GBIF record"""
        extracted = {}
        
        for field in self.dwc_fields:
            value = record.get(field)
            if field in ['decimalLatitude', 'decimalLongitude'] and value is not None:
                value = round(float(value), 5)
            elif field == 'media' and isinstance(value, list):
                value = [item.get('identifier') for item in value if item.get('identifier')]
            elif field == 'references' and isinstance(value, list):
                value = [ref for ref in value if ref]
            elif field in ['year', 'month', 'day'] and value is not None:
                value = int(value)
                
            extracted[field] = value
            
        return extracted
        
    def update_catalogs(self, record: Dict):
        """Update dataset and taxa catalogs"""
        # Dataset catalog
        dataset_key = record.get('datasetKey')
        if dataset_key and dataset_key not in self.datasets_catalog:
            self.datasets_catalog[dataset_key] = {
                'title': record.get('datasetName', ''),
                'publisher': record.get('publishingOrgKey', ''),
                'license': record.get('license', ''),
                'citation': f"{record.get('datasetName', 'Unknown')} via GBIF.org"
            }
            
        # Taxa catalog  
        taxon_key = record.get('acceptedTaxonKey') or record.get('taxonKey')
        if taxon_key and taxon_key not in self.taxa_catalog:
            self.taxa_catalog[taxon_key] = {
                'acceptedName': record.get('acceptedScientificName') or record.get('scientificName'),
                'rank': record.get('taxonRank'),
                'genus': record.get('genus'),
                'species': record.get('species'),
                'synonyms': [],
                'commonNames': []
            }
            
    def deduplicate_records(self, records: List[Dict]) -> List[Dict]:
        """Remove duplicate records based on key fields"""
        seen = set()
        deduplicated = []
        
        for record in records:
            # Create deduplication key
            key_fields = [
                record.get('scientificName', ''),
                record.get('eventDate', ''),
                str(record.get('decimalLatitude', '')),
                str(record.get('decimalLongitude', '')),
                record.get('datasetKey', '')
            ]
            dedup_key = '|'.join(key_fields)
            
            if dedup_key not in seen:
                seen.add(dedup_key)
                deduplicated.append(record)
                
        logger.info(f"Deduplicated {len(records)} -> {len(deduplicated)} records")
        return deduplicated
        
    def save_by_genus(self, records: List[Dict]):
        """Save records partitioned by genus"""
        genus_groups = {}
        
        for record in records:
            genus = record.get('genus', 'Unknown')
            if genus not in genus_groups:
                genus_groups[genus] = []
            genus_groups[genus].append(record)
            
        for genus, genus_records in genus_groups.items():
            # Save as Parquet
            df = pd.DataFrame(genus_records)
            parquet_path = self.output_dir / "gbif_orchidaceae" / "parquet" / f"genus={genus}"
            parquet_path.mkdir(exist_ok=True)
            df.to_parquet(parquet_path / "part-0001.parquet", index=False)
            
            # Save as JSONL
            jsonl_path = self.output_dir / "gbif_orchidaceae" / "jsonl" / f"genus={genus}"
            jsonl_path.mkdir(exist_ok=True)
            with open(jsonl_path / "part-0001.jsonl", 'w') as f:
                for record in genus_records:
                    f.write(json.dumps(record) + '\n')
                    
        logger.info(f"Saved {len(genus_groups)} genera to disk")
        
    def save_catalogs(self):
        """Save dataset and taxa catalogs"""
        catalog_dir = self.output_dir / "catalog"
        
        with open(catalog_dir / "datasets.json", 'w') as f:
            json.dump(self.datasets_catalog, f, indent=2)
            
        with open(catalog_dir / "taxa.json", 'w') as f:
            json.dump(self.taxa_catalog, f, indent=2)
            
        logger.info("Catalogs saved")
        
    def validate_sample(self, records: List[Dict], sample_size: int = 100) -> Dict:
        """Validate sample of records with media links"""
        import random
        
        media_records = [r for r in records if r.get('media')]
        sample = random.sample(media_records, min(sample_size, len(media_records)))
        
        validation_results = {
            'total_checked': len(sample),
            'media_accessible': 0,
            'media_broken': 0,
            'broken_urls': []
        }
        
        for record in sample:
            media_urls = record.get('media', [])
            for url in media_urls[:3]:  # Check first 3 media URLs
                try:
                    response = self.session.head(url, timeout=10)
                    if response.status_code == 200:
                        validation_results['media_accessible'] += 1
                    else:
                        validation_results['media_broken'] += 1
                        validation_results['broken_urls'].append(url)
                except:
                    validation_results['media_broken'] += 1
                    validation_results['broken_urls'].append(url)
                    
        return validation_results
        
    def generate_quality_report(self, records: List[Dict], validation: Dict):
        """Generate quality summary report"""
        report_path = self.output_dir / "reports" / "quality_summary.md"
        
        # Calculate statistics
        license_counts = {}
        basis_counts = {}
        dataset_counts = {}
        
        for record in records:
            license_counts[record.get('license', 'Unknown')] = license_counts.get(record.get('license', 'Unknown'), 0) + 1
            basis_counts[record.get('basisOfRecord', 'Unknown')] = basis_counts.get(record.get('basisOfRecord', 'Unknown'), 0) + 1
            dataset_counts[record.get('datasetKey', 'Unknown')] = dataset_counts.get(record.get('datasetKey', 'Unknown'), 0) + 1
            
        top_datasets = sorted(dataset_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        report_content = f"""# GBIF Orchidaceae Quality Report

Generated: {datetime.now().isoformat()}

## Overview
- Total records: {len(records):,}
- Unique datasets: {len(self.datasets_catalog)}
- Unique taxa: {len(self.taxa_catalog)}

## License Distribution
{chr(10).join(f"- {license}: {count:,}" for license, count in sorted(license_counts.items()))}

## Basis of Record Distribution  
{chr(10).join(f"- {basis}: {count:,}" for basis, count in sorted(basis_counts.items()))}

## Top 20 Contributing Datasets
{chr(10).join(f"{i+1}. {dataset_key}: {count:,} records" for i, (dataset_key, count) in enumerate(top_datasets))}

## Media Validation
- Total URLs checked: {validation['total_checked']}
- Accessible: {validation['media_accessible']}
- Broken: {validation['media_broken']}
- Success rate: {validation['media_accessible']/(validation['total_checked'] or 1)*100:.1f}%

## Data Dictionary
| Field | Type | Description |
|-------|------|-------------|
| gbifID | integer | Stable GBIF occurrence identifier |
| scientificName | string | Scientific name as provided by data publisher |
| acceptedScientificName | string | Accepted scientific name from GBIF backbone |
| decimalLatitude | float | Decimal latitude (WGS84, 5 decimal places) |
| decimalLongitude | float | Decimal longitude (WGS84, 5 decimal places) |
| eventDate | string | Date when record was collected/observed |
| basisOfRecord | string | Nature of the data record |
| license | string | License applied to the data |
| datasetKey | string | Unique identifier for contributing dataset |
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
            
        logger.info(f"Quality report saved to {report_path}")
        
    def harvest(self, max_records: int = 10000) -> int:
        """Main harvesting method"""
        logger.info("Starting GBIF Orchidaceae harvest")
        self.setup_directories()
        
        # Get Orchidaceae taxon key
        taxon_key = self.get_orchidaceae_taxon_key()
        
        all_records = []
        offset = 0
        limit = 300
        
        while len(all_records) < max_records:
            logger.info(f"Fetching records {offset}-{offset+limit}")
            
            try:
                response = self.search_occurrences(taxon_key, limit, offset)
                records = response.get('results', [])
                
                if not records:
                    logger.info("No more records found")
                    break
                    
                # Filter and process records
                filtered_records = []
                for record in records:
                    if self.filter_quality_issues(record):
                        processed = self.extract_record_data(record)
                        self.update_catalogs(record)
                        filtered_records.append(processed)
                        
                all_records.extend(filtered_records)
                offset += limit
                
                # Rate limiting
                time.sleep(0.1)
                
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                break
                
        # Deduplicate
        all_records = self.deduplicate_records(all_records)
        
        # Save data
        self.save_by_genus(all_records)
        self.save_catalogs()
        
        # Validation and reporting
        validation = self.validate_sample(all_records)
        self.generate_quality_report(all_records, validation)
        
        logger.info(f"Harvest complete: {len(all_records)} records saved")
        return len(all_records)

if __name__ == "__main__":
    harvester = OrchidaceaeHarvester()
    
    # Command line argument for max records
    max_records = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    
    records_count = harvester.harvest(max_records)
    print(f"Successfully harvested {records_count} Orchidaceae records from GBIF")