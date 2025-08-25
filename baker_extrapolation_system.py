"""
Baker Culture Sheet Extrapolation System
Extends Baker expertise to additional genera and orchids through AI analysis
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from app import db
from models import OrchidRecord
from orchid_ai import extrapolate_baker_culture_data, analyze_baker_culture_data
from sqlalchemy import func, or_, and_

logger = logging.getLogger(__name__)

class BakerExtrapolationSystem:
    """System for extrapolating Baker culture knowledge to additional orchids"""
    
    def __init__(self):
        self.coverage_cache = {}
        self.extrapolation_cache = {}
    
    def analyze_coverage_gaps(self) -> Dict:
        """Analyze which genera/species could benefit from Baker extrapolation"""
        try:
            # Get all Baker culture records
            baker_records = OrchidRecord.query.filter(
                OrchidRecord.photographer.like('%Baker%')
            ).all()
            
            # Get all orchid records without culture notes
            records_needing_culture = OrchidRecord.query.filter(
                or_(
                    OrchidRecord.cultural_notes.is_(None),
                    OrchidRecord.cultural_notes == ''
                ),
                OrchidRecord.scientific_name.isnot(None)
            ).limit(1000).all()  # Limit for analysis
            
            # Analyze potential extrapolations
            extrapolation_opportunities = {
                'same_genus': 0,
                'similar_climate': 0,
                'similar_growth': 0,
                'total_candidates': len(records_needing_culture),
                'baker_sources': len(baker_records),
                'genus_coverage': {},
                'climate_coverage': {}
            }
            
            # Track covered genera and climates
            baker_genera = set()
            baker_climates = set()
            
            for baker in baker_records:
                if baker.scientific_name:
                    genus = baker.scientific_name.split(' ')[0]
                    baker_genera.add(genus)
                if baker.climate_preference:
                    baker_climates.add(baker.climate_preference)
            
            # Track covered regions
            baker_regions = set()
            for baker in baker_records:
                if baker.region:
                    baker_regions.add(baker.region)
            
            # Analyze extrapolation potential for each orphan record
            for record in records_needing_culture:
                if record.scientific_name:
                    genus = record.scientific_name.split(' ')[0]
                    
                    # Same genus opportunity
                    if genus in baker_genera:
                        extrapolation_opportunities['same_genus'] += 1
                        extrapolation_opportunities['genus_coverage'][genus] = \
                            extrapolation_opportunities['genus_coverage'].get(genus, 0) + 1
                    
                    # Same/similar region opportunity (endemic area)
                    if record.region in baker_regions:
                        extrapolation_opportunities['endemic_region'] = \
                            extrapolation_opportunities.get('endemic_region', 0) + 1
                    
                    # Similar climate opportunity
                    if record.climate_preference in baker_climates:
                        extrapolation_opportunities['similar_climate'] += 1
                        extrapolation_opportunities['climate_coverage'][record.climate_preference] = \
                            extrapolation_opportunities['climate_coverage'].get(record.climate_preference, 0) + 1
                    
                    # Similar growth habit (general orchid care patterns)
                    if record.growth_habit in ['epiphytic', 'terrestrial', 'lithophytic']:
                        extrapolation_opportunities['similar_growth'] += 1
            
            return extrapolation_opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing coverage gaps: {str(e)}")
            return {'error': str(e)}
    
    def batch_extrapolate_genus(self, genus_name: str, limit: int = 50) -> Dict:
        """Extrapolate Baker culture knowledge to all species in a genus"""
        try:
            # Find target orchids in genus without culture notes
            target_orchids = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.like(f'{genus_name} %'),
                or_(
                    OrchidRecord.cultural_notes.is_(None),
                    OrchidRecord.cultural_notes == ''
                )
            ).limit(limit).all()
            
            results = {
                'genus': genus_name,
                'processed': 0,
                'successful_extrapolations': 0,
                'failed_extrapolations': 0,
                'errors': []
            }
            
            for orchid in target_orchids:
                try:
                    extrapolated_data = extrapolate_baker_culture_data(orchid)
                    if extrapolated_data:
                        # Store extrapolated data in cultural_notes field
                        extrapolated_notes = f"BAKER EXTRAPOLATED: {json.dumps(extrapolated_data)}"
                        orchid.cultural_notes = extrapolated_notes
                        orchid.metadata_source = f"Baker extrapolation (confidence: {extrapolated_data.get('confidence_level', 0.0):.2f})"
                        
                        results['successful_extrapolations'] += 1
                        logger.info(f"Extrapolated Baker culture for {orchid.display_name}")
                    else:
                        results['failed_extrapolations'] += 1
                    
                    results['processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error extrapolating for {orchid.display_name}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Commit changes
            db.session.commit()
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch extrapolation for genus {genus_name}: {str(e)}")
            return {'error': str(e)}
    
    def extrapolate_by_climate(self, climate_preference: str, limit: int = 100) -> Dict:
        """Extrapolate Baker culture knowledge to orchids with similar climate preferences"""
        try:
            target_orchids = OrchidRecord.query.filter(
                OrchidRecord.climate_preference == climate_preference,
                or_(
                    OrchidRecord.cultural_notes.is_(None),
                    OrchidRecord.cultural_notes == ''
                )
            ).limit(limit).all()
            
            results = {
                'climate': climate_preference,
                'processed': 0,
                'successful_extrapolations': 0,
                'failed_extrapolations': 0,
                'confidence_levels': []
            }
            
            for orchid in target_orchids:
                try:
                    extrapolated_data = extrapolate_baker_culture_data(orchid)
                    if extrapolated_data and extrapolated_data.get('confidence_level', 0) > 0.3:
                        # Only apply if confidence is reasonable
                        extrapolated_notes = f"BAKER CLIMATE EXTRAPOLATED: {json.dumps(extrapolated_data)}"
                        orchid.cultural_notes = extrapolated_notes
                        
                        confidence = extrapolated_data.get('confidence_level', 0.0)
                        results['confidence_levels'].append(confidence)
                        results['successful_extrapolations'] += 1
                    else:
                        results['failed_extrapolations'] += 1
                    
                    results['processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error in climate extrapolation for {orchid.display_name}: {str(e)}")
            
            db.session.commit()
            return results
            
        except Exception as e:
            logger.error(f"Error in climate extrapolation: {str(e)}")
            return {'error': str(e)}
    
    def generate_extrapolation_report(self) -> Dict:
        """Generate comprehensive report on Baker culture extrapolation potential"""
        try:
            coverage_analysis = self.analyze_coverage_gaps()
            
            # Get top genera for extrapolation
            top_genera = sorted(
                coverage_analysis.get('genus_coverage', {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Get climate distribution
            climate_distribution = coverage_analysis.get('climate_coverage', {})
            
            report = {
                'summary': {
                    'total_candidates': coverage_analysis.get('total_candidates', 0),
                    'baker_sources': coverage_analysis.get('baker_sources', 0),
                    'same_genus_opportunities': coverage_analysis.get('same_genus', 0),
                    'climate_opportunities': coverage_analysis.get('similar_climate', 0),
                    'growth_opportunities': coverage_analysis.get('similar_growth', 0)
                },
                'top_extrapolation_genera': top_genera,
                'climate_extrapolation_potential': climate_distribution,
                'recommendations': self._generate_extrapolation_recommendations(coverage_analysis)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating extrapolation report: {str(e)}")
            return {'error': str(e)}
    
    def _generate_extrapolation_recommendations(self, coverage_analysis: Dict) -> List[str]:
        """Generate actionable recommendations for Baker culture extrapolation"""
        recommendations = []
        
        same_genus = coverage_analysis.get('same_genus', 0)
        endemic_region = coverage_analysis.get('endemic_region', 0)
        similar_climate = coverage_analysis.get('similar_climate', 0)
        total_candidates = coverage_analysis.get('total_candidates', 0)
        
        if same_genus > 0:
            recommendations.append(f"High-confidence extrapolation possible for {same_genus} orchids in same genera as Baker species")
        
        if endemic_region > 0:
            recommendations.append(f"Regional expertise extrapolation possible for {endemic_region} orchids endemic to same areas as Baker species")
        
        if similar_climate > 50:
            recommendations.append(f"Climate-based extrapolation could benefit {similar_climate} orchids with similar growing conditions")
        
        if endemic_region > same_genus:
            recommendations.append("Geographic relationships provide broader coverage than taxonomic relationships - Baker's regional expertise is highly valuable")
        
        if total_candidates > 1000:
            recommendations.append("Large-scale extrapolation system recommended for comprehensive coverage")
        
        # Genus-specific recommendations
        top_genera = coverage_analysis.get('genus_coverage', {})
        for genus, count in list(top_genera.items())[:5]:
            if count >= 10:
                recommendations.append(f"Priority genus for extrapolation: {genus} ({count} candidates)")
        
        return recommendations

# Initialize system
baker_extrapolation = BakerExtrapolationSystem()