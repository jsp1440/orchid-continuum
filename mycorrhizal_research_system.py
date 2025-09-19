"""
Mycorrhizal Research System for The Orchid Continuum
Focused on mapping orchid-fungal associations and environmental correlations
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mycorrhizal_bp = Blueprint('mycorrhizal_research', __name__, url_prefix='/mycorrhizal-research')

@dataclass
class MycorrhizalAssociation:
    """Data structure for orchid-fungal associations"""
    orchid_species: str
    fungal_genus: str
    fungal_species: str
    association_type: str  # 'obligate', 'facultative', 'unknown'
    confirmed_method: str  # 'molecular', 'microscopy', 'cultivation', 'literature'
    geographic_region: str
    habitat_type: str
    soil_ph: Optional[float]
    soil_type: str
    elevation: Optional[int]
    climate_zone: str
    associated_plants: List[str]
    environmental_factors: Dict[str, Any]
    research_citation: str
    confidence_level: str  # 'high', 'medium', 'low'

class MycorrhizalResearchSystem:
    """
    System for tracking and analyzing orchid mycorrhizal associations
    """
    
    def __init__(self):
        self.research_data_dir = 'mycorrhizal_research_data'
        self.associations_dir = os.path.join(self.research_data_dir, 'associations')
        self.environmental_data_dir = os.path.join(self.research_data_dir, 'environmental')
        self.research_projects_dir = os.path.join(self.research_data_dir, 'projects')
        
        # Create directories
        for directory in [self.research_data_dir, self.associations_dir, 
                         self.environmental_data_dir, self.research_projects_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Known mycorrhizal associations database
        self.known_associations = self._load_known_associations()
        
        # Target research areas and contacts
        self.research_priorities = {
            'temperate_terrestrials': {
                'genera': ['Cypripedium', 'Platanthera', 'Spiranthes', 'Goodyera', 'Epipactis'],
                'known_fungi': ['Rhizoctonia', 'Ceratobasidium', 'Tulasnella', 'Russula', 'Sebacina'],
                'priority_regions': ['Pacific Northwest', 'Appalachian Mountains', 'Great Lakes Region'],
                'key_researchers': ['Ron Parsons', 'Dennis Wickham']
            },
            'tropical_epiphytes': {
                'genera': ['Epidendrum', 'Oncidium', 'Cattleya', 'Dendrobium', 'Bulbophyllum'],
                'known_fungi': ['Ceratobasidium', 'Tulasnella', 'Sebacina', 'Psathyrella'],
                'priority_regions': ['Central America', 'Amazon Basin', 'Southeast Asia'],
                'key_researchers': ['Mary Garrettson', 'Orchid Conservation Alliance']
            },
            'rare_endangered': {
                'genera': ['Cypripedium', 'Platanthera', 'Malaxis', 'Liparis'],
                'conservation_status': ['endangered', 'threatened', 'vulnerable'],
                'key_contacts': ['North American Orchid Conservation Center', 'NOC Network']
            }
        }
        
        logger.info("🍄 Mycorrhizal Research System initialized")

    def _load_known_associations(self) -> Dict[str, List[Dict]]:
        """Load existing mycorrhizal association data"""
        associations_file = os.path.join(self.associations_dir, 'known_associations.json')
        
        if os.path.exists(associations_file):
            with open(associations_file, 'r') as f:
                return json.load(f)
        
        # Initialize with known associations from literature
        initial_data = {
            'cypripedium_acaule': [
                {
                    'fungal_genus': 'Russula',
                    'fungal_species': 'ochroleuca',
                    'association_type': 'obligate',
                    'habitat': 'acidic pine forests',
                    'soil_ph_range': '4.0-5.5',
                    'research_citation': 'Shefferson et al. 2005, Nature'
                }
            ],
            'cypripedium_reginae': [
                {
                    'fungal_genus': 'Tulasnella',
                    'fungal_species': 'calospora',
                    'association_type': 'obligate',
                    'habitat': 'alkaline wetlands',
                    'soil_ph_range': '6.5-7.5',
                    'research_citation': 'Zelmer et al. 1996, Lindleyana'
                }
            ],
            'platanthera_ciliaris': [
                {
                    'fungal_genus': 'Ceratobasidium',
                    'fungal_species': 'sp.',
                    'association_type': 'obligate',
                    'habitat': 'wet prairies, bog edges',
                    'soil_ph_range': '5.0-6.5',
                    'research_citation': 'Batty et al. 2001, New Phytologist'
                }
            ]
        }
        
        # Save initial data
        with open(associations_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        
        return initial_data

    def create_mycorrhizal_project(self, project_data: Dict) -> str:
        """Create new mycorrhizal research project"""
        project_id = f"myco_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        project_record = {
            'project_id': project_id,
            'title': project_data.get('title'),
            'description': project_data.get('description'),
            'research_focus': project_data.get('research_focus'),
            'target_species': project_data.get('target_species', []),
            'target_fungi': project_data.get('target_fungi', []),
            'geographic_focus': project_data.get('geographic_focus'),
            'research_questions': project_data.get('research_questions', []),
            'methodology': project_data.get('methodology'),
            'collaborators': project_data.get('collaborators', []),
            'funding_source': project_data.get('funding_source'),
            'timeline': project_data.get('timeline'),
            'environmental_factors_of_interest': [
                'soil_chemistry', 'ph_levels', 'moisture_content', 
                'organic_matter', 'mineral_composition', 'microclimate',
                'associated_vegetation', 'elevation', 'slope_aspect'
            ],
            'data_collection_protocols': {
                'soil_sampling': True,
                'fungal_isolation': True,
                'molecular_identification': True,
                'environmental_monitoring': True,
                'photographic_documentation': True
            },
            'created_date': datetime.now().isoformat(),
            'status': 'active',
            'submissions': []
        }
        
        # Save project
        project_file = os.path.join(self.research_projects_dir, f"{project_id}.json")
        with open(project_file, 'w') as f:
            json.dump(project_record, f, indent=2)
        
        logger.info(f"🍄 Created mycorrhizal project: {project_id}")
        return project_id

    def submit_mycorrhizal_observation(self, observation_data: Dict) -> Dict:
        """Process mycorrhizal association observation"""
        submission_id = f"myco_obs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Process observation
        processed_observation = {
            'submission_id': submission_id,
            'project_id': observation_data.get('project_id'),
            'observer_info': {
                'name': observation_data.get('observer_name'),
                'email': observation_data.get('observer_email'),
                'institution': observation_data.get('institution'),
                'expertise_level': observation_data.get('expertise_level')
            },
            'orchid_identification': {
                'scientific_name': observation_data.get('orchid_species'),
                'common_name': observation_data.get('common_name'),
                'confidence': observation_data.get('identification_confidence'),
                'life_stage': observation_data.get('life_stage'),  # seedling, juvenile, adult, flowering
                'population_size': observation_data.get('population_size')
            },
            'fungal_data': {
                'isolation_attempted': observation_data.get('fungal_isolation', False),
                'isolation_method': observation_data.get('isolation_method'),
                'morphological_description': observation_data.get('fungal_morphology'),
                'molecular_analysis': observation_data.get('molecular_analysis', False),
                'identified_fungus': observation_data.get('identified_fungus'),
                'confidence_level': observation_data.get('fungal_confidence')
            },
            'environmental_data': {
                'location': {
                    'latitude': observation_data.get('latitude'),
                    'longitude': observation_data.get('longitude'),
                    'elevation': observation_data.get('elevation'),
                    'gps_accuracy': observation_data.get('gps_accuracy')
                },
                'soil_data': {
                    'ph': observation_data.get('soil_ph'),
                    'moisture': observation_data.get('soil_moisture'),
                    'organic_content': observation_data.get('organic_content'),
                    'soil_type': observation_data.get('soil_type'),
                    'sample_collected': observation_data.get('soil_sample_collected', False)
                },
                'microclimate': {
                    'light_level': observation_data.get('light_level'),
                    'canopy_cover': observation_data.get('canopy_cover'),
                    'humidity': observation_data.get('humidity'),
                    'temperature': observation_data.get('temperature')
                },
                'habitat_description': observation_data.get('habitat_description'),
                'associated_plants': observation_data.get('associated_plants', []),
                'disturbance_factors': observation_data.get('disturbance_factors', [])
            },
            'observation_date': observation_data.get('observation_date'),
            'submission_date': datetime.now().isoformat(),
            'photos': [],  # Will be processed separately
            'analysis_results': {},
            'conservation_notes': observation_data.get('conservation_notes', ''),
            'research_value': self._assess_research_value(observation_data)
        }
        
        # Save observation
        observation_file = os.path.join(self.associations_dir, f"{submission_id}.json")
        with open(observation_file, 'w') as f:
            json.dump(processed_observation, f, indent=2)
        
        # Update project with new submission
        self._add_submission_to_project(observation_data.get('project_id'), submission_id)
        
        # Generate analysis and recommendations
        analysis = self._analyze_mycorrhizal_observation(processed_observation)
        
        return {
            'success': True,
            'submission_id': submission_id,
            'analysis': analysis,
            'recommendations': self._generate_research_recommendations(processed_observation),
            'conservation_priority': self._assess_conservation_priority(processed_observation)
        }

    def _assess_research_value(self, observation_data: Dict) -> str:
        """Assess research value of mycorrhizal observation"""
        score = 0
        
        # Species rarity
        species = observation_data.get('orchid_species', '').lower()
        if any(rare in species for rare in ['cypripedium', 'platanthera']):
            score += 30
        
        # Fungal isolation attempted
        if observation_data.get('fungal_isolation'):
            score += 25
        
        # Molecular analysis
        if observation_data.get('molecular_analysis'):
            score += 25
        
        # Environmental data completeness
        if observation_data.get('soil_ph') and observation_data.get('soil_type'):
            score += 10
        
        # Geographic significance
        if observation_data.get('elevation') and observation_data.get('latitude'):
            score += 10
        
        if score >= 70:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'

    def _analyze_mycorrhizal_observation(self, observation: Dict) -> Dict:
        """Analyze mycorrhizal observation for patterns"""
        analysis = {
            'species_known_associations': [],
            'environmental_correlations': {},
            'research_gaps_identified': [],
            'similar_habitats': [],
            'conservation_implications': []
        }
        
        species = observation['orchid_identification']['scientific_name']
        
        # Check known associations
        species_key = species.lower().replace(' ', '_')
        if species_key in self.known_associations:
            analysis['species_known_associations'] = self.known_associations[species_key]
        
        # Environmental correlations
        soil_ph = observation['environmental_data']['soil_data'].get('ph')
        if soil_ph:
            if soil_ph < 5.5:
                analysis['environmental_correlations']['soil_acidity'] = 'acidic_preference'
                analysis['research_gaps_identified'].append('Investigate acid-tolerant fungi')
            elif soil_ph > 7.0:
                analysis['environmental_correlations']['soil_acidity'] = 'alkaline_preference'
                analysis['research_gaps_identified'].append('Investigate alkaline-tolerant fungi')
        
        # Conservation implications
        population_size = observation['orchid_identification'].get('population_size', 0)
        if population_size < 50:
            analysis['conservation_implications'].append('Small population - mycorrhizal diversity critical')
        
        return analysis

    def _add_submission_to_project(self, project_id: str, submission_id: str):
        """Add submission ID to project's submission list"""
        if not project_id:
            return
        
        try:
            project_file = os.path.join(self.research_projects_dir, f"{project_id}.json")
            if os.path.exists(project_file):
                with open(project_file, 'r') as f:
                    project = json.load(f)
                
                if 'submissions' not in project:
                    project['submissions'] = []
                
                project['submissions'].append(submission_id)
                project['last_updated'] = datetime.now().isoformat()
                
                with open(project_file, 'w') as f:
                    json.dump(project, f, indent=2)
                
                logger.info(f"🍄 Added submission {submission_id} to project {project_id}")
        except Exception as e:
            logger.error(f"Error adding submission to project: {str(e)}")

    def _generate_research_recommendations(self, observation: Dict) -> List[str]:
        """Generate research recommendations"""
        recommendations = []
        
        species = observation['orchid_identification']['scientific_name']
        
        # Fungal isolation recommendations
        if not observation['fungal_data']['isolation_attempted']:
            recommendations.append('Attempt fungal isolation from root samples')
        
        # Molecular analysis
        if not observation['fungal_data']['molecular_analysis']:
            recommendations.append('Conduct ITS sequencing for fungal identification')
        
        # Soil analysis
        if not observation['environmental_data']['soil_data'].get('ph'):
            recommendations.append('Measure soil pH and nutrient composition')
        
        # Species-specific recommendations
        if 'cypripedium' in species.lower():
            recommendations.append('Test for Russula and Tulasnella associations')
            recommendations.append('Document soil organic matter content')
        elif 'platanthera' in species.lower():
            recommendations.append('Screen for Ceratobasidium and Rhizoctonia')
            recommendations.append('Monitor soil moisture seasonally')
        
        return recommendations

    def _assess_conservation_priority(self, observation: Dict) -> Dict:
        """Assess conservation priority"""
        priority = {
            'level': 'medium',
            'factors': [],
            'actions_needed': []
        }
        
        species = observation['orchid_identification']['scientific_name']
        population_size = observation['orchid_identification'].get('population_size', 0)
        
        # Population size assessment
        if population_size < 10:
            priority['level'] = 'critical'
            priority['factors'].append('Extremely small population')
            priority['actions_needed'].append('Immediate mycorrhizal survey')
        elif population_size < 50:
            priority['level'] = 'high'
            priority['factors'].append('Small population')
        
        # Species rarity
        rare_genera = ['cypripedium', 'platanthera', 'spiranthes']
        if any(genus in species.lower() for genus in rare_genera):
            priority['factors'].append('Rare/sensitive species')
            priority['actions_needed'].append('Document mycorrhizal requirements')
        
        return priority

    def generate_conservation_outreach(self, contact_type: str) -> Dict:
        """Generate targeted outreach materials for conservation contacts"""
        
        if contact_type == 'ron_parsons':
            return {
                'contact_name': 'Ron Parsons',
                'specialization': 'Native orchid photography and documentation',
                'outreach_focus': 'Photographic documentation of mycorrhizal habitats',
                'collaboration_proposal': {
                    'title': 'Native Orchid Mycorrhizal Habitat Documentation Project',
                    'description': 'Combine your exceptional field photography with our AI-powered mycorrhizal analysis system',
                    'mutual_benefits': [
                        'Your photos provide precise habitat context for mycorrhizal research',
                        'Our AI analysis enhances scientific value of your documentation',
                        'Joint publications on orchid-fungal-habitat relationships',
                        'Advanced mapping of native orchid mycorrhizal zones'
                    ],
                    'specific_requests': [
                        'GPS-tagged photos of Cypripedium and Platanthera habitats',
                        'Soil and substrate documentation in photos',
                        'Seasonal progression photos of the same populations',
                        'Associated vegetation and microhabitat details'
                    ],
                    'what_we_provide': [
                        'AI-powered species and habitat analysis of your photos',
                        'Mycorrhizal association predictions based on environmental factors',
                        'Integration with Encyclopedia of Life database',
                        'Co-authorship on research publications'
                    ]
                }
            }
        
        elif contact_type == 'mary_garrettson':
            return {
                'contact_name': 'Mary Garrettson',
                'organization': 'Orchid Conservation Alliance',
                'specialization': 'Orchid conservation and habitat protection',
                'outreach_focus': 'Mycorrhizal research for conservation planning',
                'collaboration_proposal': {
                    'title': 'Mycorrhizal-Based Conservation Strategy Development',
                    'description': 'Integrate mycorrhizal requirements into orchid conservation planning',
                    'conservation_applications': [
                        'Habitat restoration protocols based on mycorrhizal needs',
                        'Site selection criteria including fungal partner availability',
                        'Translocation success prediction using mycorrhizal data',
                        'Climate change adaptation strategies for orchid-fungal partnerships'
                    ],
                    'research_priorities': [
                        'Identify critical mycorrhizal habitats for protection',
                        'Map fungal partner distributions across orchid ranges',
                        'Assess climate change impacts on orchid-fungal relationships',
                        'Develop ex-situ mycorrhizal preservation protocols'
                    ],
                    'alliance_benefits': [
                        'Enhanced scientific basis for conservation recommendations',
                        'Predictive tools for habitat viability assessment',
                        'Data-driven arguments for habitat protection',
                        'Collaboration with global research network'
                    ]
                }
            }
        
        elif contact_type == 'dennis_wickham':
            return {
                'contact_name': 'Dennis Wickham',
                'organization': 'Former Director, Smithsonian North American Orchid Conservation Center',
                'specialization': 'North American orchid conservation and propagation',
                'outreach_focus': 'Mycorrhizal research for propagation and reintroduction',
                'collaboration_proposal': {
                    'title': 'Mycorrhizal-Enhanced Orchid Propagation and Reintroduction',
                    'description': 'Apply mycorrhizal research to improve conservation outcomes',
                    'propagation_applications': [
                        'Optimize symbiotic seed germination protocols',
                        'Enhance seedling survival through mycorrhizal inoculation',
                        'Develop species-specific fungal cultivation methods',
                        'Improve reintroduction success rates'
                    ],
                    'naocc_synergies': [
                        'Combine NAOCC propagation expertise with mycorrhizal research',
                        'Enhance seed banking protocols with fungal partner preservation',
                        'Improve genetic rescue techniques using mycorrhizal data',
                        'Develop standardized mycorrhizal assessment protocols'
                    ],
                    'smithsonian_collaboration': [
                        'Access to Smithsonian research collections and databases',
                        'Integration with National Museum of Natural History',
                        'Collaboration with DNA barcode initiatives',
                        'Joint funding proposals for mycorrhizal research'
                    ]
                }
            }
        
        elif contact_type == 'noc_network':
            return {
                'contact_name': 'North American Orchid Conservation Network',
                'organization': 'Regional orchid conservation groups',
                'specialization': 'Grassroots orchid conservation and monitoring',
                'outreach_focus': 'Citizen science mycorrhizal monitoring',
                'collaboration_proposal': {
                    'title': 'Citizen Science Mycorrhizal Monitoring Network',
                    'description': 'Engage local orchid groups in mycorrhizal research and monitoring',
                    'network_advantages': [
                        'Wide geographic coverage across North America',
                        'Local knowledge of orchid populations and habitats',
                        'Established volunteer networks for data collection',
                        'Community connections for long-term monitoring'
                    ],
                    'training_program': [
                        'Mycorrhizal association identification workshops',
                        'Soil sampling and environmental data collection training',
                        'Photo documentation standards for mycorrhizal research',
                        'Citizen science data submission protocols'
                    ],
                    'community_benefits': [
                        'Enhanced understanding of local orchid ecology',
                        'Contribution to regional conservation planning',
                        'Scientific recognition for volunteer contributions',
                        'Access to research findings and conservation updates'
                    ]
                }
            }
        
        return {}

    def get_mycorrhizal_mapping_data(self) -> Dict:
        """Generate data for mycorrhizal association mapping"""
        return {
            'known_associations': self.known_associations,
            'research_priorities': self.research_priorities,
            'environmental_correlations': {
                'soil_ph_preferences': {
                    'acidic': ['Cypripedium acaule', 'Goodyera pubescens'],
                    'neutral': ['Cypripedium reginae', 'Platanthera psycodes'],
                    'alkaline': ['Cypripedium candidum', 'Epipactis helleborine']
                },
                'habitat_associations': {
                    'forest_floor': ['Russula', 'Lactarius', 'Cortinarius'],
                    'bog_wetland': ['Tulasnella', 'Ceratobasidium'],
                    'prairie_grassland': ['Rhizoctonia', 'Sebacina']
                }
            },
            'conservation_priorities': {
                'critical_associations': [
                    'Cypripedium-Russula partnerships in declining forests',
                    'Platanthera-Ceratobasidium in threatened wetlands',
                    'Endemic orchid-fungal pairs in isolated habitats'
                ]
            }
        }

# Global instance
mycorrhizal_system = MycorrhizalResearchSystem()

# Routes
@mycorrhizal_bp.route('/')
def mycorrhizal_home():
    """Mycorrhizal research home page"""
    research_data = mycorrhizal_system.get_mycorrhizal_mapping_data()
    return render_template('mycorrhizal/research_home.html', 
                         research_data=research_data,
                         system=mycorrhizal_system)

@mycorrhizal_bp.route('/projects')
def view_projects():
    """View active mycorrhizal research projects"""
    projects = []
    if os.path.exists(mycorrhizal_system.research_projects_dir):
        for filename in os.listdir(mycorrhizal_system.research_projects_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(mycorrhizal_system.research_projects_dir, filename)
                with open(filepath, 'r') as f:
                    project = json.load(f)
                    projects.append(project)
    
    return render_template('mycorrhizal/projects.html', projects=projects)

@mycorrhizal_bp.route('/submit-observation/<project_id>')
def submit_observation(project_id):
    """Mycorrhizal observation submission form"""
    project_file = os.path.join(mycorrhizal_system.research_projects_dir, f"{project_id}.json")
    
    if os.path.exists(project_file):
        with open(project_file, 'r') as f:
            project = json.load(f)
        return render_template('mycorrhizal/observation_form.html', 
                             project=project,
                             known_associations=mycorrhizal_system.known_associations)
    else:
        flash('Project not found', 'error')
        return redirect(url_for('mycorrhizal_research.view_projects'))

@mycorrhizal_bp.route('/outreach/<contact_type>')
def generate_outreach(contact_type):
    """Generate outreach materials for specific contacts"""
    outreach_data = mycorrhizal_system.generate_conservation_outreach(contact_type)
    
    if outreach_data:
        return render_template('mycorrhizal/outreach.html', 
                             outreach=outreach_data,
                             contact_type=contact_type)
    else:
        flash('Contact type not found', 'error')
        return redirect(url_for('mycorrhizal_research.mycorrhizal_home'))

@mycorrhizal_bp.route('/mapping')
def mycorrhizal_mapping():
    """Interactive mycorrhizal association mapping"""
    mapping_data = mycorrhizal_system.get_mycorrhizal_mapping_data()
    return render_template('mycorrhizal/mapping.html', mapping_data=mapping_data)

# API Routes
@mycorrhizal_bp.route('/api/create-project', methods=['POST'])
def api_create_project():
    """API endpoint to create mycorrhizal research project"""
    try:
        project_data = request.get_json() or request.form.to_dict()
        project_id = mycorrhizal_system.create_mycorrhizal_project(project_data)
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'message': 'Mycorrhizal research project created successfully'
        })
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mycorrhizal_bp.route('/api/submit-observation', methods=['POST'])
def api_submit_observation():
    """API endpoint to submit mycorrhizal observation"""
    try:
        observation_data = request.get_json() or request.form.to_dict()
        result = mycorrhizal_system.submit_mycorrhizal_observation(observation_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error submitting observation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mycorrhizal_bp.route('/api/mapping-data')
def api_mapping_data():
    """API endpoint for mycorrhizal mapping data"""
    try:
        mapping_data = mycorrhizal_system.get_mycorrhizal_mapping_data()
        return jsonify(mapping_data)
    except Exception as e:
        logger.error(f"Error getting mapping data: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    print("🍄 Mycorrhizal Research System standalone mode")
    print("Available research priorities:")
    for category, data in mycorrhizal_system.research_priorities.items():
        print(f"  {category}: {', '.join(data['genera'])}")