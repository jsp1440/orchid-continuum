"""
Taxonomy Validator for Orchid Continuum
Validates and corrects orchid names against authoritative databases
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import requests

logger = logging.getLogger(__name__)

class TaxonomyValidator:
    def __init__(self):
        # Load orchid taxonomy data (we'll integrate with existing taxonomy system)
        self.genus_patterns = self._load_genus_patterns()
        self.species_patterns = self._load_species_patterns()
        self.hybrid_patterns = self._load_hybrid_patterns()
        self.common_synonyms = self._load_synonyms()
    
    def validate_orchid_name(self, submitted_name: str, genus: str = "", species: str = "") -> Dict[str, any]:
        """
        Validate and correct orchid taxonomy
        Returns validated genus, species, and confidence scores
        """
        result = {
            'original_name': submitted_name,
            'submitted_genus': genus,
            'submitted_species': species,
            'validated_genus': '',
            'validated_species': '',
            'validated_name': '',
            'confidence': 0.0,
            'is_hybrid': False,
            'validation_notes': [],
            'suggested_corrections': []
        }
        
        try:
            # Clean and parse the submitted name
            cleaned_name = self._clean_orchid_name(submitted_name)
            parsed = self._parse_orchid_name(cleaned_name)
            
            # Check if it's a hybrid
            if 'x' in cleaned_name.lower() or '×' in cleaned_name:
                result['is_hybrid'] = True
                return self._validate_hybrid(cleaned_name, result)
            
            # Validate genus
            validated_genus, genus_confidence = self._validate_genus(
                genus or parsed.get('genus', '')
            )
            
            # Validate species
            validated_species, species_confidence = self._validate_species(
                species or parsed.get('species', ''),
                validated_genus
            )
            
            result.update({
                'validated_genus': validated_genus,
                'validated_species': validated_species,
                'validated_name': f"{validated_genus} {validated_species}".strip(),
                'confidence': (genus_confidence + species_confidence) / 2
            })
            
            # Add validation notes
            if genus != validated_genus:
                result['validation_notes'].append(f"Genus corrected from '{genus}' to '{validated_genus}'")
            
            if species != validated_species:
                result['validation_notes'].append(f"Species corrected from '{species}' to '{validated_species}'")
                
            return result
            
        except Exception as e:
            logger.error(f"Error validating orchid name '{submitted_name}': {e}")
            result['validation_notes'].append(f"Validation error: {str(e)}")
            return result
    
    def _clean_orchid_name(self, name: str) -> str:
        """Clean and standardize orchid name format"""
        if not name:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', name.strip())
        
        # Handle common formatting issues
        cleaned = re.sub(r"'", "'", cleaned)  # Normalize apostrophes
        cleaned = re.sub(r'"', '"', cleaned)  # Normalize quotes
        
        return cleaned
    
    def _parse_orchid_name(self, name: str) -> Dict[str, str]:
        """Parse orchid name into components"""
        parts = name.split()
        result = {'genus': '', 'species': '', 'variety': '', 'cultivar': ''}
        
        if len(parts) >= 1:
            result['genus'] = parts[0].capitalize()
        
        if len(parts) >= 2:
            result['species'] = parts[1].lower()
        
        # Look for variety or cultivar indicators
        if len(parts) > 2:
            remaining = ' '.join(parts[2:])
            
            # Check for variety markers
            if 'var.' in remaining.lower():
                var_match = re.search(r'var\.\s+(\w+)', remaining, re.IGNORECASE)
                if var_match:
                    result['variety'] = var_match.group(1)
            
            # Check for cultivar markers (in quotes or after specific indicators)
            cultivar_match = re.search(r"['\"](.*?)['\"]", remaining)
            if cultivar_match:
                result['cultivar'] = cultivar_match.group(1)
        
        return result
    
    def _validate_genus(self, genus: str) -> Tuple[str, float]:
        """Validate genus name against known orchid genera"""
        if not genus:
            return "", 0.0
        
        # Common orchid genera (we'll expand this with the actual taxonomy database)
        known_genera = {
            'phalaenopsis': 'Phalaenopsis',
            'cattleya': 'Cattleya',
            'dendrobium': 'Dendrobium',
            'oncidium': 'Oncidium',
            'paphiopedilum': 'Paphiopedilum',
            'vanda': 'Vanda',
            'cymbidium': 'Cymbidium',
            'bulbophyllum': 'Bulbophyllum',
            'epidendrum': 'Epidendrum',
            'masdevallia': 'Masdevallia',
            'pleurothallis': 'Pleurothallis',
            'maxillaria': 'Maxillaria',
            'lycaste': 'Lycaste',
            'miltonia': 'Miltonia',
            'odontoglossum': 'Odontoglossum'
        }
        
        genus_lower = genus.lower()
        
        # Exact match
        if genus_lower in known_genera:
            return known_genera[genus_lower], 1.0
        
        # Fuzzy matching for typos
        best_match = ""
        best_score = 0.0
        
        for known_genus_lower, known_genus_proper in known_genera.items():
            score = SequenceMatcher(None, genus_lower, known_genus_lower).ratio()
            if score > best_score and score > 0.8:  # 80% similarity threshold
                best_match = known_genus_proper
                best_score = score
        
        if best_match:
            return best_match, best_score
        
        # If no good match found, return capitalized version
        return genus.capitalize(), 0.5
    
    def _validate_species(self, species: str, genus: str) -> Tuple[str, float]:
        """Validate species name within the given genus"""
        if not species:
            return "", 0.0
        
        # For now, return cleaned species name
        # In production, this would check against RHS/AOS databases
        cleaned_species = species.lower()
        
        # Remove common suffixes that might be variations
        cleaned_species = re.sub(r'\s*(var|cv|forma|f)\.*\s*.*$', '', cleaned_species)
        
        # Basic validation - species names should be lowercase and alphabetic
        if re.match(r'^[a-z]+$', cleaned_species):
            return cleaned_species, 0.9
        else:
            # Try to clean it up
            cleaned = re.sub(r'[^a-z]', '', cleaned_species.lower())
            if cleaned:
                return cleaned, 0.6
        
        return species.lower(), 0.3
    
    def _validate_hybrid(self, name: str, result: Dict) -> Dict:
        """Validate hybrid orchid names"""
        result['is_hybrid'] = True
        
        # Parse hybrid notation
        if '×' in name:
            parts = name.split('×')
        elif ' x ' in name.lower():
            parts = name.lower().split(' x ')
        else:
            parts = [name]
        
        if len(parts) == 2:
            parent1 = parts[0].strip()
            parent2 = parts[1].strip()
            
            # Validate each parent
            parent1_val = self.validate_orchid_name(parent1)
            parent2_val = self.validate_orchid_name(parent2)
            
            result.update({
                'validated_name': f"{parent1_val['validated_name']} × {parent2_val['validated_name']}",
                'confidence': (parent1_val['confidence'] + parent2_val['confidence']) / 2,
                'validation_notes': [
                    f"Hybrid of {parent1_val['validated_name']} and {parent2_val['validated_name']}"
                ]
            })
        else:
            # Complex hybrid or grex name
            result.update({
                'validated_name': name,
                'confidence': 0.7,
                'validation_notes': ['Complex hybrid - manual verification recommended']
            })
        
        return result
    
    def _load_genus_patterns(self) -> Dict:
        """Load genus patterns and corrections"""
        # This would load from the taxonomy database
        return {}
    
    def _load_species_patterns(self) -> Dict:
        """Load species patterns and corrections"""
        return {}
    
    def _load_hybrid_patterns(self) -> Dict:
        """Load hybrid patterns and corrections"""
        return {}
    
    def _load_synonyms(self) -> Dict:
        """Load common synonyms and name changes"""
        return {
            # Common genus synonyms
            'doritis': 'Phalaenopsis',
            'kingidium': 'Phalaenopsis',
            'lesliea': 'Phalaenopsis',
            # Add more as needed
        }
    
    def enhance_with_database_info(self, validated_name: str) -> Dict[str, any]:
        """Enhance validated name with additional database information"""
        enhancement = {
            'family': '',
            'subfamily': '',
            'tribe': '',
            'subtribe': '',
            'common_names': [],
            'distribution': '',
            'habitat': '',
            'conservation_status': '',
            'flowering_season': '',
            'cultural_notes': ''
        }
        
        # This would query external databases like RHS, AOS, etc.
        # For now, provide basic information based on genus
        genus = validated_name.split()[0] if validated_name else ''
        
        genus_info = {
            'Phalaenopsis': {
                'family': 'Orchidaceae',
                'subfamily': 'Epidendroideae',
                'tribe': 'Vandeae',
                'common_names': ['Moth Orchid'],
                'distribution': 'Southeast Asia, Philippines',
                'habitat': 'Epiphytic in tropical forests',
                'flowering_season': 'Variable, often winter-spring'
            },
            'Cattleya': {
                'family': 'Orchidaceae',
                'subfamily': 'Epidendroideae',
                'tribe': 'Epidendreae',
                'common_names': ['Corsage Orchid'],
                'distribution': 'Central and South America',
                'habitat': 'Epiphytic in tropical forests',
                'flowering_season': 'Variable by species'
            }
        }
        
        if genus in genus_info:
            enhancement.update(genus_info[genus])
        
        return enhancement