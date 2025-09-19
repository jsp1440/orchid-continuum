#!/usr/bin/env python3
"""
Orchid Growth Comparison System - Analysis of same genus/species under different conditions
"""

from flask import Blueprint, render_template, request, jsonify
from app import app, db
from models import OrchidRecord
from sqlalchemy import func
from collections import defaultdict
import logging

# Create the blueprint
comparison_bp = Blueprint('comparison', __name__, url_prefix='/comparison')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@comparison_bp.route('/')
def comparison_home():
    """Main comparison page"""
    candidates = find_best_comparison_candidates()
    return render_template('comparison/home.html', candidates=candidates[:10])

@comparison_bp.route('/api/candidates')
def api_candidates():
    """API endpoint for comparison candidates"""
    candidates = find_best_comparison_candidates()
    return jsonify(candidates)

def find_best_comparison_candidates():
    """Find orchid species with the best data for growth comparison studies"""
    logger.info("🎯 FINDING BEST CANDIDATES FOR GROWTH COMPARISON")
    
    with app.app_context():
        # Group by display_name to find species with multiple specimens
        species_groups = defaultdict(list)
        all_records = OrchidRecord.query.all()
        
        for record in all_records:
            if record.display_name:
                species_key = record.display_name.strip().lower()
                species_groups[species_key].append(record)
        
        # Filter to groups with multiple specimens (for comparison)
        comparison_groups = {name: records for name, records in species_groups.items() 
                           if len(records) > 1}
        
        logger.info(f"Found {len(comparison_groups)} species with multiple specimens")
        
        candidates = []
        
        for species, records in comparison_groups.items():
            if len(records) < 2:  # Need at least 2 specimens for comparison
                continue
            
            # Score based on research value
            score = 0
            score += len(records) * 5  # More specimens = better
            
            photos = sum(1 for r in records if r.google_drive_id)
            score += photos * 10  # Photos essential for visual comparison
            
            photographers = len(set(r.photographer for r in records if r.photographer))
            score += photographers * 15  # Different growers = different conditions
            
            ai_descriptions = sum(1 for r in records if r.ai_description)
            score += ai_descriptions * 8
            
            scientific_names = sum(1 for r in records if r.scientific_name and len(r.scientific_name) > 2)
            score += scientific_names * 12
            
            candidates.append({
                'species': species,
                'specimens': len(records),
                'photos': photos,
                'photographers': photographers,
                'scientific_names': scientific_names,
                'ai_descriptions': ai_descriptions,
                'research_score': score
            })
        
        # Sort by research value
        candidates.sort(key=lambda x: x['research_score'], reverse=True)
        
        logger.info("TOP CANDIDATES FOR GROWTH COMPARISON RESEARCH:")
        logger.info("=" * 70)
        
        for i, candidate in enumerate(candidates[:15], 1):
            logger.info(f"{i:2d}. {candidate['species'].title()}")
            logger.info(f"    Research Score: {candidate['research_score']}")
            logger.info(f"    📊 {candidate['specimens']} specimens (different growing conditions)")
            logger.info(f"    📸 {candidate['photos']} with photos")
            logger.info(f"    👥 {candidate['photographers']} different growers/photographers")
            logger.info(f"    🔬 {candidate['scientific_names']} with scientific names")
            logger.info("")
        
        return candidates

if __name__ == "__main__":
    logger.info("🔬 ORCHID GROWTH COMPARISON ANALYSIS")
    logger.info("Finding species with multiple specimens for research...")
    
    candidates = find_best_comparison_candidates()
    
    logger.info(f"\n🎉 FOUND {len(candidates)} SPECIES FOR COMPARISON RESEARCH!")
    logger.info("Each 'duplicate' represents a different specimen/growing condition!")
    logger.info("Perfect for studying how orchids adapt to different environments!")
