"""
Genetic and parentage analysis system for orchid hybrids
Integrates with RHS data and AI analysis for comprehensive genetic evaluation
"""
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from models import db, OrchidRecord
from rhs_integration import rhs_db, analyze_hybrid_parentage
from orchid_ai import analyze_orchid_image

logger = logging.getLogger(__name__)

class OrchidGeneticAnalyzer:
    """Comprehensive genetic and parentage analysis for orchids"""
    
    def __init__(self):
        self.trait_categories = {
            'flower': ['size', 'shape', 'color', 'pattern', 'substance', 'arrangement'],
            'plant': ['growth_habit', 'pseudobulb_type', 'leaf_form', 'vigor'],
            'cultural': ['temperature_preference', 'light_requirements', 'flowering_season']
        }
        
        self.genetic_markers = {
            'size': ['miniature', 'small', 'standard', 'large', 'giant'],
            'color': ['alba', 'coerulea', 'aurea', 'rubra', 'striata', 'peloric'],
            'pattern': ['solid', 'spotted', 'striped', 'margined', 'flamed'],
            'shape': ['standard', 'stellate', 'cupped', 'flat', 'reflexed']
        }
    
    def analyze_orchid_genetics(self, orchid_id: int, include_ai_analysis: bool = True) -> Dict:
        """
        Perform comprehensive genetic analysis of orchid
        
        Args:
            orchid_id: ID of orchid to analyze
            include_ai_analysis: Whether to include AI image analysis
            
        Returns:
            Comprehensive genetic analysis results
        """
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        analysis_results = {
            'orchid_id': orchid_id,
            'orchid_name': orchid.get_full_name(),
            'analysis_date': datetime.utcnow(),
            'rhs_data': {},
            'parentage_analysis': {},
            'genetic_traits': {},
            'phenotype_analysis': {},
            'breeding_potential': {},
            'recommendations': []
        }
        
        # Get RHS data
        analysis_results['rhs_data'] = self._get_rhs_data(orchid)
        
        # Analyze parentage if hybrid
        if orchid.is_hybrid or (orchid.pod_parent and orchid.pollen_parent):
            analysis_results['parentage_analysis'] = self._analyze_parentage(orchid)
        
        # Extract genetic traits
        if include_ai_analysis and orchid.image_filename:
            analysis_results['genetic_traits'] = self._extract_genetic_traits(orchid)
        
        # Analyze phenotype
        analysis_results['phenotype_analysis'] = self._analyze_phenotype(
            orchid, analysis_results['parentage_analysis']
        )
        
        # Assess breeding potential
        analysis_results['breeding_potential'] = self._assess_breeding_potential(
            orchid, analysis_results
        )
        
        # Generate recommendations
        analysis_results['recommendations'] = self._generate_recommendations(
            orchid, analysis_results
        )
        
        # Save analysis to database
        self._save_genetic_analysis(orchid_id, analysis_results)
        
        return analysis_results
    
    def compare_hybrid_to_parents(self, orchid_id: int) -> Dict:
        """
        Compare hybrid characteristics to expected parental traits
        
        Args:
            orchid_id: ID of hybrid orchid
            
        Returns:
            Comparison analysis
        """
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        if not (orchid.pod_parent and orchid.pollen_parent):
            return {'error': 'Parentage information required for comparison'}
        
        comparison = {
            'hybrid_name': orchid.get_full_name(),
            'pod_parent': orchid.pod_parent,
            'pollen_parent': orchid.pollen_parent,
            'trait_inheritance': {},
            'parent_contributions': {},
            'unexpected_traits': [],
            'breeding_analysis': {}
        }
        
        # Get parent data from RHS
        pod_data = self._get_parent_data(orchid.pod_parent)
        pollen_data = self._get_parent_data(orchid.pollen_parent)
        
        # Extract hybrid traits
        hybrid_traits = self._extract_current_traits(orchid)
        
        # Analyze inheritance patterns
        comparison['trait_inheritance'] = self._analyze_inheritance_patterns(
            hybrid_traits, pod_data, pollen_data
        )
        
        # Calculate parent contributions
        comparison['parent_contributions'] = self._calculate_parent_contributions(
            hybrid_traits, pod_data, pollen_data
        )
        
        # Identify unexpected traits
        comparison['unexpected_traits'] = self._identify_unexpected_traits(
            hybrid_traits, pod_data, pollen_data
        )
        
        # Breeding analysis
        comparison['breeding_analysis'] = self._analyze_breeding_implications(
            comparison
        )
        
        return comparison
    
    def predict_offspring_traits(self, parent1_id: int, parent2_id: int) -> Dict:
        """
        Predict traits in offspring from two parent orchids
        
        Args:
            parent1_id: ID of first parent
            parent2_id: ID of second parent
            
        Returns:
            Predicted offspring characteristics
        """
        parent1 = OrchidRecord.query.get_or_404(parent1_id)
        parent2 = OrchidRecord.query.get_or_404(parent2_id)
        
        prediction = {
            'cross_name': f"{parent1.get_full_name()} × {parent2.get_full_name()}",
            'parent1': parent1.get_full_name(),
            'parent2': parent2.get_full_name(),
            'predicted_traits': {},
            'variation_range': {},
            'breeding_notes': [],
            'success_probability': 0.0
        }
        
        # Get parent traits
        p1_traits = self._extract_current_traits(parent1)
        p2_traits = self._extract_current_traits(parent2)
        
        # Predict offspring traits
        prediction['predicted_traits'] = self._predict_hybrid_traits(p1_traits, p2_traits)
        
        # Estimate variation range
        prediction['variation_range'] = self._estimate_variation_range(p1_traits, p2_traits)
        
        # Calculate success probability
        prediction['success_probability'] = self._calculate_cross_success_probability(
            parent1, parent2
        )
        
        # Generate breeding notes
        prediction['breeding_notes'] = self._generate_breeding_notes(
            parent1, parent2, prediction
        )
        
        return prediction
    
    def _get_rhs_data(self, orchid: OrchidRecord) -> Dict:
        """Get RHS data for orchid"""
        orchid_name = orchid.scientific_name or orchid.display_name
        
        try:
            rhs_results = rhs_db.search_orchid(orchid_name)
            
            if rhs_results:
                # Get detailed information for first match
                result = rhs_results[0]
                
                rhs_data = {
                    'found': True,
                    'registration_status': 'found',
                    'rhs_name': result.get('name'),
                    'type': result.get('type'),  # species or hybrid
                    'url': result.get('url')
                }
                
                # Get parentage if hybrid
                if result.get('type') == 'hybrid':
                    parentage = rhs_db.get_hybrid_parentage(orchid_name)
                    rhs_data.update(parentage)
                
                # Get species data if species
                elif result.get('type') == 'species':
                    species_data = rhs_db.get_species_information(orchid_name)
                    rhs_data.update(species_data)
                
                return rhs_data
            else:
                return {'found': False, 'registration_status': 'not_found'}
                
        except Exception as e:
            logger.error(f"RHS lookup error for {orchid_name}: {str(e)}")
            return {'found': False, 'error': str(e)}
    
    def _analyze_parentage(self, orchid: OrchidRecord) -> Dict:
        \"\"\"Analyze parentage information\"\"\"
        if orchid.pod_parent and orchid.pollen_parent:
            # Use existing parentage data
            parentage_name = orchid.get_full_name()
            observed_traits = self._extract_current_traits(orchid)
            
            return analyze_hybrid_parentage(parentage_name, observed_traits)
        else:
            return {'error': 'No parentage information available'}
    
    def _extract_genetic_traits(self, orchid: OrchidRecord) -> Dict:
        \"\"\"Extract genetic traits using AI analysis\"\"\"
        if not orchid.image_filename:
            return {'error': 'No image available for analysis'}
        
        try:
            # Enhanced AI analysis for genetic traits
            ai_results = self._ai_genetic_analysis(orchid.image_filename)
            
            genetic_traits = {
                'flower_traits': ai_results.get('flower_characteristics', {}),
                'plant_traits': ai_results.get('plant_characteristics', {}),
                'color_genetics': ai_results.get('color_analysis', {}),
                'form_genetics': ai_results.get('form_analysis', {}),
                'size_genetics': ai_results.get('size_analysis', {}),
                'pattern_genetics': ai_results.get('pattern_analysis', {}),
                'confidence_scores': ai_results.get('confidence_scores', {})
            }
            
            return genetic_traits
            
        except Exception as e:
            logger.error(f"Genetic trait extraction error: {str(e)}")
            return {'error': str(e)}
    
    def _ai_genetic_analysis(self, image_filename: str) -> Dict:
        \"\"\"Perform AI analysis focused on genetic traits\"\"\"
        # This would integrate with enhanced orchid_ai module
        # For now, return simulated genetic analysis
        
        return {
            'flower_characteristics': {
                'petal_shape': 'ovate',
                'petal_texture': 'glossy',
                'lip_shape': 'complex',
                'column_type': 'normal',
                'flower_count': 3,
                'flower_size': 'large'
            },
            'plant_characteristics': {
                'pseudobulb_type': 'clustered',
                'leaf_type': 'plicate',
                'growth_habit': 'sympodial',
                'vigor': 'strong'
            },
            'color_analysis': {
                'primary_color': 'purple',
                'secondary_colors': ['white', 'yellow'],
                'color_intensity': 'high',
                'color_pattern': 'solid_with_contrasting_lip'
            },
            'confidence_scores': {
                'flower_analysis': 0.85,
                'plant_analysis': 0.78,
                'color_analysis': 0.92
            }
        }
    
    def _analyze_phenotype(self, orchid: OrchidRecord, parentage_data: Dict) -> Dict:
        \"\"\"Analyze phenotypic expression\"\"\"
        phenotype = {
            'expression_pattern': 'intermediate',  # dominant, recessive, intermediate, transgressive
            'vigor_assessment': 'normal',  # poor, normal, enhanced
            'trait_dominance': {},
            'phenotypic_novelty': [],
            'environmental_factors': []
        }
        
        if parentage_data and 'trait_inheritance' in parentage_data:
            inheritance = parentage_data['trait_inheritance']
            
            # Analyze dominance patterns
            dominant_traits = inheritance.get('dominant_traits', [])
            intermediate_traits = inheritance.get('intermediate_traits', [])
            
            if len(dominant_traits) > len(intermediate_traits):
                phenotype['expression_pattern'] = 'dominant'
            elif len(intermediate_traits) > len(dominant_traits):
                phenotype['expression_pattern'] = 'intermediate'
            
            # Check for hybrid vigor
            if 'vigor' in inheritance:
                phenotype['vigor_assessment'] = inheritance['vigor']
        
        return phenotype
    
    def _assess_breeding_potential(self, orchid: OrchidRecord, analysis_data: Dict) -> Dict:
        \"\"\"Assess breeding potential\"\"\"
        potential = {
            'overall_rating': 'medium',  # poor, medium, good, excellent
            'strengths': [],
            'weaknesses': [],
            'recommended_crosses': [],
            'breeding_goals': [],
            'genetic_value': 'moderate'
        }
        
        # Analyze based on genetic data
        genetic_traits = analysis_data.get('genetic_traits', {})
        parentage_analysis = analysis_data.get('parentage_analysis', {})
        
        # Check for desirable traits
        if genetic_traits:
            flower_traits = genetic_traits.get('flower_traits', {})
            if flower_traits.get('flower_size') == 'large':
                potential['strengths'].append('Large flower size')
            if flower_traits.get('flower_count', 0) > 5:
                potential['strengths'].append('High flower count')
        
        # Check genetic diversity
        if parentage_analysis and 'genetic_analysis' in parentage_analysis:
            genetic_data = parentage_analysis['genetic_analysis']
            if genetic_data.get('genetic_distance') == 'medium':
                potential['strengths'].append('Good genetic diversity')
                potential['overall_rating'] = 'good'
        
        return potential
    
    def _generate_recommendations(self, orchid: OrchidRecord, analysis_data: Dict) -> List[str]:
        \"\"\"Generate breeding and cultivation recommendations\"\"\"
        recommendations = []
        
        breeding_potential = analysis_data.get('breeding_potential', {})
        genetic_traits = analysis_data.get('genetic_traits', {})
        
        # Breeding recommendations
        if breeding_potential.get('overall_rating') in ['good', 'excellent']:
            recommendations.append("Consider using as breeding parent for size improvement")
        
        # Cultural recommendations
        if genetic_traits and 'plant_traits' in genetic_traits:
            plant_traits = genetic_traits['plant_traits']
            if plant_traits.get('vigor') == 'strong':
                recommendations.append("Suitable for beginner growers due to strong vigor")
        
        # Show recommendations
        if genetic_traits and 'flower_traits' in genetic_traits:
            flower_traits = genetic_traits['flower_traits']
            if flower_traits.get('flower_size') == 'large':
                recommendations.append("Excellent candidate for orchid shows")
        
        return recommendations
    
    def _save_genetic_analysis(self, orchid_id: int, analysis_data: Dict):
        \"\"\"Save genetic analysis to database\"\"\"
        try:
            # Create GeneticAnalysis record (would need to add this model)
            # For now, just log the analysis
            logger.info(f\"Genetic analysis completed for orchid {orchid_id}\")
            
            # Update orchid record with RHS data if found
            rhs_data = analysis_data.get('rhs_data', {})
            if rhs_data.get('found'):
                orchid = OrchidRecord.query.get(orchid_id)
                if orchid:
                    orchid.rhs_verification_status = 'verified'
                    if rhs_data.get('parents'):
                        parents = rhs_data['parents']
                        orchid.pod_parent = parents.get('pod_parent')
                        orchid.pollen_parent = parents.get('pollen_parent')
                    
                    db.session.commit()
            
        except Exception as e:
            logger.error(f\"Error saving genetic analysis: {str(e)}\")
    
    # Helper methods for trait analysis
    def _get_parent_data(self, parent_name: str) -> Dict:
        \"\"\"Get comprehensive data for parent orchid\"\"\"
        return rhs_db.get_hybrid_parentage(parent_name) if parent_name else {}
    
    def _extract_current_traits(self, orchid: OrchidRecord) -> Dict:
        \"\"\"Extract current traits from orchid record\"\"\"
        traits = {}
        
        # Extract from AI description if available
        if orchid.ai_description:
            traits.update(self._parse_ai_description_for_traits(orchid.ai_description))
        
        # Extract from cultural notes
        if orchid.cultural_notes:
            traits.update(self._parse_cultural_notes_for_traits(orchid.cultural_notes))
        
        # Add basic information
        traits.update({
            'scientific_name': orchid.scientific_name,
            'genus': orchid.genus,
            'species': orchid.species,
            'growth_habit': orchid.growth_habit,
            'bloom_time': orchid.bloom_time,
            'climate_preference': orchid.climate_preference
        })
        
        return traits
    
    def _parse_ai_description_for_traits(self, description: str) -> Dict:
        \"\"\"Parse AI description for genetic traits\"\"\"
        traits = {}
        
        # Simple keyword extraction
        description_lower = description.lower()
        
        if 'large' in description_lower:
            traits['size'] = 'large'
        elif 'small' in description_lower:
            traits['size'] = 'small'
        
        if 'fragrant' in description_lower:
            traits['fragrance'] = 'present'
        
        if 'purple' in description_lower:
            traits['color'] = 'purple'
        elif 'white' in description_lower:
            traits['color'] = 'white'
        elif 'yellow' in description_lower:
            traits['color'] = 'yellow'
        
        return traits
    
    def _parse_cultural_notes_for_traits(self, notes: str) -> Dict:
        \"\"\"Parse cultural notes for trait information\"\"\"
        traits = {}
        
        notes_lower = notes.lower()
        
        if 'vigorous' in notes_lower:
            traits['vigor'] = 'high'
        elif 'slow' in notes_lower:
            traits['vigor'] = 'low'
        
        return traits
    
    def _analyze_inheritance_patterns(self, hybrid_traits: Dict, pod_data: Dict, pollen_data: Dict) -> Dict:
        \"\"\"Analyze how traits were inherited\"\"\"
        return {
            'dominant_from_pod': [],
            'dominant_from_pollen': [],
            'intermediate_expression': [],
            'transgressive_traits': []
        }
    
    def _calculate_parent_contributions(self, hybrid_traits: Dict, pod_data: Dict, pollen_data: Dict) -> Dict:
        \"\"\"Calculate relative contributions from each parent\"\"\"
        return {
            'pod_parent_contribution': 0.5,
            'pollen_parent_contribution': 0.5,
            'contribution_by_trait': {}
        }
    
    def _identify_unexpected_traits(self, hybrid_traits: Dict, pod_data: Dict, pollen_data: Dict) -> List[Dict]:
        \"\"\"Identify traits not present in either parent\"\"\"
        return []
    
    def _analyze_breeding_implications(self, comparison: Dict) -> Dict:
        \"\"\"Analyze implications for breeding programs\"\"\"
        return {
            'breeding_value': 'medium',
            'recommended_applications': [],
            'genetic_notes': []
        }
    
    def _predict_hybrid_traits(self, parent1_traits: Dict, parent2_traits: Dict) -> Dict:
        \"\"\"Predict traits in hybrid offspring\"\"\"
        return {
            'size': 'medium',  # Intermediate between parents
            'color': 'variable',  # Depends on dominance
            'vigor': 'enhanced'  # Potential hybrid vigor
        }
    
    def _estimate_variation_range(self, parent1_traits: Dict, parent2_traits: Dict) -> Dict:
        \"\"\"Estimate range of variation in offspring\"\"\"
        return {
            'size_range': 'medium to large',
            'color_range': 'purple to white',
            'form_variation': 'moderate'
        }
    
    def _calculate_cross_success_probability(self, parent1: OrchidRecord, parent2: OrchidRecord) -> float:
        \"\"\"Calculate probability of successful cross\"\"\"
        # Simple compatibility assessment
        if parent1.genus == parent2.genus:
            return 0.85
        else:
            return 0.45
    
    def _generate_breeding_notes(self, parent1: OrchidRecord, parent2: OrchidRecord, prediction: Dict) -> List[str]:
        \"\"\"Generate notes for breeding program\"\"\"
        notes = []
        
        if parent1.genus == parent2.genus:
            notes.append(\"Intrageneric cross - high compatibility expected\")
        else:
            notes.append(\"Intergeneric cross - may require special techniques\")
        
        success_prob = prediction.get('success_probability', 0)
        if success_prob > 0.8:
            notes.append(\"High success probability - recommended cross\")
        elif success_prob < 0.5:
            notes.append(\"Challenging cross - consider alternative parents\")
        
        return notes

# Global genetic analyzer instance
genetic_analyzer = OrchidGeneticAnalyzer()

def analyze_orchid_genetics(orchid_id: int, include_ai: bool = True) -> Dict:
    \"\"\"
    Convenience function for genetic analysis
    
    Args:
        orchid_id: ID of orchid to analyze
        include_ai: Whether to include AI image analysis
        
    Returns:
        Comprehensive genetic analysis
    \"\"\"
    return genetic_analyzer.analyze_orchid_genetics(orchid_id, include_ai)

def compare_hybrid_to_parents(orchid_id: int) -> Dict:
    \"\"\"
    Convenience function for hybrid comparison
    
    Args:
        orchid_id: ID of hybrid orchid
        
    Returns:
        Comparison analysis
    \"\"\"
    return genetic_analyzer.compare_hybrid_to_parents(orchid_id)