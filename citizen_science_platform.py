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