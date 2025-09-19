#!/usr/bin/env python3
"""
Database cleanup and orchid name parser
Extracts genus, species, and hybrid information from display names and filenames
"""

import re
from app import app, db
from models import OrchidRecord
from sqlalchemy import or_, and_

def parse_orchid_name(name):
    """
    Parse orchid name to extract genus, species, and hybrid information
    Returns: dict with genus, species, hybrid_name, clone_name, variety
    """
    if not name:
        return {}
    
    # Remove common prefixes
    name = re.sub(r'^(CT\s+|Clone\s+)', '', name, flags=re.IGNORECASE)
    
    # Common orchid abbreviations to full names
    abbreviations = {
        r'\bBc\s+': 'Brassocattleya ',
        r'\bBlc\s+': 'Brassolaeliocattleya ',
        r'\bLc\s+': 'Laeliocattleya ',
        r'\bDen\s+': 'Dendrobium ',
        r'\bBulb\s+': 'Bulbophyllum ',
        r'\bOnc\s+': 'Oncidium ',
        r'\bPaph\s+': 'Paphiopedilum ',
        r'\bPhrag\s+': 'Phragmipedium ',
        r'\bCym\s+': 'Cymbidium ',
        r'\bVan\s+': 'Vanda ',
        r'\bPhal\s+': 'Phalaenopsis ',
        r'\bCoel\s+': 'Coelogyne ',
        r'\bMasd\s+': 'Masdevallia ',
        r'\bMax\s+': 'Maxillaria ',
        r'\bEpi\s+': 'Epidendrum ',
        r'\bEnc\s+': 'Encyclia ',
        r'\bPot\s+': 'Potinara ',
        r'\bSlc\s+': 'Sophrolaeliocattleya ',
        r'\bRlc\s+': 'Rhyncholaeliocattleya '
    }
    
    # Expand abbreviations
    expanded_name = name
    for abbrev, full in abbreviations.items():
        expanded_name = re.sub(abbrev, full, expanded_name, flags=re.IGNORECASE)
    
    result = {
        'original_name': name,
        'expanded_name': expanded_name.strip(),
        'genus': None,
        'species': None,
        'hybrid_name': None,
        'clone_name': None,
        'variety': None,
        'is_hybrid': False
    }
    
    # Extract clone name (in quotes)
    clone_match = re.search(r"['\"]([^'\"]+)['\"]", expanded_name)
    if clone_match:
        result['clone_name'] = clone_match.group(1)
        expanded_name = re.sub(r"['\"][^'\"]+['\"]", '', expanded_name).strip()
    
    # Extract variety
    variety_match = re.search(r'\bvar\.?\s+(\w+)', expanded_name, re.IGNORECASE)
    if variety_match:
        result['variety'] = variety_match.group(1)
        expanded_name = re.sub(r'\bvar\.?\s+\w+', '', expanded_name, re.IGNORECASE).strip()
    
    # Split into parts
    parts = expanded_name.split()
    if len(parts) >= 1:
        # Check if it's a valid genus (starts with capital, all letters)
        potential_genus = parts[0]
        if (potential_genus and 
            len(potential_genus) > 1 and 
            potential_genus[0].isupper() and 
            potential_genus.isalpha() and
            'BOLD' not in potential_genus and
            ':' not in potential_genus):
            result['genus'] = potential_genus
            
            if len(parts) >= 2:
                # Second part could be species or hybrid name
                second_part = parts[1]
                if second_part.islower() and second_part.isalpha():
                    # It's a species
                    result['species'] = second_part
                elif len(parts) >= 2:
                    # It's likely a hybrid name
                    result['hybrid_name'] = ' '.join(parts[1:])
                    result['is_hybrid'] = True
    
    return result

def clean_genus_names():
    """Remove invalid genus names and replace with proper ones"""
    print("🧹 Starting genus cleanup...")
    
    # Get all records with invalid genus names
    invalid_records = OrchidRecord.query.filter(
        or_(
            OrchidRecord.genus.like('BOLD%'),
            OrchidRecord.genus.like('%:%'),
            OrchidRecord.genus.like('CT %'),
            OrchidRecord.genus == ''
        )
    ).all()
    
    updated_count = 0
    for record in invalid_records:
        parsed = parse_orchid_name(record.display_name)
        if parsed.get('genus'):
            record.genus = parsed['genus']
            if parsed.get('species'):
                record.species = parsed['species']
            updated_count += 1
    
    db.session.commit()
    print(f"✅ Updated {updated_count} records with proper genus names")

def parse_all_orchid_names():
    """Parse all orchid display names to fill missing metadata"""
    print("📋 Parsing all orchid names for metadata...")
    
    # Get records with missing genus or species
    records = OrchidRecord.query.filter(
        or_(
            OrchidRecord.genus.is_(None),
            OrchidRecord.species.is_(None),
            OrchidRecord.genus == ''
        )
    ).limit(1000).all()  # Process in batches
    
    updated_count = 0
    for record in records:
        parsed = parse_orchid_name(record.display_name)
        
        # Update fields if we found better data
        if parsed.get('genus') and (not record.genus or 'BOLD' in record.genus):
            record.genus = parsed['genus']
            updated_count += 1
            
        if parsed.get('species') and not record.species:
            record.species = parsed['species']
            
        if parsed.get('clone_name') and not record.clone_name:
            record.clone_name = parsed['clone_name']
            
        if parsed.get('variety') and not getattr(record, 'variety', None):
            # Add variety field if it doesn't exist
            pass
    
    db.session.commit()
    print(f"✅ Parsed and updated {updated_count} orchid records")

def get_cleanup_stats():
    """Get statistics about database cleanup progress"""
    total_records = OrchidRecord.query.count()
    
    # Count records with proper genus
    valid_genus = OrchidRecord.query.filter(
        and_(
            OrchidRecord.genus.isnot(None),
            ~OrchidRecord.genus.like('BOLD%'),
            ~OrchidRecord.genus.like('%:%'),
            OrchidRecord.genus != ''
        )
    ).count()
    
    # Count records with species
    with_species = OrchidRecord.query.filter(
        and_(
            OrchidRecord.species.isnot(None),
            OrchidRecord.species != ''
        )
    ).count()
    
    return {
        'total_records': total_records,
        'valid_genus': valid_genus,
        'with_species': with_species,
        'genus_completion': (valid_genus / total_records * 100) if total_records > 0 else 0,
        'species_completion': (with_species / total_records * 100) if total_records > 0 else 0
    }

if __name__ == '__main__':
    with app.app_context():
        print("🌺 Starting Orchid Database Cleanup")
        print("=" * 50)
        
        # Show initial stats
        initial_stats = get_cleanup_stats()
        print(f"📊 Initial stats:")
        print(f"   Total records: {initial_stats['total_records']}")
        print(f"   Valid genus: {initial_stats['valid_genus']} ({initial_stats['genus_completion']:.1f}%)")
        print(f"   With species: {initial_stats['with_species']} ({initial_stats['species_completion']:.1f}%)")
        print()
        
        # Clean up invalid genus names
        clean_genus_names()
        
        # Parse all names for metadata
        parse_all_orchid_names()
        
        # Show final stats
        final_stats = get_cleanup_stats()
        print(f"📊 Final stats:")
        print(f"   Total records: {final_stats['total_records']}")
        print(f"   Valid genus: {final_stats['valid_genus']} ({final_stats['genus_completion']:.1f}%)")
        print(f"   With species: {final_stats['with_species']} ({final_stats['species_completion']:.1f}%)")
        
        improvement = final_stats['genus_completion'] - initial_stats['genus_completion']
        print(f"🎉 Improvement: +{improvement:.1f}% genus completion")