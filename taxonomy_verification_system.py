"""
Orchid Taxonomy Verification System
Analyzes image names vs database classifications to identify misclassifications
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

# Avoid circular imports by importing in functions where needed

logger = logging.getLogger(__name__)

class TaxonomyVerificationSystem:
    """System for verifying and correcting orchid taxonomy classifications"""
    
    def __init__(self):
        # Load true orchid genera from the authoritative 34,000 taxonomy database
        self.true_genera = self._load_genera_from_database()
        self._cache_genus_lookup = {genus.lower(): genus for genus in self.true_genera}
        
        # Intergeneric hybrid designations (require × symbol)
        self.intergeneric_hybrids = {
            'Potinara': ['Brassavola', 'Cattleya', 'Laelia', 'Sophronitis'],  # 4 genera
            'Brassolaeliocattleya': ['Brassavola', 'Laelia', 'Cattleya'],     # 3 genera
            'Laeliocattleya': ['Laelia', 'Cattleya'],                         # 2 genera
            'Sophrolaeliocattleya': ['Sophronitis', 'Laelia', 'Cattleya'],   # 3 genera
            'Rhyncholaeliocattleya': ['Rhynchostele', 'Laelia', 'Cattleya'], # 3 genera
            'Cattleyonia': ['Cattleya', 'Broughtonia'],                       # 2 genera
            'Vuylstekeara': ['Cochlioda', 'Miltonia', 'Odontoglossum'],      # 3 genera
        }
        
        # Common abbreviation patterns in image filenames
        # Now dynamically updated based on database genera
        self.genus_abbreviations = self._build_abbreviation_mapping()

    def analyze_filename_vs_classification(self, orchid_record) -> Dict:
        """
        Analyze if the filename suggests a different genus than the database classification
        """
        filename_sources = [
            orchid_record.display_name,
            orchid_record.image_filename,
            orchid_record.scientific_name
        ]
        
        analysis = {
            'record_id': orchid_record.id,
            'current_genus': orchid_record.genus,
            'current_species': orchid_record.species,
            'filename_analysis': [],
            'suggested_corrections': [],
            'confidence': 0.0,
            'issue_type': None
        }
        
        for source in filename_sources:
            if not source:
                continue
                
            # Extract potential genus from filename
            filename_genus = self._extract_genus_from_text(source)
            if filename_genus:
                analysis['filename_analysis'].append({
                    'source': source,
                    'suggested_genus': filename_genus,
                    'confidence': self._calculate_confidence(source, filename_genus)
                })
        
        # Determine if there's a mismatch
        if analysis['filename_analysis']:
            most_confident = max(analysis['filename_analysis'], key=lambda x: x['confidence'])
            if most_confident['suggested_genus'] != orchid_record.genus:
                analysis['suggested_corrections'].append({
                    'from_genus': orchid_record.genus,
                    'to_genus': most_confident['suggested_genus'],
                    'reason': f"Filename suggests {most_confident['suggested_genus']}",
                    'confidence': most_confident['confidence']
                })
                analysis['confidence'] = most_confident['confidence']
                analysis['issue_type'] = self._classify_issue_type(
                    orchid_record.genus, 
                    most_confident['suggested_genus']
                )
        
        return analysis

    def _load_genera_from_database(self) -> set:
        """Load all unique genera from the authoritative OrchidTaxonomy database"""
        try:
            from models import OrchidTaxonomy
            from app import db
            
            # Get all unique genera from the database
            genera_query = db.session.query(OrchidTaxonomy.genus).distinct().all()
            genera_set = {genus[0] for genus in genera_query if genus[0]}
            
            logger.info(f"🌿 Loaded {len(genera_set)} genera from authoritative taxonomy database")
            
            # Add fallback common genera in case database is empty
            fallback_genera = {
                'Cattleya', 'Dendrobium', 'Phalaenopsis', 'Oncidium', 'Cymbidium',
                'Paphiopedilum', 'Vanda', 'Epidendrum', 'Laelia', 'Maxillaria'
            }
            
            if not genera_set:
                logger.warning("⚠️ Taxonomy database empty, using fallback genera")
                return fallback_genera
            
            return genera_set
            
        except Exception as e:
            logger.error(f"❌ Error loading genera from database: {e}")
            # Return basic fallback set
            return {
                'Cattleya', 'Dendrobium', 'Phalaenopsis', 'Oncidium', 'Cymbidium',
                'Paphiopedilum', 'Vanda', 'Epidendrum', 'Laelia', 'Maxillaria'
            }

    def _build_abbreviation_mapping(self) -> Dict[str, str]:
        """Build abbreviation mapping dynamically from database genera"""
        abbreviations = {}
        
        # Common manual abbreviations
        manual_abbrevs = {
            'Max': 'Maxillaria',
            'Den': 'Dendrobium',
            'Epi': 'Epidendrum', 
            'Cat': 'Cattleya',
            'C.': 'Cattleya',
            'L.': 'Laelia',
            'Phal': 'Phalaenopsis',
            'Onc': 'Oncidium',
            'Van': 'Vanda',
            'Paph': 'Paphiopedilum',
            'Brs': 'Brassavola',
            'Enc': 'Encyclia',
            'Bulb': 'Bulbophyllum',
            'Masd': 'Masdevallia',
            'Drac': 'Dracula'
        }
        
        # Add manual abbreviations if the genus exists in our database
        for abbrev, genus in manual_abbrevs.items():
            if genus in self.true_genera:
                abbreviations[abbrev] = genus
        
        logger.debug(f"Manual abbreviations added: {[(k, v) for k, v in abbreviations.items() if k in manual_abbrevs]}")
        
        # Only add curated abbreviations for now to avoid false positives
        # Auto-generation disabled until multi-source validation is implemented
        logger.info(f"🔤 Using curated abbreviations only: {len(abbreviations)} patterns")
        
        logger.info(f"🔤 Built {len(abbreviations)} genus abbreviations from database")
        return abbreviations

    def _extract_genus_from_text(self, text: str) -> Optional[str]:
        """Extract genus from text using various patterns"""
        if not text:
            return None
            
        # Pattern 1: Look for abbreviation patterns (including single letters and dots)
        # Matches: "C.", "Den", "Max", "PT Max", etc.
        abbrev_pattern = r'\b(?:PT\s+)?([A-Z]\.?|[A-Z][a-z]{1,4}|[A-Z][a-z]{2,})\.?\s+'
        matches = re.finditer(abbrev_pattern, text)
        
        for match in matches:
            potential_abbrev = match.group(1)
            # Try exact match first, then case-insensitive
            if potential_abbrev in self.genus_abbreviations:
                return self.genus_abbreviations[potential_abbrev]
            
            # Try with dot for single letters
            if len(potential_abbrev) == 1:
                potential_with_dot = potential_abbrev + '.'
                if potential_with_dot in self.genus_abbreviations:
                    return self.genus_abbreviations[potential_with_dot]
        
        # Pattern 2: Look for full genus names (case-insensitive with caching)
        text_lower = text.lower()
        for genus_lower, genus_proper in self._cache_genus_lookup.items():
            if re.search(rf'\b{genus_lower}\b', text_lower):
                return genus_proper
        
        # Pattern 3: Look for intergeneric hybrid names
        for hybrid in self.intergeneric_hybrids:
            if re.search(rf'\b{hybrid}\b', text, re.IGNORECASE):
                return hybrid
                
        return None

    def _calculate_confidence(self, source: str, suggested_genus: str) -> float:
        """Calculate confidence in the genus suggestion"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if it's a clear abbreviation match
        for abbrev, genus in self.genus_abbreviations.items():
            if abbrev in source and genus == suggested_genus:
                confidence += 0.3
                break
        
        # Higher confidence if genus appears early in the text
        genus_pos = source.lower().find(suggested_genus.lower())
        if genus_pos >= 0 and genus_pos < len(source) * 0.3:
            confidence += 0.2
            
        return min(confidence, 1.0)

    def _classify_issue_type(self, current_genus: str, suggested_genus: str) -> str:
        """Classify the type of taxonomy issue"""
        if current_genus in self.intergeneric_hybrids and suggested_genus in self.true_genera:
            return 'intergeneric_to_genus'
        elif current_genus in self.true_genera and suggested_genus in self.intergeneric_hybrids:
            return 'genus_to_intergeneric'
        elif current_genus in self.true_genera and suggested_genus in self.true_genera:
            return 'genus_mismatch'
        elif current_genus in self.intergeneric_hybrids and suggested_genus in self.intergeneric_hybrids:
            return 'intergeneric_mismatch'
        else:
            return 'unknown'

    def scan_all_records(self, genus_filter: str = None) -> List[Dict]:
        """Scan all records for potential taxonomy issues"""
        from models import OrchidRecord
        
        query = OrchidRecord.query
        if genus_filter:
            query = query.filter_by(genus=genus_filter)
        
        records = query.all()
        issues = []
        
        for record in records:
            analysis = self.analyze_filename_vs_classification(record)
            if analysis['suggested_corrections']:
                issues.append(analysis)
        
        return issues

    def scan_potinara_issues(self) -> List[Dict]:
        """Specifically scan Potinara records for misclassifications"""
        return self.scan_all_records('Potinara')

    def apply_corrections_safely(self, issues: List[Dict], min_confidence: float = 0.8) -> Dict:
        """Safely apply corrections using ORM instead of raw SQL"""
        from models import OrchidRecord, db
        
        results = {
            'applied': 0,
            'skipped_low_confidence': 0,
            'errors': []
        }
        
        for issue in issues:
            if not issue['suggested_corrections']:
                continue
                
            correction = issue['suggested_corrections'][0]
            if correction['confidence'] < min_confidence:
                results['skipped_low_confidence'] += 1
                continue
            
            try:
                # Use ORM for safe database updates
                record = OrchidRecord.query.get(issue['record_id'])
                if record:
                    record.genus = correction['to_genus']
                    db.session.commit()
                    results['applied'] += 1
                    logger.info(f"✅ Corrected record {issue['record_id']}: {correction['from_genus']} → {correction['to_genus']}")
            except Exception as e:
                results['errors'].append(f"Record {issue['record_id']}: {str(e)}")
                db.session.rollback()
        
        return results

    def get_taxonomy_statistics(self) -> Dict:
        """Get statistics about taxonomy issues in the database"""
        from models import OrchidRecord, db
        
        stats = {
            'total_records': OrchidRecord.query.count(),
            'by_genus': {},
            'intergeneric_hybrids': 0,
            'true_genera': 0,
            'potential_issues': 0
        }
        
        # Count by genus
        genera_counts = db.session.query(OrchidRecord.genus, db.func.count(OrchidRecord.id))\
                                 .group_by(OrchidRecord.genus)\
                                 .all()
        
        for genus, count in genera_counts:
            if genus:
                stats['by_genus'][genus] = count
                if genus in self.intergeneric_hybrids:
                    stats['intergeneric_hybrids'] += count
                elif genus in self.true_genera:
                    stats['true_genera'] += count
        
        return stats

def run_potinara_analysis():
    """Quick analysis of Potinara issues"""
    verifier = TaxonomyVerificationSystem()
    issues = verifier.scan_potinara_issues()
    
    print(f"🔍 Found {len(issues)} potential Potinara misclassifications:")
    
    genus_corrections = {}
    for issue in issues[:10]:  # Show first 10
        if issue['suggested_corrections']:
            correction = issue['suggested_corrections'][0]
            to_genus = correction['to_genus']
            genus_corrections[to_genus] = genus_corrections.get(to_genus, 0) + 1
            
            print(f"  ID {issue['record_id']}: {correction['from_genus']} → {to_genus} "
                  f"(confidence: {correction['confidence']:.2f})")
    
    print(f"\n📊 Suggested corrections by genus:")
    for genus, count in sorted(genus_corrections.items(), key=lambda x: x[1], reverse=True):
        print(f"  {genus}: {count} records")
    
    return issues

if __name__ == "__main__":
    run_potinara_analysis()