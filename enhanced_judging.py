"""
Enhanced judging system with RHS integration and genetic analysis
"""
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from models import db, OrchidRecord, JudgingAnalysis, JudgingStandard
from rhs_integration import rhs_db, analyze_hybrid_parentage
# from genetic_analysis import genetic_analyzer  # Temporarily disabled
from judging_standards import OrchidJudgingSystem as JudgingSystem

logger = logging.getLogger(__name__)

class EnhancedOrchidJudging:
    """Enhanced judging system with genetic and parentage analysis"""
    
    def __init__(self):
        self.base_judging = JudgingSystem()
        # self.genetic_analyzer = genetic_analyzer  # Temporarily disabled
        
        # Enhanced criteria weights for genetic factors
        self.genetic_criteria_weights = {
            'parentage_quality': 0.15,      # Quality of parent plants
            'hybrid_vigor': 0.10,           # Expression of hybrid vigor
            'genetic_novelty': 0.08,        # Novel trait combinations
            'breeding_potential': 0.12,     # Value for future breeding
            'rhs_verification': 0.05        # RHS registration verification
        }
    
    def comprehensive_orchid_analysis(self, orchid_id: int, organization: str = 'AOS', 
                                   user_id: Optional[int] = None) -> Dict:
        """
        Perform comprehensive analysis including genetics and parentage
        """
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        analysis_results = {
            'orchid_id': orchid_id,
            'orchid_name': orchid.get_full_name(),
            'organization': organization,
            'analysis_date': datetime.utcnow().isoformat(),
            'base_judging': {},
            'rhs_analysis': {},
            'genetic_analysis': {},
            'parentage_analysis': {},
            'enhanced_scoring': {},
            'final_assessment': {},
            'recommendations': []
        }
        
        # Step 1: Base judging analysis
        try:
            base_results = self.base_judging.analyze_orchid(orchid_id, organization)
            analysis_results['base_judging'] = base_results
        except Exception as e:
            logger.error(f"Base judging failed: {str(e)}")
            analysis_results['base_judging'] = {'error': str(e)}
        
        # Step 2: RHS integration and verification
        analysis_results['rhs_analysis'] = self._perform_rhs_analysis(orchid)
        
        # Step 3: Genetic analysis (for hybrids) - Temporarily disabled
        if orchid.is_registered_hybrid() or self._appears_to_be_hybrid(orchid):
            analysis_results['genetic_analysis'] = {'status': 'temporarily_disabled'}
            analysis_results['parentage_analysis'] = {'status': 'temporarily_disabled'}
        
        # Step 4: Enhanced scoring with genetic factors
        analysis_results['enhanced_scoring'] = self._calculate_enhanced_scoring(
            analysis_results['base_judging'],
            analysis_results['genetic_analysis'], 
            analysis_results['parentage_analysis'],
            analysis_results['rhs_analysis']
        )
        
        # Step 5: Final assessment and award determination
        analysis_results['final_assessment'] = self._determine_final_assessment(
            analysis_results, organization
        )
        
        # Step 6: Generate recommendations
        analysis_results['recommendations'] = self._generate_comprehensive_recommendations(
            orchid, analysis_results
        )
        
        # Save analysis to database
        self._save_enhanced_analysis(orchid_id, user_id, organization, analysis_results)
        
        return analysis_results
    
    def _perform_rhs_analysis(self, orchid: OrchidRecord) -> Dict:
        """Perform RHS database analysis"""
        rhs_analysis = {
            'query_performed': False,
            'registration_found': False,
            'parentage_verified': False,
            'species_confirmed': False,
            'verification_score': 0.0,
            'rhs_data': {}
        }
        
        try:
            orchid_name = orchid.scientific_name or orchid.display_name
            
            # Search RHS database
            rhs_results = rhs_db.search_orchid(orchid_name)
            rhs_analysis['query_performed'] = True
            
            if rhs_results:
                rhs_analysis['registration_found'] = True
                result = rhs_results[0]
                rhs_analysis['rhs_data'] = result
                
                # Verify orchid type
                if result.get('type') == 'hybrid':
                    # Get and verify parentage
                    parentage_data = rhs_db.get_hybrid_parentage(orchid_name)
                    if parentage_data.get('parents'):
                        rhs_analysis['parentage_verified'] = True
                        rhs_analysis['verification_score'] += 3.0
                        
                        # Update orchid record with RHS data
                        self._update_orchid_with_rhs_data(orchid, parentage_data)
                
                elif result.get('type') == 'species':
                    # Get species information
                    species_data = rhs_db.get_species_information(orchid_name)
                    if species_data:
                        rhs_analysis['species_confirmed'] = True
                        rhs_analysis['verification_score'] += 2.5
                        
                        # Update orchid record with species data
                        self._update_orchid_with_species_data(orchid, species_data)
                
                # General RHS registration bonus
                rhs_analysis['verification_score'] += 2.0
            
        except Exception as e:
            logger.error(f"RHS analysis failed: {str(e)}")
            rhs_analysis['error'] = str(e)
        
        return rhs_analysis
    
    def _perform_genetic_analysis(self, orchid: OrchidRecord) -> Dict:
        """Perform genetic analysis using genetic analyzer"""
        # Temporarily return dummy data
        return {
            'genetic_diversity_score': 5.0,
            'hybrid_vigor_assessment': 'normal',
            'trait_expression_quality': 6.0,
            'breeding_value_score': 5.5,
            'genetic_novelty_score': 4.0,
            'overall_genetic_score': 5.1
        }
    
    def _perform_parentage_analysis(self, orchid: OrchidRecord) -> Dict:
        """Perform detailed parentage analysis"""
        parentage_analysis = {
            'parentage_known': False,
            'parentage_quality_score': 0.0,
            'inheritance_analysis': {},
            'parent_quality_assessment': {},
            'breeding_implications': {}
        }
        
        try:
            if orchid.pod_parent and orchid.pollen_parent:
                parentage_analysis['parentage_known'] = True
                
                # Analyze parent quality
                parentage_analysis['parent_quality_assessment'] = self._assess_parent_quality(
                    orchid.pod_parent, orchid.pollen_parent
                )
                
                # Analyze inheritance patterns
                hybrid_name = orchid.get_full_name()
                observed_traits = self._extract_observed_traits(orchid)
                
                inheritance_data = analyze_hybrid_parentage(hybrid_name, observed_traits)
                parentage_analysis['inheritance_analysis'] = inheritance_data
                
                # Calculate parentage quality score
                parentage_analysis['parentage_quality_score'] = self._calculate_parentage_quality_score(
                    parentage_analysis['parent_quality_assessment'],
                    parentage_analysis['inheritance_analysis']
                )
                
                # Assess breeding implications
                parentage_analysis['breeding_implications'] = self._assess_breeding_implications(
                    orchid, parentage_analysis
                )
        
        except Exception as e:
            logger.error(f"Parentage analysis failed: {str(e)}")
            parentage_analysis['error'] = str(e)
        
        return parentage_analysis
    
    def _calculate_enhanced_scoring(self, base_judging: Dict, genetic_analysis: Dict, 
                                   parentage_analysis: Dict, rhs_analysis: Dict) -> Dict:
        """Calculate enhanced scoring incorporating genetic factors"""
        enhanced_scoring = {
            'base_score': 0.0,
            'genetic_bonus': 0.0,
            'parentage_bonus': 0.0,
            'rhs_bonus': 0.0,
            'total_enhanced_score': 0.0,
            'scoring_breakdown': {}
        }
        
        # Extract base score
        if base_judging and isinstance(base_judging, dict):
            enhanced_scoring['base_score'] = base_judging.get('total_score', 0.0)
        
        # Calculate genetic bonus
        if genetic_analysis and 'overall_genetic_score' in genetic_analysis:
            genetic_score = genetic_analysis['overall_genetic_score']
            enhanced_scoring['genetic_bonus'] = genetic_score * self.genetic_criteria_weights['hybrid_vigor']
        
        # Calculate parentage bonus
        if parentage_analysis and 'parentage_quality_score' in parentage_analysis:
            parentage_score = parentage_analysis['parentage_quality_score']
            enhanced_scoring['parentage_bonus'] = parentage_score * self.genetic_criteria_weights['parentage_quality']
        
        # Calculate RHS bonus
        if rhs_analysis and 'verification_score' in rhs_analysis:
            rhs_score = rhs_analysis['verification_score']
            enhanced_scoring['rhs_bonus'] = rhs_score * self.genetic_criteria_weights['rhs_verification']
        
        # Calculate total enhanced score
        enhanced_scoring['total_enhanced_score'] = (
            enhanced_scoring['base_score'] +
            enhanced_scoring['genetic_bonus'] +
            enhanced_scoring['parentage_bonus'] +
            enhanced_scoring['rhs_bonus']
        )
        
        # Create scoring breakdown
        enhanced_scoring['scoring_breakdown'] = {
            'base_judging': enhanced_scoring['base_score'],
            'genetic_factors': enhanced_scoring['genetic_bonus'],
            'parentage_quality': enhanced_scoring['parentage_bonus'],
            'rhs_verification': enhanced_scoring['rhs_bonus'],
            'enhancement_total': (enhanced_scoring['genetic_bonus'] + 
                                enhanced_scoring['parentage_bonus'] + 
                                enhanced_scoring['rhs_bonus'])
        }
        
        return enhanced_scoring
    
    def _determine_final_assessment(self, analysis_results: Dict, organization: str) -> Dict:
        """Determine final assessment and award recommendation"""
        enhanced_scoring = analysis_results.get('enhanced_scoring', {})
        total_score = enhanced_scoring.get('total_enhanced_score', 0.0)
        
        # Award thresholds by organization (enhanced with genetic factors)
        award_thresholds = {
            'AOS': {
                'FCC': 90.0,  # First Class Certificate
                'AM': 80.0,   # Award of Merit  
                'HCC': 75.0   # Highly Commended Certificate
            },
            'EU': {
                'Gold': 85.0,
                'Silver': 75.0,
                'Bronze': 65.0
            },
            'AU': {
                'Champion': 88.0,
                'Excellence': 78.0,
                'Merit': 68.0
            }
            # Add other organizations as needed
        }
        
        thresholds = award_thresholds.get(organization, award_thresholds['AOS'])
        
        final_assessment = {
            'total_score': total_score,
            'percentage': min(total_score, 100.0),
            'is_award_worthy': False,
            'suggested_award_level': None,
            'award_justification': '',
            'genetic_contribution': enhanced_scoring.get('enhancement_total', 0.0),
            'assessment_notes': []
        }
        
        # Determine award level
        for award_level, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                final_assessment['is_award_worthy'] = True
                final_assessment['suggested_award_level'] = award_level
                final_assessment['award_justification'] = f"Score of {total_score:.1f} exceeds {award_level} threshold of {threshold}"
                break
        
        # Add assessment notes
        genetic_contribution = enhanced_scoring.get('enhancement_total', 0.0)
        if genetic_contribution > 5.0:
            final_assessment['assessment_notes'].append(
                f"Significant genetic enhancement (+{genetic_contribution:.1f} points)"
            )
        
        if analysis_results.get('rhs_analysis', {}).get('registration_found'):
            final_assessment['assessment_notes'].append("RHS registration verified")
        
        if analysis_results.get('parentage_analysis', {}).get('parentage_known'):
            final_assessment['assessment_notes'].append("Parentage confirmed and analyzed")
        
        return final_assessment
    
    def _generate_comprehensive_recommendations(self, orchid: OrchidRecord, analysis_results: Dict) -> List[str]:
        """Generate comprehensive recommendations"""
        recommendations = []
        
        final_assessment = analysis_results.get('final_assessment', {})
        genetic_analysis = analysis_results.get('genetic_analysis', {})
        parentage_analysis = analysis_results.get('parentage_analysis', {})
        
        # Award recommendations
        if final_assessment.get('is_award_worthy'):
            award_level = final_assessment.get('suggested_award_level')
            recommendations.append(f"Recommended for {award_level} award based on comprehensive analysis")
        
        # Breeding recommendations
        breeding_value = genetic_analysis.get('breeding_value_score', 0)
        if breeding_value > 7.0:
            recommendations.append("Excellent breeding potential - consider using as parent plant")
        elif breeding_value > 5.0:
            recommendations.append("Good breeding potential for specific traits")
        
        # Show recommendations
        if final_assessment.get('total_score', 0) > 75:
            recommendations.append("Excellent candidate for orchid shows and exhibitions")
        
        # Cultural recommendations based on genetic analysis
        if genetic_analysis.get('hybrid_vigor_assessment') == 'enhanced':
            recommendations.append("Strong vigor makes this suitable for beginner growers")
        
        # Parentage-specific recommendations
        if parentage_analysis.get('parentage_known') and parentage_analysis.get('parentage_quality_score', 0) > 8.0:
            recommendations.append("Outstanding parentage contributes significantly to plant quality")
        
        # RHS recommendations
        if not analysis_results.get('rhs_analysis', {}).get('registration_found'):
            if orchid.is_registered_hybrid():
                recommendations.append("Consider verifying RHS registration for additional recognition")
        
        return recommendations
    
    # Helper methods
    def _appears_to_be_hybrid(self, orchid: OrchidRecord) -> bool:
        """Check if orchid appears to be a hybrid based on naming"""
        name = orchid.scientific_name or orchid.display_name or ''
        # Hybrids typically have more than 2 words or contain common hybrid indicators
        return (len(name.split()) > 2 or 
                any(indicator in name.lower() for indicator in ['×', 'x ', 'hybrid', 'cross']))
    
    def _update_orchid_with_rhs_data(self, orchid: OrchidRecord, parentage_data: Dict):
        """Update orchid record with RHS parentage data"""
        try:
            parents = parentage_data.get('parents', {})
            if parents:
                orchid.pod_parent = parents.get('pod_parent')
                orchid.pollen_parent = parents.get('pollen_parent')
                orchid.parentage_formula = parentage_data.get('parentage_formula')
                orchid.generation = parentage_data.get('generation')
                orchid.registrant = parentage_data.get('registrant')
                orchid.is_hybrid = True
                orchid.rhs_verification_status = 'verified'
                
                # Parse grex and clone names
                if parentage_data.get('grex'):
                    orchid.grex_name = parentage_data['grex']
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Failed to update orchid with RHS data: {str(e)}")
    
    def _update_orchid_with_species_data(self, orchid: OrchidRecord, species_data: Dict):
        """Update orchid record with RHS species data"""
        try:
            orchid.scientific_name = species_data.get('accepted_name', orchid.scientific_name)
            orchid.native_habitat = species_data.get('habitat', orchid.native_habitat)
            orchid.cultural_notes = species_data.get('cultivation_notes', orchid.cultural_notes)
            orchid.bloom_time = species_data.get('flowering_time', orchid.bloom_time)
            orchid.is_species = True
            orchid.rhs_verification_status = 'verified'
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update orchid with species data: {str(e)}")
    
    def _extract_observed_traits(self, orchid: OrchidRecord) -> Dict:
        """Extract observed traits from orchid record"""
        traits = {}
        
        # Extract from AI description
        if orchid.ai_description:
            # Simple trait extraction - could be enhanced with NLP
            desc = orchid.ai_description.lower()
            if 'large' in desc:
                traits['size'] = 'large'
            if 'fragrant' in desc:
                traits['fragrance'] = 'present'
            # Add more trait extraction logic
        
        return traits
    
    def _calculate_genetic_diversity_score(self, genetic_results: Dict) -> float:
        """Calculate genetic diversity score"""
        # Simplified calculation - could be enhanced
        breeding_potential = genetic_results.get('breeding_potential', {})
        return float(breeding_potential.get('genetic_value', 5.0))
    
    def _assess_hybrid_vigor(self, genetic_results: Dict) -> str:
        """Assess hybrid vigor from genetic analysis"""
        phenotype = genetic_results.get('phenotype_analysis', {})
        vigor = phenotype.get('vigor_assessment', 'normal')
        return vigor
    
    def _evaluate_trait_expression(self, genetic_results: Dict) -> float:
        """Evaluate quality of trait expression"""
        genetic_traits = genetic_results.get('genetic_traits', {})
        confidence_scores = genetic_traits.get('confidence_scores', {})
        
        if confidence_scores:
            return sum(confidence_scores.values()) / len(confidence_scores) * 10
        return 5.0
    
    def _calculate_breeding_value(self, genetic_results: Dict) -> float:
        """Calculate breeding value score"""
        breeding_potential = genetic_results.get('breeding_potential', {})
        rating = breeding_potential.get('overall_rating', 'medium')
        
        rating_scores = {'poor': 2.0, 'medium': 5.0, 'good': 8.0, 'excellent': 10.0}
        return rating_scores.get(rating, 5.0)
    
    def _assess_genetic_novelty(self, genetic_results: Dict) -> float:
        """Assess genetic novelty and uniqueness"""
        parentage_analysis = genetic_results.get('parentage_analysis', {})
        trait_inheritance = parentage_analysis.get('trait_inheritance', {})
        
        novel_traits = trait_inheritance.get('novel_traits', [])
        return min(len(novel_traits) * 2.0, 10.0)
    
    def _assess_parent_quality(self, pod_parent: str, pollen_parent: str) -> Dict:
        """Assess quality of parent plants"""
        assessment = {
            'pod_parent_quality': self._evaluate_parent_quality(pod_parent),
            'pollen_parent_quality': self._evaluate_parent_quality(pollen_parent),
            'parent_compatibility': self._assess_parent_compatibility(pod_parent, pollen_parent)
        }
        
        assessment['overall_parent_quality'] = (
            assessment['pod_parent_quality'] + 
            assessment['pollen_parent_quality'] + 
            assessment['parent_compatibility']
        ) / 3
        
        return assessment
    
    def _evaluate_parent_quality(self, parent_name: str) -> float:
        """Evaluate individual parent quality"""
        if not parent_name:
            return 0.0
        
        # Check for award indicators in name
        award_indicators = ['fcc', 'am', 'hcc', 'champion', 'gold', 'silver', 'premier']
        quality_score = 5.0  # Base score
        
        parent_lower = parent_name.lower()
        for indicator in award_indicators:
            if indicator in parent_lower:
                quality_score += 2.0
                break
        
        return min(quality_score, 10.0)
    
    def _assess_parent_compatibility(self, pod_parent: str, pollen_parent: str) -> float:
        """Assess compatibility between parents"""
        if not pod_parent or not pollen_parent:
            return 0.0
        
        # Same genus = high compatibility
        pod_genus = pod_parent.split()[0] if pod_parent else ''
        pollen_genus = pollen_parent.split()[0] if pollen_parent else ''
        
        if pod_genus == pollen_genus:
            return 8.0
        else:
            return 5.0  # Intergeneric crosses
    
    def _calculate_parentage_quality_score(self, parent_assessment: Dict, inheritance_analysis: Dict) -> float:
        """Calculate overall parentage quality score"""
        parent_quality = parent_assessment.get('overall_parent_quality', 5.0)
        
        # Bonus for good inheritance patterns
        inheritance_bonus = 0.0
        if inheritance_analysis and 'trait_inheritance' in inheritance_analysis:
            trait_inheritance = inheritance_analysis['trait_inheritance']
            dominant_traits = trait_inheritance.get('dominant_traits', [])
            intermediate_traits = trait_inheritance.get('intermediate_traits', [])
            
            # Bonus for diverse trait expression
            if len(dominant_traits) > 3:
                inheritance_bonus += 1.0
            if len(intermediate_traits) > 2:
                inheritance_bonus += 0.5
        
        return min(parent_quality + inheritance_bonus, 10.0)
    
    def _assess_breeding_implications(self, orchid: OrchidRecord, parentage_analysis: Dict) -> Dict:
        """Assess implications for breeding programs"""
        return {
            'breeding_value': 'medium',
            'recommended_uses': ['line_breeding', 'outcrossing'],
            'genetic_contributions': 'balanced',
            'fertility_prediction': 'normal'
        }
    
    def _save_enhanced_analysis(self, orchid_id: int, user_id: Optional[int], organization: str, results: Dict):
        """Save enhanced analysis results to database"""
        try:
            # Get or create judging standard
            standard = JudgingStandard.query.filter_by(
                organization=organization,
                standard_name='Enhanced Genetic Analysis'
            ).first()
            
            if not standard:
                standard = JudgingStandard(
                    organization=organization,
                    standard_name='Enhanced Genetic Analysis',
                    category='comprehensive',
                    criteria_name='Genetic and Parentage Analysis',
                    description='Comprehensive analysis including genetics and parentage',
                    max_points=100
                )
                db.session.add(standard)
                db.session.commit()
            
            # Create enhanced judging analysis record
            analysis = JudgingAnalysis(
                orchid_id=orchid_id,
                user_id=user_id,
                judging_standard_id=standard.id,
                score=results['final_assessment']['total_score'],
                percentage=results['final_assessment']['percentage'],
                ai_comments=json.dumps(results['recommendations']),
                detailed_analysis=json.dumps(results),
                is_award_worthy=results['final_assessment']['is_award_worthy'],
                suggested_award_level=results['final_assessment']['suggested_award_level'],
                award_justification=results['final_assessment']['award_justification'],
                ai_model_used='Enhanced Genetic Analysis v1.0',
                confidence_level=0.85
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            logger.info(f"Enhanced analysis saved for orchid {orchid_id}")
            
        except Exception as e:
            logger.error(f"Failed to save enhanced analysis: {str(e)}")
            db.session.rollback()

# Global enhanced judging system instance
enhanced_judging = EnhancedOrchidJudging()

def analyze_orchid_with_genetics(orchid_id: int, organization: str = 'AOS', user_id: Optional[int] = None) -> Dict:
    """
    Convenience function for enhanced orchid analysis
    """
    return enhanced_judging.comprehensive_orchid_analysis(orchid_id, organization, user_id)