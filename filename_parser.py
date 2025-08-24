"""
Advanced filename parsing utilities for orchid names
Handles conversions from abbreviations to full genus/species names
Includes metadata extraction and intelligent parsing algorithms
Enhanced for Ron Parsons and major orchid database integration
"""
import re
import os
from typing import Dict, Tuple, Optional, List
from PIL import Image
from PIL.ExifTags import TAGS
import logging
from datetime import datetime

# Comprehensive genus abbreviation mapping
GENUS_ABBREVIATIONS = {
    # Cattleya Alliance
    'c.': 'Cattleya',
    'cat.': 'Cattleya',
    'cattleya': 'Cattleya',
    'bc.': 'Brassolaeliacattleya',
    'blc.': 'Brassolaeliacattleya',
    'lc.': 'Laeliocattleya',
    'slc.': 'Sophrolaeliacattleya',
    'rlc.': 'Rhyncholaeliacattleya',
    'pot.': 'Potinara',
    'brs.': 'Brassavola',
    'l.': 'Laelia',
    'laelia': 'Laelia',
    'rsc.': 'Rhyncosophrocattleya',
    
    # Dendrobium Alliance  
    'den.': 'Dendrobium',
    'dend.': 'Dendrobium',
    'dendrobium': 'Dendrobium',
    
    # Oncidium Alliance
    'onc.': 'Oncidium',
    'oncidium': 'Oncidium',
    'milt.': 'Miltonia',
    'miltonia': 'Miltonia',
    'odm.': 'Oncidium',
    'odont.': 'Odontoglossum',
    'odontoglossum': 'Odontoglossum',
    'colm.': 'Colmanara',
    'beall.': 'Beallara',
    'wilso.': 'Wilsonara',
    
    # Paphiopedilum Alliance
    'paph.': 'Paphiopedilum',
    'paphiopedilum': 'Paphiopedilum',
    'phrag.': 'Phragmipedium',
    'phragmipedium': 'Phragmipedium',
    'cypripedium': 'Cypripedium',
    'cyp.': 'Cypripedium',
    
    # Phalaenopsis Alliance
    'phal.': 'Phalaenopsis',
    'phalaenopsis': 'Phalaenopsis',
    'dtps.': 'Doritaenopsis',
    'dor.': 'Doritis',
    
    # Vandaceous Alliance
    'v.': 'Vanda',
    'vanda': 'Vanda',
    'asctm.': 'Ascocentrum',
    'ascda.': 'Ascocenda',
    'rhy.': 'Rhynchostylis',
    'aerides': 'Aerides',
    'aer.': 'Aerides',
    'neof.': 'Neofinetia',
    'renanthera': 'Renanthera',
    'ren.': 'Renanthera',
    
    # Other Popular Genera
    'cymbidium': 'Cymbidium',
    'cym.': 'Cymbidium',
    'bulb.': 'Bulbophyllum',
    'bulbophyllum': 'Bulbophyllum',
    'masd.': 'Masdevallia',
    'masdevallia': 'Masdevallia',
    'pleur.': 'Pleurothallis',
    'pleurothallis': 'Pleurothallis',
    'dracula': 'Dracula',
    'drac.': 'Dracula',
    'coelogyne': 'Coelogyne',
    'coel.': 'Coelogyne',
    'lycaste': 'Lycaste',
    'lyc.': 'Lycaste',
    'zygopetalum': 'Zygopetalum',
    'zygo.': 'Zygopetalum',
    'maxillaria': 'Maxillaria',
    'max.': 'Maxillaria',
    'epidendrum': 'Epidendrum',
    'epi.': 'Epidendrum',
    'encyclia': 'Encyclia',
    'enc.': 'Encyclia',
    'stanhopea': 'Stanhopea',
    'stan.': 'Stanhopea',
    'vanilla': 'Vanilla',
    'van.': 'Vanilla',
}

# Common species patterns and corrections
SPECIES_CORRECTIONS = {
    # Common misspellings and variations
    'ancep': 'anceps',
    'purpurata': 'purpurata',
    'warscewiczii': 'warscewiczii',
    'nobile': 'nobile',
    'phalaenopsis': 'phalaenopsis',
    'amabilis': 'amabilis',
    'stuartiana': 'stuartiana',
    'schilleriana': 'schilleriana',
    'equestris': 'equestris',
}

# Hybrid indicators
HYBRID_INDICATORS = [
    'x', '×', 'hybrid', 'grex', 'clone'
]

class OrchidFilenameParser:
    """Parse orchid names from filenames"""
    
    def __init__(self):
        self.genus_map = {k.lower(): v for k, v in GENUS_ABBREVIATIONS.items()}
        self.species_corrections = {k.lower(): v for k, v in SPECIES_CORRECTIONS.items()}
    
    def parse_filename(self, filename: str) -> Dict[str, any]:
        """
        Parse orchid information from filename
        
        Args:
            filename: Original filename (e.g., "l.anceps.PNG", "C. warscewiczii var alba.jpg")
            
        Returns:
            Dict with parsed information and confidence score
        """
        # Remove file extension and clean filename
        clean_name = self._clean_filename(filename)
        
        # Try different parsing strategies
        strategies = [
            self._parse_abbreviated_format,
            self._parse_full_format,
            self._parse_hybrid_format,
            self._parse_loose_format
        ]
        
        best_result = None
        best_confidence = 0.0
        
        for strategy in strategies:
            try:
                result = strategy(clean_name)
                if result and result.get('confidence', 0) > best_confidence:
                    best_result = result
                    best_confidence = result['confidence']
            except Exception:
                continue
        
        return best_result or self._create_empty_result(clean_name)
    
    def _clean_filename(self, filename: str) -> str:
        """Clean and normalize filename"""
        # Remove file extension
        name = re.sub(r'\.[a-zA-Z0-9]+$', '', filename)
        
        # Remove common photo suffixes
        name = re.sub(r'[-_]?\d+$', '', name)  # Remove trailing numbers
        name = re.sub(r'[-_]?(img|image|photo|pic|orchid|flower)[-_]?\d*$', '', name, flags=re.IGNORECASE)
        
        # Replace underscores and hyphens with spaces
        name = re.sub(r'[-_]+', ' ', name)
        
        # Clean up multiple spaces
        name = re.sub(r'\s+', ' ', name.strip())
        
        return name
    
    def _parse_abbreviated_format(self, name: str) -> Optional[Dict]:
        """Parse abbreviated format like 'L. anceps' or 'C. warscewiczii var alba'"""
        # Pattern: genus_abbrev. species [var/forma variety]
        pattern = r'^([a-zA-Z]+\.?)\s+([a-zA-Z]+)(?:\s+(var\.?|forma?\.?|f\.?)\s+([a-zA-Z]+))?'
        match = re.match(pattern, name, re.IGNORECASE)
        
        if not match:
            return None
        
        genus_abbrev = match.group(1).lower().rstrip('.')
        species = match.group(2).lower()
        variety_type = match.group(3)
        variety = match.group(4)
        
        # Look up full genus name
        if genus_abbrev + '.' in self.genus_map:
            genus = self.genus_map[genus_abbrev + '.']
        elif genus_abbrev in self.genus_map:
            genus = self.genus_map[genus_abbrev]
        else:
            return None
        
        # Correct species if needed
        if species in self.species_corrections:
            species = self.species_corrections[species]
        
        confidence = 0.9 if genus_abbrev + '.' in self.genus_map else 0.7
        
        result = {
            'genus': genus,
            'species': species,
            'variety': variety.lower() if variety else None,
            'variety_type': variety_type.lower().rstrip('.') if variety_type else None,
            'is_hybrid': False,
            'confidence': confidence,
            'parsing_method': 'abbreviated_format'
        }
        
        return result
    
    def _parse_full_format(self, name: str) -> Optional[Dict]:
        """Parse full format like 'Cattleya warscewiczii var alba'"""
        # Pattern: Genus species [var/forma variety]
        pattern = r'^([A-Z][a-z]+)\s+([a-z]+)(?:\s+(var\.?|forma?\.?|f\.?)\s+([a-zA-Z]+))?'
        match = re.match(pattern, name)
        
        if not match:
            return None
        
        genus = match.group(1)
        species = match.group(2).lower()
        variety_type = match.group(3)
        variety = match.group(4)
        
        # Verify genus is known
        genus_lower = genus.lower()
        known_genus = any(v.lower() == genus_lower for v in GENUS_ABBREVIATIONS.values())
        
        if not known_genus:
            return None
        
        # Correct species if needed
        if species in self.species_corrections:
            species = self.species_corrections[species]
        
        result = {
            'genus': genus,
            'species': species,
            'variety': variety.lower() if variety else None,
            'variety_type': variety_type.lower().rstrip('.') if variety_type else None,
            'is_hybrid': False,
            'confidence': 0.8,
            'parsing_method': 'full_format'
        }
        
        return result
    
    def _parse_hybrid_format(self, name: str) -> Optional[Dict]:
        """Parse hybrid format like 'Cattleya Chocolate Drop' or 'Lc. Mini Purple'"""
        # Check for hybrid indicators
        has_hybrid_indicator = any(indicator in name.lower() for indicator in HYBRID_INDICATORS)
        
        # Pattern: [Genus_abbrev.] Hybrid Name
        patterns = [
            r'^([a-zA-Z]+\.?)\s+([A-Z][a-zA-Z\s]+)$',  # Abbreviated + hybrid name
            r'^([A-Z][a-z]+)\s+([A-Z][a-zA-Z\s]+)$',   # Full genus + hybrid name
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name)
            if not match:
                continue
            
            genus_part = match.group(1)
            hybrid_name = match.group(2).strip()
            
            # Determine if it's likely a hybrid (capitalized words typically indicate hybrids)
            is_likely_hybrid = (
                has_hybrid_indicator or
                len(hybrid_name.split()) > 1 or
                bool(any(word[0].isupper() for word in hybrid_name.split()))
            )
            
            if not is_likely_hybrid:
                continue
            
            # Resolve genus
            genus = None
            if genus_part.endswith('.'):
                genus_abbrev = genus_part.lower()
                genus = self.genus_map.get(genus_abbrev)
            elif genus_part[0].isupper():
                genus = genus_part
                genus_lower = genus.lower()
                known_genus = any(v.lower() == genus_lower for v in GENUS_ABBREVIATIONS.values())
                if not known_genus:
                    continue
            
            if not genus:
                continue
            
            result = {
                'genus': genus,
                'species': None,
                'variety': None,
                'variety_type': None,
                'hybrid_name': hybrid_name,
                'is_hybrid': True,
                'confidence': 0.7,
                'parsing_method': 'hybrid_format'
            }
            
            return result
        
        return None
    
    def _parse_loose_format(self, name: str) -> Optional[Dict]:
        """Attempt loose parsing for difficult cases"""
        words = name.split()
        if len(words) < 2:
            return None
        
        # Try to find genus in first word
        first_word = words[0].lower().rstrip('.')
        genus = None
        
        # Check abbreviations first
        if first_word + '.' in self.genus_map:
            genus = self.genus_map[first_word + '.']
        elif first_word in self.genus_map:
            genus = self.genus_map[first_word]
        elif words[0][0].isupper():  # Might be full genus name
            genus = words[0]
        
        if genus:
            # Try to identify species in second word
            second_word = words[1].lower()
            if second_word in self.species_corrections:
                second_word = self.species_corrections[second_word]
            
            # Check if it looks like a species (all lowercase) or hybrid (mixed case)
            is_hybrid = bool(words[1][0].isupper() or len(words) > 2)
            
            result = {
                'genus': genus,
                'species': second_word if not is_hybrid else None,
                'variety': None,
                'variety_type': None,
                'hybrid_name': ' '.join(words[1:]) if is_hybrid else None,
                'is_hybrid': is_hybrid,
                'confidence': 0.5,
                'parsing_method': 'loose_format'
            }
            
            return result
        
        return None
    
    def _create_empty_result(self, original_name: str) -> Dict:
        """Create empty result for unparseable names"""
        return {
            'genus': None,
            'species': None,
            'variety': None,
            'variety_type': None,
            'hybrid_name': None,
            'is_hybrid': False,
            'confidence': 0.0,
            'parsing_method': 'failed',
            'original_name': original_name
        }
    
    def format_scientific_name(self, parsed_data: Dict) -> str:
        """Format parsed data into proper scientific name"""
        if not parsed_data.get('genus'):
            return parsed_data.get('original_name', 'Unknown')
        
        if parsed_data.get('is_hybrid'):
            hybrid_name = parsed_data.get('hybrid_name', '')
            return f"{parsed_data['genus']} {hybrid_name}"
        
        parts = [parsed_data['genus']]
        
        if parsed_data.get('species'):
            parts.append(parsed_data['species'])
        
        if parsed_data.get('variety_type') and parsed_data.get('variety'):
            parts.extend([parsed_data['variety_type'], parsed_data['variety']])
        
        return ' '.join(parts)

# Global parser instance
orchid_parser = OrchidFilenameParser()

def parse_orchid_filename(filename: str) -> Dict[str, any]:
    """
    Convenience function to parse orchid filename
    
    Args:
        filename: The original filename
        
    Returns:
        Dictionary with parsed orchid information
    """
    return orchid_parser.parse_filename(filename)

def test_parser():
    """Test function to validate parser with common examples"""
    test_cases = [
        "l.anceps.PNG",
        "C. warscewiczii var alba.jpg", 
        "Dendrobium nobile.jpeg",
        "Phal. Brother Sara Gold.png",
        "Cattleya Chocolate Drop.JPG",
        "onc. Sharry Baby.tiff",
        "Laelia anceps var alba.png",
        "Bc. Maikai Mayumi.jpg",
        "paph. Maudiae.png",
        "Vanda coerulea.jpeg"
    ]
    
    for test_case in test_cases:
        result = parse_orchid_filename(test_case)
        scientific_name = orchid_parser.format_scientific_name(result)
        print(f"{test_case:30} -> {scientific_name:30} (confidence: {result['confidence']:.2f})")

def extract_metadata_from_image(image_path: str) -> Dict[str, str]:
    """Extract EXIF metadata from image file for orchid identification"""
    metadata = {}
    
    try:
        # Extract filename-based information first
        filename = os.path.basename(image_path)
        metadata['filename'] = filename
        metadata['filename_analysis'] = analyze_filename_for_orchid_name(filename)
        
        # For web URLs, skip EXIF extraction
        if image_path.startswith('http'):
            metadata['source'] = 'web_url'
            return metadata
            
    except Exception as e:
        logging.warning(f"Error extracting metadata from {image_path}: {e}")
        metadata['error'] = str(e)
    
    return metadata

def analyze_filename_for_orchid_name(filename: str) -> Dict[str, Optional[str]]:
    """Advanced filename analysis specifically for orchid names"""
    analysis = {
        'detected_genus': None,
        'detected_species': None,
        'confidence': 0.0,
        'parsing_method': None,
        'full_parsed_name': None
    }
    
    # Use existing parser
    parsed = parse_orchid_filename(filename)
    
    if parsed.get('genus'):
        analysis['detected_genus'] = parsed['genus']
        analysis['detected_species'] = parsed.get('species')
        analysis['confidence'] = parsed.get('confidence', 0.0)
        analysis['parsing_method'] = 'existing_parser'
        
        if parsed.get('genus') and parsed.get('species'):
            analysis['full_parsed_name'] = f"{parsed['genus']} {parsed['species']}"
    
    return analysis

if __name__ == "__main__":
    test_parser()