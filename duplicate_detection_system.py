#!/usr/bin/env python3
"""
Advanced Duplicate Detection System for Five Cities Orchid Society
Analyzes new collections for duplicates with existing database
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from app import app, db
from models import OrchidRecord
from datetime import datetime

logger = logging.getLogger(__name__)

class DuplicateDetectionSystem:
    """Advanced duplicate detection for orchid collections"""
    
    def __init__(self):
        self.exact_matches = []
        self.potential_duplicates = []
        self.name_variations = []
        self.unique_records = []
    
    def normalize_genus_name(self, genus: str) -> str:
        """Normalize genus abbreviations to full names"""
        if not genus:
            return ""
        
        # Common genus abbreviations from the spreadsheet
        genus_mappings = {
            'Angcm': 'Angraecum',
            'Lc': 'Laeliocattleya', 
            'Slc': 'Sophrolaeliocattleya',
            'Blc': 'Brassolaeliocattleya',
            'Bc': 'Brassocattleya',
            'Pot': 'Potinara',
            'Epi': 'Epidendrum',
            'Epc': 'Epicattleya',
            'Ctna': 'Cattleyanthe',
            'Jum': 'Jumellea',
            'Aerangis': 'Aerangis',  # Keep full names
            'T': '',  # These seem to be tags, not genus names
            'It': '',
            'I': '',
            'C': '',
            'Ct': '',
            'St': ''
        }
        
        return genus_mappings.get(genus, genus)
    
    def extract_orchid_info_from_spreadsheet_row(self, row: Dict) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extract genus, species, cultivar from spreadsheet row"""
        try:
            # Get basic info
            genus = self.normalize_genus_name(row.get('Genus', '').strip())
            species = row.get('Species', '').strip()
            cultivar = row.get('Cultivar', '').strip()
            hybrid = row.get('Hybrid', '').strip()
            name = row.get('Name', '').strip()
            
            # Handle hybrid names
            if hybrid and 'x' in hybrid:
                if genus:
                    full_name = f"{genus} {hybrid}"
                else:
                    full_name = hybrid
            elif species:
                if genus:
                    full_name = f"{genus} {species}"
                else:
                    full_name = species
            elif cultivar:
                if genus:
                    full_name = f"{genus} {cultivar}"
                else:
                    full_name = cultivar
            else:
                full_name = name
            
            return genus, species, cultivar, full_name
            
        except Exception as e:
            logger.error(f"Error parsing spreadsheet row: {e}")
            return None, None, None, None
    
    def similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower().strip(), str2.lower().strip()).ratio()
    
    def find_existing_matches(self, genus: str, species: str, cultivar: str, full_name: str) -> List[OrchidRecord]:
        """Find potential matches in existing database"""
        matches = []
        
        try:
            # Query existing records
            query = db.session.query(OrchidRecord)
            
            # Exact genus and species match
            if genus and species:
                exact_matches = query.filter(
                    OrchidRecord.genus == genus,
                    OrchidRecord.species == species
                ).all()
                matches.extend(exact_matches)
            
            # Genus match with similar species or cultivar
            if genus:
                genus_matches = query.filter(OrchidRecord.genus == genus).all()
                for record in genus_matches:
                    # Check species similarity
                    if species and record.species:
                        if self.similarity_score(species, record.species) > 0.8:
                            matches.append(record)
                    
                    # Check cultivar similarity 
                    if cultivar and record.display_name:
                        if cultivar.lower() in record.display_name.lower():
                            matches.append(record)
            
            # Full name similarity search
            if full_name:
                all_records = query.all()
                for record in all_records:
                    if record.display_name:
                        similarity = self.similarity_score(full_name, record.display_name)
                        if similarity > 0.85:
                            matches.append(record)
            
            # Remove duplicates
            unique_matches = []
            seen_ids = set()
            for match in matches:
                if match.id not in seen_ids:
                    unique_matches.append(match)
                    seen_ids.add(match.id)
            
            return unique_matches
            
        except Exception as e:
            logger.error(f"Error finding matches: {e}")
            return []
    
    def analyze_collection_for_duplicates(self, collection_data: List[Dict]) -> Dict:
        """Analyze entire collection for duplicates"""
        
        results = {
            'total_analyzed': len(collection_data),
            'exact_matches': [],
            'potential_duplicates': [],
            'name_variations': [],
            'unique_records': [],
            'errors': []
        }
        
        try:
            print(f"🔍 ANALYZING {len(collection_data)} RECORDS FOR DUPLICATES")
            print("=" * 60)
            
            for i, row in enumerate(collection_data):
                try:
                    # Extract orchid information
                    genus, species, cultivar, full_name = self.extract_orchid_info_from_spreadsheet_row(row)
                    
                    if not full_name:
                        results['errors'].append(f"Row {i+1}: Could not extract orchid name")
                        continue
                    
                    # Find existing matches
                    matches = self.find_existing_matches(genus, species, cultivar, full_name)
                    
                    file_id = row.get('File ID', '')
                    filename = row.get('Name', '')
                    
                    entry = {
                        'row_number': i + 1,
                        'filename': filename,
                        'file_id': file_id,
                        'extracted_name': full_name,
                        'genus': genus,
                        'species': species,
                        'cultivar': cultivar,
                        'matches': []
                    }
                    
                    if matches:
                        for match in matches:
                            match_info = {
                                'id': match.id,
                                'display_name': match.display_name,
                                'genus': match.genus,
                                'species': match.species,
                                'photographer': match.photographer,
                                'similarity': self.similarity_score(full_name, match.display_name or ''),
                                'data_source': match.data_source
                            }
                            entry['matches'].append(match_info)
                        
                        # Categorize by similarity
                        highest_similarity = max(m['similarity'] for m in entry['matches'])
                        
                        if highest_similarity >= 0.95:
                            results['exact_matches'].append(entry)
                        elif highest_similarity >= 0.8:
                            results['potential_duplicates'].append(entry)
                        else:
                            results['name_variations'].append(entry)
                    else:
                        results['unique_records'].append(entry)
                    
                    # Progress logging
                    if (i + 1) % 10 == 0:
                        print(f"📊 Analyzed {i + 1}/{len(collection_data)} records...")
                
                except Exception as e:
                    results['errors'].append(f"Row {i+1}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing collection: {e}")
            results['errors'].append(f"System error: {str(e)}")
            return results

def parse_google_sheets_data() -> List[Dict]:
    """Parse the Google Sheets data from the web fetch"""
    
    # Sample data extracted from the spreadsheet (first 10 rows for testing)
    sample_data = [
        {
            'File ID': '1bUDCfCrZCLeRWgDrDQfLbDbOmXTDQHjH',
            'Name': '3799T_Angcm Longiscott.jpg',
            'Genus': 'T',
            'Species': '',
            'Hybrid': '',
            'Cultivar': 'Longiscott',
            'Display Name': 'T "Longiscott"'
        },
        {
            'File ID': '1c7yWdruGscDd9c5j1ZaIXvTbNb9SPMzF', 
            'Name': '3799_Angcm Longiscott.jpg',
            'Genus': 'Angcm',
            'Species': '',
            'Hybrid': '',
            'Cultivar': '',
            'Display Name': 'Angcm'
        },
        {
            'File ID': '1gd9BbXslt1IzAgMpeMWYQUfcJHWtHzhS',
            'Name': '2600_Angcm didieri.jpg', 
            'Genus': 'Angcm',
            'Species': 'didieri',
            'Hybrid': '',
            'Cultivar': '',
            'Display Name': 'Angcm didieri'
        },
        {
            'File ID': '1nzzA_Y3ejeT4C_ObzZEyPjn3LMQarES9',
            'Name': '2860_Angcm magdelanae.jpg',
            'Genus': 'Angcm', 
            'Species': 'magdelanae',
            'Hybrid': '',
            'Cultivar': '',
            'Display Name': 'Angcm magdelanae'
        },
        {
            'File ID': '1ZsL5Sb9LhxVDtNYGyTYuZF8eXk-IINyw',
            'Name': '2860_Angcm magdelanae x 2.jpg',
            'Genus': 'Angcm',
            'Species': 'magdelanae', 
            'Hybrid': '',
            'Cultivar': '',
            'Display Name': 'Angcm magdelanae'
        },
        {
            'File ID': '17-ck3H5VeAr-vYDT3oMvT-az1E3-X7_v',
            'Name': '3825_Aerangis Elro.jpg',
            'Genus': 'Aerangis',
            'Species': '',
            'Hybrid': '',
            'Cultivar': '',
            'Display Name': 'Aerangis'
        },
        {
            'File ID': '1rd9OYa4G4qmhFXS84uHA5M-_kQEYkJxJ',
            'Name': '3825T_Aerangis Elro.jpg',
            'Genus': 'T',
            'Species': '',
            'Hybrid': '',
            'Cultivar': 'Elro',
            'Display Name': 'T "Elro"'
        },
        {
            'File ID': '1A6rRril5Jd8ZX0BAhtHciymgKSz8pxLB',
            'Name': '3187_Lc Ken Battle.jpg',
            'Genus': 'Lc',
            'Species': '',
            'Hybrid': '',
            'Cultivar': 'Battle',
            'Display Name': 'Lc "Battle"'
        },
        {
            'File ID': '1OvQ1-9Q-VTSI3ymfWozFS7PwNdhJCEGC',
            'Name': '3187T_Lc Ken Battle.jpg',
            'Genus': 'T',
            'Species': '',
            'Hybrid': '',
            'Cultivar': 'Ken',
            'Display Name': 'T "Ken"'
        },
        {
            'File ID': '1Lrz9vkGG94zvKaGQUy9grfXVJ9NSoMu8',
            'Name': '3202_Slc Coastal Sunrise.jpg',
            'Genus': 'Slc',
            'Species': '',
            'Hybrid': '',
            'Cultivar': 'Sunrise',
            'Display Name': 'Slc "Sunrise"'
        }
    ]
    
    return sample_data

def run_duplicate_analysis():
    """Run the duplicate analysis on the new collection"""
    
    with app.app_context():
        try:
            # Get collection data
            collection_data = parse_google_sheets_data()
            
            # Initialize duplicate detector
            detector = DuplicateDetectionSystem()
            
            # Run analysis
            results = detector.analyze_collection_for_duplicates(collection_data)
            
            # Print results
            print(f"\n🎯 DUPLICATE ANALYSIS RESULTS")
            print("=" * 50)
            print(f"📊 Total Records Analyzed: {results['total_analyzed']}")
            print(f"🎯 Exact Matches: {len(results['exact_matches'])}")
            print(f"⚠️  Potential Duplicates: {len(results['potential_duplicates'])}")
            print(f"🔄 Name Variations: {len(results['name_variations'])}")
            print(f"✅ Unique Records: {len(results['unique_records'])}")
            print(f"❌ Errors: {len(results['errors'])}")
            
            # Show exact matches
            if results['exact_matches']:
                print(f"\n🎯 EXACT MATCHES FOUND:")
                for match in results['exact_matches']:
                    print(f"📁 {match['filename']}")
                    print(f"   → Extracted: {match['extracted_name']}")
                    for existing in match['matches']:
                        print(f"   ↔️  Matches: {existing['display_name']} ({existing['similarity']:.2%} similar)")
                        print(f"       Source: {existing['data_source']}, Photographer: {existing['photographer']}")
                    print()
            
            # Show potential duplicates
            if results['potential_duplicates']:
                print(f"\n⚠️  POTENTIAL DUPLICATES:")
                for dup in results['potential_duplicates']:
                    print(f"📁 {dup['filename']}")
                    print(f"   → Extracted: {dup['extracted_name']}")
                    for existing in dup['matches']:
                        print(f"   ⚠️  Similar to: {existing['display_name']} ({existing['similarity']:.2%} similar)")
                    print()
            
            # Show unique records (subset)
            if results['unique_records']:
                print(f"\n✅ UNIQUE RECORDS (first 5):")
                for unique in results['unique_records'][:5]:
                    print(f"📁 {unique['filename']} → {unique['extracted_name']}")
            
            return results
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return None

if __name__ == "__main__":
    run_duplicate_analysis()