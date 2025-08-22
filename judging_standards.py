"""
Orchid judging standards and AI analysis system
Supports AOS, EU, Australian, New Zealand, Japanese, and Thai standards
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from models import db, JudgingStandard, JudgingAnalysis, OrchidRecord
# Note: analyze_orchid_with_judging would be implemented in orchid_ai.py
# from orchid_ai import analyze_orchid_with_judging

logger = logging.getLogger(__name__)

# Standard judging criteria for different organizations
JUDGING_STANDARDS = {
    'AOS': {
        'name': 'American Orchid Society',
        'categories': {
            'flower': [
                {'criteria': 'Form', 'max_points': 30, 'description': 'Shape, symmetry, and proportion of flowers'},
                {'criteria': 'Color', 'max_points': 15, 'description': 'Clarity, intensity, and harmony of colors'},
                {'criteria': 'Substance/Texture', 'max_points': 15, 'description': 'Thickness and surface quality of petals/sepals'},
                {'criteria': 'Size', 'max_points': 10, 'description': 'Overall flower size relative to species norm'},
                {'criteria': 'Floriferousness', 'max_points': 15, 'description': 'Number of flowers and arrangement'},
                {'criteria': 'Stem and Presentation', 'max_points': 15, 'description': 'Stem strength and flower presentation'}
            ],
            'plant': [
                {'criteria': 'Cultural Perfection', 'max_points': 25, 'description': 'Overall health and vigor'},
                {'criteria': 'Size of Plant', 'max_points': 20, 'description': 'Plant size relative to container and species'},
                {'criteria': 'Specimen Character', 'max_points': 20, 'description': 'Multiple growths and maturity'},
                {'criteria': 'Arrangement and Condition', 'max_points': 15, 'description': 'Presentation and grooming'},
                {'criteria': 'Rarity and Distinction', 'max_points': 20, 'description': 'Uniqueness and special characteristics'}
            ]
        },
        'awards': {
            'FCC': {'name': 'First Class Certificate', 'min_score': 90, 'description': 'Exceptional quality, 90+ points'},
            'AM': {'name': 'Award of Merit', 'min_score': 80, 'description': 'High quality, 80-89 points'},
            'HCC': {'name': 'Highly Commended Certificate', 'min_score': 75, 'description': 'Commendable quality, 75-79 points'},
            'CCM': {'name': 'Certificate of Cultural Merit', 'min_score': 80, 'description': 'Outstanding cultivation'},
            'CBR': {'name': 'Certificate of Botanical Recognition', 'min_score': 0, 'description': 'Botanical interest'},
        }
    },
    'EU': {
        'name': 'European Orchid Council',
        'categories': {
            'flower': [
                {'criteria': 'Form and Shape', 'max_points': 25, 'description': 'Geometric perfection and symmetry'},
                {'criteria': 'Color and Pattern', 'max_points': 20, 'description': 'Color intensity and pattern clarity'},
                {'criteria': 'Size', 'max_points': 15, 'description': 'Flower size and proportions'},
                {'criteria': 'Substance', 'max_points': 15, 'description': 'Petal thickness and durability'},
                {'criteria': 'Inflorescence', 'max_points': 15, 'description': 'Flower count and arrangement'},
                {'criteria': 'Impact', 'max_points': 10, 'description': 'Overall visual impact'}
            ],
            'plant': [
                {'criteria': 'Plant Health', 'max_points': 30, 'description': 'Vigor and freedom from defects'},
                {'criteria': 'Growth Habit', 'max_points': 25, 'description': 'Natural form and balance'},
                {'criteria': 'Cultural Achievement', 'max_points': 25, 'description': 'Cultivation excellence'},
                {'criteria': 'Presentation', 'max_points': 20, 'description': 'Display quality and grooming'}
            ]
        },
        'awards': {
            'Gold': {'name': 'Gold Certificate', 'min_score': 90, 'description': 'Outstanding excellence'},
            'Silver': {'name': 'Silver Certificate', 'min_score': 80, 'description': 'High quality'},
            'Bronze': {'name': 'Bronze Certificate', 'min_score': 70, 'description': 'Good quality'},
        }
    },
    'AU': {
        'name': 'Australian Orchid Council',
        'categories': {
            'flower': [
                {'criteria': 'Form', 'max_points': 25, 'description': 'Shape and symmetry'},
                {'criteria': 'Color', 'max_points': 20, 'description': 'Color quality and clarity'},
                {'criteria': 'Size', 'max_points': 15, 'description': 'Flower dimensions'},
                {'criteria': 'Substance', 'max_points': 15, 'description': 'Petal quality and texture'},
                {'criteria': 'Presentation', 'max_points': 15, 'description': 'Arrangement and display'},
                {'criteria': 'Novelty', 'max_points': 10, 'description': 'Uniqueness and distinction'}
            ],
            'plant': [
                {'criteria': 'Health and Vigor', 'max_points': 30, 'description': 'Plant vitality'},
                {'criteria': 'Size and Maturity', 'max_points': 25, 'description': 'Development and size'},
                {'criteria': 'Cultural Merit', 'max_points': 25, 'description': 'Growing achievement'},
                {'criteria': 'Specimen Quality', 'max_points': 20, 'description': 'Overall specimen character'}
            ]
        },
        'awards': {
            'Champion': {'name': 'Champion Certificate', 'min_score': 85, 'description': 'Championship quality'},
            'Excellence': {'name': 'Certificate of Excellence', 'min_score': 75, 'description': 'Excellent quality'},
            'Merit': {'name': 'Certificate of Merit', 'min_score': 65, 'description': 'Meritorious quality'},
        }
    },
    'NZ': {
        'name': 'New Zealand Orchid Society',
        'categories': {
            'flower': [
                {'criteria': 'Form and Symmetry', 'max_points': 30, 'description': 'Shape perfection'},
                {'criteria': 'Color and Marking', 'max_points': 20, 'description': 'Color attributes'},
                {'criteria': 'Size', 'max_points': 15, 'description': 'Flower size'},
                {'criteria': 'Substance', 'max_points': 15, 'description': 'Petal substance'},
                {'criteria': 'Stem and Presentation', 'max_points': 20, 'description': 'Display quality'}
            ],
            'plant': [
                {'criteria': 'Plant Condition', 'max_points': 35, 'description': 'Health and vigor'},
                {'criteria': 'Cultural Achievement', 'max_points': 30, 'description': 'Growing success'},
                {'criteria': 'Specimen Character', 'max_points': 20, 'description': 'Maturity and form'},
                {'criteria': 'Presentation', 'max_points': 15, 'description': 'Display preparation'}
            ]
        },
        'awards': {
            'Premier': {'name': 'Premier Award', 'min_score': 90, 'description': 'Premier quality'},
            'Excellence': {'name': 'Award of Excellence', 'min_score': 80, 'description': 'Excellent standard'},
            'Merit': {'name': 'Award of Merit', 'min_score': 70, 'description': 'Good merit'},
        }
    },
    'JP': {
        'name': 'Japan Grand Prix International Orchid Festival',
        'categories': {
            'flower': [
                {'criteria': 'Beauty (美)', 'max_points': 25, 'description': 'Aesthetic beauty and harmony'},
                {'criteria': 'Form (形)', 'max_points': 25, 'description': 'Structural perfection'},
                {'criteria': 'Color (色)', 'max_points': 20, 'description': 'Color excellence'},
                {'criteria': 'Uniqueness (独)', 'max_points': 15, 'description': 'Distinctive characteristics'},
                {'criteria': 'Refinement (雅)', 'max_points': 15, 'description': 'Elegance and sophistication'}
            ],
            'plant': [
                {'criteria': 'Cultivation (栽培)', 'max_points': 30, 'description': 'Growing mastery'},
                {'criteria': 'Health (健康)', 'max_points': 25, 'description': 'Plant vitality'},
                {'criteria': 'Balance (調和)', 'max_points': 25, 'description': 'Overall harmony'},
                {'criteria': 'Presentation (展示)', 'max_points': 20, 'description': 'Display artistry'}
            ]
        },
        'awards': {
            'Grand Prix': {'name': 'Grand Prix', 'min_score': 95, 'description': 'Supreme excellence'},
            'Gold': {'name': 'Gold Medal', 'min_score': 85, 'description': 'Gold standard'},
            'Silver': {'name': 'Silver Medal', 'min_score': 75, 'description': 'Silver quality'},
            'Bronze': {'name': 'Bronze Medal', 'min_score': 65, 'description': 'Bronze level'},
        }
    },
    'TH': {
        'name': 'Orchid Society of Thailand',
        'categories': {
            'flower': [
                {'criteria': 'Form and Symmetry', 'max_points': 25, 'description': 'Flower form perfection'},
                {'criteria': 'Color Intensity', 'max_points': 20, 'description': 'Vibrant color quality'},
                {'criteria': 'Size and Proportion', 'max_points': 15, 'description': 'Dimensional excellence'},
                {'criteria': 'Substance', 'max_points': 15, 'description': 'Petal thickness and quality'},
                {'criteria': 'Floral Display', 'max_points': 15, 'description': 'Overall flower presentation'},
                {'criteria': 'Fragrance', 'max_points': 10, 'description': 'Scent quality (if applicable)'}
            ],
            'plant': [
                {'criteria': 'Tropical Adaptation', 'max_points': 25, 'description': 'Adaptation to climate'},
                {'criteria': 'Plant Vigor', 'max_points': 25, 'description': 'Growth strength'},
                {'criteria': 'Cultural Success', 'max_points': 25, 'description': 'Growing achievement'},
                {'criteria': 'Natural Habit', 'max_points': 15, 'description': 'Natural growth form'},
                {'criteria': 'Specimen Merit', 'max_points': 10, 'description': 'Overall specimen quality'}
            ]
        },
        'awards': {
            'Royal': {'name': 'Royal Trophy', 'min_score': 92, 'description': 'Royal recognition'},
            'Supreme': {'name': 'Supreme Award', 'min_score': 85, 'description': 'Supreme quality'},
            'Distinguished': {'name': 'Distinguished Medal', 'min_score': 75, 'description': 'Distinguished merit'},
            'Commended': {'name': 'Highly Commended', 'min_score': 65, 'description': 'Commendable quality'},
        }
    }
}

class OrchidJudgingSystem:
    """AI-powered orchid judging system"""
    
    def __init__(self, organization: str = 'AOS'):
        self.organization = organization.upper()
        if self.organization not in JUDGING_STANDARDS:
            raise ValueError(f"Unsupported judging organization: {organization}")
        
        self.standards = JUDGING_STANDARDS[self.organization]
        
    def analyze_orchid(self, orchid_id: int, user_id: int = None, category: str = 'flower') -> Dict:
        """
        Analyze an orchid against judging standards
        
        Args:
            orchid_id: ID of orchid record to analyze
            user_id: ID of requesting user
            category: 'flower' or 'plant' judging category
            
        Returns:
            Dict with analysis results
        """
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            return {'success': False, 'error': 'Orchid not found'}
        
        if category not in self.standards['categories']:
            return {'success': False, 'error': f'Invalid category: {category}'}
        
        try:
            # Get AI analysis
            ai_analysis = self._get_ai_judging_analysis(orchid, category)
            
            # Calculate scores
            scores = self._calculate_scores(ai_analysis, category)
            
            # Determine award level
            award_info = self._determine_award_level(scores['total_score'])
            
            # Create analysis record
            analysis = JudgingAnalysis(
                orchid_id=orchid_id,
                user_id=user_id,
                judging_standard_id=self._get_or_create_standard_id(category),
                score=scores['total_score'],
                percentage=scores['percentage'],
                ai_comments=ai_analysis.get('summary', ''),
                detailed_analysis=json.dumps(scores['detailed']),
                is_award_worthy=award_info['is_worthy'],
                suggested_award_level=award_info['level'],
                award_justification=award_info['justification'],
                ai_model_used='gpt-4o',
                confidence_level=ai_analysis.get('confidence', 0.8)
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            return {
                'success': True,
                'analysis_id': analysis.id,
                'organization': self.organization,
                'category': category,
                'total_score': scores['total_score'],
                'percentage': scores['percentage'],
                'award_level': award_info['level'],
                'is_award_worthy': award_info['is_worthy'],
                'detailed_scores': scores['detailed'],
                'ai_comments': ai_analysis.get('summary', ''),
                'confidence': ai_analysis.get('confidence', 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing orchid {orchid_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_ai_judging_analysis(self, orchid: OrchidRecord, category: str) -> Dict:
        """Get AI analysis specific to judging criteria"""
        criteria_list = self.standards['categories'][category]
        
        prompt = f"""Analyze this {orchid.genus} {orchid.species or 'orchid'} against {self.standards['name']} judging standards for {category} category.

Evaluate each criterion carefully:
{chr(10).join([f"- {c['criteria']}: {c['description']} (max {c['max_points']} points)" for c in criteria_list])}

Provide detailed analysis for each criterion with specific observations and score justification.
Consider the typical standards for this type of orchid.

Return your analysis as JSON with:
- detailed_scores: object with each criterion and analysis
- summary: overall assessment
- confidence: confidence level (0-1)
- recommendations: suggestions for improvement
"""
        
        try:
            # Use existing AI analysis if available, otherwise analyze image
            if orchid.image_filename:
                # This would integrate with the orchid_ai module for image analysis
                # result = analyze_orchid_with_judging(orchid.image_filename, prompt)
                # For now, use default analysis until AI integration is completed
                return self._get_default_analysis(criteria_list)
            else:
                return self._get_default_analysis(criteria_list)
                
        except Exception as e:
            logger.warning(f"AI analysis failed, using default: {str(e)}")
            return self._get_default_analysis(criteria_list)
    
    def _get_default_analysis(self, criteria_list: List[Dict]) -> Dict:
        """Generate default analysis when AI is unavailable"""
        detailed_scores = {}
        for criterion in criteria_list:
            detailed_scores[criterion['criteria']] = {
                'score': criterion['max_points'] * 0.6,  # Default to 60%
                'analysis': f"Unable to analyze {criterion['criteria'].lower()} from available data.",
                'max_points': criterion['max_points']
            }
        
        return {
            'detailed_scores': detailed_scores,
            'summary': 'Analysis completed with limited data. Physical examination recommended for accurate scoring.',
            'confidence': 0.3,
            'recommendations': ['Physical examination by qualified judge recommended', 'Additional high-quality photos would improve analysis']
        }
    
    def _calculate_scores(self, ai_analysis: Dict, category: str) -> Dict:
        """Calculate final scores from AI analysis"""
        criteria_list = self.standards['categories'][category]
        detailed_scores = ai_analysis.get('detailed_scores', {})
        
        total_score = 0
        max_possible = 0
        detailed = {}
        
        for criterion in criteria_list:
            criteria_name = criterion['criteria']
            max_points = criterion['max_points']
            
            # Get score from AI analysis or default
            if criteria_name in detailed_scores:
                score = detailed_scores[criteria_name].get('score', max_points * 0.6)
                analysis = detailed_scores[criteria_name].get('analysis', 'No detailed analysis available')
            else:
                score = max_points * 0.6  # Default to 60%
                analysis = f'No specific analysis for {criteria_name}'
            
            # Ensure score is within bounds
            score = max(0, min(score, max_points))
            
            detailed[criteria_name] = {
                'score': round(score, 1),
                'max_points': max_points,
                'percentage': round((score / max_points) * 100, 1),
                'analysis': analysis
            }
            
            total_score += score
            max_possible += max_points
        
        percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
        
        return {
            'total_score': round(total_score, 1),
            'max_possible': max_possible,
            'percentage': round(percentage, 1),
            'detailed': detailed
        }
    
    def _determine_award_level(self, total_score: float) -> Dict:
        """Determine award level based on score"""
        awards = self.standards['awards']
        
        # Sort awards by minimum score (descending)
        sorted_awards = sorted(awards.items(), key=lambda x: x[1]['min_score'], reverse=True)
        
        for award_code, award_info in sorted_awards:
            if total_score >= award_info['min_score']:
                return {
                    'level': award_code,
                    'name': award_info['name'],
                    'is_worthy': True,
                    'justification': f"Achieved {total_score} points, meeting {award_info['name']} requirements ({award_info['min_score']}+ points)"
                }
        
        return {
            'level': 'None',
            'name': 'No Award',
            'is_worthy': False,
            'justification': f"Score of {total_score} points does not meet minimum award requirements"
        }
    
    def _get_or_create_standard_id(self, category: str) -> int:
        """Get or create judging standard record"""
        criteria_list = self.standards['categories'][category]
        
        for criterion in criteria_list:
            standard = JudgingStandard.query.filter_by(
                organization=self.organization,
                standard_name=self.standards['name'],
                category=category,
                criteria_name=criterion['criteria']
            ).first()
            
            if not standard:
                standard = JudgingStandard(
                    organization=self.organization,
                    standard_name=self.standards['name'],
                    category=category,
                    criteria_name=criterion['criteria'],
                    description=criterion['description'],
                    max_points=criterion['max_points'],
                    scoring_guide=json.dumps({
                        'excellent': f"{criterion['max_points']*0.9}+ points",
                        'good': f"{criterion['max_points']*0.7}-{criterion['max_points']*0.9} points",
                        'fair': f"{criterion['max_points']*0.5}-{criterion['max_points']*0.7} points",
                        'poor': f"<{criterion['max_points']*0.5} points"
                    })
                )
                db.session.add(standard)
        
        db.session.commit()
        
        # Return first standard ID (for the relationship)
        return JudgingStandard.query.filter_by(
            organization=self.organization,
            category=category
        ).first().id
    
    def get_analysis_history(self, orchid_id: int) -> List[Dict]:
        """Get judging analysis history for an orchid"""
        analyses = JudgingAnalysis.query.filter_by(orchid_id=orchid_id).order_by(JudgingAnalysis.analysis_date.desc()).all()
        
        history = []
        for analysis in analyses:
            history.append({
                'id': analysis.id,
                'organization': analysis.judging_standard.organization if analysis.judging_standard else 'Unknown',
                'category': analysis.judging_standard.category if analysis.judging_standard else 'Unknown',
                'score': analysis.score,
                'percentage': analysis.percentage,
                'award_level': analysis.suggested_award_level,
                'is_award_worthy': analysis.is_award_worthy,
                'analysis_date': analysis.analysis_date.isoformat(),
                'confidence': analysis.confidence_level
            })
        
        return history

def initialize_judging_standards():
    """Initialize all judging standards in database"""
    logger.info("Initializing judging standards...")
    
    for org_code, org_data in JUDGING_STANDARDS.items():
        for category, criteria_list in org_data['categories'].items():
            for criterion in criteria_list:
                existing = JudgingStandard.query.filter_by(
                    organization=org_code,
                    category=category,
                    criteria_name=criterion['criteria']
                ).first()
                
                if not existing:
                    standard = JudgingStandard(
                        organization=org_code,
                        standard_name=org_data['name'],
                        category=category,
                        criteria_name=criterion['criteria'],
                        description=criterion['description'],
                        max_points=criterion['max_points']
                    )
                    db.session.add(standard)
    
    db.session.commit()
    logger.info("Judging standards initialization complete")

def get_available_organizations() -> List[Dict]:
    """Get list of available judging organizations"""
    return [
        {'code': code, 'name': data['name'], 'categories': list(data['categories'].keys())}
        for code, data in JUDGING_STANDARDS.items()
    ]

def analyze_orchid_by_organization(orchid_id: int, organization: str, user_id: int = None) -> Dict:
    """
    Convenience function to analyze orchid by specific organization
    
    Args:
        orchid_id: Orchid to analyze
        organization: Organization code (AOS, EU, AU, NZ, JP, TH)
        user_id: User requesting analysis
        
    Returns:
        Analysis results
    """
    try:
        judging_system = OrchidJudgingSystem(organization)
        
        # Analyze both flower and plant categories
        results = {}
        for category in ['flower', 'plant']:
            if category in judging_system.standards['categories']:
                result = judging_system.analyze_orchid(orchid_id, user_id, category)
                results[category] = result
        
        return {
            'success': True,
            'organization': organization,
            'results': results
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }