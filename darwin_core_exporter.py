#!/usr/bin/env python3
"""
Darwin Core Archive Exporter for Orchid Atlas
Based on provided mapping specification
"""

import csv
import os
import zipfile
from datetime import datetime, date
from io import StringIO

class DarwinCoreExporter:
    """Export Orchid Atlas data to Darwin Core Archive format"""
    
    def __init__(self):
        # Exact field order from user specification
        self.dwc_fields = [
            'occurrenceID', 'basisOfRecord', 'scientificName', 'scientificNameAuthorship',
            'taxonRank', 'kingdom', 'family', 'genus', 'specificEpithet', 'infraspecificEpithet',
            'taxonRemarks', 'eventDate', 'year', 'month', 'day', 'recordedBy', 'identifiedBy',
            'decimalLatitude', 'decimalLongitude', 'coordinateUncertaintyInMeters',
            'country', 'countryCode', 'stateProvince', 'county', 'locality', 'elevation',
            'elevationUnit', 'habitat', 'associatedTaxa', 'occurrenceRemarks',
            'catalogNumber', 'institutionCode', 'collectionCode', 'license', 'rightsHolder',
            'datasetName', 'references'
        ]
        
    def export_to_dwc_archive(self, output_dir="darwin_core_export", enhance_data=True):
        """Export all orchid records to Darwin Core Archive with optional enhancement"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Export occurrence data with enhancement
        occurrence_file = os.path.join(output_dir, "occurrence.txt")
        self.export_occurrence_data(occurrence_file, enhance_data=enhance_data)
        
        # Create meta.xml
        meta_file = os.path.join(output_dir, "meta.xml")
        self.create_meta_xml(meta_file)
        
        # Create EML metadata
        eml_file = os.path.join(output_dir, "eml.xml")
        self.create_eml_metadata(eml_file)
        
        # Create ZIP archive
        archive_file = os.path.join(output_dir, "orchid_atlas_dwc_archive.zip")
        self.create_zip_archive(output_dir, archive_file)
        
        return archive_file
    
    def export_occurrence_data(self, output_file, enhance_data=True):
        """Export occurrence.txt with all orchid records, optionally enhanced"""
        
        from models import OrchidRecord
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.dwc_fields, delimiter='\t')
            writer.writeheader()
            
            # Get all orchid records
            records = OrchidRecord.query.all()
            
            # Create basic Darwin Core records
            dwc_records = []
            for record in records:
                dwc_record = self.map_orchid_to_dwc(record)
                dwc_records.append(dwc_record)
            
            # Enhance with authoritative data if requested
            if enhance_data:
                print(f"🔧 Enhancing {len(dwc_records)} records with taxonomic data...")
                try:
                    from darwin_core_enhancer import OrchidDataEnhancer
                    enhancer = OrchidDataEnhancer()
                    dwc_records = enhancer.enhance_darwin_core_records(dwc_records)
                    print(f"✅ Enhanced {enhancer.enhanced_count} records")
                except ImportError:
                    print("⚠️ Data enhancer not available, using basic mapping")
            
            # Write enhanced records
            for dwc_record in dwc_records:
                writer.writerow(dwc_record)
    
    def map_orchid_to_dwc(self, orchid):
        """Map OrchidRecord to Darwin Core fields"""
        
        # Handle date parsing
        event_date = ""
        year = ""
        month = ""
        day = ""
        
        if hasattr(orchid, 'photo_date') and orchid.photo_date:
            if isinstance(orchid.photo_date, date):
                event_date = orchid.photo_date.isoformat()
                year = str(orchid.photo_date.year)
                month = str(orchid.photo_date.month)
                day = str(orchid.photo_date.day)
        elif orchid.created_at:
            event_date = orchid.created_at.date().isoformat()
            year = str(orchid.created_at.year)
            month = str(orchid.created_at.month)
            day = str(orchid.created_at.day)
        
        # Handle coordinates
        lat = ""
        lng = ""
        uncertainty = ""
        
        # Try to extract coordinates from region field if it contains lat/lon
        if orchid.region and 'Lat:' in orchid.region:
            try:
                # Parse "Lat: XX.XXXX, Lon: XX.XXXX" format
                parts = orchid.region.split(',')
                lat_part = parts[0].replace('Lat:', '').strip()
                lng_part = parts[1].replace('Lon:', '').strip()
                lat = lat_part
                lng = lng_part
                uncertainty = "1000"  # Default uncertainty in meters
            except:
                pass
        
        # Build associated taxa (pollinators, parents, etc.)
        associated_taxa = []
        if hasattr(orchid, 'pollinator_types') and orchid.pollinator_types:
            for pollinator in orchid.pollinator_types:
                associated_taxa.append(f"pollinator: {pollinator}")
        
        if hasattr(orchid, 'mycorrhizal_fungi') and orchid.mycorrhizal_fungi:
            for fungus in orchid.mycorrhizal_fungi:
                associated_taxa.append(f"mycorrhizal: {fungus}")
        
        # Handle hybrid parentage
        if orchid.pod_parent or orchid.pollen_parent:
            if orchid.pod_parent and orchid.pollen_parent:
                associated_taxa.append(f"parents: {orchid.pod_parent} × {orchid.pollen_parent}")
            elif orchid.parentage_formula:
                associated_taxa.append(f"parents: {orchid.parentage_formula}")
        
        # Build taxon remarks
        taxon_remarks = []
        if hasattr(orchid, 'is_hybrid') and orchid.is_hybrid:
            taxon_remarks.append("hybrid")
        if orchid.clone_name:
            taxon_remarks.append(f"clone: {orchid.clone_name}")
        if hasattr(orchid, 'rhs_registration_id') and orchid.rhs_registration_id:
            taxon_remarks.append(f"RHS: {orchid.rhs_registration_id}")
        
        # Determine taxonomic rank
        taxon_rank = "species"
        if hasattr(orchid, 'is_hybrid') and orchid.is_hybrid:
            taxon_rank = "hybrid"
        
        # Build occurrence remarks
        remarks = []
        if orchid.cultural_notes:
            remarks.append(orchid.cultural_notes)
        if orchid.ai_description:
            remarks.append(f"AI description: {orchid.ai_description}")
        if hasattr(orchid, 'native_habitat') and orchid.native_habitat:
            remarks.append(f"Habitat: {orchid.native_habitat}")
        
        return {
            'occurrenceID': f"ORCHID_{orchid.id}",
            'basisOfRecord': "HumanObservation",
            'scientificName': orchid.scientific_name or orchid.display_name,
            'scientificNameAuthorship': getattr(orchid, 'author', '') or '',
            'taxonRank': taxon_rank,
            'kingdom': "Plantae",
            'family': "Orchidaceae",
            'genus': orchid.genus or '',
            'specificEpithet': orchid.species or '',
            'infraspecificEpithet': orchid.clone_name or '',
            'taxonRemarks': '; '.join(taxon_remarks),
            'eventDate': event_date,
            'year': year,
            'month': month,
            'day': day,
            'recordedBy': orchid.photographer or '',
            'identifiedBy': orchid.photographer or '',
            'decimalLatitude': lat,
            'decimalLongitude': lng,
            'coordinateUncertaintyInMeters': uncertainty,
            'country': self.parse_country_from_region(orchid.region),
            'countryCode': self.get_country_code(orchid.region),
            'stateProvince': orchid.region or '',
            'county': '',
            'locality': orchid.region or '',
            'elevation': '',
            'elevationUnit': 'meters',
            'habitat': getattr(orchid, 'native_habitat', '') or '',
            'associatedTaxa': '; '.join(associated_taxa),
            'occurrenceRemarks': '; '.join(remarks),
            'catalogNumber': str(orchid.id),
            'institutionCode': "FCOS",
            'collectionCode': orchid.ingestion_source or '',
            'license': "CC-BY-NC",
            'rightsHolder': "Five Cities Orchid Society",
            'datasetName': "Five Cities Orchid Society Collection Database",
            'references': "https://atlas.fivecitiescalifornia.org"
        }
    
    def parse_country_from_region(self, region):
        """Extract country name from region string"""
        if not region:
            return ""
        
        # Common country mappings
        country_mappings = {
            'philippines': 'Philippines',
            'thailand': 'Thailand',
            'indonesia': 'Indonesia',
            'malaysia': 'Malaysia',
            'myanmar': 'Myanmar',
            'india': 'India',
            'ecuador': 'Ecuador',
            'california': 'United States',
            'java': 'Indonesia',
            'borneo': 'Malaysia',
            'sumatra': 'Indonesia'
        }
        
        region_lower = region.lower()
        for key, country in country_mappings.items():
            if key in region_lower:
                return country
        
        return region  # Return as-is if no mapping found
    
    def get_country_code(self, region):
        """Get ISO country code from region"""
        country = self.parse_country_from_region(region)
        
        country_codes = {
            'Philippines': 'PH',
            'Thailand': 'TH',
            'Indonesia': 'ID',
            'Malaysia': 'MY',
            'Myanmar': 'MM',
            'India': 'IN',
            'Ecuador': 'EC',
            'United States': 'US'
        }
        
        return country_codes.get(country, '')
    
    def create_meta_xml(self, output_file):
        """Create meta.xml file for Darwin Core Archive"""
        
        meta_content = '''<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/" metadata="eml.xml">
  <core encoding="UTF-8" linesTerminatedBy="\\n" fieldsTerminatedBy="\\t" fieldsEnclosedBy='"' ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files>
      <location>occurrence.txt</location>
    </files>
    <id index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/occurrenceID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/basisOfRecord"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/scientificNameAuthorship"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/taxonRank"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/kingdom"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/family"/>
    <field index="7" term="http://rs.tdwg.org/dwc/terms/genus"/>
    <field index="8" term="http://rs.tdwg.org/dwc/terms/specificEpithet"/>
    <field index="9" term="http://rs.tdwg.org/dwc/terms/infraspecificEpithet"/>
    <field index="10" term="http://rs.tdwg.org/dwc/terms/taxonRemarks"/>
    <field index="11" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
    <field index="12" term="http://rs.tdwg.org/dwc/terms/year"/>
    <field index="13" term="http://rs.tdwg.org/dwc/terms/month"/>
    <field index="14" term="http://rs.tdwg.org/dwc/terms/day"/>
    <field index="15" term="http://rs.tdwg.org/dwc/terms/recordedBy"/>
    <field index="16" term="http://rs.tdwg.org/dwc/terms/identifiedBy"/>
    <field index="17" term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
    <field index="18" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
    <field index="19" term="http://rs.tdwg.org/dwc/terms/coordinateUncertaintyInMeters"/>
    <field index="20" term="http://rs.tdwg.org/dwc/terms/country"/>
    <field index="21" term="http://rs.tdwg.org/dwc/terms/countryCode"/>
    <field index="22" term="http://rs.tdwg.org/dwc/terms/stateProvince"/>
    <field index="23" term="http://rs.tdwg.org/dwc/terms/county"/>
    <field index="24" term="http://rs.tdwg.org/dwc/terms/locality"/>
    <field index="25" term="http://rs.tdwg.org/dwc/terms/elevation"/>
    <field index="26" term="http://rs.tdwg.org/dwc/terms/elevationUnit"/>
    <field index="27" term="http://rs.tdwg.org/dwc/terms/habitat"/>
    <field index="28" term="http://rs.tdwg.org/dwc/terms/associatedTaxa"/>
    <field index="29" term="http://rs.tdwg.org/dwc/terms/occurrenceRemarks"/>
    <field index="30" term="http://rs.tdwg.org/dwc/terms/catalogNumber"/>
    <field index="31" term="http://rs.tdwg.org/dwc/terms/institutionCode"/>
    <field index="32" term="http://rs.tdwg.org/dwc/terms/collectionCode"/>
    <field index="33" term="http://purl.org/dc/terms/license"/>
    <field index="34" term="http://purl.org/dc/terms/rightsHolder"/>
  </core>
</archive>'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(meta_content)
    
    def create_eml_metadata(self, output_file):
        """Create EML metadata file"""
        
        eml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<eml:eml xmlns:eml="eml://ecoinformatics.org/eml-2.1.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="eml://ecoinformatics.org/eml-2.1.1 http://rs.gbif.org/schema/eml-gbif-profile/1.1/eml.xsd"
         packageId="orchid-atlas-{datetime.now().strftime('%Y%m%d')}" system="Five Cities Orchid Society">
    
    <dataset>
        <title>Five Cities Orchid Society Collection Database</title>
        <creator>
            <organizationName>Five Cities Orchid Society</organizationName>
            <electronicMailAddress>curator@fivecitiescalifornia.org</electronicMailAddress>
        </creator>
        
        <pubDate>{datetime.now().strftime('%Y-%m-%d')}</pubDate>
        
        <language>en</language>
        
        <abstract>
            <para>Comprehensive orchid occurrence dataset from the Five Cities Orchid Society collection,
            featuring cultivated and documented orchid specimens from around the world.
            This dataset includes taxonomic information, cultivation data, and photographic documentation
            of orchid species and hybrids.</para>
        </abstract>
        
        <keywordSet>
            <keyword>Orchidaceae</keyword>
            <keyword>orchid</keyword>
            <keyword>cultivation</keyword>
            <keyword>horticultural collection</keyword>
            <keyword>botanical</keyword>
        </keywordSet>
        
        <intellectualRights>
            <para>This work is licensed under a Creative Commons Attribution-NonCommercial (CC-BY-NC) 4.0 License.</para>
        </intellectualRights>
        
        <coverage>
            <geographicCoverage>
                <geographicDescription>Global orchid species and hybrids in cultivation</geographicDescription>
                <boundingCoordinates>
                    <westBoundingCoordinate>-180</westBoundingCoordinate>
                    <eastBoundingCoordinate>180</eastBoundingCoordinate>
                    <northBoundingCoordinate>90</northBoundingCoordinate>
                    <southBoundingCoordinate>-90</southBoundingCoordinate>
                </boundingCoordinates>
            </geographicCoverage>
            
            <temporalCoverage>
                <rangeOfDates>
                    <beginDate><calendarDate>2020-01-01</calendarDate></beginDate>
                    <endDate><calendarDate>{datetime.now().strftime('%Y-%m-%d')}</calendarDate></endDate>
                </rangeOfDates>
            </temporalCoverage>
            
            <taxonomicCoverage>
                <generalTaxonomicCoverage>Family Orchidaceae</generalTaxonomicCoverage>
                <taxonomicClassification>
                    <taxonRankName>family</taxonRankName>
                    <taxonRankValue>Orchidaceae</taxonRankValue>
                </taxonomicClassification>
            </taxonomicCoverage>
        </coverage>
        
        <contact>
            <organizationName>Five Cities Orchid Society</organizationName>
            <electronicMailAddress>curator@fivecitiescalifornia.org</electronicMailAddress>
        </contact>
    </dataset>
</eml:eml>'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(eml_content)
    
    def create_zip_archive(self, export_dir, archive_file):
        """Create ZIP archive of Darwin Core files"""
        
        with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add core files
            zipf.write(os.path.join(export_dir, 'occurrence.txt'), 'occurrence.txt')
            zipf.write(os.path.join(export_dir, 'meta.xml'), 'meta.xml')
            zipf.write(os.path.join(export_dir, 'eml.xml'), 'eml.xml')
        
        print(f"Darwin Core Archive created: {archive_file}")
        return archive_file


def export_orchid_atlas_to_dwc():
    """Main export function for command line use"""
    
    from app import app
    from models import OrchidRecord
    
    with app.app_context():
        exporter = DarwinCoreExporter()
        archive_file = exporter.export_to_dwc_archive()
        
        # Print summary
        total_records = OrchidRecord.query.count()
        print(f"✅ Exported {total_records} orchid records to Darwin Core Archive")
        print(f"📦 Archive file: {archive_file}")
        print(f"🌍 Ready for GBIF publishing!")
        
        return archive_file


if __name__ == "__main__":
    export_orchid_atlas_to_dwc()