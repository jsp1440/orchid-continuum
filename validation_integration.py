#!/usr/bin/env python3
"""
Scraper Validation Integration System
====================================
Provides validation services for all orchid scrapers to ensure data quality
before importing records into the database.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ScraperValidationSystem:
    """Comprehensive validation system for orchid scrapers"""
    
    def __init__(self):
        self.validation_stats = {
            'total_processed': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'rejected_genera': {},
            'accepted_genera': {},
            'validation_errors': []
        }
        
        # Initialize taxonomy verifier
        self.taxonomy_verifier = None
        self._load_taxonomy_verifier()
    
    def _load_taxonomy_verifier(self):
        """Load the taxonomy verification system"""
        try:
            from taxonomy_verification_system import TaxonomyVerificationSystem
            self.taxonomy_verifier = TaxonomyVerificationSystem()
            logger.info("✅ Taxonomy verifier loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load taxonomy verifier: {e}")
            self.taxonomy_verifier = None
    
    def validate_orchid_record(self, record_data: Dict) -> Tuple[bool, Dict]:
        """
        Validate a single orchid record before database insertion
        
        Returns:
            (is_valid, validation_result)
        """
        self.validation_stats['total_processed'] += 1
        
        validation_result = {
            'is_valid': False,
            'genus': record_data.get('genus', ''),
            'species': record_data.get('species', ''),
            'display_name': record_data.get('display_name', ''),
            'issues': [],
            'corrections': [],
            'confidence': 0.0
        }
        
        try:
            # Extract genus from various fields
            genus = self._extract_genus(record_data)
            validation_result['genus'] = genus
            
            if not genus:
                validation_result['issues'].append("No genus found in record")
                self._log_validation_failure(validation_result, "missing_genus")
                return False, validation_result
            
            # Validate genus against taxonomy database
            is_valid_genus = self._validate_genus(genus)
            
            if is_valid_genus:
                # Additional validation checks
                additional_checks = self._perform_additional_validation(record_data, genus)
                
                if additional_checks['passed']:
                    validation_result['is_valid'] = True
                    validation_result['confidence'] = additional_checks['confidence']
                    self._log_validation_success(validation_result)
                    return True, validation_result
                else:
                    validation_result['issues'].extend(additional_checks['issues'])
                    self._log_validation_failure(validation_result, "additional_checks_failed")
                    return False, validation_result
            else:
                # Try to find corrections
                suggested_genus = self._suggest_genus_correction(genus)
                if suggested_genus:
                    validation_result['corrections'].append({
                        'field': 'genus',
                        'original': genus,
                        'suggested': suggested_genus,
                        'confidence': 0.8
                    })
                    validation_result['issues'].append(f"Invalid genus '{genus}', suggested: '{suggested_genus}'")
                else:
                    validation_result['issues'].append(f"Invalid genus '{genus}' - not found in orchid taxonomy")
                
                self._log_validation_failure(validation_result, "invalid_genus")
                return False, validation_result
                
        except Exception as e:
            validation_result['issues'].append(f"Validation error: {str(e)}")
            self._log_validation_failure(validation_result, "validation_error")
            logger.error(f"❌ Validation error for record: {e}")
            return False, validation_result
    
    def _extract_genus(self, record_data: Dict) -> Optional[str]:
        """Extract genus from record data using multiple strategies"""
        
        # Strategy 1: Direct genus field
        if record_data.get('genus'):
            return record_data['genus'].strip()
        
        # Strategy 2: Parse from scientific_name
        scientific_name = record_data.get('scientific_name', '')
        if scientific_name:
            parts = scientific_name.split()
            if parts:
                return parts[0].strip()
        
        # Strategy 3: Parse from display_name
        display_name = record_data.get('display_name', '')
        if display_name:
            parts = display_name.split()
            if parts:
                # Check if first word looks like a genus (capitalized)
                first_word = parts[0].strip()
                if first_word and first_word[0].isupper():
                    return first_word
        
        return None
    
    def _validate_genus(self, genus: str) -> bool:
        """Validate genus against authoritative taxonomy database"""
        if not self.taxonomy_verifier:
            logger.warning("⚠️ No taxonomy verifier available, allowing genus")
            return True
        
        try:
            # Check if genus exists in our authoritative database
            valid_genera = self.taxonomy_verifier.true_genera
            if genus in valid_genera:
                return True
            
            # For Google Drive imports, be more lenient with genus validation
            # These are likely legitimate orchid genera that may not be in our database yet
            google_drive_lenient_genera = {
                'Rhyncholaelia', 'Neolauchea', 'Barkeria', 'Bark', 'Nagiela', 
                'Guarianthe', 'Prosthechea', 'Myrmecophila', 'Rhynchostele', 
                'Microlaelia', 'Pseudolaelia', 'Schomburgkia', 'Sophronitis',
                'Pot', 'Potinara', 'Blc', 'Slc', 'Brassolaeliocattleya'
            }
            
            if genus in google_drive_lenient_genera:
                logger.info(f"🌿 Allowing genus '{genus}' for Google Drive import (lenient validation)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error validating genus {genus}: {e}")
            # Be lenient on validation errors for Google Drive imports
            return True
    
    def _suggest_genus_correction(self, invalid_genus: str) -> Optional[str]:
        """Suggest corrections for invalid genus names"""
        if not self.taxonomy_verifier:
            return None
        
        try:
            # Check abbreviation mappings
            abbreviations = self.taxonomy_verifier.genus_abbreviations
            if invalid_genus in abbreviations:
                return abbreviations[invalid_genus]
            
            # Check case-insensitive matches
            genus_lower = invalid_genus.lower()
            for valid_genus in self.taxonomy_verifier.true_genera:
                if valid_genus.lower() == genus_lower:
                    return valid_genus
            
            # Check for common patterns
            common_corrections = {
                'C': 'Cattleya',
                'Den': 'Dendrobium',
                'Phal': 'Phalaenopsis',
                'Onc': 'Oncidium',
                'Paph': 'Paphiopedilum',
                'Masd': 'Masdevallia',
                'Max': 'Maxillaria'
            }
            
            if invalid_genus in common_corrections:
                suggested = common_corrections[invalid_genus]
                if suggested in self.taxonomy_verifier.true_genera:
                    return suggested
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error suggesting correction for {invalid_genus}: {e}")
            return None
    
    def _perform_additional_validation(self, record_data: Dict, genus: str) -> Dict:
        """Perform additional validation checks beyond genus validation"""
        
        result = {
            'passed': True,
            'confidence': 1.0,
            'issues': []
        }
        
        try:
            # Determine if this is a hybrid orchid
            is_hybrid = self._is_hybrid_orchid(record_data, genus)
            
            # Check for reasonable scientific name format with different rules for hybrids
            scientific_name = record_data.get('scientific_name', '')
            if scientific_name:
                if is_hybrid:
                    if not self._validate_hybrid_name_format(scientific_name):
                        result['issues'].append("Invalid hybrid name format")
                        result['confidence'] *= 0.9  # More lenient for hybrids
                else:
                    if not self._validate_scientific_name_format(scientific_name):
                        result['issues'].append("Invalid scientific name format")
                        result['confidence'] *= 0.8
            
            # Check for suspicious content (like insect families)
            display_name = record_data.get('display_name', '')
            if self._contains_suspicious_content(display_name):
                result['issues'].append("Contains suspicious non-orchid content")
                result['confidence'] *= 0.3
                result['passed'] = False
            
            # Check data source credibility
            source = record_data.get('ingestion_source', '')
            if source and not self._is_credible_source(source):
                result['issues'].append("Data from non-credible source")
                result['confidence'] *= 0.7
            
            # Set different confidence thresholds for hybrids vs species
            confidence_threshold = 0.4 if is_hybrid else 0.6
            
            # Set passed status based on confidence
            if result['confidence'] < confidence_threshold:
                result['passed'] = False
            
        except Exception as e:
            result['issues'].append(f"Additional validation error: {str(e)}")
            result['passed'] = False
            result['confidence'] = 0.0
        
        return result
    
    def _is_hybrid_orchid(self, record_data: Dict, genus: str) -> bool:
        """Determine if this is a hybrid orchid based on multiple indicators"""
        
        # Check explicit hybrid flag
        if record_data.get('is_hybrid'):
            return True
        
        # Check for intergeneric hybrid genera
        intergeneric_hybrids = {
            'Potinara', 'Brassolaeliocattleya', 'Laeliocattleya', 
            'Sophrolaeliocattleya', 'Brassocattleya', 'Rhyncholaeliocattleya',
            'Cattleyonia', 'Vuylstekeara'
        }
        if genus in intergeneric_hybrids:
            return True
        
        # Check for hybrid indicators in names
        text_to_check = ' '.join([
            record_data.get('display_name', ''),
            record_data.get('scientific_name', ''),
            record_data.get('ai_description', '')
        ]).lower()
        
        hybrid_indicators = ['x ', ' x ', 'cross', 'hybrid', 'grex', 'breeding']
        if any(indicator in text_to_check for indicator in hybrid_indicators):
            return True
        
        # Check source indicates hybrids
        source = record_data.get('ingestion_source', '')
        if 'hybrid' in source.lower() or 'svo' in source.lower():
            return True
        
        return False
    
    def _validate_hybrid_name_format(self, scientific_name: str) -> bool:
        """Validate hybrid name format - more flexible than species names"""
        import re
        
        if not scientific_name or len(scientific_name.strip()) < 3:
            return False
        
        name = scientific_name.strip()
        
        # Allow various hybrid naming patterns:
        # 1. Traditional: Genus species
        # 2. Cultivar: Genus 'Cultivar Name'
        # 3. Cross: Genus Parent1 x Parent2
        # 4. Grex: Genus Grex Name
        # 5. Intergeneric: ComplexGenus Name
        
        hybrid_patterns = [
            r'^[A-Z][a-zA-Z]+ [A-Za-z\s\'"×x\-\.]+$',  # General hybrid pattern
            r'^[A-Z][a-zA-Z]+ \'[^\']+\'$',              # Cultivar format 'Name'
            r'^[A-Z][a-zA-Z]+ [A-Za-z\s]+ [×x] [A-Za-z\s]+$',  # Cross format Parent1 x Parent2
            r'^[A-Z][a-zA-Z]+ [A-Z][a-zA-Z\s]+$',       # Grex or cultivar names
            r'^\d+[A-Z]* [A-Z][a-zA-Z]+ [A-Za-z\s]+$'   # Numbered hybrids like "2811T Pot Name"
        ]
        
        return any(re.match(pattern, name) for pattern in hybrid_patterns)
    
    def _validate_scientific_name_format(self, scientific_name: str) -> bool:
        """Validate basic scientific name format (Genus species)"""
        import re
        
        # Basic pattern: Genus species [author]
        pattern = r'^[A-Z][a-z]+ [a-z]+.*$'
        return bool(re.match(pattern, scientific_name.strip()))
    
    def _contains_suspicious_content(self, text: str) -> bool:
        """Check for suspicious non-orchid content"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Known non-orchid families that appeared in our data
        suspicious_terms = [
            'trichogrammatidae',  # Wasp family
            'trichogramma',       # Wasp genus
            'hymenoptera',        # Insect order
            'parasitoid',         # Wasp descriptor
            'chalcidoidea',       # Wasp superfamily
            'pteromalidae',       # Another wasp family
            'braconidae',         # Another wasp family
        ]
        
        return any(term in text_lower for term in suspicious_terms)
    
    def _is_credible_source(self, source: str) -> bool:
        """Check if the ingestion source is credible"""
        credible_sources = [
            'gary_optimized_search',
            'gary_species_url', 
            'gary_json_data',
            'roberta_fox_comprehensive',
            'svo_hybrids',
            'google_drive_svo_direct',
            'google_drive_svo_hybrids',
            'google_sheets_import',
            'gbif_botanical_service',
            'manual_entry',
            'ai_analysis'
        ]
        
        return source in credible_sources
    
    def _log_validation_success(self, validation_result: Dict):
        """Log successful validation"""
        self.validation_stats['valid_records'] += 1
        genus = validation_result['genus']
        
        if genus in self.validation_stats['accepted_genera']:
            self.validation_stats['accepted_genera'][genus] += 1
        else:
            self.validation_stats['accepted_genera'][genus] = 1
    
    def _log_validation_failure(self, validation_result: Dict, reason: str):
        """Log validation failure"""
        self.validation_stats['invalid_records'] += 1
        genus = validation_result['genus']
        
        if genus in self.validation_stats['rejected_genera']:
            self.validation_stats['rejected_genera'][genus] += 1
        else:
            self.validation_stats['rejected_genera'][genus] = 1
        
        self.validation_stats['validation_errors'].append({
            'genus': genus,
            'reason': reason,
            'issues': validation_result['issues'],
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def apply_auto_corrections(self, record_data: Dict, validation_result: Dict) -> Dict:
        """Apply automatic corrections to record data where possible"""
        corrected_data = record_data.copy()
        
        for correction in validation_result.get('corrections', []):
            if correction['confidence'] >= 0.8:  # Only high-confidence corrections
                field = correction['field']
                suggested_value = correction['suggested']
                
                logger.info(f"🔧 Auto-correcting {field}: {correction['original']} → {suggested_value}")
                corrected_data[field] = suggested_value
                
                # Update scientific name if genus was corrected
                if field == 'genus' and 'scientific_name' in corrected_data:
                    original_sci_name = corrected_data['scientific_name']
                    parts = original_sci_name.split()
                    if parts:
                        parts[0] = suggested_value
                        corrected_data['scientific_name'] = ' '.join(parts)
        
        return corrected_data
    
    def get_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        
        total = self.validation_stats['total_processed']
        valid = self.validation_stats['valid_records']
        invalid = self.validation_stats['invalid_records']
        
        return {
            'summary': {
                'total_processed': total,
                'valid_records': valid,
                'invalid_records': invalid,
                'validation_rate': round((valid / total * 100) if total > 0 else 0, 1),
                'rejection_rate': round((invalid / total * 100) if total > 0 else 0, 1)
            },
            'accepted_genera': dict(sorted(
                self.validation_stats['accepted_genera'].items(), 
                key=lambda x: x[1], reverse=True
            )),
            'rejected_genera': dict(sorted(
                self.validation_stats['rejected_genera'].items(), 
                key=lambda x: x[1], reverse=True
            )),
            'recent_errors': self.validation_stats['validation_errors'][-10:],  # Last 10 errors
            'taxonomy_status': {
                'verifier_loaded': self.taxonomy_verifier is not None,
                'available_genera': len(self.taxonomy_verifier.true_genera) if self.taxonomy_verifier else 0
            }
        }
    
    def reset_stats(self):
        """Reset validation statistics"""
        self.validation_stats = {
            'total_processed': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'rejected_genera': {},
            'accepted_genera': {},
            'validation_errors': []
        }
        logger.info("📊 Validation statistics reset")


def create_validated_orchid_record(record_data: Dict, scraper_name: str = "unknown") -> Optional[Dict]:
    """
    Helper function to create a validated orchid record
    
    Usage by scrapers:
        validated_record = create_validated_orchid_record(raw_data, "gary_scraper")
        if validated_record:
            # Add to database
        else:
            # Log rejection
    """
    validator = ScraperValidationSystem()
    
    is_valid, validation_result = validator.validate_orchid_record(record_data)
    
    if is_valid:
        # Apply any auto-corrections
        corrected_data = validator.apply_auto_corrections(record_data, validation_result)
        
        # Add validation metadata
        corrected_data['validation_confidence'] = validation_result['confidence']
        corrected_data['validated_by'] = 'scraper_validation_system'
        corrected_data['validation_timestamp'] = datetime.utcnow()
        
        logger.info(f"✅ Validated record: {corrected_data.get('display_name', 'Unknown')} "
                   f"(confidence: {validation_result['confidence']:.2f})")
        
        return corrected_data
    else:
        logger.warning(f"❌ Rejected record: {record_data.get('display_name', 'Unknown')} "
                      f"- Issues: {', '.join(validation_result['issues'])}")
        return None


if __name__ == "__main__":
    # Test the validation system
    test_data = [
        {'genus': 'Cattleya', 'species': 'labiata', 'display_name': 'Cattleya labiata'},
        {'genus': 'Trichogrammatidae', 'species': 'unknown', 'display_name': 'Some wasp'},
        {'genus': 'C', 'species': 'mossiae', 'display_name': 'C. mossiae'},
        {'genus': 'InvalidGenus', 'species': 'test', 'display_name': 'Invalid test'},
    ]
    
    validator = ScraperValidationSystem()
    
    for test_record in test_data:
        result = create_validated_orchid_record(test_record, "test_scraper")
        print(f"Record: {test_record['display_name']} - Valid: {result is not None}")
    
    # Print validation report
    report = validator.get_validation_report()
    print("\n📊 Validation Report:")
    print(f"Valid: {report['summary']['valid_records']}")
    print(f"Invalid: {report['summary']['invalid_records']}")
    print(f"Validation rate: {report['summary']['validation_rate']}%")