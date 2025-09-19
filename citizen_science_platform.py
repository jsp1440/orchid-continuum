"""
Citizen Science Platform for Wild Orchid Conservation
Native Species Photography Integration with Genetic Analysis

This module provides tools for native orchid photographers and researchers
to contribute to conservation science through systematic photo documentation
and trait analysis of wild orchid populations.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import exifread
from models import OrchidRecord, db
from orchid_ai import analyze_orchid_image
from eol_integration import eol_integrator

logger = logging.getLogger(__name__)

# Create blueprint for citizen science routes
citizen_science_bp = Blueprint('citizen_science', __name__, url_prefix='/citizen-science')

class CitizenSciencePlatform:
    """
    Platform for coordinating citizen science orchid photography projects
    with conservation organizations and native species societies
    """
    
    def __init__(self):
        self.partner_organizations = {
            'native_orchid_society': {
                'name': 'Native Orchid Society',
                'contact': 'research@nativeorchidsociety.org',
                'specialties': ['North American native orchids', 'habitat documentation'],
                'active_projects': ['Prairie orchid monitoring', 'Forest fragmentation impact']
            },
            'north_american_orchid_conservation': {
                'name': 'North American Orchid Conservation Center',
                'contact': 'conservation@naocc.org',
                'specialties': ['Endangered species monitoring', 'Population genetics'],
                'active_projects': ['Cypripedium recovery', 'Platanthera surveys']
            },
            'international_orchid_foundation': {
                'name': 'International Orchid Foundation',
                'contact': 'research@orchid-foundation.org',
                'specialties': ['Global orchid diversity', 'Climate impact studies'],
                'active_projects': ['Tropical orchid surveys', 'Elevation gradient studies']
            }
        }
        
        self.submission_categories = {
            'wild_population_survey': {
                'title': 'Wild Population Survey',
                'description': 'Document entire wild orchid populations for genetic analysis',
                'required_data': ['GPS coordinates', 'population count', 'habitat description'],
                'analysis_focus': 'Population genetics and selection pressures'
            },
            'rare_species_documentation': {
                'title': 'Rare Species Documentation',
                'description': 'Document rare or endangered orchid species',
                'required_data': ['Precise location', 'threat assessment', 'conservation status'],
                'analysis_focus': 'Conservation priority and threat analysis'
            },
            'phenology_monitoring': {
                'title': 'Phenology Monitoring',
                'description': 'Track flowering times and seasonal patterns',
                'required_data': ['Flowering stage', 'environmental conditions', 'climate data'],
                'analysis_focus': 'Climate change impact analysis'
            },
            'habitat_characterization': {
                'title': 'Habitat Characterization',
                'description': 'Document orchid habitats and ecological relationships',
                'required_data': ['Soil conditions', 'associated species', 'microclimate'],
                'analysis_focus': 'Habitat preferences and requirements'
            },
            'pollinator_interaction': {
                'title': 'Pollinator Interaction Studies',
                'description': 'Document orchid-pollinator relationships',
                'required_data': ['Pollinator species', 'interaction frequency', 'time of day'],
                'analysis_focus': 'Pollination ecology and specialization'
            }
        }
    
    def create_submission_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new citizen science project for orchid documentation
        """
        try:
            project = {
                'project_id': f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'title': project_data.get('title'),
                'description': project_data.get('description'),
                'category': project_data.get('category'),
                'target_species': project_data.get('target_species', []),
                'geographic_focus': project_data.get('geographic_focus'),
                'partner_organization': project_data.get('partner_organization'),
                'project_lead': project_data.get('project_lead'),
                'start_date': project_data.get('start_date'),
                'end_date': project_data.get('end_date'),
                'submission_guidelines': self._generate_submission_guidelines(project_data),
                'data_requirements': self.submission_categories.get(
                    project_data.get('category'), {}
                ).get('required_data', []),
                'created_date': datetime.utcnow().isoformat(),
                'status': 'active',
                'submissions_count': 0,
                'contributors': [],
                'analysis_results': {}
            }
            
            # Store project data
            self._store_project(project)
            
            # Generate project webpage and submission forms
            project_page = self._generate_project_page(project)
            
            return {
                'success': True,
                'project_id': project['project_id'],
                'project_url': f"/citizen-science/projects/{project['project_id']}",
                'submission_url': f"/citizen-science/submit/{project['project_id']}",
                'project_data': project
            }
            
        except Exception as e:
            logger.error(f"Error creating citizen science project: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_wild_orchid_submission(self, submission_data: Dict[str, Any], photo_files: List) -> Dict[str, Any]:
        """
        Process citizen science submission of wild orchid photos
        """
        try:
            # Validate submission data
            validation_result = self._validate_submission(submission_data)
            if not validation_result['valid']:
                return {'success': False, 'errors': validation_result['errors']}
            
            # Process photos and extract metadata
            processed_photos = []
            for photo_file in photo_files:
                photo_analysis = self._process_citizen_photo(photo_file, submission_data)
                if photo_analysis['success']:
                    processed_photos.append(photo_analysis['data'])
            
            # Create submission record
            submission_record = {
                'submission_id': f"cs_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'project_id': submission_data.get('project_id'),
                'contributor_name': submission_data.get('contributor_name'),
                'contributor_email': submission_data.get('contributor_email'),
                'organization': submission_data.get('organization'),
                'submission_date': datetime.utcnow().isoformat(),
                'species_name': submission_data.get('species_name'),
                'location': {
                    'latitude': submission_data.get('latitude'),
                    'longitude': submission_data.get('longitude'),
                    'location_description': submission_data.get('location_description'),
                    'habitat_description': submission_data.get('habitat_description')
                },
                'observation_details': {
                    'observation_date': submission_data.get('observation_date'),
                    'population_count': submission_data.get('population_count'),
                    'flowering_stage': submission_data.get('flowering_stage'),
                    'environmental_conditions': submission_data.get('environmental_conditions'),
                    'threats_observed': submission_data.get('threats_observed', []),
                    'associated_species': submission_data.get('associated_species', [])
                },
                'photos': processed_photos,
                'ai_analysis_summary': self._summarize_ai_analysis(processed_photos),
                'validation_status': 'pending_review',
                'conservation_flags': self._identify_conservation_flags(submission_data, processed_photos)
            }
            
            # Store submission
            self._store_submission(submission_record)
            
            # Submit to EOL if configured
            eol_submission = None
            if eol_integrator.api_key:
                eol_submission = self._submit_to_eol(submission_record)
            
            # Generate contributor feedback
            feedback = self._generate_contributor_feedback(submission_record, eol_submission)
            
            return {
                'success': True,
                'submission_id': submission_record['submission_id'],
                'photos_processed': len(processed_photos),
                'ai_analysis': submission_record['ai_analysis_summary'],
                'conservation_flags': submission_record['conservation_flags'],
                'eol_submission': eol_submission,
                'feedback': feedback
            }
            
        except Exception as e:
            logger.error(f"Error processing citizen science submission: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_population_genetics(self, project_id: str) -> Dict[str, Any]:
        """
        Analyze genetic patterns across all submissions for a project
        """
        try:
            project_submissions = self._get_project_submissions(project_id)
            
            if not project_submissions:
                return {'error': 'No submissions found for project'}
            
            # Aggregate photo analysis data
            all_photos = []
            for submission in project_submissions:
                all_photos.extend(submission.get('photos', []))
            
            # Use EOL integration for population analysis
            population_analysis = eol_integrator.analyze_wild_population_traits(all_photos)
            
            # Generate conservation insights
            conservation_analysis = self._generate_conservation_insights(
                population_analysis, project_submissions
            )
            
            # Create population genetics report
            genetics_report = {
                'project_id': project_id,
                'analysis_date': datetime.utcnow().isoformat(),
                'total_submissions': len(project_submissions),
                'total_photos': len(all_photos),
                'population_analysis': population_analysis,
                'conservation_insights': conservation_analysis,
                'selection_pressures': self._identify_selection_pressures(all_photos),
                'genetic_diversity_assessment': self._assess_genetic_diversity(all_photos),
                'recommendations': self._generate_scientific_recommendations(population_analysis)
            }
            
            # Store analysis results
            self._store_analysis_results(project_id, genetics_report)
            
            return genetics_report
            
        except Exception as e:
            logger.error(f"Error analyzing population genetics: {str(e)}")
            return {'error': str(e)}
    
    def generate_outreach_materials(self, target_organization: str) -> Dict[str, Any]:
        """
        Generate customized outreach materials for partner organizations
        """
        try:
            org_info = self.partner_organizations.get(target_organization)
            if not org_info:
                return {'error': 'Unknown organization'}
            
            # Create customized pitch materials
            materials = {
                'organization': target_organization,
                'organization_info': org_info,
                'pitch_document': self._create_pitch_document(org_info),
                'technical_specifications': self._create_technical_specs(org_info),
                'sample_projects': self._create_sample_projects(org_info),
                'partnership_benefits': self._create_partnership_benefits(org_info),
                'contact_template': self._create_contact_template(org_info),
                'presentation_slides': self._create_presentation_outline(org_info)
            }
            
            return materials
            
        except Exception as e:
            logger.error(f"Error generating outreach materials: {str(e)}")
            return {'error': str(e)}
    
    def _process_citizen_photo(self, photo_file, submission_data: Dict) -> Dict[str, Any]:
        """Process individual citizen science photo"""
        try:
            # Extract EXIF data
            exif_data = self._extract_exif_data(photo_file)
            
            # Run AI analysis
            ai_analysis = analyze_orchid_image(photo_file)
            
            # Enhance analysis with submission context
            enhanced_analysis = self._enhance_analysis_with_context(
                ai_analysis, submission_data, exif_data
            )
            
            return {
                'success': True,
                'data': {
                    'filename': secure_filename(photo_file.filename),
                    'exif_data': exif_data,
                    'ai_analysis': enhanced_analysis,
                    'quality_score': self._calculate_photo_quality(exif_data, enhanced_analysis),
                    'conservation_value': self._assess_conservation_value(enhanced_analysis, submission_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing citizen photo: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_exif_data(self, photo_file) -> Dict[str, Any]:
        """Extract EXIF metadata from photo"""
        try:
            exif_data = {}
            
            # Read EXIF data
            photo_file.seek(0)
            tags = exifread.process_file(photo_file)
            
            for tag, value in tags.items():
                if tag not in ['JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote']:
                    exif_data[tag] = str(value)
            
            # Extract key metadata
            extracted_data = {
                'camera_make': exif_data.get('Image Make', 'Unknown'),
                'camera_model': exif_data.get('Image Model', 'Unknown'),
                'datetime': exif_data.get('EXIF DateTimeOriginal', 'Unknown'),
                'gps_coordinates': self._extract_gps_coordinates(exif_data),
                'focal_length': exif_data.get('EXIF FocalLength', 'Unknown'),
                'aperture': exif_data.get('EXIF FNumber', 'Unknown'),
                'iso': exif_data.get('EXIF ISOSpeedRatings', 'Unknown'),
                'image_dimensions': {
                    'width': exif_data.get('EXIF ExifImageWidth', 'Unknown'),
                    'height': exif_data.get('EXIF ExifImageLength', 'Unknown')
                }
            }
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting EXIF data: {str(e)}")
            return {}
    
    def _extract_gps_coordinates(self, exif_data: Dict) -> Optional[Dict[str, float]]:
        """Extract GPS coordinates from EXIF data"""
        try:
            gps_lat = exif_data.get('GPS GPSLatitude')
            gps_lat_ref = exif_data.get('GPS GPSLatitudeRef')
            gps_lon = exif_data.get('GPS GPSLongitude')
            gps_lon_ref = exif_data.get('GPS GPSLongitudeRef')
            
            if all([gps_lat, gps_lat_ref, gps_lon, gps_lon_ref]):
                # Convert DMS to decimal degrees
                lat = self._dms_to_decimal(gps_lat, gps_lat_ref)
                lon = self._dms_to_decimal(gps_lon, gps_lon_ref)
                
                return {'latitude': lat, 'longitude': lon}
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting GPS coordinates: {str(e)}")
            return None
    
    def _dms_to_decimal(self, dms_str: str, ref: str) -> float:
        """Convert DMS coordinates to decimal degrees"""
        # Parse DMS format: [34, 51, 249/10]
        parts = str(dms_str).strip('[]').split(', ')
        degrees = float(parts[0])
        minutes = float(parts[1])
        
        # Handle fractional seconds
        if '/' in parts[2]:
            num, den = parts[2].split('/')
            seconds = float(num) / float(den)
        else:
            seconds = float(parts[2])
        
        decimal = degrees + minutes/60 + seconds/3600
        
        # Apply hemisphere reference
        if ref in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    
    def _validate_submission(self, submission_data: Dict) -> Dict[str, Any]:
        """Validate citizen science submission data"""
        errors = []
        
        # Required fields
        required_fields = ['contributor_name', 'species_name', 'latitude', 'longitude', 'observation_date']
        for field in required_fields:
            if not submission_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate coordinates
        lat = submission_data.get('latitude')
        lon = submission_data.get('longitude')
        if lat and (lat < -90 or lat > 90):
            errors.append("Invalid latitude: must be between -90 and 90")
        if lon and (lon < -180 or lon > 180):
            errors.append("Invalid longitude: must be between -180 and 180")
        
        # Validate date
        obs_date = submission_data.get('observation_date')
        if obs_date:
            try:
                datetime.fromisoformat(obs_date)
            except ValueError:
                errors.append("Invalid observation date format")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _generate_submission_guidelines(self, project_data: Dict) -> Dict[str, Any]:
        """Generate specific submission guidelines for a project"""
        category = project_data.get('category')
        category_info = self.submission_categories.get(category, {})
        
        guidelines = {
            'photography_requirements': {
                'image_quality': 'High resolution (minimum 2MP), sharp focus on flowers',
                'composition': 'Include whole plant and close-up of flowers',
                'lighting': 'Natural lighting preferred, avoid harsh shadows',
                'multiple_angles': 'Take photos from multiple angles when possible'
            },
            'data_collection': {
                'location_precision': 'GPS coordinates accurate to within 10 meters',
                'population_counting': 'Count all visible flowering plants',
                'habitat_documentation': 'Describe surrounding vegetation and conditions',
                'threat_assessment': 'Note any visible threats or disturbances'
            },
            'metadata_requirements': category_info.get('required_data', []),
            'submission_format': {
                'photo_format': 'JPEG with EXIF data intact',
                'data_format': 'Complete all required fields in submission form',
                'file_naming': 'Use descriptive filenames with date and location'
            }
        }
        
        return guidelines
    
    def _store_project(self, project: Dict):
        """Store citizen science project data"""
        projects_dir = 'citizen_science_projects'
        os.makedirs(projects_dir, exist_ok=True)
        
        filename = f"{project['project_id']}.json"
        filepath = os.path.join(projects_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(project, f, indent=2)
    
    def _store_submission(self, submission: Dict):
        """Store citizen science submission data"""
        submissions_dir = 'citizen_science_submissions'
        os.makedirs(submissions_dir, exist_ok=True)
        
        filename = f"{submission['submission_id']}.json"
        filepath = os.path.join(submissions_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(submission, f, indent=2)
    
    def _create_pitch_document(self, org_info: Dict) -> str:
        """Create customized pitch document for organization"""
        return f"""
        Partnership Proposal: Orchid Continuum Citizen Science Platform
        
        Dear {org_info['name']} Team,
        
        The Orchid Continuum platform offers an unprecedented opportunity to advance
        orchid conservation through systematic citizen science data collection and
        AI-powered genetic analysis.
        
        Your organization's expertise in {', '.join(org_info['specialties'])} 
        perfectly aligns with our platform's capabilities for:
        
        • Automated trait analysis from field photographs
        • Population genetics assessment from citizen observations
        • Conservation priority identification through AI analysis
        • Integration with Encyclopedia of Life TraitBank database
        
        We propose a partnership that would enhance your current projects:
        {chr(10).join(f'• {project}' for project in org_info['active_projects'])}
        
        This collaboration would provide your members with powerful tools for
        documenting wild orchid populations while contributing to global
        conservation science efforts.
        
        Best regards,
        The Orchid Continuum Team
        """
    
    def _create_technical_specs(self, org_info: Dict) -> Dict[str, Any]:
        """Create technical specifications document"""
        return {
            'platform_capabilities': [
                'AI-powered orchid identification and trait analysis',
                'GPS-tagged photo documentation system',
                'Population genetics analysis from photo data',
                'Encyclopedia of Life integration for trait validation',
                'Automated conservation threat assessment'
            ],
            'data_requirements': [
                'High-resolution photos with EXIF data',
                'GPS coordinates (±10m accuracy)',
                'Observation metadata (date, population size, habitat)',
                'Environmental condition documentation'
            ],
            'analysis_outputs': [
                'Species identification confidence scores',
                'Trait variation analysis within populations',
                'Selection pressure identification',
                'Conservation priority recommendations',
                'Genetic diversity assessments'
            ],
            'integration_options': [
                'Custom project creation and management',
                'Branded submission portals for your organization',
                'Data export in Darwin Core standard format',
                'Direct submission to EOL TraitBank',
                'Integration with existing databases'
            ]
        }
    
    def _load_all_projects(self) -> List[Dict]:
        """Load all projects from storage"""
        try:
            projects_dir = 'citizen_science_projects'
            if not os.path.exists(projects_dir):
                return []
            
            projects = []
            for filename in os.listdir(projects_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(projects_dir, filename)
                    with open(filepath, 'r') as f:
                        project = json.load(f)
                        projects.append(project)
            
            return sorted(projects, key=lambda x: x.get('created_date', ''), reverse=True)
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            return []
    
    def _load_project(self, project_id: str) -> Optional[Dict]:
        """Load specific project from storage"""
        try:
            projects_dir = 'citizen_science_projects'
            filepath = os.path.join(projects_dir, f"{project_id}.json")
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading project {project_id}: {str(e)}")
            return None
    
    def _get_project_submissions(self, project_id: str) -> List[Dict]:
        """Get all submissions for a project"""
        try:
            submissions_dir = 'citizen_science_submissions'
            if not os.path.exists(submissions_dir):
                return []
            
            project_submissions = []
            for filename in os.listdir(submissions_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(submissions_dir, filename)
                    with open(filepath, 'r') as f:
                        submission = json.load(f)
                        if submission.get('project_id') == project_id:
                            project_submissions.append(submission)
            
            return project_submissions
        except Exception as e:
            logger.error(f"Error loading project submissions: {str(e)}")
            return []
    
    def _summarize_ai_analysis(self, processed_photos: List[Dict]) -> Dict[str, Any]:
        """Summarize AI analysis results across all photos"""
        if not processed_photos:
            return {}
        
        summary = {
            'total_photos': len(processed_photos),
            'species_identified': set(),
            'average_quality_score': 0,
            'trait_variations': {},
            'conservation_flags': []
        }
        
        total_quality = 0
        for photo in processed_photos:
            ai_analysis = photo.get('ai_analysis', {})
            
            # Collect species
            species = ai_analysis.get('species_name')
            if species:
                summary['species_identified'].add(species)
            
            # Sum quality scores
            quality = photo.get('quality_score', 0)
            total_quality += quality
            
            # Collect traits
            traits = ai_analysis.get('traits', {})
            for trait_name, trait_value in traits.items():
                if trait_name not in summary['trait_variations']:
                    summary['trait_variations'][trait_name] = []
                summary['trait_variations'][trait_name].append(trait_value)
        
        # Calculate averages
        if processed_photos:
            summary['average_quality_score'] = total_quality / len(processed_photos)
        
        # Convert set to list for JSON serialization
        summary['species_identified'] = list(summary['species_identified'])
        
        return summary
    
    def _identify_conservation_flags(self, submission_data: Dict, processed_photos: List[Dict]) -> List[str]:
        """Identify conservation concerns from submission"""
        flags = []
        
        # Check population size
        pop_count = submission_data.get('population_count')
        if pop_count and isinstance(pop_count, int):
            if pop_count < 10:
                flags.append('CRITICAL_SMALL_POPULATION')
            elif pop_count < 50:
                flags.append('VULNERABLE_POPULATION')
        
        # Check threats
        threats = submission_data.get('threats_observed', [])
        if threats:
            flags.append('THREATS_IDENTIFIED')
        
        # Check species rarity (would need database lookup)
        species_name = submission_data.get('species_name', '')
        rare_indicators = ['cypripedium', 'platanthera', 'spiranthes', 'goodyera']
        if any(indicator in species_name.lower() for indicator in rare_indicators):
            flags.append('POTENTIALLY_RARE_SPECIES')
        
        return flags
    
    def _enhance_analysis_with_context(self, ai_analysis: Dict, submission_data: Dict, exif_data: Dict) -> Dict:
        """Enhance AI analysis with submission context"""
        enhanced = ai_analysis.copy()
        
        # Add location context
        enhanced['location_context'] = {
            'coordinates': {
                'latitude': submission_data.get('latitude'),
                'longitude': submission_data.get('longitude')
            },
            'habitat_description': submission_data.get('habitat_description'),
            'elevation': submission_data.get('elevation'),
            'microclimate': submission_data.get('microclimate')
        }
        
        # Add temporal context
        enhanced['temporal_context'] = {
            'observation_date': submission_data.get('observation_date'),
            'flowering_stage': submission_data.get('flowering_stage'),
            'seasonal_context': self._determine_seasonal_context(submission_data.get('observation_date'))
        }
        
        # Add population context
        enhanced['population_context'] = {
            'population_count': submission_data.get('population_count'),
            'associated_species': submission_data.get('associated_species', []),
            'threats_present': submission_data.get('threats_observed', [])
        }
        
        # Add photo metadata
        enhanced['photo_metadata'] = exif_data
        
        return enhanced
    
    def _determine_seasonal_context(self, observation_date: str) -> str:
        """Determine seasonal context from observation date"""
        if not observation_date:
            return 'unknown'
        
        try:
            date_obj = datetime.fromisoformat(observation_date)
            month = date_obj.month
            
            if month in [12, 1, 2]:
                return 'winter'
            elif month in [3, 4, 5]:
                return 'spring'
            elif month in [6, 7, 8]:
                return 'summer'
            elif month in [9, 10, 11]:
                return 'fall'
        except:
            return 'unknown'
        
        return 'unknown'
    
    def _calculate_photo_quality(self, exif_data: Dict, ai_analysis: Dict) -> float:
        """Calculate photo quality score for conservation science"""
        score = 0.0
        max_score = 100.0
        
        # Image resolution (25 points)
        width = exif_data.get('image_dimensions', {}).get('width', 'Unknown')
        if width != 'Unknown' and isinstance(width, (int, str)):
            try:
                w = int(width) if isinstance(width, str) else width
                if w >= 3000:  # High resolution
                    score += 25
                elif w >= 1920:  # Medium resolution
                    score += 20
                elif w >= 1280:  # Low resolution
                    score += 15
            except:
                pass
        
        # GPS data presence (20 points)
        gps_coords = exif_data.get('gps_coordinates')
        if gps_coords and gps_coords.get('latitude') and gps_coords.get('longitude'):
            score += 20
        
        # AI analysis confidence (25 points)
        confidence = ai_analysis.get('confidence', 0)
        if isinstance(confidence, (int, float)):
            score += confidence * 0.25  # Scale to 25 points
        
        # Trait extraction success (20 points)
        traits = ai_analysis.get('traits', {})
        trait_count = len(traits)
        if trait_count >= 5:
            score += 20
        elif trait_count >= 3:
            score += 15
        elif trait_count >= 1:
            score += 10
        
        # Focus and composition (10 points)
        # This would require more sophisticated image analysis
        # For now, assume good quality if other metrics are high
        if score >= 70:
            score += 10
        elif score >= 50:
            score += 5
        
        return min(score, max_score)  # Cap at 100
    
    def _assess_conservation_value(self, ai_analysis: Dict, submission_data: Dict) -> float:
        """Assess conservation value of the observation"""
        value = 0.0
        
        # Species rarity (40 points)
        species_name = submission_data.get('species_name', '').lower()
        if any(rare in species_name for rare in ['cypripedium', 'platanthera', 'spiranthes']):
            value += 40
        elif any(uncommon in species_name for uncommon in ['goodyera', 'malaxis', 'liparis']):
            value += 30
        else:
            value += 20  # Any wild orchid has conservation value
        
        # Population size (20 points)
        pop_count = submission_data.get('population_count')
        if pop_count:
            if pop_count < 10:
                value += 20  # Very high conservation value for small populations
            elif pop_count < 50:
                value += 15
            elif pop_count < 100:
                value += 10
            else:
                value += 5
        
        # Habitat quality (20 points)
        threats = submission_data.get('threats_observed', [])
        if not threats:
            value += 20  # Pristine habitat
        elif len(threats) <= 2:
            value += 10  # Some threats but manageable
        # No points for heavily threatened habitats
        
        # Data quality (20 points)
        ai_confidence = ai_analysis.get('confidence', 0)
        value += ai_confidence * 0.2  # Scale to 20 points
        
        return min(value, 100.0)
    
    def _submit_to_eol(self, submission_record: Dict) -> Optional[Dict]:
        """Submit observation to Encyclopedia of Life"""
        try:
            if not eol_integrator.api_key:
                return {'status': 'skipped', 'reason': 'No EOL API key configured'}
            
            # Format data for EOL submission
            eol_data = {
                'species_name': submission_record.get('species_name'),
                'observer_name': submission_record.get('contributor_name'),
                'observation_date': submission_record.get('observation_details', {}).get('observation_date'),
                'latitude': submission_record.get('location', {}).get('latitude'),
                'longitude': submission_record.get('location', {}).get('longitude'),
                'traits_observed': self._extract_traits_for_eol(submission_record),
                'photo_urls': [],  # Would need to upload photos first
                'habitat_notes': submission_record.get('location', {}).get('habitat_description', '')
            }
            
            result = eol_integrator.submit_citizen_observation(eol_data)
            return result
            
        except Exception as e:
            logger.error(f"Error submitting to EOL: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _extract_traits_for_eol(self, submission_record: Dict) -> Dict:
        """Extract traits from submission for EOL format"""
        traits = {}
        
        # Extract from AI analysis
        for photo in submission_record.get('photos', []):
            ai_traits = photo.get('ai_analysis', {}).get('traits', {})
            traits.update(ai_traits)
        
        # Add observation context
        obs_details = submission_record.get('observation_details', {})
        traits.update({
            'flowering_stage': obs_details.get('flowering_stage'),
            'population_count': obs_details.get('population_count'),
            'habitat_type': submission_record.get('location', {}).get('habitat_description')
        })
        
        return traits
    
    def _generate_contributor_feedback(self, submission_record: Dict, eol_submission: Optional[Dict]) -> Dict:
        """Generate feedback for contributor"""
        feedback = {
            'submission_quality': 'excellent',
            'conservation_impact': 'high',
            'scientific_value': 'significant',
            'recommendations': [],
            'next_steps': []
        }
        
        # Assess submission quality
        avg_quality = 0
        photos = submission_record.get('photos', [])
        if photos:
            avg_quality = sum(p.get('quality_score', 0) for p in photos) / len(photos)
        
        if avg_quality >= 80:
            feedback['submission_quality'] = 'excellent'
            feedback['recommendations'].append('Outstanding photo quality - perfect for research')
        elif avg_quality >= 60:
            feedback['submission_quality'] = 'good'
            feedback['recommendations'].append('Good photo quality - useful for analysis')
        else:
            feedback['submission_quality'] = 'needs_improvement'
            feedback['recommendations'].append('Consider higher resolution photos for better analysis')
        
        # Conservation flags
        flags = submission_record.get('conservation_flags', [])
        if 'CRITICAL_SMALL_POPULATION' in flags:
            feedback['conservation_impact'] = 'critical'
            feedback['next_steps'].append('Alert local conservation authorities')
        elif 'VULNERABLE_POPULATION' in flags:
            feedback['conservation_impact'] = 'high'
            feedback['next_steps'].append('Continue monitoring this population')
        
        # EOL submission status
        if eol_submission and eol_submission.get('success'):
            feedback['next_steps'].append('Data successfully submitted to Encyclopedia of Life')
        
        return feedback
    
    def _generate_conservation_insights(self, population_analysis: Dict, project_submissions: List[Dict]) -> Dict:
        """Generate conservation insights from population analysis"""
        insights = {
            'overall_assessment': 'unknown',
            'priority_level': 'medium',
            'recommended_actions': [],
            'monitoring_needs': [],
            'research_opportunities': []
        }
        
        total_submissions = len(project_submissions)
        
        # Assess overall population health
        critical_flags = sum(1 for s in project_submissions 
                           if 'CRITICAL_SMALL_POPULATION' in s.get('conservation_flags', []))
        
        if critical_flags > total_submissions * 0.3:  # More than 30% critical
            insights['overall_assessment'] = 'critical'
            insights['priority_level'] = 'high'
            insights['recommended_actions'].append('Immediate conservation intervention needed')
        elif critical_flags > 0:
            insights['overall_assessment'] = 'concerning'
            insights['priority_level'] = 'medium-high'
            insights['recommended_actions'].append('Enhanced monitoring and protection measures')
        else:
            insights['overall_assessment'] = 'stable'
            insights['priority_level'] = 'medium'
            insights['recommended_actions'].append('Continue current monitoring protocols')
        
        # Identify research opportunities
        species_diversity = set()
        for submission in project_submissions:
            species = submission.get('species_name')
            if species:
                species_diversity.add(species)
        
        if len(species_diversity) > 1:
            insights['research_opportunities'].append('Multi-species interaction studies')
        
        insights['research_opportunities'].extend([
            'Genetic diversity assessment',
            'Climate change impact analysis',
            'Pollinator relationship studies'
        ])
        
        return insights
    
    def _identify_selection_pressures(self, all_photos: List[Dict]) -> Dict:
        """Identify potential selection pressures from photo analysis"""
        pressures = {
            'environmental': [],
            'anthropogenic': [],
            'biological': [],
            'genetic': []
        }
        
        # Analyze traits for directional selection
        trait_data = {}
        for photo in all_photos:
            traits = photo.get('ai_analysis', {}).get('traits', {})
            for trait_name, trait_value in traits.items():
                if trait_name not in trait_data:
                    trait_data[trait_name] = []
                trait_data[trait_name].append(trait_value)
        
        # Simple analysis for demonstration
        for trait_name, values in trait_data.items():
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if len(numeric_values) > 3:
                variation = max(numeric_values) - min(numeric_values)
                if variation > 0:
                    if 'size' in trait_name.lower():
                        pressures['environmental'].append(f'Size variation in {trait_name}')
                    elif 'color' in trait_name.lower():
                        pressures['biological'].append(f'Color polymorphism in {trait_name}')
        
        return pressures
    
    def _assess_genetic_diversity(self, all_photos: List[Dict]) -> Dict:
        """Assess genetic diversity from trait variations"""
        assessment = {
            'diversity_level': 'unknown',
            'trait_variations': {},
            'recommendations': []
        }
        
        # Count trait variations
        trait_counts = {}
        for photo in all_photos:
            traits = photo.get('ai_analysis', {}).get('traits', {})
            for trait_name in traits.keys():
                trait_counts[trait_name] = trait_counts.get(trait_name, 0) + 1
        
        # Simple diversity assessment
        avg_trait_count = sum(trait_counts.values()) / len(trait_counts) if trait_counts else 0
        
        if avg_trait_count > 10:
            assessment['diversity_level'] = 'high'
            assessment['recommendations'].append('Population shows good genetic diversity')
        elif avg_trait_count > 5:
            assessment['diversity_level'] = 'medium'
            assessment['recommendations'].append('Monitor for genetic bottlenecks')
        else:
            assessment['diversity_level'] = 'low'
            assessment['recommendations'].append('Investigate potential inbreeding')
        
        assessment['trait_variations'] = trait_counts
        
        return assessment
    
    def _generate_scientific_recommendations(self, population_analysis: Dict) -> List[str]:
        """Generate scientific recommendations from analysis"""
        recommendations = [
            'Continue systematic photo documentation',
            'Expand geographic sampling if possible',
            'Document flowering phenology across seasons',
            'Investigate pollinator relationships',
            'Monitor population trends over time'
        ]
        
        # Add specific recommendations based on analysis
        conservation_insights = population_analysis.get('conservation_insights', {})
        if conservation_insights.get('priority_level') == 'high':
            recommendations.insert(0, 'Prioritize immediate conservation action')
        
        return recommendations
    
    def _store_analysis_results(self, project_id: str, analysis_results: Dict):
        """Store population analysis results"""
        try:
            analysis_dir = 'population_analysis_results'
            os.makedirs(analysis_dir, exist_ok=True)
            
            filename = f"{project_id}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(analysis_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(analysis_results, f, indent=2)
            
            logger.info(f"Stored analysis results: {filename}")
            
        except Exception as e:
            logger.error(f"Error storing analysis results: {str(e)}")


# Initialize the platform
citizen_science_platform = CitizenSciencePlatform()

# Flask routes for citizen science functionality
@citizen_science_bp.route('/')
def citizen_science_home():
    """Main citizen science platform page"""
    return render_template('citizen_science/platform_home.html', 
                         platform=citizen_science_platform)

@citizen_science_bp.route('/projects')
def view_projects():
    """View all active citizen science projects"""
    # Load projects from storage
    projects = citizen_science_platform._load_all_projects()
    return render_template('citizen_science/projects.html', projects=projects)

@citizen_science_bp.route('/submit/<project_id>')
def submission_form(project_id):
    """Show submission form for specific project"""
    project = citizen_science_platform._load_project(project_id)
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('citizen_science.view_projects'))
    
    return render_template('citizen_science/submission_form.html', project=project)

@citizen_science_bp.route('/api/submit', methods=['POST'])
def api_submit_observation():
    """API endpoint for submitting citizen science observations"""
    try:
        # Get form data
        submission_data = request.form.to_dict()
        
        # Get uploaded photos
        photo_files = request.files.getlist('photos')
        
        # Process submission
        result = citizen_science_platform.process_wild_orchid_submission(
            submission_data, photo_files
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in submission API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@citizen_science_bp.route('/api/projects/<project_id>/analysis')
def api_project_analysis(project_id):
    """Get population genetics analysis for a project"""
    try:
        analysis = citizen_science_platform.analyze_population_genetics(project_id)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error in project analysis API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@citizen_science_bp.route('/outreach/<organization>')
def generate_outreach(organization):
    """Generate outreach materials for specific organization"""
    try:
        materials = citizen_science_platform.generate_outreach_materials(organization)
        return render_template('citizen_science/outreach_materials.html', 
                             materials=materials)
    except Exception as e:
        logger.error(f"Error generating outreach: {str(e)}")
        flash('Error generating outreach materials', 'error')
        return redirect(url_for('citizen_science.citizen_science_home'))