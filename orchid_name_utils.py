#!/usr/bin/env python3
"""
Orchid Name Utilities
Handles orchid name expansions, abbreviations, and proper taxonomic formatting

Features:
- Expand common orchid abbreviations to full names
- Format hybrid names properly
- Validate taxonomic names
- Handle intergeneric hybrids
"""

import re
from typing import Optional, Tuple

class OrchidNameUtils:
    """Utility class for orchid name processing and expansion"""
    
    def __init__(self):
        # Common orchid genus abbreviations and their full names
        self.genus_abbreviations = {
            # Cattleya Alliance
            'C.': 'Cattleya',
            'Ct': 'Cattleya', 
            'Catt': 'Cattleya',
            'LC': 'Laeliacattleya',
            'Lc': 'Laeliacattleya',
            'Lc.': 'Laeliacattleya',
            'BC': 'Brassolaeliocattleya',
            'Bc': 'Brassolaeliocattleya', 
            'Bc.': 'Brassolaeliocattleya',
            'BLC': 'Brassolaeliocattleya',
            'Blc': 'Brassolaeliocattleya',
            'Blc.': 'Brassolaeliocattleya',
            'SLC': 'Sophrolaeliocattleya',
            'Slc': 'Sophrolaeliocattleya',
            'Slc.': 'Sophrolaeliocattleya',
            'Pot': 'Potinara',
            'Pot.': 'Potinara',
            'Rlc': 'Rhyncholaeliocattleya',
            'Rlc.': 'Rhyncholaeliocattleya',
            'RLC': 'Rhyncholaeliocattleya',
            'L.': 'Laelia',
            'Lae': 'Laelia',
            'Brs': 'Brassavola',
            'Brs.': 'Brassavola',
            
            # Dendrobium Alliance  
            'Den': 'Dendrobium',
            'Den.': 'Dendrobium',
            'D.': 'Dendrobium',
            
            # Oncidium Alliance
            'Onc': 'Oncidium',
            'Onc.': 'Oncidium',
            'O.': 'Oncidium',
            'Odm': 'Oncidium',
            'Odm.': 'Oncidium',
            'Colm': 'Colmanara',
            'Colm.': 'Colmanara',
            'Wilsn': 'Wilsonara',
            'Wilsn.': 'Wilsonara',
            
            # Phalaenopsis Alliance
            'Phal': 'Phalaenopsis',
            'Phal.': 'Phalaenopsis',
            'P.': 'Phalaenopsis',
            'Dtps': 'Doritaenopsis',
            'Dtps.': 'Doritaenopsis',
            
            # Vanda Alliance
            'V.': 'Vanda',
            'Vnd': 'Vanda',
            'Vnd.': 'Vanda',
            'Asctm': 'Ascocenda',
            'Asctm.': 'Ascocenda',
            
            # Paphiopedilum Alliance
            'Paph': 'Paphiopedilum',
            'Paph.': 'Paphiopedilum',
            'P.': 'Paphiopedilum',  # Context dependent
            
            # Cymbidium Alliance
            'Cym': 'Cymbidium',
            'Cym.': 'Cymbidium',
            
            # Other Common Genera
            'Masd': 'Masdevallia',
            'Masd.': 'Masdevallia',
            'Bulb': 'Bulbophyllum',
            'Bulb.': 'Bulbophyllum',
            'Max': 'Maxillaria',
            'Max.': 'Maxillaria',
            'Epi': 'Epidendrum',
            'Epi.': 'Epidendrum',
            'Enc': 'Encyclia',
            'Enc.': 'Encyclia',
            'Ctsm': 'Catasetum',
            'Ctsm.': 'Catasetum',
            'T': 'Trichocentrum',  # Sometimes abbreviated as just T
            'Trich': 'Trichocentrum',
            'Trich.': 'Trichocentrum'
        }
        
        # Intergeneric hybrid patterns
        self.intergeneric_patterns = {
            'x ': ' × ',  # Replace x with proper multiplication symbol
            ' x ': ' × ',
            'X ': ' × ',
            ' X ': ' × '
        }
    
    def expand_orchid_name(self, name: str) -> str:
        """Expand abbreviated orchid name to full name"""
        if not name:
            return name
            
        expanded_name = name
        
        # Handle quoted cultivar names (preserve them)
        cultivar_match = re.search(r'"([^"]+)"', name)
        cultivar_name = cultivar_match.group(0) if cultivar_match else ""
        base_name = name.replace(cultivar_name, "").strip()
        
        # Split name into parts
        parts = base_name.split()
        if not parts:
            return name
        
        # Check first part for abbreviation
        first_part = parts[0]
        
        # Try exact match first
        if first_part in self.genus_abbreviations:
            expanded_first = self.genus_abbreviations[first_part]
            parts[0] = expanded_first
        else:
            # Try with period added
            first_with_period = first_part + '.'
            if first_with_period in self.genus_abbreviations:
                expanded_first = self.genus_abbreviations[first_with_period]
                parts[0] = expanded_first
        
        # Reconstruct name
        expanded_base = ' '.join(parts)
        
        # Add cultivar name back if it existed
        if cultivar_name:
            expanded_name = f"{expanded_base} {cultivar_name}".strip()
        else:
            expanded_name = expanded_base
        
        # Handle intergeneric hybrid symbols
        for pattern, replacement in self.intergeneric_patterns.items():
            expanded_name = expanded_name.replace(pattern, replacement)
        
        return expanded_name.strip()
    
    def is_valid_taxonomic_name(self, name: str) -> bool:
        """Check if name represents a valid taxonomic name (not generic)"""
        if not name or name.strip() == "":
            return False
            
        # Generic names to reject
        generic_names = {
            'Unknown Orchid', 'Unknown', 'Orchid', 'Unidentified',
            'No Name', 'Unnamed', 'Mystery Orchid', 'T', 'Unknown Species'
        }
        
        if name.strip() in generic_names:
            return False
        
        # Must have at least a genus or be a recognizable hybrid
        expanded_name = self.expand_orchid_name(name)
        parts = expanded_name.split()
        
        if len(parts) == 0:
            return False
        
        # Check if first part is a recognized genus (expanded)
        first_part = parts[0]
        
        # List of valid orchid genera (partial list of common ones)
        valid_genera = {
            'Cattleya', 'Laeliacattleya', 'Brassolaeliocattleya', 'Sophrolaeliocattleya',
            'Potinara', 'Rhyncholaeliocattleya', 'Laelia', 'Brassavola',
            'Dendrobium', 'Oncidium', 'Colmanara', 'Wilsonara',
            'Phalaenopsis', 'Doritaenopsis', 'Vanda', 'Ascocenda',
            'Paphiopedilum', 'Cymbidium', 'Masdevallia', 'Bulbophyllum',
            'Maxillaria', 'Epidendrum', 'Encyclia', 'Catasetum',
            'Trichocentrum', 'Miltonia', 'Odontoglossum', 'Zygopetalum',
            'Vanilla', 'Ophrys', 'Orchis', 'Cypripedium', 'Pleione',
            'Dracula', 'Pleurothallis', 'Restrepia', 'Stelis'
        }
        
        # Check if it's a valid genus
        if first_part in valid_genera:
            return True
        
        # Check if it contains quotation marks (cultivar names)
        if '"' in expanded_name and len(parts) >= 1:
            return True
        
        # Check if it contains hybrid indicators
        if '×' in expanded_name or 'x' in expanded_name.lower():
            return True
        
        # If it has 2+ parts and looks taxonomic, accept it
        if len(parts) >= 2 and parts[0][0].isupper():
            return True
        
        return False
    
    def format_scientific_name(self, genus: str, species: str = None, 
                             cultivar: str = None) -> str:
        """Format a proper scientific name"""
        if not genus:
            return ""
        
        # Expand genus if abbreviated
        expanded_genus = self.genus_abbreviations.get(genus, genus)
        
        parts = [expanded_genus]
        
        if species:
            parts.append(species.lower())  # Species should be lowercase
        
        scientific_name = ' '.join(parts)
        
        if cultivar:
            # Remove quotes if already present
            clean_cultivar = cultivar.strip('"')
            scientific_name += f' "{clean_cultivar}"'
        
        return scientific_name
    
    def get_display_name(self, display_name: str, genus: str = None, 
                        species: str = None) -> str:
        """Get the best display name for an orchid"""
        if display_name:
            expanded = self.expand_orchid_name(display_name)
            if self.is_valid_taxonomic_name(expanded):
                return expanded
        
        # Fall back to genus/species if available
        if genus:
            return self.format_scientific_name(genus, species)
        
        return display_name or "Unknown Orchid"

# Global instance for easy importing
orchid_name_utils = OrchidNameUtils()

def expand_orchid_name(name: str) -> str:
    """Convenience function to expand orchid names"""
    return orchid_name_utils.expand_orchid_name(name)

def is_valid_taxonomic_name(name: str) -> bool:
    """Convenience function to check taxonomic validity"""
    return orchid_name_utils.is_valid_taxonomic_name(name)

if __name__ == "__main__":
    # Test the expansion
    test_names = [
        "Lc", "LC", "Ct", "Den", "Phal", "Onc",
        'Lc "Coastal Sunrise"', 'Ct walkeriana',
        'Den nobile "Spring Beauty"', 'T',
        'Unknown Orchid', 'Cattleya labiata'
    ]
    
    utils = OrchidNameUtils()
    for name in test_names:
        expanded = utils.expand_orchid_name(name)
        valid = utils.is_valid_taxonomic_name(expanded)
        print(f"{name:20} → {expanded:30} (Valid: {valid})")