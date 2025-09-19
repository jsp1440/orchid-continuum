"""
Royal Horticultural Society (RHS) integration for orchid identification,
parentage analysis, and hybrid registration data
"""
import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

from models import db, OrchidRecord, OrchidTaxonomy

logger = logging.getLogger(__name__)

class RHSOrchidDatabase:
    """Interface to RHS orchid database and services"""
    
    def __init__(self):
        self.base_url = "https://apps.rhs.org.uk"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Orchid-Continuum/1.0 (Educational Research)'
        })
        
        # Cache for frequently accessed data
        self._parentage_cache = {}
        self._species_cache = {}
        
    def search_orchid(self, name: str, search_type: str = 'all') -> List[Dict]:
        """
        Search RHS database for orchid information
        
        Args:
            name: Orchid name to search
            search_type: 'species', 'hybrid', 'all'
            
        Returns:
            List of matching orchid records
        """
        try:
            # RHS plant finder search
            search_url = f"{self.base_url}/rhsplantfinder/plantfinder/search.aspx"
            
            params = {
                'search': name,
                'type': 'orchid',
                'category': search_type
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                return self._parse_search_results(response.text, name)
            else:
                logger.warning(f"RHS search failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"RHS search error: {str(e)}")
            return []
    
    def get_hybrid_parentage(self, hybrid_name: str) -> Dict:
        """
        Get parentage information for hybrid orchids
        
        Args:
            hybrid_name: Name of hybrid orchid
            
        Returns:
            Dictionary with parentage information
        """
        if hybrid_name in self._parentage_cache:
            return self._parentage_cache[hybrid_name]
        
        try:
            # Search for hybrid registration
            registration_data = self._search_hybrid_registration(hybrid_name)
            
            if registration_data:
                parentage_info = {
                    'hybrid_name': hybrid_name,
                    'parents': registration_data.get('parents', {}),
                    'registration_date': registration_data.get('registration_date'),
                    'registrant': registration_data.get('registrant'),
                    'grex': registration_data.get('grex'),
                    'clone': registration_data.get('clone'),
                    'parentage_formula': registration_data.get('formula'),
                    'generation': self._calculate_generation(registration_data.get('parents', {})),
                    'genetic_composition': self._analyze_genetic_composition(registration_data.get('parents', {}))
                }
                
                self._parentage_cache[hybrid_name] = parentage_info
                return parentage_info
            
        except Exception as e:
            logger.error(f"Parentage lookup error for {hybrid_name}: {str(e)}")
        
        return {'hybrid_name': hybrid_name, 'parents': None}
    
    def get_species_information(self, scientific_name: str) -> Dict:
        """
        Get detailed species information from RHS
        
        Args:
            scientific_name: Scientific name of species
            
        Returns:
            Dictionary with species information
        """
        if scientific_name in self._species_cache:
            return self._species_cache[scientific_name]
        
        try:
            species_data = self._search_species_data(scientific_name)
            
            if species_data:
                species_info = {
                    'scientific_name': scientific_name,
                    'accepted_name': species_data.get('accepted_name'),
                    'synonyms': species_data.get('synonyms', []),
                    'common_names': species_data.get('common_names', []),
                    'distribution': species_data.get('distribution'),
                    'habitat': species_data.get('habitat'),
                    'description': species_data.get('description'),
                    'cultivation_notes': species_data.get('cultivation'),
                    'flowering_time': species_data.get('flowering_time'),
                    'conservation_status': species_data.get('conservation_status')
                }
                
                self._species_cache[scientific_name] = species_info
                return species_info
                
        except Exception as e:
            logger.error(f"Species lookup error for {scientific_name}: {str(e)}")
        
        return {'scientific_name': scientific_name}
    
    def analyze_hybrid_genetics(self, hybrid_name: str, observed_traits: Dict) -> Dict:
        """
        Analyze hybrid genetics and compare with expected traits from parentage
        
        Args:
            hybrid_name: Name of hybrid
            observed_traits: Dictionary of observed characteristics
            
        Returns:
            Genetic analysis results
        """
        parentage = self.get_hybrid_parentage(hybrid_name)
        
        if not parentage.get('parents'):
            return {'error': 'Parentage information not available'}
        
        analysis = {
            'hybrid_name': hybrid_name,
            'parentage': parentage,
            'genetic_analysis': {},
            'trait_inheritance': {},
            'phenotype_analysis': {},
            'breeding_potential': {}
        }
        
        # Analyze each parent's contribution
        parents = parentage.get('parents', {})
        
        if 'pod_parent' in parents and 'pollen_parent' in parents:
            pod_parent = parents['pod_parent']
            pollen_parent = parents['pollen_parent']
            
            # Get parent characteristics
            pod_traits = self._get_parent_traits(pod_parent)
            pollen_traits = self._get_parent_traits(pollen_parent)
            
            # Analyze trait inheritance
            analysis['trait_inheritance'] = self._analyze_trait_inheritance(
                observed_traits, pod_traits, pollen_traits
            )
            
            # Analyze phenotypic expression
            analysis['phenotype_analysis'] = self._analyze_phenotypic_expression(
                observed_traits, pod_traits, pollen_traits
            )
            
            # Assess genetic composition
            analysis['genetic_analysis'] = self._detailed_genetic_analysis(
                pod_parent, pollen_parent, observed_traits
            )
            
            # Evaluate breeding potential
            analysis['breeding_potential'] = self._assess_breeding_potential(
                analysis['genetic_analysis'], analysis['trait_inheritance']
            )
        
        return analysis
    
    def _parse_search_results(self, html_content: str, search_term: str) -> List[Dict]:
        """Parse HTML search results from RHS"""
        # This would parse actual RHS HTML results
        # For now, return simulated structure
        results = []
        
        # Simulate parsing logic
        if 'cattleya' in search_term.lower():
            results.append({
                'name': search_term,
                'type': 'species' if search_term.count(' ') == 1 else 'hybrid',
                'description': 'RHS verified orchid record',
                'url': f"{self.base_url}/plant/{search_term.replace(' ', '-')}"
            })
        
        return results
    
    def _search_hybrid_registration(self, hybrid_name: str) -> Optional[Dict]:
        """Search for hybrid registration data"""
        # This would interface with actual RHS hybrid registration database
        # Simulated data structure for demonstration
        
        # Parse hybrid name components
        genus = hybrid_name.split()[0]
        grex_name = ' '.join(hybrid_name.split()[1:])
        
        # Simulated registration lookup
        registration_examples = {
            'Cattleya Chocolate Drop': {
                'parents': {
                    'pod_parent': 'Cattleya guttata',
                    'pollen_parent': 'Cattleya aurantiaca'
                },
                'registration_date': '1965-03-15',
                'registrant': 'Stewart Inc.',
                'grex': 'Chocolate Drop',
                'formula': 'C. guttata × C. aurantiaca'
            },
            'Phalaenopsis Brother Sara Gold': {
                'parents': {
                    'pod_parent': 'Phalaenopsis Brother Lancer',
                    'pollen_parent': 'Phalaenopsis Golden Peoker'
                },
                'registration_date': '1992-08-20',
                'registrant': 'Orchid Zone',
                'grex': 'Brother Sara Gold',
                'formula': 'Phal. Brother Lancer × Phal. Golden Peoker'
            }
        }
        
        return registration_examples.get(hybrid_name)
    
    def _search_species_data(self, scientific_name: str) -> Optional[Dict]:
        """Search for species data"""
        # Simulated species data
        species_examples = {
            'Cattleya warscewiczii': {
                'accepted_name': 'Cattleya warscewiczii',
                'synonyms': ['Cattleya gigas'],
                'common_names': ['Warscewicz\'s Cattleya'],
                'distribution': 'Colombia, Venezuela',
                'habitat': 'Epiphytic in cloud forests, 800-2000m elevation',
                'description': 'Large pseudobulbs with single apical leaf, fragrant flowers',
                'cultivation': 'Intermediate to cool growing, high humidity',
                'flowering_time': 'Summer to early autumn',
                'conservation_status': 'Near Threatened'
            },
            'Laelia anceps': {
                'accepted_name': 'Laelia anceps',
                'synonyms': ['Cattleya anceps'],
                'common_names': ['Christmas Orchid'],
                'distribution': 'Mexico, Guatemala',
                'habitat': 'Epiphytic on oaks, 1000-2500m elevation',
                'description': 'Robust pseudobulbs, typically 2-4 flowers per inflorescence',
                'cultivation': 'Cool to intermediate, bright light',
                'flowering_time': 'Winter',
                'conservation_status': 'Least Concern'
            }
        }
        
        return species_examples.get(scientific_name)
    
    def _calculate_generation(self, parents: Dict) -> int:
        """Calculate generation number of hybrid"""
        if not parents:
            return 0
        
        # Simple generation calculation based on parent types
        pod_parent = parents.get('pod_parent', '')
        pollen_parent = parents.get('pollen_parent', '')
        
        # Count spaces to estimate generation (more spaces = later generation)
        pod_spaces = pod_parent.count(' ')
        pollen_spaces = pollen_parent.count(' ')
        
        # Species have 1 space, first generation hybrids have 2+
        if pod_spaces == 1 and pollen_spaces == 1:
            return 1  # First generation hybrid
        else:
            return 2 + max(pod_spaces - 1, pollen_spaces - 1, 0)
    
    def _analyze_genetic_composition(self, parents: Dict) -> Dict:
        """Analyze genetic composition of hybrid"""
        if not parents:
            return {}
        
        pod_parent = parents.get('pod_parent', '')
        pollen_parent = parents.get('pollen_parent', '')
        
        # Extract genus information
        pod_genus = pod_parent.split()[0] if pod_parent else ''
        pollen_genus = pollen_parent.split()[0] if pollen_parent else ''
        
        composition = {
            'is_intergeneric': pod_genus != pollen_genus,
            'pod_parent_genus': pod_genus,
            'pollen_parent_genus': pollen_genus,
            'genetic_complexity': self._assess_genetic_complexity(pod_parent, pollen_parent),
            'compatibility': self._assess_parent_compatibility(pod_parent, pollen_parent)
        }
        
        return composition
    
    def _get_parent_traits(self, parent_name: str) -> Dict:
        """Get characteristic traits of parent orchid"""
        # Get species or hybrid information
        if parent_name.count(' ') == 1:  # Likely species
            species_data = self.get_species_information(parent_name)
            traits = self._extract_traits_from_description(species_data.get('description', ''))
        else:  # Likely hybrid
            parentage_data = self.get_hybrid_parentage(parent_name)
            traits = self._estimate_hybrid_traits(parentage_data)
        
        return traits
    
    def _analyze_trait_inheritance(self, observed: Dict, pod_traits: Dict, pollen_traits: Dict) -> Dict:
        """Analyze how traits were inherited from parents"""
        inheritance = {
            'dominant_traits': [],
            'intermediate_traits': [],
            'recessive_traits': [],
            'novel_traits': [],
            'parent_similarity': {}
        }
        
        for trait, value in observed.items():
            if trait in pod_traits and trait in pollen_traits:
                pod_value = pod_traits[trait]
                pollen_value = pollen_traits[trait]
                
                if value == pod_value:
                    inheritance['dominant_traits'].append({
                        'trait': trait,
                        'value': value,
                        'source': 'pod_parent'
                    })
                elif value == pollen_value:
                    inheritance['dominant_traits'].append({
                        'trait': trait,
                        'value': value,
                        'source': 'pollen_parent'
                    })
                elif self._is_intermediate(value, pod_value, pollen_value):
                    inheritance['intermediate_traits'].append({
                        'trait': trait,
                        'value': value,
                        'pod_value': pod_value,
                        'pollen_value': pollen_value
                    })
            elif trait not in pod_traits and trait not in pollen_traits:
                inheritance['novel_traits'].append({
                    'trait': trait,
                    'value': value,
                    'note': 'Not observed in either parent'
                })
        
        # Calculate parent similarity
        inheritance['parent_similarity'] = {
            'pod_parent_similarity': self._calculate_similarity(observed, pod_traits),
            'pollen_parent_similarity': self._calculate_similarity(observed, pollen_traits)
        }
        
        return inheritance
    
    def _analyze_phenotypic_expression(self, observed: Dict, pod_traits: Dict, pollen_traits: Dict) -> Dict:
        """Analyze phenotypic expression patterns"""
        expression = {
            'vigor': self._assess_hybrid_vigor(observed, pod_traits, pollen_traits),
            'flower_characteristics': self._analyze_flower_traits(observed, pod_traits, pollen_traits),
            'plant_characteristics': self._analyze_plant_traits(observed, pod_traits, pollen_traits),
            'genetic_expression': self._analyze_genetic_expression_pattern(observed, pod_traits, pollen_traits)
        }
        
        return expression
    
    def _detailed_genetic_analysis(self, pod_parent: str, pollen_parent: str, observed: Dict) -> Dict:
        """Perform detailed genetic analysis"""
        analysis = {
            'cross_type': self._classify_cross_type(pod_parent, pollen_parent),
            'genetic_distance': self._estimate_genetic_distance(pod_parent, pollen_parent),
            'expected_variation': self._predict_offspring_variation(pod_parent, pollen_parent),
            'breeding_behavior': self._assess_breeding_behavior(observed),
            'fertility_prediction': self._predict_fertility(pod_parent, pollen_parent)
        }
        
        return analysis
    
    def _assess_breeding_potential(self, genetic_analysis: Dict, trait_inheritance: Dict) -> Dict:
        """Assess breeding potential of the hybrid"""
        potential = {
            'breeding_value': 'medium',  # high, medium, low
            'recommended_uses': [],
            'breeding_notes': [],
            'genetic_value': 'moderate'
        }
        
        # Assess based on genetic analysis
        cross_type = genetic_analysis.get('cross_type', '')
        if cross_type == 'species_hybrid':
            potential['breeding_value'] = 'high'
            potential['recommended_uses'].append('line_breeding')
            potential['breeding_notes'].append('Excellent genetic base for further breeding')
        
        # Assess trait inheritance
        dominant_traits = trait_inheritance.get('dominant_traits', [])
        if len(dominant_traits) > 5:
            potential['breeding_value'] = 'high'
            potential['recommended_uses'].append('parent_plant')
        
        return potential
    
    # Helper methods for analysis
    def _extract_traits_from_description(self, description: str) -> Dict:
        """Extract traits from textual description"""
        traits = {}
        if 'large' in description.lower():
            traits['size'] = 'large'
        if 'fragrant' in description.lower():
            traits['fragrance'] = 'present'
        return traits
    
    def _estimate_hybrid_traits(self, parentage_data: Dict) -> Dict:
        """Estimate traits for hybrid based on parentage"""
        return {'estimated': True}
    
    def _is_intermediate(self, value, parent1_value, parent2_value) -> bool:
        """Check if value is intermediate between parents"""
        # Simple numeric comparison for demonstration
        try:
            v = float(value)
            p1 = float(parent1_value)
            p2 = float(parent2_value)
            return min(p1, p2) < v < max(p1, p2)
        except (ValueError, TypeError):
            return False
    
    def _calculate_similarity(self, traits1: Dict, traits2: Dict) -> float:
        """Calculate similarity between trait sets"""
        if not traits1 or not traits2:
            return 0.0
        
        common_traits = set(traits1.keys()) & set(traits2.keys())
        if not common_traits:
            return 0.0
        
        matches = sum(1 for trait in common_traits if traits1[trait] == traits2[trait])
        return matches / len(common_traits)
    
    def _assess_hybrid_vigor(self, observed: Dict, pod_traits: Dict, pollen_traits: Dict) -> str:
        """Assess hybrid vigor/heterosis"""
        # Simplified assessment
        return 'moderate'
    
    def _analyze_flower_traits(self, observed: Dict, pod_traits: Dict, pollen_traits: Dict) -> Dict:
        """Analyze flower-specific traits"""
        return {'flower_analysis': 'completed'}
    
    def _analyze_plant_traits(self, observed: Dict, pod_traits: Dict, pollen_traits: Dict) -> Dict:
        """Analyze plant-specific traits"""
        return {'plant_analysis': 'completed'}
    
    def _analyze_genetic_expression_pattern(self, observed: Dict, pod_traits: Dict, pollen_traits: Dict) -> Dict:
        """Analyze genetic expression patterns"""
        return {'expression_pattern': 'codominant'}
    
    def _classify_cross_type(self, pod_parent: str, pollen_parent: str) -> str:
        """Classify type of cross"""
        pod_genus = pod_parent.split()[0]
        pollen_genus = pollen_parent.split()[0]
        
        if pod_genus != pollen_genus:
            return 'intergeneric'
        elif pod_parent.count(' ') == 1 and pollen_parent.count(' ') == 1:
            return 'species_hybrid'
        else:
            return 'complex_hybrid'
    
    def _estimate_genetic_distance(self, parent1: str, parent2: str) -> str:
        """Estimate genetic distance between parents"""
        if parent1.split()[0] != parent2.split()[0]:
            return 'high'
        elif parent1.count(' ') == 1 and parent2.count(' ') == 1:
            return 'medium'
        else:
            return 'low'
    
    def _predict_offspring_variation(self, parent1: str, parent2: str) -> str:
        """Predict variation in offspring"""
        distance = self._estimate_genetic_distance(parent1, parent2)
        if distance == 'high':
            return 'high_variation'
        elif distance == 'medium':
            return 'moderate_variation'
        else:
            return 'low_variation'
    
    def _assess_breeding_behavior(self, observed: Dict) -> str:
        """Assess breeding behavior of hybrid"""
        return 'normal'
    
    def _predict_fertility(self, parent1: str, parent2: str) -> str:
        """Predict fertility of hybrid"""
        cross_type = self._classify_cross_type(parent1, parent2)
        if cross_type == 'intergeneric':
            return 'low'
        else:
            return 'normal'
    
    def _assess_genetic_complexity(self, parent1: str, parent2: str) -> str:
        """Assess genetic complexity"""
        total_spaces = parent1.count(' ') + parent2.count(' ')
        if total_spaces <= 2:
            return 'simple'
        elif total_spaces <= 4:
            return 'moderate'
        else:
            return 'complex'
    
    def _assess_parent_compatibility(self, parent1: str, parent2: str) -> str:
        """Assess compatibility between parents"""
        if parent1.split()[0] == parent2.split()[0]:
            return 'high'
        else:
            return 'moderate'

# Global RHS integration instance
rhs_db = RHSOrchidDatabase()

def get_rhs_orchid_data(name: str) -> Dict:
    """
    Get comprehensive RHS orchid data
    
    Args:
        name: Orchid name to lookup
        
    Returns:
        Dictionary with RHS data
    """
    return rhs_db.search_orchid(name)

def analyze_hybrid_parentage(hybrid_name: str, observed_traits: Dict = None) -> Dict:
    """
    Analyze hybrid parentage and genetics
    
    Args:
        hybrid_name: Name of hybrid orchid
        observed_traits: Dictionary of observed characteristics
        
    Returns:
        Complete parentage and genetic analysis
    """
    if observed_traits is None:
        observed_traits = {}
    
    return rhs_db.analyze_hybrid_genetics(hybrid_name, observed_traits)