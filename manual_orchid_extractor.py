"""
Manual orchid data extraction for when AI is unavailable
"""

import re
from models import OrchidRecord, db
from datetime import datetime

def extract_orchids_from_text(text, source):
    """Extract orchid names from text without AI"""
    orchids_found = []
    
    # Common orchid genus patterns
    orchid_genera = [
        'Aerides', 'Angraecum', 'Brassavola', 'Cattleya', 'Cymbidium', 
        'Dendrobium', 'Epidendrum', 'Laelia', 'Masdevallia', 'Maxillaria', 
        'Oncidium', 'Paphiopedilum', 'Phalaenopsis', 'Phragmipedium', 
        'Pleurothallis', 'Rhyncholaelia', 'Vanda', 'Zygopetalum'
    ]
    
    # Extract scientific names (Genus species)
    for genus in orchid_genera:
        pattern = rf'\b{genus}\s+([a-z]+(?:\s+[a-z]+)*)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for species_part in matches:
            full_name = f"{genus} {species_part.strip()}"
            if len(full_name) > 5:  # Basic validation
                orchids_found.append({
                    'display_name': full_name,
                    'scientific_name': full_name,
                    'genus': genus,
                    'species': species_part.strip().split()[0]  # First word as species
                })
    
    # Extract hybrid names (look for 'x' pattern)
    hybrid_pattern = r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\s*[\'"]([^\'\"]+)[\'"]'
    hybrid_matches = re.findall(hybrid_pattern, text)
    
    for genus, species, cultivar in hybrid_matches:
        full_name = f"{genus} {species} '{cultivar}'"
        orchids_found.append({
            'display_name': full_name,
            'scientific_name': f"{genus} {species}",
            'genus': genus,
            'species': species,
            'clone_name': cultivar
        })
    
    # Save to database
    saved_count = 0
    for orchid_data in orchids_found:
        # Check if already exists
        existing = OrchidRecord.query.filter_by(
            display_name=orchid_data['display_name'],
            ingestion_source=source
        ).first()
        
        if not existing:
            orchid = OrchidRecord(
                display_name=orchid_data['display_name'],
                scientific_name=orchid_data.get('scientific_name'),
                genus=orchid_data.get('genus'),
                species=orchid_data.get('species'),
                clone_name=orchid_data.get('clone_name'),
                ingestion_source=source,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(orchid)
            saved_count += 1
    
    try:
        db.session.commit()
        return {'processed': saved_count, 'found': len(orchids_found)}
    except Exception as e:
        db.session.rollback()
        return {'processed': 0, 'found': len(orchids_found), 'error': str(e)}

def run_manual_extraction():
    """Run manual extraction on known good content"""
    
    # Roberta Fox content we saw in the logs
    roberta_content = """
    Rhyncholaelia digbyana Citrus-like scent
    Brassavola nodosa 
    Brassavola cucullata Sweet fragrance similar to B. nodosa
    Angcm. Longiscott 'Hihimanu' Not as strong as some Angreacums, but sweet by night.
    Zygo. B. G. White 'Stonehurst' Most Zygos are intensely fragrant.
    Den. Star Sapphire Most nobile-type dendrobiums have a mild fragrance.
    Maxillaria tenuifolia Coconut
    Den. delicatum 'Brechts' Wintergreen
    Eps. Veitchii Soft scent of roses
    Den. Nestor 
    Den. kingianum
    Cattleya warscewiczii
    Cattleya walkeriana
    Epidendrum nocturnum
    Angraecum sesquipedale
    Cymbidium ensifolium
    """
    
    # Extract from Roberta Fox content
    roberta_result = extract_orchids_from_text(roberta_content, 'scrape_roberta')
    
    return {
        'roberta_fox': roberta_result
    }