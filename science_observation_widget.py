"""
Science Lab Observation Data Integration Widget
Integrates field observations and research data into the scientific method platform
"""

import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, session
from sqlalchemy import text, func, and_, or_
from flask import send_file
from werkzeug.utils import secure_filename
import io
from app import db, app
from models import OrchidRecord

logger = logging.getLogger(__name__)

science_obs_bp = Blueprint('science_lab_observations', __name__)

class ObservationDataIntegrator:
    """Integrates field observations with existing botanical data"""
    
    def __init__(self):
        self.observation_types = [
            'flowering_observation',
            'habitat_conditions', 
            'phenotype_measurement',
            'geographic_sighting',
            'cultivation_experiment',
            'pollinator_interaction',
            'environmental_data'
        ]
        
        # Export formats supported
        self.export_formats = ['text', 'word', 'pdf', 'jpeg', 'csv', 'json']
        
        # File upload settings
        self.allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx', 'docx'}
        self.max_file_size = 16 * 1024 * 1024  # 16MB limit
        
    def collect_field_observation(self, observation_data, uploaded_files=None):
        """Process and integrate field observation data with file uploads"""
        try:
            # Validate observation data
            validated_data = self._validate_observation(observation_data)
            
            # Process uploaded files if any
            file_data = self._process_uploaded_files(uploaded_files) if uploaded_files else []
            
            # Match with existing orchid records
            matching_records = self._find_matching_records(validated_data)
            
            # Create observation entry with files
            observation_entry = self._create_observation_entry(validated_data, matching_records)
            
            # Update related statistics
            self._update_botany_lab_stats(observation_entry)
            
            # Store in Google Sheets if configured
            self._store_in_google_sheets(observation_entry)
            
            return {
                'success': True,
                'observation_id': observation_entry['id'],
                'matched_records': len(matching_records),
                'observation_type': validated_data['type'],
                'timestamp': observation_entry['timestamp'],
                'files_uploaded': len(file_data),
                'export_available': True
            }
            
        except Exception as e:
            logger.error(f"Error processing field observation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_uploaded_files(self, uploaded_files):
        """Process and store uploaded files"""
        file_data = []
        
        for file in uploaded_files:
            if file and self._allowed_file(file.filename):
                try:
                    # Create unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{file.filename}"
                    
                    # Store file metadata (in production, save to cloud storage)
                    file_info = {
                        'original_name': file.filename,
                        'stored_name': filename,
                        'file_type': file.content_type,
                        'file_size': len(file.read()),
                        'upload_time': datetime.now().isoformat()
                    }
                    
                    file.seek(0)  # Reset file pointer
                    file_data.append(file_info)
                    
                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {e}")
                    
        return file_data
    
    def _allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _store_in_google_sheets(self, observation_entry):
        """Store observation data in Google Sheets for collaboration"""
        try:
            # Check if Google Sheets integration is available
            from google_sheets_service import GoogleSheetsService
            
            sheets_service = GoogleSheetsService()
            
            # Prepare data for Google Sheets
            sheet_data = {
                'Timestamp': observation_entry['timestamp'],
                'Observer': observation_entry['observer'],
                'Type': observation_entry['type'],
                'Location': observation_entry['location'],
                'Description': observation_entry['description'],
                'Quality Score': observation_entry['data_quality']['score'],
                'Matched Orchids': len(observation_entry['matched_orchids']),
                'Coordinates': f"{observation_entry['coordinates']['latitude']},{observation_entry['coordinates']['longitude']}" if observation_entry['coordinates']['latitude'] else ''
            }
            
            # Add to "Research Observations" sheet (would need custom append_row method)
            logger.info(f"Would save to Google Sheets: {sheet_data}")
            
        except ImportError:
            logger.info("Google Sheets integration not available")
        except Exception as e:
            logger.error(f"Error storing in Google Sheets: {e}")
    
    def search_orchid_database(self, search_params):
        """Search the orchid continuum database for data selection"""
        try:
            query = OrchidRecord.query
            results = []
            
            # Apply search filters
            if search_params.get('genus'):
                query = query.filter(OrchidRecord.genus.ilike(f"%{search_params['genus']}%"))
            
            if search_params.get('species'):
                query = query.filter(OrchidRecord.species.ilike(f"%{search_params['species']}%"))
            
            if search_params.get('location'):
                query = query.filter(OrchidRecord.region.ilike(f"%{search_params['location']}%"))
            
            if search_params.get('has_image'):
                query = query.filter(OrchidRecord.google_drive_id.isnot(None))
            
            # Execute search with limit
            limit = min(search_params.get('limit', 50), 100)  # Max 100 results
            orchids = query.limit(limit).all()
            
            # Format results for selection
            for orchid in orchids:
                results.append({
                    'id': orchid.id,
                    'scientific_name': orchid.scientific_name or f"{orchid.genus} {orchid.species}",
                    'genus': orchid.genus,
                    'species': orchid.species,
                    'location': orchid.region,
                    'has_image': bool(orchid.google_drive_id),
                    'description': orchid.ai_description[:200] if orchid.ai_description else '',
                    'coordinates': {
                        'lat': orchid.decimal_latitude,
                        'lng': orchid.decimal_longitude
                    } if orchid.decimal_latitude else None
                })
            
            return {
                'success': True,
                'results': results,
                'total_found': len(results),
                'search_params': search_params
            }
            
        except Exception as e:
            logger.error(f"Error searching orchid database: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def export_observation_data(self, observation_id, export_format, user_profile=None):
        """Export observation data in specified format"""
        try:
            # Find the observation
            observations = session.get('recent_observations', [])
            observation = next((obs for obs in observations if obs['id'] == observation_id), None)
            
            if not observation:
                return {'success': False, 'error': 'Observation not found'}
            
            # Generate export based on format
            if export_format == 'text':
                return self._export_as_text(observation, user_profile)
            elif export_format == 'word':
                return self._export_as_word(observation, user_profile)
            elif export_format == 'pdf':
                return self._export_as_pdf(observation, user_profile)
            elif export_format == 'jpeg':
                return self._export_as_jpeg(observation, user_profile)
            elif export_format == 'csv':
                return self._export_as_csv(observation, user_profile)
            elif export_format == 'json':
                return self._export_as_json(observation, user_profile)
            else:
                return {'success': False, 'error': f'Unsupported export format: {export_format}'}
                
        except Exception as e:
            logger.error(f"Error exporting observation data: {e}")
            return {'success': False, 'error': str(e)}
    
    def _export_as_text(self, observation, user_profile):
        """Export observation as formatted text"""
        header = self._generate_header(user_profile) if user_profile else ""
        
        content = f"""{header}
FIELD OBSERVATION REPORT
========================

Observation ID: {observation['id']}
Date/Time: {observation['timestamp']}
Observer: {observation['observer']}
Type: {observation['type'].replace('_', ' ').title()}
Location: {observation['location']}

DESCRIPTION:
{observation['description']}

COORDINATES:
Latitude: {observation['coordinates']['latitude'] or 'Not provided'}
Longitude: {observation['coordinates']['longitude'] or 'Not provided'}

DATA QUALITY:
Quality Level: {observation['data_quality']['level']}
Quality Score: {observation['data_quality']['score']}%
Quality Factors: {', '.join(observation['data_quality']['factors'])}

MATCHED ORCHID RECORDS:
"""
        
        for i, orchid in enumerate(observation['matched_orchids'], 1):
            content += f"{i}. {orchid['scientific_name']} (ID: {orchid['id']})\n"
        
        if observation.get('environmental_conditions'):
            content += f"\nENVIRONMENTAL CONDITIONS:\n{observation['environmental_conditions']}\n"
        
        content += f"\n---\nGenerated by The Orchid Continuum Science Platform\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return {
            'success': True,
            'content': content,
            'filename': f"observation_{observation['id']}.txt",
            'mime_type': 'text/plain'
        }
    
    def _export_as_json(self, observation, user_profile):
        """Export observation as JSON"""
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'exported_by': user_profile.get('name') if user_profile else 'Anonymous',
                'platform': 'The Orchid Continuum Science Platform'
            },
            'user_profile': user_profile or {},
            'observation': observation
        }
        
        return {
            'success': True,
            'content': json.dumps(export_data, indent=2),
            'filename': f"observation_{observation['id']}.json",
            'mime_type': 'application/json'
        }
    
    def _generate_header(self, user_profile):
        """Generate header with user credentials"""
        if not user_profile:
            return ""
        
        header = f"""RESEARCHER INFORMATION:
Name: {user_profile.get('name', 'Not provided')}
Affiliation: {user_profile.get('affiliation', 'Not provided')}
Credentials: {user_profile.get('credentials', 'Not provided')}
Contact: {user_profile.get('email', 'Not provided')}

"""
        return header
    
    def _validate_observation(self, data):
        """Validate and standardize observation data"""
        required_fields = ['type', 'description', 'location']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Standardize observation type
        if data['type'] not in self.observation_types:
            data['type'] = 'general_observation'
        
        # Add timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Parse coordinates if provided
        if 'coordinates' in data:
            coords = data['coordinates']
            if isinstance(coords, str):
                try:
                    # Parse "lat,lng" format
                    lat, lng = map(float, coords.split(','))
                    data['latitude'] = lat
                    data['longitude'] = lng
                except:
                    logger.warning(f"Could not parse coordinates: {coords}")
        
        return data
    
    def _find_matching_records(self, observation_data):
        """Find orchid records that match the observation"""
        try:
            query = OrchidRecord.query
            matches = []
            
            # Match by scientific name if provided
            if 'scientific_name' in observation_data:
                scientific_match = query.filter(
                    OrchidRecord.scientific_name.ilike(f"%{observation_data['scientific_name']}%")
                ).first()
                if scientific_match:
                    matches.append(scientific_match)
            
            # Match by genus if provided
            if 'genus' in observation_data:
                genus_matches = query.filter(
                    OrchidRecord.genus.ilike(f"%{observation_data['genus']}%")
                ).limit(5).all()
                matches.extend(genus_matches)
            
            # Geographic matching if coordinates provided
            if 'latitude' in observation_data and 'longitude' in observation_data:
                lat = observation_data['latitude']
                lng = observation_data['longitude']
                
                # Find orchids within ~50km radius (approximately 0.5 degrees)
                geographic_matches = query.filter(
                    and_(
                        OrchidRecord.decimal_latitude.between(lat - 0.5, lat + 0.5),
                        OrchidRecord.decimal_longitude.between(lng - 0.5, lng + 0.5)
                    )
                ).limit(10).all()
                matches.extend(geographic_matches)
            
            # Remove duplicates while preserving order
            unique_matches = []
            seen_ids = set()
            for match in matches:
                if match.id not in seen_ids:
                    unique_matches.append(match)
                    seen_ids.add(match.id)
            
            return unique_matches[:10]  # Limit to top 10 matches
            
        except Exception as e:
            logger.error(f"Error finding matching records: {e}")
            return []
    
    def _create_observation_entry(self, validated_data, matching_records):
        """Create standardized observation entry"""
        observation_entry = {
            'id': f"obs_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': validated_data['timestamp'],
            'type': validated_data['type'],
            'description': validated_data['description'],
            'location': validated_data['location'],
            'observer': validated_data.get('observer', 'Anonymous'),
            'coordinates': {
                'latitude': validated_data.get('latitude'),
                'longitude': validated_data.get('longitude')
            },
            'environmental_conditions': validated_data.get('conditions', {}),
            'matched_orchids': [
                {
                    'id': record.id,
                    'scientific_name': record.scientific_name,
                    'genus': record.genus,
                    'species': record.species
                } for record in matching_records
            ],
            'confidence_score': self._calculate_confidence(validated_data, matching_records),
            'data_quality': self._assess_data_quality(validated_data)
        }
        
        # Store in session for widget display
        if 'recent_observations' not in session:
            session['recent_observations'] = []
        
        session['recent_observations'].insert(0, observation_entry)
        session['recent_observations'] = session['recent_observations'][:50]  # Keep last 50
        
        return observation_entry
    
    def _calculate_confidence(self, data, matches):
        """Calculate confidence score for the observation"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data completeness
        if 'scientific_name' in data:
            confidence += 0.2
        if 'coordinates' in data or ('latitude' in data and 'longitude' in data):
            confidence += 0.2
        if 'environmental_conditions' in data or 'conditions' in data:
            confidence += 0.1
        
        # Increase confidence if we found matching records
        if matches:
            confidence += min(0.2, len(matches) * 0.02)
        
        return min(1.0, confidence)
    
    def _assess_data_quality(self, data):
        """Assess the quality of observation data"""
        quality_score = 0
        quality_factors = []
        
        # Check for key scientific fields
        if 'scientific_name' in data:
            quality_score += 25
            quality_factors.append('Scientific name provided')
        
        if 'coordinates' in data or ('latitude' in data and 'longitude' in data):
            quality_score += 25
            quality_factors.append('GPS coordinates included')
        
        if 'environmental_conditions' in data or 'conditions' in data:
            quality_score += 20
            quality_factors.append('Environmental data recorded')
        
        if len(data.get('description', '')) > 50:
            quality_score += 15
            quality_factors.append('Detailed description')
        
        if 'timestamp' in data:
            quality_score += 10
            quality_factors.append('Timestamp recorded')
        
        if 'observer' in data:
            quality_score += 5
            quality_factors.append('Observer identified')
        
        quality_level = 'Poor'
        if quality_score >= 80:
            quality_level = 'Excellent'
        elif quality_score >= 60:
            quality_level = 'Good'
        elif quality_score >= 40:
            quality_level = 'Fair'
        
        return {
            'score': quality_score,
            'level': quality_level,
            'factors': quality_factors
        }
    
    def _update_botany_lab_stats(self, observation_entry):
        """Update botany lab statistics and integrate with scientific method workflow"""
        try:
            # Update observation statistics in session
            if 'lab_stats' not in session:
                session['lab_stats'] = {
                    'total_observations': 0,
                    'observations_by_type': {},
                    'recent_activity': [],
                    'data_quality_distribution': {'Poor': 0, 'Fair': 0, 'Good': 0, 'Excellent': 0}
                }
            
            stats = session['lab_stats']
            
            # Update totals
            stats['total_observations'] += 1
            
            # Update by type
            obs_type = observation_entry['type']
            if obs_type not in stats['observations_by_type']:
                stats['observations_by_type'][obs_type] = 0
            stats['observations_by_type'][obs_type] += 1
            
            # Update quality distribution
            quality_level = observation_entry['data_quality']['level']
            stats['data_quality_distribution'][quality_level] += 1
            
            # Add to recent activity
            activity_entry = {
                'timestamp': observation_entry['timestamp'],
                'type': obs_type,
                'quality': quality_level,
                'matches': len(observation_entry['matched_orchids'])
            }
            stats['recent_activity'].insert(0, activity_entry)
            stats['recent_activity'] = stats['recent_activity'][:20]  # Keep last 20
            
            session['lab_stats'] = stats
            
            # INTEGRATE WITH SCIENTIFIC METHOD WORKFLOW
            self._integrate_with_research_platform(observation_entry)
            
        except Exception as e:
            logger.error(f"Error updating botany lab stats: {e}")
    
    def _integrate_with_research_platform(self, observation_entry):
        """Connect observation to existing scientific method platform"""
        try:
            # Initialize research workflow if not exists
            if 'research_workflow' not in session:
                session['research_workflow'] = {
                    'current_stage': 'observation',
                    'stages_completed': [],
                    'observations_collected': [],
                    'hypotheses_generated': [],
                    'experiments_designed': [],
                    'data_analyzed': []
                }
            
            workflow = session['research_workflow']
            
            # Add to observations collected
            workflow['observations_collected'].append({
                'id': observation_entry['id'],
                'description': observation_entry['description'],
                'type': observation_entry['type'],
                'quality_score': observation_entry['data_quality']['score'],
                'matched_orchids': len(observation_entry['matched_orchids']),
                'timestamp': observation_entry['timestamp'],
                'ready_for_hypothesis': observation_entry['data_quality']['score'] >= 60
            })
            
            # Mark observation stage as completed if we have quality data
            if 'observation' not in workflow['stages_completed'] and observation_entry['data_quality']['score'] >= 60:
                workflow['stages_completed'].append('observation')
                workflow['current_stage'] = 'hypothesis'
            
            # Auto-generate suggested research questions
            workflow['suggested_questions'] = self._generate_research_questions(observation_entry)
            
            session['research_workflow'] = workflow
            
        except Exception as e:
            logger.error(f"Error integrating with research platform: {e}")
    
    def _generate_research_questions(self, observation_entry):
        """Generate research questions based on the observation"""
        questions = []
        obs_type = observation_entry['type']
        description = observation_entry['description']
        
        # Generate specific questions based on observation type
        if obs_type == 'flowering_observation':
            questions = [
                f"What environmental factors trigger flowering in the observed orchid?",
                f"How does flowering timing correlate with temperature and humidity?",
                f"Are there genetic markers associated with this flowering pattern?"
            ]
        elif obs_type == 'habitat_conditions':
            questions = [
                f"What microclimate conditions are optimal for this orchid species?",
                f"How do habitat conditions affect orchid health and reproduction?",
                f"Can these habitat requirements be replicated in cultivation?"
            ]
        elif obs_type == 'pollinator_interaction':
            questions = [
                f"What attracts specific pollinators to this orchid species?",
                f"How does pollinator behavior affect orchid evolution?",
                f"Are there co-evolution patterns between this orchid and its pollinators?"
            ]
        elif obs_type == 'geographic_sighting':
            questions = [
                f"What factors determine the geographic distribution of this orchid?",
                f"How is climate change affecting orchid ranges?",
                f"Are there migration patterns in orchid populations?"
            ]
        else:
            questions = [
                f"What patterns can be identified in this orchid observation?",
                f"How does this observation relate to known orchid biology?",
                f"What experimental approach could test hypotheses about this observation?"
            ]
        
        return questions
    
    def _export_as_word(self, observation, user_profile):
        """Export observation as Word document (placeholder)"""
        # Note: Full Word export would require python-docx library
        return {
            'success': False,
            'error': 'Word export requires additional setup'
        }
    
    def _export_as_pdf(self, observation, user_profile):
        """Export observation as PDF (placeholder)"""
        # Note: Full PDF export would require reportlab library
        return {
            'success': False,
            'error': 'PDF export requires additional setup'
        }
    
    def _export_as_jpeg(self, observation, user_profile):
        """Export observation as JPEG image (placeholder)"""
        return {
            'success': False,
            'error': 'JPEG export requires additional setup'
        }
    
    def _export_as_csv(self, observation, user_profile):
        """Export observation as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ['Field', 'Value']
        writer.writerow(headers)
        
        # Write observation data
        writer.writerow(['Observation ID', observation['id']])
        writer.writerow(['Timestamp', observation['timestamp']])
        writer.writerow(['Observer', observation['observer']])
        writer.writerow(['Type', observation['type']])
        writer.writerow(['Location', observation['location']])
        writer.writerow(['Description', observation['description']])
        writer.writerow(['Quality Score', observation['data_quality']['score']])
        writer.writerow(['Matched Orchids', len(observation['matched_orchids'])])
        
        if user_profile:
            writer.writerow(['Researcher Name', user_profile.get('name', '')])
            writer.writerow(['Affiliation', user_profile.get('affiliation', '')])
        
        return {
            'success': True,
            'content': output.getvalue(),
            'filename': f"observation_{observation['id']}.csv",
            'mime_type': 'text/csv'
        }
    
    def get_observation_summary(self):
        """Get summary of recent observations for widget display"""
        try:
            recent_obs = session.get('recent_observations', [])
            lab_stats = session.get('lab_stats', {})
            
            return {
                'total_observations': len(recent_obs),
                'recent_observations': recent_obs[:10],  # Last 10 for display
                'statistics': lab_stats,
                'quality_metrics': self._calculate_quality_metrics(recent_obs),
                'geographic_coverage': self._calculate_geographic_coverage(recent_obs)
            }
            
        except Exception as e:
            logger.error(f"Error getting observation summary: {e}")
            return {
                'total_observations': 0,
                'recent_observations': [],
                'statistics': {},
                'error': str(e)
            }
    
    def _calculate_quality_metrics(self, observations):
        """Calculate quality metrics for observations"""
        if not observations:
            return {'average_quality': 0, 'high_quality_count': 0}
        
        total_quality = sum(obs.get('data_quality', {}).get('score', 0) for obs in observations)
        average_quality = total_quality / len(observations)
        high_quality_count = sum(1 for obs in observations 
                               if obs.get('data_quality', {}).get('score', 0) >= 70)
        
        return {
            'average_quality': round(average_quality, 1),
            'high_quality_count': high_quality_count,
            'high_quality_percentage': round((high_quality_count / len(observations)) * 100, 1)
        }
    
    def _calculate_geographic_coverage(self, observations):
        """Calculate geographic coverage of observations"""
        locations = set()
        coordinates_count = 0
        
        for obs in observations:
            if 'location' in obs:
                locations.add(obs['location'])
            if obs.get('coordinates', {}).get('latitude'):
                coordinates_count += 1
        
        return {
            'unique_locations': len(locations),
            'gps_coverage': coordinates_count,
            'gps_percentage': round((coordinates_count / len(observations)) * 100, 1) if observations else 0
        }

# Initialize the integrator
observation_integrator = ObservationDataIntegrator()

@science_obs_bp.route('/api/submit-observation', methods=['POST'])
def submit_field_observation():
    """API endpoint to submit field observations"""
    try:
        observation_data = request.get_json()
        result = observation_integrator.collect_field_observation(observation_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in submit_field_observation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@science_obs_bp.route('/api/observation-summary')
def get_observation_summary():
    """Get summary of observations for dashboard"""
    try:
        summary = observation_integrator.get_observation_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error in get_observation_summary: {e}")
        return jsonify({'error': str(e)}), 500

@science_obs_bp.route('/api/research-workflow-status')
def get_research_workflow_status():
    """Get current research workflow status integrated with observations"""
    try:
        workflow = session.get('research_workflow', {})
        observations = session.get('recent_observations', [])
        
        # Calculate workflow progress
        total_stages = 7  # observation, question, hypothesis, experiment, data, analysis, conclusion
        completed_stages = len(workflow.get('stages_completed', []))
        progress_percentage = (completed_stages / total_stages) * 100
        
        return jsonify({
            'workflow_status': workflow,
            'total_observations': len(observations),
            'ready_for_hypothesis': len([obs for obs in observations if obs.get('data_quality', {}).get('score', 0) >= 60]),
            'progress_percentage': progress_percentage,
            'current_stage': workflow.get('current_stage', 'observation'),
            'suggested_questions': workflow.get('suggested_questions', [])
        })
    except Exception as e:
        logger.error(f"Error getting research workflow status: {e}")
        return jsonify({'error': str(e)}), 500

@science_obs_bp.route('/api/generate-hypothesis-from-observation', methods=['POST'])
def generate_hypothesis_from_observation():
    """Generate AI hypothesis from observation data"""
    try:
        data = request.get_json()
        observation_id = data.get('observation_id')
        
        if not observation_id:
            return jsonify({'error': 'Observation ID required'}), 400
        
        # Find the observation
        observations = session.get('recent_observations', [])
        observation = next((obs for obs in observations if obs['id'] == observation_id), None)
        
        if not observation:
            return jsonify({'error': 'Observation not found'}), 400
        
        # Use AI to generate hypothesis (integrating with existing AI systems)
        try:
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            
            prompt = f"""
            Based on this field observation:
            
            Type: {observation['type']}
            Description: {observation['description']}
            Location: {observation['location']}
            Quality Score: {observation['data_quality']['score']}%
            Matched Orchids: {len(observation['matched_orchids'])} species
            
            Generate 3 testable scientific hypotheses that could explain or explore this observation.
            For each hypothesis, provide:
            1. Clear hypothesis statement
            2. Testable prediction
            3. Required data collection methods
            4. Statistical analysis approach
            5. Connection to orchid biology principles
            
            Format as structured JSON for research planning.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a botanical research specialist. Generate testable hypotheses from field observations using scientific method principles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            ai_hypotheses = response.choices[0].message.content
            
            # Update workflow with generated hypotheses
            workflow = session.get('research_workflow', {})
            if 'hypotheses_generated' not in workflow:
                workflow['hypotheses_generated'] = []
            
            workflow['hypotheses_generated'].append({
                'observation_id': observation_id,
                'generated_hypotheses': ai_hypotheses,
                'timestamp': datetime.now().isoformat(),
                'ready_for_experiment': True
            })
            
            if 'hypothesis' not in workflow.get('stages_completed', []):
                workflow['stages_completed'].append('hypothesis')
                workflow['current_stage'] = 'experiment'
            
            session['research_workflow'] = workflow
            
            return jsonify({
                'success': True,
                'observation_id': observation_id,
                'generated_hypotheses': ai_hypotheses,
                'workflow_updated': True,
                'next_stage': 'experiment'
            })
            
        except Exception as ai_error:
            logger.error(f"AI hypothesis generation error: {ai_error}")
            return jsonify({'error': f'AI hypothesis generation failed: {ai_error}'}), 500
            
    except Exception as e:
        logger.error(f"Error in generate_hypothesis_from_observation: {e}")
        return jsonify({'error': str(e)}), 500

@science_obs_bp.route('/api/search-orchid-database', methods=['POST'])
def search_orchid_database():
    """API endpoint to search the orchid continuum database"""
    try:
        search_params = request.get_json() or {}
        results = observation_integrator.search_orchid_database(search_params)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in search_orchid_database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@science_obs_bp.route('/api/export-observation/<observation_id>/<export_format>')
def export_observation(observation_id, export_format):
    """API endpoint to export observation data"""
    try:
        # Get user profile from session if available
        user_profile = session.get('user_profile', {})
        
        result = observation_integrator.export_observation_data(
            observation_id, export_format, user_profile
        )
        
        if result['success']:
            # Create file response
            file_content = result['content']
            
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
            
            return send_file(
                io.BytesIO(file_content),
                mimetype=result['mime_type'],
                as_attachment=True,
                download_name=result['filename']
            )
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in export_observation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@science_obs_bp.route('/api/upload-observation-files', methods=['POST'])
def upload_observation_files():
    """API endpoint to handle file uploads for observations"""
    try:
        uploaded_files = request.files.getlist('files')
        observation_data = request.form.to_dict()
        
        # Process observation with files
        result = observation_integrator.collect_field_observation(
            observation_data, uploaded_files
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in upload_observation_files: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@science_obs_bp.route('/api/save-user-profile', methods=['POST'])
def save_user_profile():
    """API endpoint to save user profile and credentials"""
    try:
        profile_data = request.get_json()
        
        # Validate required fields
        required_fields = ['name']
        for field in required_fields:
            if field not in profile_data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Store in session (in production, store in database)
        session['user_profile'] = {
            'name': profile_data.get('name'),
            'affiliation': profile_data.get('affiliation', ''),
            'credentials': profile_data.get('credentials', ''),
            'email': profile_data.get('email', ''),
            'research_interests': profile_data.get('research_interests', ''),
            'saved_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'User profile saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in save_user_profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@science_obs_bp.route('/api/get-user-profile')
def get_user_profile():
    """API endpoint to get current user profile"""
    try:
        profile = session.get('user_profile', {})
        return jsonify({
            'success': True,
            'profile': profile
        })
    except Exception as e:
        logger.error(f"Error in get_user_profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@science_obs_bp.route('/widget/science-observations')
def science_observations_widget():
    """Standalone science observations widget"""
    try:
        summary = observation_integrator.get_observation_summary()
        return render_template('widgets/science_observations.html', 
                             widget_data=summary, 
                             standalone=True)
    except Exception as e:
        logger.error(f"Error in science_observations_widget: {e}")
        return render_template('widgets/science_observations.html', 
                             widget_data={'error': str(e)}, 
                             standalone=True)

@science_obs_bp.route('/widget/enhanced-science-observations')
def enhanced_science_observations_widget():
    """Enhanced science observations widget with full scientific method integration"""
    try:
        summary = observation_integrator.get_observation_summary()
        return render_template('widgets/enhanced_science_observations.html', 
                             widget_data=summary, 
                             standalone=True)
    except Exception as e:
        logger.error(f"Error in enhanced_science_observations_widget: {e}")
        return render_template('widgets/enhanced_science_observations.html', 
                             widget_data={'error': str(e)}, 
                             standalone=True)

@science_obs_bp.route('/science-lab-dashboard')
def science_lab_dashboard():
    """Full science lab dashboard with observation integration"""
    try:
        summary = observation_integrator.get_observation_summary()
        
        # Get botany lab statistics
        try:
            from botany_lab_stats import BotanyLabStats
            botany_stats = BotanyLabStats().parse_csv_data("")  # Use available method
        except ImportError:
            botany_stats = {'error': 'Botany lab stats not available'}
        
        return render_template('science_lab_dashboard.html', 
                             observation_data=summary,
                             botany_stats=botany_stats)
    except Exception as e:
        logger.error(f"Error in science_lab_dashboard: {e}")
        return render_template('science_lab_dashboard.html', 
                             observation_data={'error': str(e)},
                             botany_stats={'error': str(e)})

def register_science_observation_routes(app):
    """Register science observation routes with the Flask app"""
    # Check if blueprint is already registered
    if 'science_lab_observations' not in [bp.name for bp in app.blueprints.values()]:
        app.register_blueprint(science_obs_bp)
        logger.info("🔬 Science Observation Widget registered successfully")
    else:
        logger.info("🔬 Science Observation Widget already registered")

# Auto-register if running directly
if __name__ != '__main__':
    try:
        from app import app
        register_science_observation_routes(app)
    except Exception as e:
        logger.error(f"Failed to register science observation routes: {e}")