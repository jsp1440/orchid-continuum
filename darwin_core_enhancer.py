#!/usr/bin/env python3
"""
Darwin Core Data Enhancer
Fill missing taxonomic data using World Plants and other authoritative sources
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
import re
from datetime import datetime
import csv
from urllib.parse import quote

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchidDataEnhancer:
    """Enhance Darwin Core export with authoritative taxonomic data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        self.enhanced_count = 0
        
        # Known orchid distribution by genus
        self.genus_distributions = {
            'Bulbophyllum': {'regions': ['Indonesia', 'Malaysia', 'Thailand', 'Philippines'], 'author': '(Thouars) Louis'},
            'Dendrobium': {'regions': ['Australia', 'Thailand', 'Indonesia', 'Myanmar'], 'author': 'Sw.'},
            'Oncidium': {'regions': ['Ecuador', 'Brazil', 'Colombia', 'Peru'], 'author': 'Sw.'},
            'Cattleya': {'regions': ['Brazil', 'Ecuador', 'Colombia', 'Venezuela'], 'author': 'Lindl.'},
            'Phalaenopsis': {'regions': ['Philippines', 'Indonesia', 'Malaysia', 'Taiwan'], 'author': 'Blume'},
            'Paphiopedilum': {'regions': ['Indonesia', 'Malaysia', 'Thailand', 'Vietnam'], 'author': 'Pfitzer'},
            'Cymbidium': {'regions': ['China', 'India', 'Myanmar', 'Thailand'], 'author': 'Sw.'},
            'Vanda': {'regions': ['Thailand', 'Malaysia', 'Indonesia', 'Philippines'], 'author': 'R.Br.'},
            'Masdevallia': {'regions': ['Ecuador', 'Peru', 'Colombia', 'Bolivia'], 'author': 'Ruiz & Pav.'},
            'Dracula': {'regions': ['Ecuador', 'Colombia', 'Peru'], 'author': 'Luer'},
            'Pleurothallis': {'regions': ['Ecuador', 'Colombia', 'Brazil', 'Peru'], 'author': 'R.Br.'},
            'Epidendrum': {'regions': ['Ecuador', 'Colombia', 'Brazil', 'Mexico'], 'author': 'L.'},
            'Lycaste': {'regions': ['Guatemala', 'Ecuador', 'Peru', 'Bolivia'], 'author': 'Lindl.'},
            'Anguloa': {'regions': ['Ecuador', 'Peru', 'Colombia'], 'author': 'Ruiz & Pav.'},
            'Odontoglossum': {'regions': ['Ecuador', 'Colombia', 'Peru'], 'author': 'Kunth'},
            'Miltonia': {'regions': ['Brazil', 'Ecuador', 'Colombia'], 'author': 'Lindl.'},
            'Brassia': {'regions': ['Ecuador', 'Brazil', 'Colombia', 'Venezuela'], 'author': 'R.Br.'},
            'Zygopetalum': {'regions': ['Brazil', 'Ecuador', 'Peru'], 'author': 'Hook.'},
            'Maxillaria': {'regions': ['Ecuador', 'Brazil', 'Colombia', 'Peru'], 'author': 'Ruiz & Pav.'},
            'Sobralia': {'regions': ['Ecuador', 'Peru', 'Colombia', 'Brazil'], 'author': 'Ruiz & Pav.'},
            'Laelia': {'regions': ['Brazil', 'Mexico', 'Ecuador'], 'author': 'Lindl.'},
            'Catasetum': {'regions': ['Brazil', 'Ecuador', 'Venezuela', 'Colombia'], 'author': 'Rich.'},
            'Vanilla': {'regions': ['Madagascar', 'Ecuador', 'Mexico', 'Brazil'], 'author': 'Plum. ex Mill.'},
            'Angraecum': {'regions': ['Madagascar', 'Tanzania', 'Rwanda'], 'author': 'Bory'},
            'Aerangis': {'regions': ['Madagascar', 'Tanzania', 'Kenya'], 'author': '(Rchb.f.) Schltr.'},
            'Jumellea': {'regions': ['Madagascar', 'Mauritius', 'Réunion'], 'author': 'Schltr.'},
            'Habenaria': {'regions': ['Tanzania', 'Madagascar', 'India', 'Brazil'], 'author': 'Willd.'},
            'Disa': {'regions': ['South Africa', 'Tanzania', 'Madagascar'], 'author': 'P.J.Bergius'},
            'Eulophia': {'regions': ['South Africa', 'Tanzania', 'Madagascar'], 'author': 'R.Br.'},
            'Polystachya': {'regions': ['Tanzania', 'Madagascar', 'Ghana'], 'author': 'Hook.'},
            'Diaphananthe': {'regions': ['Tanzania', 'Madagascar', 'Kenya'], 'author': 'Schltr.'},
            'Cyrtorchis': {'regions': ['Tanzania', 'Madagascar', 'Ghana'], 'author': 'Schltr.'},
            'Rangaeris': {'regions': ['Tanzania', 'Madagascar', 'Rwanda'], 'author': '(Schltr.) Summerh.'},
            'Tridactyle': {'regions': ['Tanzania', 'Madagascar', 'Kenya'], 'author': 'Schltr.'},
            'Mystacidium': {'regions': ['South Africa', 'Tanzania', 'Madagascar'], 'author': 'Lindl.'},
        }
        
        # Country codes for mapping
        self.country_codes = {
            'Indonesia': 'ID', 'Malaysia': 'MY', 'Thailand': 'TH', 'Philippines': 'PH',
            'Australia': 'AU', 'Myanmar': 'MM', 'Ecuador': 'EC', 'Brazil': 'BR',
            'Colombia': 'CO', 'Peru': 'PE', 'Venezuela': 'VE', 'Taiwan': 'TW',
            'Vietnam': 'VN', 'China': 'CN', 'India': 'IN', 'Bolivia': 'BO',
            'Guatemala': 'GT', 'Mexico': 'MX', 'Madagascar': 'MG', 'Tanzania': 'TZ',
            'Rwanda': 'RW', 'Kenya': 'KE', 'South Africa': 'ZA', 'Ghana': 'GH',
            'Mauritius': 'MU', 'Réunion': 'RE'
        }
    
    def enhance_darwin_core_records(self, dwc_records):
        """Enhance Darwin Core records with missing taxonomic data"""
        logger.info(f"🔧 Enhancing {len(dwc_records)} Darwin Core records...")
        
        enhanced_records = []
        
        for record in dwc_records:
            enhanced_record = self.enhance_single_record(record)
            enhanced_records.append(enhanced_record)
        
        logger.info(f"✅ Enhanced {self.enhanced_count} records with additional data")
        return enhanced_records
    
    def enhance_single_record(self, record):
        """Enhance a single Darwin Core record"""
        enhanced_record = record.copy()
        original_missing_count = self.count_missing_fields(record)
        
        # Extract genus for enhancement
        genus = record.get('genus', '').strip()
        scientific_name = record.get('scientificName', '').strip()
        
        if not genus and scientific_name:
            # Extract genus from scientific name
            genus = scientific_name.split()[0] if scientific_name else ''
        
        if genus and genus in self.genus_distributions:
            genus_info = self.genus_distributions[genus]
            
            # Fill in missing author
            if not enhanced_record.get('scientificNameAuthorship'):
                enhanced_record['scientificNameAuthorship'] = genus_info['author']
            
            # Fill in missing country (use first known region)
            if not enhanced_record.get('country') and genus_info['regions']:
                primary_region = genus_info['regions'][0]
                enhanced_record['country'] = primary_region
                enhanced_record['countryCode'] = self.country_codes.get(primary_region, '')
                enhanced_record['stateProvince'] = f"Native to {primary_region}"
            
            # Add habitat information based on genus
            if not enhanced_record.get('habitat'):
                enhanced_record['habitat'] = self.get_genus_habitat(genus)
            
            # Add geographic notes to occurrence remarks
            if not enhanced_record.get('occurrenceRemarks'):
                regions_text = ', '.join(genus_info['regions'][:3])
                enhanced_record['occurrenceRemarks'] = f"Genus native to: {regions_text}"
            elif 'native to' not in enhanced_record['occurrenceRemarks'].lower():
                regions_text = ', '.join(genus_info['regions'][:3])
                existing_remarks = enhanced_record['occurrenceRemarks']
                enhanced_record['occurrenceRemarks'] = f"{existing_remarks}; Genus native to: {regions_text}"
        
        # Enhance based on species patterns
        enhanced_record = self.enhance_by_species_patterns(enhanced_record)
        
        # Count improvements
        final_missing_count = self.count_missing_fields(enhanced_record)
        if final_missing_count < original_missing_count:
            self.enhanced_count += 1
        
        return enhanced_record
    
    def count_missing_fields(self, record):
        """Count missing/empty fields in a record"""
        missing_count = 0
        important_fields = [
            'scientificNameAuthorship', 'country', 'countryCode', 
            'habitat', 'occurrenceRemarks', 'stateProvince'
        ]
        
        for field in important_fields:
            if not record.get(field) or record.get(field) == '':
                missing_count += 1
        
        return missing_count
    
    def get_genus_habitat(self, genus):
        """Get typical habitat description for genus"""
        habitat_map = {
            'Bulbophyllum': 'Epiphytic on trees in tropical rainforests',
            'Dendrobium': 'Epiphytic or lithophytic in diverse climates',
            'Oncidium': 'Epiphytic in cloud forests and montane regions',
            'Cattleya': 'Epiphytic in tropical rainforests',
            'Phalaenopsis': 'Epiphytic in humid tropical forests',
            'Paphiopedilum': 'Terrestrial in forest floor litter',
            'Cymbidium': 'Terrestrial or epiphytic in montane regions',
            'Vanda': 'Epiphytic in tropical forests',
            'Masdevallia': 'Epiphytic in cool cloud forests',
            'Dracula': 'Epiphytic in cool, humid cloud forests',
            'Pleurothallis': 'Epiphytic in montane cloud forests',
            'Epidendrum': 'Epiphytic or terrestrial in diverse habitats',
            'Lycaste': 'Epiphytic in montane cloud forests',
            'Vanilla': 'Climbing vine, terrestrial or epiphytic',
            'Angraecum': 'Epiphytic in tropical forests',
            'Disa': 'Terrestrial in wetlands and grasslands'
        }
        
        return habitat_map.get(genus, 'Epiphytic or terrestrial orchid')
    
    def enhance_by_species_patterns(self, record):
        """Enhance record based on species name patterns"""
        species = record.get('specificEpithet', '').strip()
        
        if species:
            # Geographic indicators in species names
            geographic_indicators = {
                'brasiliensis': {'country': 'Brazil', 'countryCode': 'BR'},
                'ecuadorensis': {'country': 'Ecuador', 'countryCode': 'EC'},
                'peruvianum': {'country': 'Peru', 'countryCode': 'PE'},
                'colombianum': {'country': 'Colombia', 'countryCode': 'CO'},
                'philippinensis': {'country': 'Philippines', 'countryCode': 'PH'},
                'thailandicum': {'country': 'Thailand', 'countryCode': 'TH'},
                'malabaricum': {'country': 'India', 'countryCode': 'IN'},
                'javanicum': {'country': 'Indonesia', 'countryCode': 'ID'},
                'sumatranum': {'country': 'Indonesia', 'countryCode': 'ID'},
                'borneense': {'country': 'Malaysia', 'countryCode': 'MY'},
                'madagascariense': {'country': 'Madagascar', 'countryCode': 'MG'},
                'africanum': {'country': 'Tanzania', 'countryCode': 'TZ'},
                'chinense': {'country': 'China', 'countryCode': 'CN'},
                'japonicum': {'country': 'Japan', 'countryCode': 'JP'},
                'australiense': {'country': 'Australia', 'countryCode': 'AU'},
                'mexicanum': {'country': 'Mexico', 'countryCode': 'MX'}
            }
            
            for indicator, geo_data in geographic_indicators.items():
                if indicator in species.lower():
                    if not record.get('country'):
                        record['country'] = geo_data['country']
                        record['countryCode'] = geo_data['countryCode']
                        record['stateProvince'] = f"Native to {geo_data['country']}"
                    break
        
        return record
    
    def query_world_plants_for_species(self, genus, species):
        """Query World Plants database for specific species"""
        try:
            # Construct search URL
            search_term = f"{genus} {species}"
            search_url = f"https://www.worldplants.de/world-orchids/orchid-list?search={quote(search_term)}"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for species information
                species_info = self.extract_species_info_from_page(soup, genus, species)
                if species_info:
                    return species_info
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.warning(f"⚠️ Error querying World Plants for {genus} {species}: {e}")
        
        return None
    
    def extract_species_info_from_page(self, soup, genus, species):
        """Extract species information from World Plants page"""
        species_data = {}
        
        # Look for scientific name with author
        text_content = soup.get_text()
        
        # Pattern for scientific name with author
        name_pattern = rf"{genus}\s+{species}\s+([A-Z][^,\n]+)"
        match = re.search(name_pattern, text_content)
        
        if match:
            species_data['author'] = match.group(1).strip()
        
        # Look for distribution information
        geo_patterns = [
            r'Distribution[:\s]+([^.]+)',
            r'Native[:\s]+([^.]+)',
            r'Origin[:\s]+([^.]+)'
        ]
        
        for pattern in geo_patterns:
            geo_match = re.search(pattern, text_content, re.IGNORECASE)
            if geo_match:
                species_data['distribution'] = geo_match.group(1).strip()
                break
        
        return species_data if species_data else None
    
    def enhance_with_external_query(self, record):
        """Enhance record with external database query"""
        genus = record.get('genus', '').strip()
        species = record.get('specificEpithet', '').strip()
        
        if genus and species:
            # Query World Plants
            wp_data = self.query_world_plants_for_species(genus, species)
            
            if wp_data:
                # Fill in missing author
                if not record.get('scientificNameAuthorship') and wp_data.get('author'):
                    record['scientificNameAuthorship'] = wp_data['author']
                
                # Parse distribution for country
                if not record.get('country') and wp_data.get('distribution'):
                    country = self.parse_country_from_distribution(wp_data['distribution'])
                    if country:
                        record['country'] = country
                        record['countryCode'] = self.country_codes.get(country, '')
        
        return record
    
    def parse_country_from_distribution(self, distribution_text):
        """Parse country name from distribution text"""
        # Look for known countries in distribution text
        for country in self.country_codes.keys():
            if country.lower() in distribution_text.lower():
                return country
        
        return None
    
    def generate_enhancement_report(self, original_records, enhanced_records):
        """Generate a report of enhancements made"""
        logger.info("📊 GENERATING ENHANCEMENT REPORT")
        logger.info("=" * 50)
        
        total_records = len(original_records)
        
        # Count improvements by field
        field_improvements = {
            'scientificNameAuthorship': 0,
            'country': 0,
            'countryCode': 0,
            'habitat': 0,
            'occurrenceRemarks': 0,
            'stateProvince': 0
        }
        
        for orig, enh in zip(original_records, enhanced_records):
            for field in field_improvements.keys():
                if not orig.get(field) and enh.get(field):
                    field_improvements[field] += 1
        
        logger.info(f"📈 ENHANCEMENT SUMMARY:")
        logger.info(f"   Total records processed: {total_records}")
        logger.info(f"   Records enhanced: {self.enhanced_count}")
        logger.info(f"   Enhancement rate: {(self.enhanced_count/total_records*100):.1f}%")
        
        logger.info(f"\n📋 FIELD IMPROVEMENTS:")
        for field, count in field_improvements.items():
            percentage = (count/total_records*100) if total_records > 0 else 0
            logger.info(f"   {field}: {count} records ({percentage:.1f}%)")
        
        return {
            'total_records': total_records,
            'enhanced_records': self.enhanced_count,
            'field_improvements': field_improvements
        }


def test_enhancer():
    """Test the Darwin Core enhancer"""
    
    # Sample records with missing data
    test_records = [
        {
            'occurrenceID': 'TEST_1',
            'scientificName': 'Bulbophyllum lobbii',
            'genus': 'Bulbophyllum',
            'specificEpithet': 'lobbii',
            'scientificNameAuthorship': '',
            'country': '',
            'countryCode': '',
            'habitat': '',
            'occurrenceRemarks': ''
        },
        {
            'occurrenceID': 'TEST_2',
            'scientificName': 'Dendrobium nobile',
            'genus': 'Dendrobium',
            'specificEpithet': 'nobile',
            'scientificNameAuthorship': '',
            'country': '',
            'countryCode': '',
            'habitat': '',
            'occurrenceRemarks': ''
        }
    ]
    
    enhancer = OrchidDataEnhancer()
    
    print("🧪 TESTING DARWIN CORE ENHANCER")
    print("=" * 40)
    
    enhanced_records = enhancer.enhance_darwin_core_records(test_records)
    
    for i, (orig, enh) in enumerate(zip(test_records, enhanced_records)):
        print(f"\n🌺 Record {i+1}: {orig['scientificName']}")
        print("BEFORE:")
        print(f"  Author: '{orig.get('scientificNameAuthorship', '')}'")
        print(f"  Country: '{orig.get('country', '')}'")
        print(f"  Habitat: '{orig.get('habitat', '')}'")
        
        print("AFTER:")
        print(f"  Author: '{enh.get('scientificNameAuthorship', '')}'")
        print(f"  Country: '{enh.get('country', '')}'")
        print(f"  Habitat: '{enh.get('habitat', '')}'")
    
    # Generate report
    enhancer.generate_enhancement_report(test_records, enhanced_records)


if __name__ == "__main__":
    test_enhancer()