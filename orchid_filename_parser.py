#!/usr/bin/env python3
"""
Orchid Filename Parser
Parse Chris Howard and Roberta Fox collection filenames to extract genus and species
"""

import re
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Comprehensive genus abbreviation mapping based on common orchid nomenclature
GENUS_ABBREVIATIONS = {
    'B': 'Brassavola',
    'Blc': 'Brassolaeliocattleya', 
    'C': 'Cattleya',
    'Cycd': 'Cycnoches',
    'Ctna': 'Cattleytonia',
    'Dilac': 'Dialaelia',
    'E': 'Epidendrum',
    'Enc': 'Encyclia',
    'Epi': 'Epidendrum',
    'L': 'Laelia',
    'Lc': 'Laeliocattleya',
    'Pot': 'Potinara',
    'Sc': 'Sophrocattleya',
    'Slc': 'Sophrolaeliocattleya',
    'Prosthechea': 'Prosthechea',
    'Ansellia': 'Ansellia',
    'Chysis': 'Chysis',
    'Scaphoglottis': 'Scaphoglottis',
    'Scaphyglottis': 'Scaphoglottis',  # Spelling variant
}

def parse_chris_howard_filename(filename: str) -> Dict[str, Optional[str]]:
    """
    Parse Chris Howard collection filename to extract orchid information
    
    Format: [NUMBER]_[GENUS_ABBREV]_[SPECIES/HYBRID].jpg
    Examples:
    - 4_Blc_Ranger_Six_2056.jpg → Brassolaeliocattleya Ranger Six
    - 125_B_nodosa.jpg → Brassavola nodosa
    - 1644_Cycd_Roberta_Fox.jpg → Cycnoches Roberta Fox
    """
    try:
        # Remove file extension
        base_name = filename.replace('.jpg', '').replace('.JPG', '')
        
        # Pattern: NUMBER_GENUS_SPECIES_INFO
        # Handle various patterns with optional elements
        patterns = [
            # Standard pattern: NUMBER_GENUS_SPECIES
            r'^(\d+[A-Z]*T?)_([A-Za-z]+)_(.+)$',
            # Alternative pattern for complex names
            r'^(\d+)_([A-Za-z]+)\s+(.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, base_name)
            if match:
                number = match.group(1)
                genus_abbrev = match.group(2)
                species_part = match.group(3)
                
                # Expand genus abbreviation
                full_genus = GENUS_ABBREVIATIONS.get(genus_abbrev, genus_abbrev)
                
                # Clean up species name
                species_clean = clean_species_name(species_part)
                
                # Determine if it's a species or hybrid
                is_hybrid = detect_hybrid(species_clean)
                
                return {
                    'filename': filename,
                    'collection_number': number,
                    'genus_abbreviation': genus_abbrev,
                    'genus': full_genus,
                    'species': species_clean if not is_hybrid else None,
                    'hybrid_name': species_clean if is_hybrid else None,
                    'display_name': f"{full_genus} {species_clean}",
                    'is_hybrid': is_hybrid,
                    'source': 'Chris Howard Collection'
                }
        
        # Fallback - couldn't parse with standard patterns
        logger.warning(f"Could not parse filename: {filename}")
        return {
            'filename': filename,
            'genus': 'Unknown',
            'species': None,
            'display_name': f"Unknown Orchid ({filename})",
            'source': 'Chris Howard Collection',
            'parse_error': True
        }
        
    except Exception as e:
        logger.error(f"Error parsing filename {filename}: {e}")
        return {
            'filename': filename,
            'genus': 'Unknown',
            'species': None,
            'display_name': f"Parse Error ({filename})",
            'source': 'Chris Howard Collection',
            'parse_error': True
        }

def clean_species_name(species_part: str) -> str:
    """Clean and normalize species name from filename"""
    # Replace underscores with spaces
    cleaned = species_part.replace('_', ' ')
    
    # Remove common suffixes and metadata
    suffixes_to_remove = [
        r'\s+\d+$',  # Trailing numbers
        r'\s+[A-Z]$',  # Single trailing letters
        r'\s+var\s+\w+',  # Variety indicators
        r'\s+f\s+\w+',  # Form indicators
    ]
    
    for suffix_pattern in suffixes_to_remove:
        cleaned = re.sub(suffix_pattern, '', cleaned)
    
    # Clean up extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def detect_hybrid(name: str) -> bool:
    """Detect if this is a hybrid name vs species name"""
    hybrid_indicators = [
        # Capital letters in middle (hybrid names)
        r'[a-z]+[A-Z][a-z]*',
        # Quotes around cultivar names
        r"['\"].*['\"]",
        # "x" indicating cross
        r'\s+x\s+',
        # Multiple capital words (cultivar names)
        r'^[A-Z]\w+\s+[A-Z]\w+',
        # Common hybrid name patterns
        r'(Love|Beauty|Star|Dream|Fantasy|Magic)',
    ]
    
    for pattern in hybrid_indicators:
        if re.search(pattern, name):
            return True
    
    # If all lowercase or simple binomial, likely species
    if re.match(r'^[a-z]+(\s+[a-z]+)?$', name):
        return False
    
    # Default to hybrid for complex names
    return True

def parse_roberta_fox_filename(filename: str) -> Dict[str, Optional[str]]:
    """
    Parse Roberta Fox collection filename
    (Similar patterns but may have different conventions)
    """
    # For now, use similar logic to Chris Howard
    # Can be customized based on specific Roberta Fox patterns
    return parse_chris_howard_filename(filename)

def get_collection_source_from_filename(filename: str) -> str:
    """Determine which collection this filename is from"""
    # This can be enhanced with more sophisticated detection
    if 'roberta' in filename.lower() or 'fox' in filename.lower():
        return 'Roberta Fox Collection'
    else:
        return 'Chris Howard Collection'

if __name__ == "__main__":
    # Test the parser with sample filenames
    test_filenames = [
        "4_Blc_Ranger_Six_2056.jpg",
        "125_B_nodosa.jpg", 
        "1644_Cycd_Roberta_Fox.jpg",
        "1518_Enc_prismatocarpa.jpg",
        "168_L_Gouldiana.jpg"
    ]
    
    for filename in test_filenames:
        result = parse_chris_howard_filename(filename)
        print(f"\n{filename}:")
        print(f"  Genus: {result.get('genus')}")
        print(f"  Species: {result.get('species')}")  
        print(f"  Hybrid: {result.get('hybrid_name')}")
        print(f"  Display: {result.get('display_name')}")
        print(f"  Is Hybrid: {result.get('is_hybrid')}")