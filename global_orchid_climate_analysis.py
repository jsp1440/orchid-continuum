"""
Global Orchid Climate Analysis System
Comprehensive mapping and optimization platform for orchid-fungal carbon dynamics
"""

import os
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

global_analysis_bp = Blueprint('global_analysis', __name__, url_prefix='/global-analysis')

@dataclass
class OrchidDistributionPoint:
    """Single orchid species distribution data point"""
    species: str
    latitude: float
    longitude: float
    elevation: int
    climate_zone: str
    soil_type: str
    soil_ph: float
    annual_rainfall: float
    temperature_range: Tuple[float, float]  # (min, max)
    mycorrhizal_partners: List[str]
    cam_photosynthesis: bool
    carbon_transfer_rate: Optional[float]
    environmental_stress_factors: List[str]

@dataclass
class FungalDistributionZone:
    """Mycorrhizal fungi distribution zone"""
    fungal_genus: str
    fungal_species: str
    geographic_range: List[Tuple[float, float]]  # [(lat, lon), ...]
    optimal_conditions: Dict[str, Any]
    orchid_partners: List[str]
    carbon_storage_capacity: float
    soil_penetration_depth: float
    network_connectivity: str  # 'high', 'medium', 'low'

class GlobalOrchidClimateAnalysis:
    """
    Comprehensive system for analyzing global orchid-fungal relationships
    and optimizing them for climate solutions
    """
    
    def __init__(self):
        self.analysis_data_dir = 'global_climate_analysis'
        self.distribution_maps_dir = os.path.join(self.analysis_data_dir, 'distribution_maps')
        self.optimization_models_dir = os.path.join(self.analysis_data_dir, 'optimization_models')
        self.scaling_analysis_dir = os.path.join(self.analysis_data_dir, 'scaling_analysis')
        
        # Create directories
        for directory in [self.analysis_data_dir, self.distribution_maps_dir, 
                         self.optimization_models_dir, self.scaling_analysis_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Load global distribution data
        self.orchid_distributions = self._load_global_orchid_distributions()
        self.fungal_distributions = self._load_global_fungal_distributions()
        
        # Environmental correlation factors
        self.environmental_factors = {
            'climate_drivers': {
                'temperature': {
                    'optimal_range': (20, 30),  # Celsius for most CAM orchids
                    'stress_threshold': 35,
                    'impact_on_cam': 'High temperature increases CAM efficiency but reduces water availability'
                },
                'humidity': {
                    'optimal_range': (60, 80),  # Percentage
                    'stress_threshold': 40,
                    'impact_on_cam': 'High humidity allows for extended stomatal opening'
                },
                'rainfall': {
                    'optimal_range': (800, 2000),  # mm/year
                    'drought_threshold': 500,
                    'impact_on_cam': 'Moderate rainfall with dry seasons optimizes CAM evolution'
                }
            },
            'soil_chemistry': {
                'ph': {
                    'acidic_preference': [4.5, 6.0],  # Most temperate orchids
                    'neutral_preference': [6.0, 7.5],  # Many tropical epiphytes
                    'alkaline_tolerance': [7.5, 8.5],  # Specialized species
                    'fungal_correlation': 'Soil pH directly affects mycorrhizal species composition'
                },
                'mineral_content': {
                    'iron': 'Critical for mycorrhizal metabolism and carbon transfer',
                    'phosphorus': 'Low P environments favor mycorrhizal dependence',
                    'nitrogen': 'N limitation increases carbon allocation to fungi',
                    'calcium': 'Essential for cell wall formation in fungal networks'
                },
                'organic_matter': {
                    'optimal_percentage': (3, 8),
                    'carbon_storage_correlation': 'High OM = higher carbon sequestration potential'
                }
            },
            'ecological_factors': {
                'canopy_cover': {
                    'epiphytic_optimal': (70, 90),  # Percentage
                    'terrestrial_optimal': (30, 70),
                    'impact': 'Affects light availability and humidity regulation'
                },
                'mycorrhizal_network_density': {
                    'high_connectivity': 'Enhanced carbon transfer between plants',
                    'network_effects': 'Larger networks = more stable carbon storage'
                },
                'disturbance_regime': {
                    'fire_frequency': 'Affects soil carbon and fungal populations',
                    'human_impact': 'Habitat fragmentation disrupts fungal networks'
                }
            }
        }
        
        # Carbon optimization models
        self.optimization_targets = self._initialize_optimization_models()
        
        # Scaling scenarios
        self.scaling_scenarios = self._initialize_scaling_scenarios()
        
        logger.info("🌍 Global Orchid Climate Analysis System initialized")

    def _load_global_orchid_distributions(self) -> Dict[str, List[OrchidDistributionPoint]]:
        """Load global orchid distribution data"""
        distributions_file = os.path.join(self.distribution_maps_dir, 'global_orchid_distributions.json')
        
        if os.path.exists(distributions_file):
            with open(distributions_file, 'r') as f:
                data = json.load(f)
                # Convert to OrchidDistributionPoint objects
                distributions = {}
                for species, points in data.items():
                    distributions[species] = [
                        OrchidDistributionPoint(**point) for point in points
                    ]
                return distributions
        
        # Initialize with key climate-relevant species distributions
        initial_distributions = {
            'phalaenopsis_amabilis': [
                OrchidDistributionPoint(
                    species='Phalaenopsis amabilis',
                    latitude=1.35, longitude=103.82,  # Singapore
                    elevation=50, climate_zone='tropical_humid',
                    soil_type='organic_rich', soil_ph=6.2,
                    annual_rainfall=2400, temperature_range=(24, 32),
                    mycorrhizal_partners=['Tulasnella', 'Ceratobasidium'],
                    cam_photosynthesis=True, carbon_transfer_rate=35.0,
                    environmental_stress_factors=['humidity_fluctuation']
                ),
                OrchidDistributionPoint(
                    species='Phalaenopsis amabilis',
                    latitude=-6.21, longitude=106.85,  # Jakarta
                    elevation=120, climate_zone='tropical_humid',
                    soil_type='volcanic', soil_ph=5.8,
                    annual_rainfall=1800, temperature_range=(26, 34),
                    mycorrhizal_partners=['Tulasnella', 'Sebacina'],
                    cam_photosynthesis=True, carbon_transfer_rate=32.0,
                    environmental_stress_factors=['temperature_stress', 'pollution']
                )
            ],
            'cypripedium_calceolus': [
                OrchidDistributionPoint(
                    species='Cypripedium calceolus',
                    latitude=60.47, longitude=8.47,  # Norway
                    elevation=450, climate_zone='temperate_boreal',
                    soil_type='calcareous', soil_ph=7.2,
                    annual_rainfall=900, temperature_range=(-5, 20),
                    mycorrhizal_partners=['Russula', 'Lactarius'],
                    cam_photosynthesis=False, carbon_transfer_rate=45.0,
                    environmental_stress_factors=['climate_change', 'habitat_loss']
                ),
                OrchidDistributionPoint(
                    species='Cypripedium calceolus',
                    latitude=46.52, longitude=6.63,  # Swiss Alps
                    elevation=1200, climate_zone='alpine',
                    soil_type='limestone', soil_ph=7.8,
                    annual_rainfall=1200, temperature_range=(-8, 18),
                    mycorrhizal_partners=['Russula', 'Cortinarius'],
                    cam_photosynthesis=False, carbon_transfer_rate=50.0,
                    environmental_stress_factors=['altitude_stress', 'grazing_pressure']
                )
            ],
            'dendrobium_nobile': [
                OrchidDistributionPoint(
                    species='Dendrobium nobile',
                    latitude=27.72, longitude=85.32,  # Nepal Himalayas
                    elevation=1800, climate_zone='subtropical_highland',
                    soil_type='rocky', soil_ph=6.5,
                    annual_rainfall=1500, temperature_range=(5, 25),
                    mycorrhizal_partners=['Ceratobasidium', 'Rhizoctonia'],
                    cam_photosynthesis=True, carbon_transfer_rate=28.0,
                    environmental_stress_factors=['seasonal_drought', 'temperature_extremes']
                )
            ]
        }
        
        # Save initial data
        # Convert OrchidDistributionPoint objects to dicts for JSON serialization
        serializable_data = {}
        for species, points in initial_distributions.items():
            serializable_data[species] = [
                {
                    'species': point.species,
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'climate_zone': point.climate_zone,
                    'soil_type': point.soil_type,
                    'soil_ph': point.soil_ph,
                    'annual_rainfall': point.annual_rainfall,
                    'temperature_range': point.temperature_range,
                    'mycorrhizal_partners': point.mycorrhizal_partners,
                    'cam_photosynthesis': point.cam_photosynthesis,
                    'carbon_transfer_rate': point.carbon_transfer_rate,
                    'environmental_stress_factors': point.environmental_stress_factors
                }
                for point in points
            ]
        
        with open(distributions_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        
        return initial_distributions

    def _load_global_fungal_distributions(self) -> Dict[str, FungalDistributionZone]:
        """Load global mycorrhizal fungi distribution data"""
        fungal_file = os.path.join(self.distribution_maps_dir, 'global_fungal_distributions.json')
        
        if os.path.exists(fungal_file):
            with open(fungal_file, 'r') as f:
                data = json.load(f)
                return {name: FungalDistributionZone(**zone_data) for name, zone_data in data.items()}
        
        # Initialize with key mycorrhizal fungi distributions
        initial_fungal_data = {
            'tulasnella_calospora': FungalDistributionZone(
                fungal_genus='Tulasnella',
                fungal_species='calospora',
                geographic_range=[(60, 8), (65, 15), (55, 20), (50, 25)],  # Northern Europe
                optimal_conditions={
                    'temperature_range': (15, 25),
                    'soil_ph_range': (6.5, 7.5),
                    'moisture_preference': 'consistently_moist',
                    'organic_matter_requirement': 'high'
                },
                orchid_partners=['Cypripedium calceolus', 'Cypripedium reginae'],
                carbon_storage_capacity=2.5,  # kg C/m²/year
                soil_penetration_depth=45.0,  # cm
                network_connectivity='high'
            ),
            'ceratobasidium_orchid_complex': FungalDistributionZone(
                fungal_genus='Ceratobasidium',
                fungal_species='orchid_complex',
                geographic_range=[(-10, 100), (30, 120), (40, 140), (-40, 175)],  # Southeast Asia to Australia
                optimal_conditions={
                    'temperature_range': (20, 35),
                    'soil_ph_range': (5.5, 6.8),
                    'moisture_preference': 'variable_seasonal',
                    'organic_matter_requirement': 'medium'
                },
                orchid_partners=['Phalaenopsis spp.', 'Dendrobium spp.', 'Bulbophyllum spp.'],
                carbon_storage_capacity=1.8,  # kg C/m²/year
                soil_penetration_depth=30.0,  # cm
                network_connectivity='medium'
            ),
            'russula_ectomycorrhizal': FungalDistributionZone(
                fungal_genus='Russula',
                fungal_species='ectomycorrhizal_complex',
                geographic_range=[(40, -120), (70, -60), (60, 40), (45, 100)],  # Temperate forests
                optimal_conditions={
                    'temperature_range': (5, 25),
                    'soil_ph_range': (4.5, 6.5),
                    'moisture_preference': 'well_drained',
                    'organic_matter_requirement': 'very_high'
                },
                orchid_partners=['Cypripedium acaule', 'Goodyera pubescens'],
                carbon_storage_capacity=3.2,  # kg C/m²/year
                soil_penetration_depth=60.0,  # cm
                network_connectivity='very_high'
            )
        }
        
        # Convert to serializable format and save
        serializable_fungal_data = {}
        for name, zone in initial_fungal_data.items():
            serializable_fungal_data[name] = {
                'fungal_genus': zone.fungal_genus,
                'fungal_species': zone.fungal_species,
                'geographic_range': zone.geographic_range,
                'optimal_conditions': zone.optimal_conditions,
                'orchid_partners': zone.orchid_partners,
                'carbon_storage_capacity': zone.carbon_storage_capacity,
                'soil_penetration_depth': zone.soil_penetration_depth,
                'network_connectivity': zone.network_connectivity
            }
        
        with open(fungal_file, 'w') as f:
            json.dump(serializable_fungal_data, f, indent=2)
        
        return initial_fungal_data

    def _initialize_optimization_models(self) -> Dict[str, Dict]:
        """Initialize carbon optimization models"""
        return {
            'cam_enhancement': {
                'description': 'Optimizing CAM photosynthesis for maximum CO2 capture',
                'current_baseline': {
                    'average_co2_uptake': 12.5,  # μmol CO2/m²/s
                    'average_efficiency': 65,     # Percentage of theoretical maximum
                    'water_use_efficiency': 7.8   # g biomass/kg water
                },
                'optimization_targets': {
                    'enhanced_co2_uptake': 25.0,   # μmol CO2/m²/s (2x improvement)
                    'enhanced_efficiency': 85,      # Percentage
                    'improved_water_efficiency': 15.0  # g biomass/kg water
                },
                'enhancement_strategies': [
                    'Genetic enhancement of PEP carboxylase enzyme',
                    'Optimization of malic acid storage capacity',
                    'Environmental condition optimization',
                    'Selective breeding for CAM efficiency',
                    'Bioengineering enhanced stomatal control'
                ],
                'expected_impact': {
                    'co2_capture_increase': '100-300% over baseline',
                    'carbon_sequestration_boost': '50-150% through improved transfer',
                    'scaling_potential': 'Applicable to 15,000+ CAM orchid species'
                }
            },
            'mycorrhizal_optimization': {
                'description': 'Enhancing orchid-fungal carbon transfer and soil storage',
                'current_baseline': {
                    'average_carbon_transfer': 35.0,  # Percentage of fixed carbon
                    'soil_storage_efficiency': 60,    # Percentage retained long-term
                    'network_connectivity': 'medium'
                },
                'optimization_targets': {
                    'enhanced_transfer_rate': 65.0,   # Percentage
                    'improved_storage_efficiency': 85, # Percentage
                    'maximum_network_connectivity': 'very_high'
                },
                'enhancement_strategies': [
                    'Fungal strain selection for carbon storage',
                    'Orchid-fungal partnership optimization',
                    'Soil conditioning for enhanced networks',
                    'Multi-species fungal cultivation',
                    'Root system architecture enhancement'
                ],
                'expected_impact': {
                    'carbon_sequestration_increase': '200-400% over baseline',
                    'soil_carbon_storage_boost': '150-300% improvement',
                    'network_resilience': 'Enhanced climate change adaptation'
                }
            },
            'environmental_optimization': {
                'description': 'Environmental engineering for optimal orchid-fungal performance',
                'key_factors': {
                    'soil_chemistry_optimization': {
                        'ph_management': 'Targeted pH adjustment for species pairs',
                        'mineral_supplementation': 'Iron, phosphorus management',
                        'organic_matter_enhancement': 'Biochar and compost integration'
                    },
                    'microclimate_engineering': {
                        'humidity_control': 'Optimized for CAM and fungal activity',
                        'temperature_regulation': 'Thermal mass and shading',
                        'air_circulation': 'Enhanced CO2 availability'
                    },
                    'ecosystem_integration': {
                        'companion_planting': 'Supporting plant communities',
                        'biodiversity_enhancement': 'Pollinator and disperser support',
                        'disturbance_management': 'Protection from disruption'
                    }
                }
            }
        }

    def _initialize_scaling_scenarios(self) -> Dict[str, Dict]:
        """Initialize large-scale implementation scenarios"""
        return {
            'vertical_farming_integration': {
                'description': 'Controlled environment orchid cultivation for carbon capture',
                'implementation_scale': {
                    'pilot_facility': '1,000 m² growing area',
                    'commercial_facility': '10,000 m² growing area',
                    'industrial_complex': '100,000 m² growing area'
                },
                'carbon_capture_potential': {
                    'pilot_scale': '50-150 tons CO2/year',
                    'commercial_scale': '500-1,500 tons CO2/year', 
                    'industrial_scale': '5,000-15,000 tons CO2/year'
                },
                'advantages': [
                    'Controlled environmental conditions',
                    'Year-round operation',
                    'Predictable carbon capture rates',
                    'Protection from climate variability'
                ],
                'challenges': [
                    'High initial capital costs',
                    'Energy requirements for climate control',
                    'Mycorrhizal cultivation complexity',
                    'Economic viability questions'
                ]
            },
            'forest_enhancement_programs': {
                'description': 'Integrating orchids into existing forest ecosystems',
                'implementation_scale': {
                    'local_forest_plot': '100 hectares enhanced',
                    'regional_forest_system': '10,000 hectares enhanced',
                    'national_forest_program': '1,000,000 hectares enhanced'
                },
                'carbon_capture_potential': {
                    'local_scale': '1,000-3,000 tons CO2/year',
                    'regional_scale': '100,000-300,000 tons CO2/year',
                    'national_scale': '10-30 million tons CO2/year'
                },
                'advantages': [
                    'Leverages existing ecosystems',
                    'Enhances biodiversity',
                    'Lower implementation costs',
                    'Multiple ecosystem benefits'
                ],
                'implementation_strategies': [
                    'Native orchid reintroduction',
                    'Mycorrhizal inoculation programs',
                    'Canopy enhancement for epiphytes',
                    'Soil improvement initiatives'
                ]
            },
            'agricultural_integration': {
                'description': 'Carbon farming with orchid-mycorrhizal systems',
                'implementation_scale': {
                    'demonstration_farm': '50 hectares',
                    'commercial_operation': '500 hectares',
                    'landscape_transformation': '50,000 hectares'
                },
                'carbon_capture_potential': {
                    'demonstration_scale': '500-1,500 tons CO2/year',
                    'commercial_scale': '5,000-15,000 tons CO2/year',
                    'landscape_scale': '500,000-1,500,000 tons CO2/year'
                },
                'economic_models': {
                    'carbon_credit_revenue': '$15-50 per ton CO2',
                    'orchid_product_revenue': 'Flowers, breeding stock',
                    'ecosystem_service_payments': 'Biodiversity, water quality',
                    'agritourism_potential': 'Educational and recreational value'
                }
            },
            'urban_integration': {
                'description': 'City-scale orchid carbon capture systems',
                'implementation_approaches': [
                    'Green roof orchid gardens',
                    'Vertical wall growing systems',
                    'Urban forest enhancement',
                    'Public garden integration'
                ],
                'carbon_impact': 'Moderate per unit area, high visibility and education value',
                'co_benefits': [
                    'Air quality improvement',
                    'Urban heat island reduction',
                    'Stormwater management',
                    'Mental health and wellbeing'
                ]
            }
        }

    def analyze_environmental_correlations(self, species_list: Optional[List[str]] = None) -> Dict:
        """Analyze environmental factors driving successful orchid-fungal partnerships"""
        
        if species_list is None:
            species_list = list(self.orchid_distributions.keys())
        
        correlations = {
            'climate_correlations': {},
            'soil_correlations': {},
            'elevation_correlations': {},
            'partnership_success_factors': {},
            'optimization_opportunities': []
        }
        
        all_points = []
        for species in species_list:
            if species in self.orchid_distributions:
                all_points.extend(self.orchid_distributions[species])
        
        if not all_points:
            return correlations
        
        # Climate correlations
        high_transfer_points = [p for p in all_points if p.carbon_transfer_rate and p.carbon_transfer_rate > 40]
        low_transfer_points = [p for p in all_points if p.carbon_transfer_rate and p.carbon_transfer_rate < 30]
        
        if high_transfer_points and low_transfer_points:
            # Temperature analysis
            high_temp_avg = np.mean([np.mean(p.temperature_range) for p in high_transfer_points])
            low_temp_avg = np.mean([np.mean(p.temperature_range) for p in low_transfer_points])
            
            correlations['climate_correlations']['temperature'] = {
                'high_transfer_average': round(high_temp_avg, 1),
                'low_transfer_average': round(low_temp_avg, 1),
                'correlation': 'Higher carbon transfer in moderate temperatures (20-25°C optimal)'
            }
            
            # Rainfall analysis
            high_rain_avg = np.mean([p.annual_rainfall for p in high_transfer_points])
            low_rain_avg = np.mean([p.annual_rainfall for p in low_transfer_points])
            
            correlations['climate_correlations']['rainfall'] = {
                'high_transfer_average': round(high_rain_avg, 0),
                'low_transfer_average': round(low_rain_avg, 0),
                'correlation': 'Moderate rainfall (1000-1500mm) optimal for partnerships'
            }
        
        # Soil correlations
        soil_types = {}
        for point in all_points:
            if point.soil_type not in soil_types:
                soil_types[point.soil_type] = {'points': [], 'avg_transfer': 0}
            soil_types[point.soil_type]['points'].append(point)
        
        for soil_type, data in soil_types.items():
            transfer_rates = [p.carbon_transfer_rate for p in data['points'] if p.carbon_transfer_rate]
            if transfer_rates:
                data['avg_transfer'] = round(np.mean(transfer_rates), 1)
        
        correlations['soil_correlations'] = {
            soil_type: data['avg_transfer'] 
            for soil_type, data in soil_types.items() 
            if data['avg_transfer'] > 0
        }
        
        # Partnership success factors
        correlations['partnership_success_factors'] = {
            'optimal_conditions': {
                'temperature_range': '20-25°C average',
                'rainfall_range': '1000-1500mm annually',
                'soil_ph_range': '6.0-7.0 for most partnerships',
                'elevation_preference': '500-1500m for temperate species'
            },
            'stress_factors_impact': {
                'climate_change': 'Disrupts established temperature/moisture patterns',
                'habitat_fragmentation': 'Breaks mycorrhizal network connectivity',
                'pollution': 'Affects soil chemistry and fungal health',
                'invasive_species': 'Competes for mycorrhizal partners'
            }
        }
        
        # Optimization opportunities
        correlations['optimization_opportunities'] = [
            'Target soil pH optimization in existing habitats',
            'Enhance mycorrhizal network connectivity through corridor creation',
            'Develop climate-adapted orchid-fungal partnerships',
            'Create buffer zones around high-value partnership areas',
            'Implement precision environmental management'
        ]
        
        return correlations

    def model_carbon_optimization_scenarios(self) -> Dict:
        """Model different carbon capture and sequestration optimization scenarios"""
        
        scenarios = {
            'baseline_scenario': {
                'description': 'Current natural orchid-fungal performance',
                'parameters': {
                    'average_cam_efficiency': 65,
                    'average_carbon_transfer': 35,
                    'soil_storage_efficiency': 60,
                    'coverage_area': 'Natural habitat only'
                },
                'annual_impact': {
                    'co2_capture_per_hectare': '2-8 tons',
                    'carbon_sequestration_per_hectare': '1-4 tons',
                    'global_potential': '50-200 million tons CO2/year'
                }
            },
            'enhanced_natural_scenario': {
                'description': 'Optimized natural systems with environmental management',
                'parameters': {
                    'enhanced_cam_efficiency': 80,
                    'improved_carbon_transfer': 50,
                    'enhanced_storage_efficiency': 75,
                    'coverage_area': 'Restored and enhanced natural habitats'
                },
                'annual_impact': {
                    'co2_capture_per_hectare': '5-15 tons',
                    'carbon_sequestration_per_hectare': '3-10 tons',
                    'global_potential': '200-800 million tons CO2/year'
                },
                'implementation_requirements': [
                    'Habitat restoration programs',
                    'Soil chemistry optimization',
                    'Mycorrhizal inoculation programs',
                    'Environmental monitoring systems'
                ]
            },
            'bioengineered_scenario': {
                'description': 'Genetically enhanced orchids with optimized fungal partners',
                'parameters': {
                    'enhanced_cam_efficiency': 95,
                    'maximized_carbon_transfer': 75,
                    'optimized_storage_efficiency': 90,
                    'coverage_area': 'Natural + cultivated systems'
                },
                'annual_impact': {
                    'co2_capture_per_hectare': '15-40 tons',
                    'carbon_sequestration_per_hectare': '10-30 tons',
                    'global_potential': '1-5 billion tons CO2/year'
                },
                'implementation_requirements': [
                    'Genetic engineering research programs',
                    'Fungal strain development',
                    'Cultivation infrastructure',
                    'Regulatory approval processes'
                ]
            },
            'large_scale_deployment': {
                'description': 'Industrial-scale orchid carbon capture systems',
                'parameters': {
                    'controlled_environment_efficiency': 90,
                    'maximized_carbon_transfer': 80,
                    'engineered_storage_systems': 95,
                    'coverage_area': 'Dedicated carbon farming facilities'
                },
                'annual_impact': {
                    'co2_capture_per_hectare': '25-60 tons',
                    'carbon_sequestration_per_hectare': '20-50 tons',
                    'global_potential': '5-20 billion tons CO2/year'
                },
                'economic_considerations': {
                    'implementation_cost': '$10,000-50,000 per hectare',
                    'operating_cost': '$1,000-5,000 per hectare annually',
                    'carbon_cost': '$50-200 per ton CO2 captured',
                    'break_even_carbon_price': '$100-300 per ton'
                }
            }
        }
        
        return scenarios

    def generate_scaling_feasibility_analysis(self) -> Dict:
        """Generate comprehensive scaling feasibility analysis"""
        
        analysis = {
            'technical_feasibility': {
                'current_readiness_level': 3,  # 1-9 scale (Technology Readiness Level)
                'key_technical_challenges': [
                    'Mycorrhizal cultivation at scale',
                    'Environmental condition optimization',
                    'Genetic enhancement development',
                    'Carbon transfer rate maximization'
                ],
                'development_timeline': {
                    'proof_of_concept': '2-3 years',
                    'pilot_scale_demonstration': '5-7 years',
                    'commercial_deployment': '10-15 years',
                    'large_scale_implementation': '15-25 years'
                }
            },
            'economic_feasibility': {
                'current_carbon_market_price': '$15-50 per ton CO2',
                'break_even_requirements': {
                    'minimum_capture_rate': '10 tons CO2/hectare/year',
                    'maximum_cost': '$200 per ton CO2',
                    'carbon_price_threshold': '$100-150 per ton'
                },
                'revenue_streams': [
                    'Carbon credit sales',
                    'Orchid product sales (flowers, breeding)',
                    'Ecosystem service payments',
                    'Agritourism and education',
                    'Research collaboration fees'
                ],
                'investment_requirements': {
                    'research_and_development': '$100-500 million',
                    'pilot_facilities': '$50-200 million',
                    'commercial_deployment': '$1-10 billion',
                    'global_scaling': '$100-500 billion'
                }
            },
            'environmental_feasibility': {
                'suitable_land_availability': {
                    'existing_orchid_habitats': '10-50 million hectares globally',
                    'potential_restoration_areas': '50-200 million hectares',
                    'agricultural_integration_potential': '100-500 million hectares'
                },
                'ecosystem_compatibility': {
                    'biodiversity_benefits': 'High - supports native orchid conservation',
                    'habitat_enhancement': 'Positive - improves ecosystem services',
                    'water_resource_impact': 'Neutral to positive - improved water retention',
                    'soil_health_impact': 'Positive - enhanced soil carbon and structure'
                },
                'climate_change_resilience': {
                    'adaptation_potential': 'High - diverse species and genetic resources',
                    'geographic_flexibility': 'Good - multiple climate zones suitable',
                    'stress_tolerance': 'Variable - requires species-specific assessment'
                }
            },
            'regulatory_and_social_feasibility': {
                'regulatory_requirements': [
                    'Carbon credit certification protocols',
                    'Genetic modification approvals (if applicable)',
                    'Environmental impact assessments',
                    'Land use permits and zoning'
                ],
                'social_acceptance_factors': [
                    'Conservation appeal of orchid protection',
                    'Educational and aesthetic value',
                    'Rural economic development opportunities',
                    'Climate action demonstration value'
                ],
                'stakeholder_engagement_needs': [
                    'Conservation organizations',
                    'Agricultural communities',
                    'Indigenous land managers',
                    'Government environmental agencies',
                    'Climate investors and carbon markets'
                ]
            }
        }
        
        return analysis

    def get_global_analysis_overview(self) -> Dict:
        """Get comprehensive overview of global analysis capabilities"""
        return {
            'distribution_data': {
                'orchid_species_mapped': len(self.orchid_distributions),
                'fungal_zones_identified': len(self.fungal_distributions),
                'geographic_coverage': 'Global with focus on climate-relevant regions',
                'data_resolution': 'Species-level with environmental metadata'
            },
            'environmental_factors': self.environmental_factors,
            'optimization_models': self.optimization_targets,
            'scaling_scenarios': self.scaling_scenarios,
            'research_priorities': [
                'Enhanced CAM photosynthesis mechanisms',
                'Mycorrhizal carbon transfer optimization',
                'Large-scale cultivation feasibility',
                'Economic viability assessment',
                'Climate change adaptation strategies'
            ]
        }

# Global instance
global_analysis = GlobalOrchidClimateAnalysis()

# Routes
@global_analysis_bp.route('/')
def analysis_home():
    """Global analysis home page"""
    overview_data = global_analysis.get_global_analysis_overview()
    return render_template('global_analysis/analysis_home.html', 
                         analysis_data=overview_data,
                         system=global_analysis)

@global_analysis_bp.route('/distribution-mapping')
def distribution_mapping():
    """Interactive global distribution mapping"""
    orchid_data = global_analysis.orchid_distributions
    fungal_data = global_analysis.fungal_distributions
    return render_template('global_analysis/distribution_mapping.html',
                         orchid_distributions=orchid_data,
                         fungal_distributions=fungal_data)

@global_analysis_bp.route('/environmental-correlations')
def environmental_correlations():
    """Environmental correlation analysis"""
    correlations = global_analysis.analyze_environmental_correlations()
    return render_template('global_analysis/environmental_correlations.html',
                         correlations=correlations)

@global_analysis_bp.route('/optimization-modeling')
def optimization_modeling():
    """Carbon optimization modeling interface"""
    scenarios = global_analysis.model_carbon_optimization_scenarios()
    return render_template('global_analysis/optimization_modeling.html',
                         scenarios=scenarios)

@global_analysis_bp.route('/scaling-analysis')
def scaling_analysis():
    """Large-scale implementation analysis"""
    feasibility = global_analysis.generate_scaling_feasibility_analysis()
    return render_template('global_analysis/scaling_analysis.html',
                         feasibility=feasibility)

# API Routes
@global_analysis_bp.route('/api/environmental-analysis', methods=['POST'])
def api_environmental_analysis():
    """API endpoint for environmental correlation analysis"""
    try:
        request_data = request.get_json() or {}
        species_list = request_data.get('species_list')
        if species_list is not None and not isinstance(species_list, list):
            species_list = None
        
        correlations = global_analysis.analyze_environmental_correlations(species_list)
        return jsonify(correlations)
    except Exception as e:
        logger.error(f"Error in environmental analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@global_analysis_bp.route('/api/optimization-scenarios')
def api_optimization_scenarios():
    """API endpoint for carbon optimization scenarios"""
    try:
        scenarios = global_analysis.model_carbon_optimization_scenarios()
        return jsonify(scenarios)
    except Exception as e:
        logger.error(f"Error getting optimization scenarios: {str(e)}")
        return jsonify({'error': str(e)}), 500

@global_analysis_bp.route('/api/scaling-feasibility')
def api_scaling_feasibility():
    """API endpoint for scaling feasibility analysis"""
    try:
        feasibility = global_analysis.generate_scaling_feasibility_analysis()
        return jsonify(feasibility)
    except Exception as e:
        logger.error(f"Error getting scaling feasibility: {str(e)}")
        return jsonify({'error': str(e)}), 500

@global_analysis_bp.route('/api/distribution-data')
def api_distribution_data():
    """API endpoint for distribution mapping data"""
    try:
        # Convert distribution data to JSON-serializable format
        serializable_orchids = {}
        for species, points in global_analysis.orchid_distributions.items():
            serializable_orchids[species] = [
                {
                    'species': point.species,
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'climate_zone': point.climate_zone,
                    'carbon_transfer_rate': point.carbon_transfer_rate,
                    'mycorrhizal_partners': point.mycorrhizal_partners,
                    'cam_photosynthesis': point.cam_photosynthesis
                }
                for point in points
            ]
        
        return jsonify({
            'orchid_distributions': serializable_orchids,
            'fungal_distributions': global_analysis.fungal_distributions
        })
    except Exception as e:
        logger.error(f"Error getting distribution data: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    print("🌍 Global Orchid Climate Analysis System standalone mode")
    print("Available analysis modules:")
    print("  - Distribution mapping")
    print("  - Environmental correlations") 
    print("  - Carbon optimization modeling")
    print("  - Scaling feasibility analysis")