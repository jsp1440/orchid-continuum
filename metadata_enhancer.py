"""
Metadata Enhancer for Orchid Continuum
Fills missing fields and discovers additional metadata from botanical databases and AI analysis
"""

import logging
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai
import os

logger = logging.getLogger(__name__)

class MetadataEnhancer:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        self.botanical_databases = {
            'rhs': 'https://www.rhs.org.uk/plants',
            'aos': 'https://www.aos.org',
            'wcsp': 'https://wcsp.science.kew.org.uk',
            'worldplants': 'https://worldplants.de'
        }
    
    def enhance_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a form submission with additional metadata from multiple sources
        """
        enhanced = {
            'original_submission': submission_data,
            'enhancement_timestamp': datetime.now().isoformat(),
            'enhanced_fields': {},
            'ai_analysis': {},
            'botanical_data': {},
            'cultural_requirements': {},
            'judging_analysis': {},
            'photo_analysis': {},
            'morphological_tags': [],
            'ecological_data': {},
            'processing_log': []
        }
        
        try:
            # Extract validated taxonomy
            validated_name = submission_data.get('validated_name', '')
            genus = submission_data.get('validated_genus', '')
            species = submission_data.get('validated_species', '')
            
            # Enhance with botanical database information
            botanical_data = self._get_botanical_database_info(validated_name, genus, species)
            enhanced['botanical_data'] = botanical_data
            
            # Fill missing fields from submission
            enhanced_fields = self._fill_missing_fields(submission_data, botanical_data)
            enhanced['enhanced_fields'] = enhanced_fields
            
            # AI-powered photo analysis if photo URL provided
            photo_url = submission_data.get('photo_url')
            if photo_url and self.openai_client:
                ai_analysis = self._analyze_photo_with_ai(photo_url, validated_name)
                enhanced['ai_analysis'] = ai_analysis
                enhanced['photo_analysis'] = ai_analysis.get('photo_analysis', {})
                enhanced['morphological_tags'] = ai_analysis.get('morphological_tags', [])
            
            # Generate cultural requirements with photoperiod analysis
            cultural_reqs = self._generate_cultural_requirements(genus, species, botanical_data)
            enhanced['cultural_requirements'] = cultural_reqs
            
            # Add comprehensive photoperiod analysis
            photoperiod_data = self._analyze_photoperiod_requirements(genus, species, botanical_data, ai_analysis)
            if photoperiod_data:
                enhanced['photoperiod_analysis'] = photoperiod_data
            
            # Perform judging analysis
            judging_analysis = self._perform_judging_analysis(submission_data, enhanced['ai_analysis'])
            enhanced['judging_analysis'] = judging_analysis
            
            # Extract ecological data
            ecological_data = self._extract_ecological_data(botanical_data, enhanced['ai_analysis'])
            enhanced['ecological_data'] = ecological_data
            
            enhanced['processing_log'].append(f"Enhancement completed at {datetime.now().isoformat()}")
            
        except Exception as e:
            logger.error(f"Error enhancing submission: {e}")
            enhanced['processing_log'].append(f"Enhancement error: {str(e)}")
        
        return enhanced
    
    def _get_botanical_database_info(self, validated_name: str, genus: str, species: str) -> Dict[str, Any]:
        """Query botanical databases for additional information"""
        database_info = {
            'family': '',
            'subfamily': '',
            'distribution': '',
            'habitat': '',
            'conservation_status': '',
            'synonyms': [],
            'common_names': [],
            'flowering_season': '',
            'plant_size': '',
            'flower_size': '',
            'fragrance': '',
            'sources': []
        }
        
        # Enhanced genus-specific information
        genus_data = self._get_genus_specific_info(genus)
        database_info.update(genus_data)
        
        # For production, this would query real databases
        # For now, we provide enhanced mock data based on common orchid knowledge
        
        return database_info
    
    def _get_genus_specific_info(self, genus: str) -> Dict[str, Any]:
        """Get genus-specific information"""
        genus_info = {
            'Phalaenopsis': {
                'family': 'Orchidaceae',
                'subfamily': 'Epidendroideae',
                'tribe': 'Vandeae',
                'distribution': 'Southeast Asia, Philippines, Indonesia',
                'habitat': 'Epiphytic in lowland tropical forests',
                'common_names': ['Moth Orchid'],
                'typical_flowering': 'Winter to Spring',
                'light_requirements': 'Low to medium light (1000-1500 fc)',
                'temperature_range': '65-80°F (18-27°C)',
                'humidity_preference': '50-70%',
                'watering_frequency': 'Weekly, allow to dry between waterings',
                'growing_medium': 'Coarse bark mix with perlite'
            },
            'Cattleya': {
                'family': 'Orchidaceae',
                'subfamily': 'Epidendroideae',
                'tribe': 'Epidendreae',
                'distribution': 'Central and South America',
                'habitat': 'Epiphytic in cloud forests and humid regions',
                'common_names': ['Corsage Orchid', 'Queen of Orchids'],
                'typical_flowering': 'Variable, often fall to spring',
                'light_requirements': 'Medium to high light (2000-3000 fc)',
                'temperature_range': '60-85°F (15-29°C)',
                'humidity_preference': '50-80%',
                'watering_frequency': 'When pseudobulbs begin to wrinkle',
                'growing_medium': 'Coarse bark with good drainage'
            },
            'Dendrobium': {
                'family': 'Orchidaceae',
                'subfamily': 'Epidendroideae',
                'distribution': 'Asia, Australia, Pacific Islands',
                'habitat': 'Diverse habitats from sea level to mountains',
                'common_names': ['Dendrobium'],
                'typical_flowering': 'Spring to summer',
                'light_requirements': 'Medium to high light (2000-4000 fc)',
                'temperature_range': 'Variable by species (50-90°F)',
                'humidity_preference': '50-70%',
                'watering_frequency': 'Regular during growing season, reduce in winter',
                'growing_medium': 'Well-draining bark mix'
            }
        }
        
        return genus_info.get(genus, {})
    
    def _fill_missing_fields(self, submission: Dict[str, Any], botanical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in missing fields from the original submission using botanical data"""
        filled_fields = {}
        
        # Field mappings from botanical data to submission fields
        field_mappings = {
            'family': botanical_data.get('family', ''),
            'distribution': botanical_data.get('distribution', ''),
            'habitat': botanical_data.get('habitat', ''),
            'common_names': ', '.join(botanical_data.get('common_names', [])),
            'flowering_season': botanical_data.get('typical_flowering', ''),
            'light_requirements': botanical_data.get('light_requirements', ''),
            'temperature_range': botanical_data.get('temperature_range', ''),
            'humidity_preference': botanical_data.get('humidity_preference', ''),
            'watering_notes': botanical_data.get('watering_frequency', ''),
            'growing_medium': botanical_data.get('growing_medium', '')
        }
        
        for field, value in field_mappings.items():
            if not submission.get(field) and value:
                filled_fields[field] = value
        
        return filled_fields
    
    def _analyze_photo_with_ai(self, photo_url: str, orchid_name: str) -> Dict[str, Any]:
        """Use AI to analyze the orchid photo for additional metadata"""
        if not self.openai_client:
            return {'error': 'OpenAI client not available'}
        
        try:
            # Comprehensive AI analysis prompt
            analysis_prompt = f"""
            Analyze this orchid photo ({orchid_name}) and provide detailed botanical analysis:

            1. MORPHOLOGICAL ANALYSIS:
            - Flower structure, shape, and arrangement
            - Color patterns and variations
            - Size estimation
            - Petal/sepal characteristics
            - Lip structure and markings
            - Column characteristics

            2. PLANT CHARACTERISTICS:
            - Growth habit (monopodial/sympodial)
            - Leaf structure and arrangement
            - Pseudobulb presence and characteristics
            - Root visibility and health

            3. CONDITION ASSESSMENT:
            - Overall plant health
            - Flowering stage
            - Growing environment indicators
            - Cultural care observations

            4. IDENTIFICATION MARKERS:
            - Species-specific features
            - Hybrid characteristics if applicable
            - Distinguishing features from similar species

            5. JUDGING ANALYSIS:
            - Form and structure quality
            - Color intensity and clarity
            - Size relative to species standard
            - Presentation and arrangement
            - Overall quality rating (1-10)

            Provide detailed, scientific observations in JSON format.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": photo_url}
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to structured text
            try:
                analysis_data = json.loads(ai_response)
            except:
                analysis_data = self._parse_ai_response_text(ai_response)
            
            return {
                'photo_analysis': analysis_data,
                'morphological_tags': self._extract_morphological_tags(analysis_data),
                'quality_assessment': analysis_data.get('overall_quality_rating', 0),
                'ai_confidence': analysis_data.get('identification_confidence', 0),
                'processing_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI photo analysis: {e}")
            return {'error': str(e)}
    
    def _parse_ai_response_text(self, text: str) -> Dict[str, Any]:
        """Parse AI response text into structured data"""
        # Basic parsing for non-JSON responses
        return {
            'analysis_text': text,
            'parsed': True,
            'structure': 'text'
        }
    
    def _extract_morphological_tags(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract morphological tags from AI analysis"""
        tags = []
        
        # Extract tags from various analysis sections
        if isinstance(analysis_data, dict):
            for key, value in analysis_data.items():
                if isinstance(value, str):
                    # Extract descriptive words
                    words = value.lower().split()
                    botanical_terms = [
                        'spotted', 'striped', 'fragrant', 'large', 'small', 'white', 'pink', 'purple',
                        'yellow', 'red', 'green', 'waxy', 'velvety', 'glossy', 'matte', 'ruffled',
                        'flat', 'cupped', 'reflexed', 'twisted', 'fringed', 'solid', 'gradient'
                    ]
                    tags.extend([word for word in words if word in botanical_terms])
        
        return list(set(tags))  # Remove duplicates
    
    def _generate_cultural_requirements(self, genus: str, species: str, botanical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive cultural requirements"""
        base_requirements = botanical_data.copy()
        
        # Add specific cultural guidance
        cultural_guide = {
            'light': {
                'requirement': base_requirements.get('light_requirements', 'Medium light'),
                'details': 'Place in bright, indirect light. Avoid direct sunlight.',
                'seasonal_changes': 'May need supplemental lighting in winter.'
            },
            'temperature': {
                'range': base_requirements.get('temperature_range', '65-80°F'),
                'day_night_differential': '10-15°F difference recommended',
                'seasonal_requirements': 'Cool period may trigger flowering'
            },
            'humidity': {
                'preference': base_requirements.get('humidity_preference', '50-70%'),
                'methods': 'Use humidity trays, grouping plants, or humidifier',
                'air_circulation': 'Good air movement essential to prevent fungal issues'
            },
            'watering': {
                'frequency': base_requirements.get('watering_frequency', 'Weekly'),
                'method': 'Water thoroughly, allow excess to drain',
                'water_quality': 'Use rainwater or distilled water if tap water is hard',
                'seasonal_adjustments': 'Reduce watering in cooler months'
            },
            'fertilizing': {
                'frequency': 'Weekly weakly (1/4 strength balanced fertilizer)',
                'type': '20-20-20 or orchid-specific fertilizer',
                'seasonal_changes': 'Reduce in winter, increase during active growth'
            },
            'repotting': {
                'frequency': 'Every 1-2 years or when medium breaks down',
                'timing': 'Best after flowering, during new growth',
                'medium': base_requirements.get('growing_medium', 'Bark-based orchid mix')
            },
            'photoperiod': {
                'importance': 'Critical for flowering in most orchids',
                'optimal_hours': base_requirements.get('light_duration', '12 hours'),
                'seasonal_variation': 'Natural seasonal changes help trigger blooming',
                'notes': 'Day length often more important than light intensity for flowering'
            }
        }
        
        return cultural_guide
    
    def _perform_judging_analysis(self, submission: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform orchid judging analysis based on AOS/RHS standards"""
        judging_criteria = {
            'form': {'score': 0, 'notes': '', 'max_points': 30},
            'color': {'score': 0, 'notes': '', 'max_points': 20},
            'size': {'score': 0, 'notes': '', 'max_points': 15},
            'substance': {'score': 0, 'notes': '', 'max_points': 15},
            'arrangement': {'score': 0, 'notes': '', 'max_points': 10},
            'floriferousness': {'score': 0, 'notes': '', 'max_points': 10}
        }
        
        # Use AI analysis data if available
        if ai_analysis and 'photo_analysis' in ai_analysis:
            photo_analysis = ai_analysis['photo_analysis']
            
            # Extract judging scores from AI analysis
            if isinstance(photo_analysis, dict):
                judging_criteria['form']['score'] = photo_analysis.get('form_score', 20)
                judging_criteria['color']['score'] = photo_analysis.get('color_score', 15)
                judging_criteria['size']['score'] = photo_analysis.get('size_score', 12)
                judging_criteria['substance']['score'] = photo_analysis.get('substance_score', 12)
                judging_criteria['arrangement']['score'] = photo_analysis.get('arrangement_score', 8)
                judging_criteria['floriferousness']['score'] = photo_analysis.get('flower_count_score', 8)
        
        # Calculate total score
        total_score = sum(criterion['score'] for criterion in judging_criteria.values())
        max_score = sum(criterion['max_points'] for criterion in judging_criteria.values())
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        
        return {
            'criteria_scores': judging_criteria,
            'total_score': total_score,
            'max_possible': max_score,
            'percentage': percentage,
            'award_recommendation': self._determine_award_level(percentage),
            'judging_notes': 'AI-assisted analysis based on submitted photo'
        }
    
    def _determine_award_level(self, percentage: float) -> str:
        """Determine award recommendation based on percentage score"""
        if percentage >= 90:
            return "First Class Certificate (FCC) potential"
        elif percentage >= 80:
            return "Award of Merit (AM) potential"
        elif percentage >= 75:
            return "Highly Commended Certificate (HCC) potential"
        elif percentage >= 70:
            return "Certificate of Botanical Merit potential"
        else:
            return "Needs improvement for award consideration"
    
    def _extract_ecological_data(self, botanical_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ecological and environmental data"""
        return {
            'native_habitat': botanical_data.get('habitat', ''),
            'distribution': botanical_data.get('distribution', ''),
            'conservation_status': botanical_data.get('conservation_status', 'Not Evaluated'),
            'ecological_role': 'Epiphytic orchid in tropical ecosystem',
            'pollinators': 'Various insects, species-specific',
            'threats': 'Habitat loss, climate change, overcollection',
            'cultivation_impact': 'Reduces pressure on wild populations'
        }