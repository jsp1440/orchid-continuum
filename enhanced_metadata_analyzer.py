"""
Enhanced metadata analyzer integrating multiple botanical databases
for comprehensive orchid identification and analysis
"""
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from models import OrchidRecord, db
from botanical_databases import search_botanical_databases, get_cultivation_recommendations, verify_botanical_accuracy
from rhs_integration import get_rhs_orchid_data
from orchid_ai import analyze_orchid_image

logger = logging.getLogger(__name__)

class EnhancedMetadataAnalyzer:
    """
    Advanced metadata analyzer using multiple botanical databases
    """
    
    def __init__(self):
        self.confidence_weights = {
            'aos': 0.25,           # High authority for awards/judging
            'rhs': 0.25,           # High authority for registration
            'worldplants': 0.20,   # Good for botanical accuracy
            'jays_encyclopedia': 0.15,  # Comprehensive species info
            'ecuagenera': 0.10,    # Good for cultivation
            'andys_orchids': 0.05  # Supplementary cultivation info
        }
    
    def comprehensive_orchid_analysis(self, orchid_id: int) -> Dict:
        """
        Perform comprehensive orchid analysis using all available databases
        
        Args:
            orchid_id: ID of orchid record to analyze
            
        Returns:
            Comprehensive analysis results
        """
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        orchid_name = orchid.scientific_name or orchid.display_name
        
        analysis_results = {
            'orchid_id': orchid_id,
            'orchid_name': orchid_name,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'ai_analysis': {},
            'rhs_data': {},
            'botanical_databases': {},
            'metadata_synthesis': {},
            'cultivation_recommendations': {},
            'botanical_verification': {},
            'confidence_assessment': {},
            'final_metadata': {}
        }
        
        try:
            # Step 1: AI Image Analysis
            if orchid.image_filename:
                analysis_results['ai_analysis'] = self._perform_ai_analysis(orchid)
            
            # Step 2: RHS Database Search
            analysis_results['rhs_data'] = self._search_rhs_database(orchid_name)
            
            # Step 3: Multiple Botanical Database Search
            analysis_results['botanical_databases'] = search_botanical_databases(orchid_name)
            
            # Step 4: Synthesize Metadata
            analysis_results['metadata_synthesis'] = self._synthesize_metadata(
                analysis_results['ai_analysis'],
                analysis_results['rhs_data'],
                analysis_results['botanical_databases']
            )
            
            # Step 5: Cultivation Recommendations
            analysis_results['cultivation_recommendations'] = get_cultivation_recommendations(orchid_name)
            
            # Step 6: Botanical Verification
            analysis_results['botanical_verification'] = verify_botanical_accuracy(orchid_name)
            
            # Step 7: Confidence Assessment
            analysis_results['confidence_assessment'] = self._assess_confidence(analysis_results)
            
            # Step 8: Generate Final Metadata
            analysis_results['final_metadata'] = self._generate_final_metadata(
                orchid, analysis_results
            )
            
            # Step 9: Update Orchid Record
            self._update_orchid_record(orchid, analysis_results['final_metadata'])
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed for orchid {orchid_id}: {str(e)}")
            analysis_results['error'] = str(e)
        
        return analysis_results
    
    def _perform_ai_analysis(self, orchid: OrchidRecord) -> Dict:
        """Perform AI analysis on orchid image"""
        try:
            if orchid.ai_description:
                # Use existing AI analysis
                return {
                    'description': orchid.ai_description,
                    'confidence': orchid.ai_confidence,
                    'metadata': json.loads(orchid.ai_extracted_metadata) if orchid.ai_extracted_metadata else {}
                }
            else:
                # Perform new AI analysis
                ai_result = analyze_orchid_image(orchid.image_filename)
                return ai_result
                
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _search_rhs_database(self, orchid_name: str) -> Dict:
        """Search RHS database"""
        try:
            return get_rhs_orchid_data(orchid_name)
        except Exception as e:
            logger.error(f"RHS search failed: {str(e)}")
            return {'error': str(e)}
    
    def _synthesize_metadata(self, ai_data: Dict, rhs_data: Dict, botanical_data: Dict) -> Dict:
        """Synthesize metadata from all sources"""
        synthesis = {
            'scientific_name_consensus': None,
            'taxonomic_classification': {},
            'morphological_features': {},
            'distribution_info': {},
            'cultivation_synthesis': {},
            'breeding_information': {},
            'data_quality_score': 0.0
        }
        
        # Collect scientific names from all sources
        scientific_names = []
        
        if ai_data.get('metadata', {}).get('scientific_name'):
            scientific_names.append(ai_data['metadata']['scientific_name'])
        
        if rhs_data.get('scientific_name'):
            scientific_names.append(rhs_data['scientific_name'])
        
        if botanical_data.get('consolidated_info', {}).get('scientific_name'):
            scientific_names.append(botanical_data['consolidated_info']['scientific_name'])
        
        # Determine consensus scientific name
        if scientific_names:
            # Simple consensus - take most common name
            name_counts = {}
            for name in scientific_names:
                name_counts[name] = name_counts.get(name, 0) + 1
            
            synthesis['scientific_name_consensus'] = max(name_counts.keys(), key=lambda x: name_counts.get(x, 0))
        
        # Synthesize morphological features
        synthesis['morphological_features'] = self._synthesize_morphology(ai_data, botanical_data)
        
        # Synthesize distribution information
        synthesis['distribution_info'] = self._synthesize_distribution(rhs_data, botanical_data)
        
        # Synthesize cultivation information
        synthesis['cultivation_synthesis'] = self._synthesize_cultivation(botanical_data)
        
        # Calculate data quality score
        synthesis['data_quality_score'] = self._calculate_data_quality(ai_data, rhs_data, botanical_data)
        
        return synthesis
    
    def _synthesize_morphology(self, ai_data: Dict, botanical_data: Dict) -> Dict:
        """Synthesize morphological features"""
        morphology = {
            'flower_characteristics': {},
            'plant_characteristics': {},
            'growth_habit': None,
            'size_classification': None
        }
        
        # Extract from AI analysis
        if ai_data.get('metadata', {}).get('flower_characteristics'):
            morphology['flower_characteristics'].update(ai_data['metadata']['flower_characteristics'])
        
        # Extract from botanical databases
        for source, data in botanical_data.get('data_found', {}).items():
            if data.get('found') and 'characteristics' in data:
                morphology['flower_characteristics'].update(data['characteristics'])
        
        return morphology
    
    def _synthesize_distribution(self, rhs_data: Dict, botanical_data: Dict) -> Dict:
        """Synthesize distribution information"""
        distribution = {
            'native_regions': [],
            'cultivation_zones': [],
            'habitat_preferences': {}
        }
        
        # Extract from RHS data
        if rhs_data.get('native_habitat'):
            distribution['native_regions'].append(rhs_data['native_habitat'])
        
        # Extract from botanical databases
        for source, data in botanical_data.get('data_found', {}).items():
            if data.get('found') and 'distribution' in data:
                distribution['native_regions'].extend(data['distribution'])
        
        # Remove duplicates
        distribution['native_regions'] = list(set(distribution['native_regions']))
        
        return distribution
    
    def _synthesize_cultivation(self, botanical_data: Dict) -> Dict:
        """Synthesize cultivation information"""
        cultivation = {
            'temperature_preferences': {},
            'light_requirements': {},
            'humidity_needs': {},
            'growing_medium': {},
            'care_difficulty': None
        }
        
        # Collect cultivation data from all sources
        cultivation_sources = []
        
        for source, data in botanical_data.get('data_found', {}).items():
            if data.get('found') and 'cultivation' in data:
                cultivation_sources.append(data['cultivation'])
        
        # Synthesize cultivation recommendations
        if cultivation_sources:
            # Simple synthesis - take most common values
            for key in ['temperature', 'light', 'humidity', 'growing_medium']:
                values = []
                for cult_data in cultivation_sources:
                    if key in cult_data:
                        values.append(cult_data[key])
                
                if values:
                    # Take most common value
                    value_counts = {}
                    for value in values:
                        value_counts[value] = value_counts.get(value, 0) + 1
                    
                    cultivation[f'{key}_preferences'] = max(value_counts.keys(), key=lambda x: value_counts.get(x, 0))
        
        return cultivation
    
    def _calculate_data_quality(self, ai_data: Dict, rhs_data: Dict, botanical_data: Dict) -> float:
        """Calculate overall data quality score"""
        quality_factors = []
        
        # AI analysis quality
        if ai_data.get('confidence'):
            quality_factors.append(ai_data['confidence'])
        
        # RHS data quality
        if rhs_data.get('found', False):
            quality_factors.append(0.9)  # High quality for RHS data
        
        # Botanical databases quality
        sources_found = len([s for s in botanical_data.get('data_found', {}).values() if s.get('found')])
        total_sources = len(botanical_data.get('data_found', {}))
        
        if total_sources > 0:
            botanical_quality = sources_found / total_sources
            quality_factors.append(botanical_quality)
        
        # Calculate weighted average
        if quality_factors:
            return sum(quality_factors) / len(quality_factors)
        else:
            return 0.0
    
    def _assess_confidence(self, analysis_results: Dict) -> Dict:
        """Assess confidence in analysis results"""
        confidence = {
            'overall_confidence': 0.0,
            'source_reliability': {},
            'data_consistency': {},
            'recommendation_confidence': {}
        }
        
        # Calculate source reliability scores
        for source in ['ai_analysis', 'rhs_data', 'botanical_databases']:
            if source in analysis_results and not analysis_results[source].get('error'):
                if source == 'ai_analysis':
                    confidence['source_reliability'][source] = analysis_results[source].get('confidence', 0.0)
                elif source == 'rhs_data':
                    confidence['source_reliability'][source] = 0.9 if analysis_results[source].get('found') else 0.0
                elif source == 'botanical_databases':
                    sources_found = len([s for s in analysis_results[source].get('data_found', {}).values() if s.get('found')])
                    total_sources = len(analysis_results[source].get('data_found', {}))
                    confidence['source_reliability'][source] = sources_found / max(total_sources, 1)
        
        # Calculate overall confidence
        if confidence['source_reliability']:
            weighted_scores = []
            for source, score in confidence['source_reliability'].items():
                weight = self.confidence_weights.get(source, 0.1)
                weighted_scores.append(score * weight)
            
            confidence['overall_confidence'] = sum(weighted_scores) / sum(self.confidence_weights.values())
        
        return confidence
    
    def _generate_final_metadata(self, orchid: OrchidRecord, analysis_results: Dict) -> Dict:
        """Generate final consolidated metadata"""
        metadata = {
            'scientific_name': None,
            'common_names': [],
            'taxonomic_classification': {},
            'morphological_description': '',
            'native_habitat': '',
            'cultivation_requirements': {},
            'flowering_information': {},
            'breeding_notes': '',
            'data_sources': [],
            'confidence_score': 0.0,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        synthesis = analysis_results.get('metadata_synthesis', {})
        
        # Scientific name
        metadata['scientific_name'] = synthesis.get('scientific_name_consensus') or orchid.scientific_name
        
        # Morphological description
        morphology = synthesis.get('morphological_features', {})
        if morphology.get('flower_characteristics'):
            metadata['morphological_description'] = json.dumps(morphology['flower_characteristics'])
        
        # Native habitat
        distribution = synthesis.get('distribution_info', {})
        if distribution.get('native_regions'):
            metadata['native_habitat'] = ', '.join(distribution['native_regions'][:3])  # Limit to 3 regions
        
        # Cultivation requirements
        cultivation = analysis_results.get('cultivation_recommendations', {})
        metadata['cultivation_requirements'] = {
            'temperature': cultivation.get('temperature'),
            'light': cultivation.get('light'),
            'humidity': cultivation.get('humidity'),
            'growing_medium': cultivation.get('growing_medium')
        }
        
        # Data sources
        if analysis_results.get('rhs_data', {}).get('found'):
            metadata['data_sources'].append('RHS International Register')
        
        botanical_sources = analysis_results.get('botanical_databases', {}).get('sources_searched', [])
        metadata['data_sources'].extend(botanical_sources)
        
        # Confidence score
        metadata['confidence_score'] = analysis_results.get('confidence_assessment', {}).get('overall_confidence', 0.0)
        
        return metadata
    
    def _update_orchid_record(self, orchid: OrchidRecord, final_metadata: Dict):
        """Update orchid record with enhanced metadata"""
        try:
            # Update fields with high-confidence data
            if final_metadata.get('confidence_score', 0) > 0.7:
                if final_metadata.get('scientific_name'):
                    orchid.scientific_name = final_metadata['scientific_name']
                
                if final_metadata.get('native_habitat'):
                    orchid.native_habitat = final_metadata['native_habitat']
                
                # Update cultivation requirements
                cult_req = final_metadata.get('cultivation_requirements', {})
                if cult_req.get('temperature'):
                    orchid.temperature_range = cult_req['temperature']
                if cult_req.get('light'):
                    orchid.light_requirements = cult_req['light']
                
                # Store complete metadata as JSON
                orchid.ai_extracted_metadata = json.dumps(final_metadata)
                
                # Update confidence
                orchid.ai_confidence = final_metadata.get('confidence_score', 0.0)
            
            db.session.commit()
            logger.info(f"Updated orchid record {orchid.id} with enhanced metadata")
            
        except Exception as e:
            logger.error(f"Failed to update orchid record: {str(e)}")
            db.session.rollback()

# Global enhanced metadata analyzer instance
enhanced_analyzer = EnhancedMetadataAnalyzer()

def analyze_orchid_with_botanical_databases(orchid_id: int) -> Dict:
    """
    Convenience function for comprehensive orchid analysis
    
    Args:
        orchid_id: ID of orchid record to analyze
        
    Returns:
        Comprehensive analysis results
    """
    return enhanced_analyzer.comprehensive_orchid_analysis(orchid_id)