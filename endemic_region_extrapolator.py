"""
Endemic Region Extrapolator for Baker Culture Sheets
Specifically handles geographic/regional relationships for orchid culture extrapolation
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from app import db
from models import OrchidRecord
from sqlalchemy import func, or_, and_

logger = logging.getLogger(__name__)

class EndemicRegionExtrapolator:
    """Specialized system for applying Baker culture knowledge based on endemic geographic relationships"""
    
    def __init__(self):
        self.regional_mappings = self._build_regional_mappings()
    
    def _build_regional_mappings(self) -> Dict:
        """Build geographic region mappings for broader extrapolation"""
        return {
            'South America': {
                'countries': ['brazil', 'ecuador', 'colombia', 'peru', 'venezuela', 'guyana', 'bolivia'],
                'keywords': ['south america', 'amazonia', 'andes', 'tropical america'],
                'climate_zones': ['tropical', 'subtropical', 'montane']
            },
            'Central America': {
                'countries': ['costa rica', 'panama', 'guatemala', 'honduras', 'nicaragua', 'mexico'],
                'keywords': ['central america', 'mesoamerica'],
                'climate_zones': ['tropical', 'cloud forest', 'montane']
            },
            'Southeast Asia': {
                'countries': ['thailand', 'vietnam', 'malaysia', 'indonesia', 'philippines', 'myanmar'],
                'keywords': ['southeast asia', 'indochina', 'maritime'],
                'climate_zones': ['tropical', 'monsoon']
            },
            'Madagascar & Africa': {
                'countries': ['madagascar', 'kenya', 'tanzania', 'south africa', 'cameroon'],
                'keywords': ['africa', 'malagasy'],
                'climate_zones': ['tropical', 'subtropical', 'temperate']
            },
            'Oceania': {
                'countries': ['australia', 'new guinea', 'papua', 'solomon islands'],
                'keywords': ['oceania', 'pacific', 'australasia'],
                'climate_zones': ['tropical', 'temperate']
            }
        }
    
    def analyze_regional_coverage(self) -> Dict:
        """Analyze Baker culture sheet coverage by geographic region"""
        try:
            # Get all Baker records with regions
            baker_records = OrchidRecord.query.filter(
                OrchidRecord.photographer.like('%Baker%'),
                OrchidRecord.region.isnot(None)
            ).all()
            
            # Group by specific regions
            regional_coverage = {}
            broader_coverage = {}
            
            for record in baker_records:
                region = record.region
                if region:
                    # Specific region
                    regional_coverage[region] = regional_coverage.get(region, 0) + 1
                    
                    # Broader geographic categorization
                    broader_region = self._categorize_region(region)
                    if broader_region:
                        broader_coverage[broader_region] = broader_coverage.get(broader_region, 0) + 1
            
            return {
                'specific_regions': regional_coverage,
                'broader_regions': broader_coverage,
                'total_baker_sheets': len(baker_records)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing regional coverage: {str(e)}")
            return {'error': str(e)}
    
    def _categorize_region(self, region_text: str) -> Optional[str]:
        """Categorize a specific region into broader geographic areas"""
        if not region_text:
            return None
        
        region_lower = region_text.lower()
        
        for broader_region, data in self.regional_mappings.items():
            # Check countries
            if any(country in region_lower for country in data['countries']):
                return broader_region
            
            # Check keywords
            if any(keyword in region_lower for keyword in data['keywords']):
                return broader_region
        
        return None
    
    def find_endemic_extrapolation_candidates(self, region: str, limit: int = 100) -> Dict:
        """Find orchids endemic to same region as Baker species for extrapolation"""
        try:
            # Find Baker records from this region
            baker_records = OrchidRecord.query.filter(
                OrchidRecord.photographer.like('%Baker%'),
                OrchidRecord.region == region
            ).all()
            
            if not baker_records:
                return {'error': f'No Baker culture sheets found for region: {region}'}
            
            # Find candidate orchids from same region without culture notes
            candidates = OrchidRecord.query.filter(
                OrchidRecord.region == region,
                OrchidRecord.photographer.notlike('%Baker%'),
                or_(
                    OrchidRecord.cultural_notes.is_(None),
                    OrchidRecord.cultural_notes == ''
                )
            ).limit(limit).all()
            
            # Analyze genus diversity
            baker_genera = set()
            candidate_genera = set()
            
            for baker in baker_records:
                if baker.scientific_name:
                    genus = baker.scientific_name.split(' ')[0]
                    baker_genera.add(genus)
            
            for candidate in candidates:
                if candidate.scientific_name:
                    genus = candidate.scientific_name.split(' ')[0]
                    candidate_genera.add(genus)
            
            # Calculate cross-genus applicability
            cross_genus_candidates = [c for c in candidates if c.scientific_name and 
                                    c.scientific_name.split(' ')[0] not in baker_genera]
            
            return {
                'region': region,
                'baker_sources': len(baker_records),
                'baker_genera': list(baker_genera),
                'total_candidates': len(candidates),
                'cross_genus_candidates': len(cross_genus_candidates),
                'candidate_genera': list(candidate_genera),
                'samples': [
                    {
                        'name': c.display_name,
                        'scientific_name': c.scientific_name,
                        'genus': c.scientific_name.split(' ')[0] if c.scientific_name else None
                    } for c in candidates[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error finding endemic candidates for {region}: {str(e)}")
            return {'error': str(e)}
    
    def batch_extrapolate_region(self, region: str, limit: int = 50) -> Dict:
        """Apply Baker culture knowledge to all orchids from same endemic region"""
        try:
            from orchid_ai import extrapolate_baker_culture_data
            
            # Get candidates
            candidates_info = self.find_endemic_extrapolation_candidates(region, limit)
            if 'error' in candidates_info:
                return candidates_info
            
            # Get actual candidate records
            candidate_records = OrchidRecord.query.filter(
                OrchidRecord.region == region,
                OrchidRecord.photographer.notlike('%Baker%'),
                or_(
                    OrchidRecord.cultural_notes.is_(None),
                    OrchidRecord.cultural_notes == ''
                )
            ).limit(limit).all()
            
            results = {
                'region': region,
                'processed': 0,
                'successful_extrapolations': 0,
                'failed_extrapolations': 0,
                'cross_genus_successes': 0,
                'confidence_levels': [],
                'genus_breakdown': {}
            }
            
            for orchid in candidate_records:
                try:
                    # Apply regional extrapolation
                    extrapolated_data = extrapolate_baker_culture_data(orchid)
                    
                    if extrapolated_data and extrapolated_data.get('confidence_level', 0) > 0.2:
                        # Store with regional emphasis
                        extrapolated_notes = f"BAKER REGIONAL EXTRAPOLATED ({region}): {json.dumps(extrapolated_data)}"
                        orchid.cultural_notes = extrapolated_notes
                        orchid.metadata_source = f"Baker regional extrapolation - {region}"
                        
                        confidence = extrapolated_data.get('confidence_level', 0.0)
                        results['confidence_levels'].append(confidence)
                        results['successful_extrapolations'] += 1
                        
                        # Track genus
                        if orchid.scientific_name:
                            genus = orchid.scientific_name.split(' ')[0]
                            results['genus_breakdown'][genus] = results['genus_breakdown'].get(genus, 0) + 1
                            
                            # Check if cross-genus
                            baker_genera = candidates_info.get('baker_genera', [])
                            if genus not in baker_genera:
                                results['cross_genus_successes'] += 1
                        
                        logger.info(f"Regional extrapolation success for {orchid.display_name} (confidence: {confidence:.2f})")
                    else:
                        results['failed_extrapolations'] += 1
                    
                    results['processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error in regional extrapolation for {orchid.display_name}: {str(e)}")
                    results['failed_extrapolations'] += 1
                    results['processed'] += 1
            
            # Commit changes
            db.session.commit()
            
            # Calculate statistics
            if results['confidence_levels']:
                results['average_confidence'] = sum(results['confidence_levels']) / len(results['confidence_levels'])
            else:
                results['average_confidence'] = 0.0
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch regional extrapolation: {str(e)}")
            return {'error': str(e)}
    
    def generate_regional_extrapolation_report(self) -> Dict:
        """Generate comprehensive report on regional extrapolation opportunities"""
        try:
            coverage = self.analyze_regional_coverage()
            
            if 'error' in coverage:
                return coverage
            
            # Analyze top regions for extrapolation
            specific_regions = coverage.get('specific_regions', {})
            broader_regions = coverage.get('broader_regions', {})
            
            # Find best regional opportunities
            regional_opportunities = []
            
            for region, baker_count in sorted(specific_regions.items(), key=lambda x: x[1], reverse=True)[:10]:
                candidate_info = self.find_endemic_extrapolation_candidates(region, 200)
                
                if 'error' not in candidate_info:
                    opportunity = {
                        'region': region,
                        'baker_sources': baker_count,
                        'total_candidates': candidate_info.get('total_candidates', 0),
                        'cross_genus_candidates': candidate_info.get('cross_genus_candidates', 0),
                        'leverage_ratio': candidate_info.get('total_candidates', 0) / max(baker_count, 1),
                        'cross_genus_ratio': candidate_info.get('cross_genus_candidates', 0) / max(baker_count, 1)
                    }
                    regional_opportunities.append(opportunity)
            
            return {
                'regional_coverage': coverage,
                'top_opportunities': sorted(regional_opportunities, key=lambda x: x['leverage_ratio'], reverse=True)[:8],
                'cross_genus_opportunities': sorted(regional_opportunities, key=lambda x: x['cross_genus_ratio'], reverse=True)[:5],
                'summary': {
                    'total_regions_covered': len(specific_regions),
                    'total_baker_sheets': coverage.get('total_baker_sheets', 0),
                    'broader_geographic_coverage': len(broader_regions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating regional report: {str(e)}")
            return {'error': str(e)}

# Initialize the endemic region extrapolator
endemic_extrapolator = EndemicRegionExtrapolator()