#!/usr/bin/env python3
"""
Comprehensive Pollinator Ecosystem Database Models
==================================================
Advanced ecological relationship models for orchid-pollinator-mycorrhizal networks
"""

from app import db
from datetime import datetime, timedelta
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON, Enum, Index
from sqlalchemy.orm import relationship
import enum

# Enums for standardized vocabularies
class PollinatorTypeEnum(enum.Enum):
    BEE = "bee"
    BUTTERFLY = "butterfly"
    MOTH = "moth"
    BEETLE = "beetle"
    FLY = "fly"
    WASP = "wasp"
    BIRD = "bird"
    BAT = "bat"
    BEETLE_WEEVIL = "beetle_weevil"
    ANT = "ant"
    THRIPS = "thrips"
    OTHER = "other"

class RelationshipTypeEnum(enum.Enum):
    MUTUALISTIC = "mutualistic"
    DECEPTIVE = "deceptive"
    OCCASIONAL = "occasional"
    PRIMARY = "primary"
    SPECIALIST = "specialist"
    GENERALIST = "generalist"
    PREDATORY = "predatory"
    COMPETITIVE = "competitive"

class LifecycleStageEnum(enum.Enum):
    EGG = "egg"
    LARVA = "larva"
    PUPA = "pupa"
    ADULT = "adult"
    JUVENILE = "juvenile"
    NYMPH = "nymph"

class MigrationTypeEnum(enum.Enum):
    SEASONAL = "seasonal"
    ALTITUDINAL = "altitudinal"
    LOCAL = "local"
    LONG_DISTANCE = "long_distance"
    NOMADIC = "nomadic"
    NONE = "none"

# Enhanced Pollinator Model
class Pollinator(db.Model):
    """
    Comprehensive pollinator species database with ecological data
    """
    __tablename__ = 'pollinators'
    
    id = db.Column(Integer, primary_key=True)
    
    # Taxonomic Information
    scientific_name = db.Column(String(200), nullable=False, index=True)
    common_name = db.Column(String(200), nullable=True)
    family = db.Column(String(100), nullable=False, index=True)
    genus = db.Column(String(100), nullable=False, index=True)
    species = db.Column(String(100), nullable=False)
    subspecies = db.Column(String(100), nullable=True)
    author = db.Column(String(200), nullable=True)
    year_described = db.Column(Integer, nullable=True)
    
    # Classification and Type
    pollinator_type = db.Column(Enum(PollinatorTypeEnum), nullable=False, index=True)
    taxonomic_order = db.Column(String(100), nullable=True)
    taxonomic_class = db.Column(String(100), nullable=True)
    
    # Physical Characteristics
    body_length_mm = db.Column(Float, nullable=True)
    wingspan_mm = db.Column(Float, nullable=True)
    body_mass_mg = db.Column(Float, nullable=True)
    tongue_length_mm = db.Column(Float, nullable=True)
    color_pattern = db.Column(Text, nullable=True)
    
    # Foraging and Behavior
    foraging_behavior = db.Column(String(100), nullable=True)
    social_structure = db.Column(String(50), nullable=True)  # solitary, social, eusocial
    activity_pattern = db.Column(String(50), nullable=True)  # diurnal, nocturnal, crepuscular
    nesting_behavior = db.Column(Text, nullable=True)
    foraging_range_km = db.Column(Float, nullable=True)
    flower_specialization = db.Column(String(100), nullable=True)
    
    # Geographic and Habitat Data
    native_range = db.Column(Text, nullable=True)
    introduced_range = db.Column(Text, nullable=True)
    altitude_min_m = db.Column(Integer, nullable=True)
    altitude_max_m = db.Column(Integer, nullable=True)
    habitat_types = db.Column(JSON, nullable=True)  # List of habitat types
    climate_preferences = db.Column(JSON, nullable=True)  # Temperature, humidity ranges
    
    # Phenology and Timing
    flight_period_start = db.Column(Integer, nullable=True)  # Day of year
    flight_period_end = db.Column(Integer, nullable=True)
    generations_per_year = db.Column(Integer, nullable=True)
    overwintering_stage = db.Column(String(50), nullable=True)
    
    # Conservation Status
    iucn_status = db.Column(String(20), nullable=True)
    population_trend = db.Column(String(20), nullable=True)  # increasing, stable, declining
    threat_level = db.Column(String(20), nullable=True)
    conservation_notes = db.Column(Text, nullable=True)
    
    # External Database Links
    gbif_key = db.Column(String(50), nullable=True, index=True)
    eol_page_id = db.Column(String(50), nullable=True)
    bold_systems_id = db.Column(String(50), nullable=True)
    
    # Data Source and Quality
    data_source = db.Column(String(100), nullable=True)
    source_url = db.Column(String(500), nullable=True)
    data_quality_score = db.Column(Float, default=0.5)
    verification_status = db.Column(String(20), default='unverified')
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lifecycle_stages = relationship('PollinatorLifecycle', back_populates='pollinator', cascade='all, delete-orphan')
    migration_patterns = relationship('MigrationPattern', back_populates='pollinator', cascade='all, delete-orphan')
    orchid_relationships = relationship('OrchidPollinatorRelationship', back_populates='pollinator')
    predator_relationships = relationship('PreyPredatorRelationship', foreign_keys='PreyPredatorRelationship.prey_id', back_populates='prey')
    prey_relationships = relationship('PreyPredatorRelationship', foreign_keys='PreyPredatorRelationship.predator_id', back_populates='predator')
    
    def to_dict(self):
        return {
            'id': self.id,
            'scientific_name': self.scientific_name,
            'common_name': self.common_name,
            'family': self.family,
            'genus': self.genus,
            'species': self.species,
            'pollinator_type': self.pollinator_type.value if self.pollinator_type else None,
            'body_length_mm': self.body_length_mm,
            'foraging_behavior': self.foraging_behavior,
            'native_range': self.native_range,
            'conservation_status': self.iucn_status,
            'flight_period': f"{self.flight_period_start}-{self.flight_period_end}" if self.flight_period_start else None
        }

class PollinatorLifecycle(db.Model):
    """
    Detailed lifecycle stages and timing for pollinators
    """
    __tablename__ = 'pollinator_lifecycles'
    
    id = db.Column(Integer, primary_key=True)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Lifecycle Stage Information
    stage = db.Column(Enum(LifecycleStageEnum), nullable=False)
    duration_days = db.Column(Integer, nullable=True)
    temperature_requirements = db.Column(JSON, nullable=True)  # {min: X, max: Y, optimal: Z}
    humidity_requirements = db.Column(JSON, nullable=True)
    host_plant_requirements = db.Column(Text, nullable=True)
    
    # Timing and Seasonality
    start_day_of_year = db.Column(Integer, nullable=True)
    end_day_of_year = db.Column(Integer, nullable=True)
    peak_activity_day = db.Column(Integer, nullable=True)
    
    # Environmental Triggers
    photoperiod_trigger = db.Column(Float, nullable=True)  # Hours of daylight
    temperature_trigger = db.Column(Float, nullable=True)  # Celsius
    diapause_stage = db.Column(Boolean, default=False)
    
    # Habitat Requirements
    microhabitat = db.Column(Text, nullable=True)
    substrate_requirements = db.Column(Text, nullable=True)
    shelter_requirements = db.Column(Text, nullable=True)
    
    # Mortality and Survival
    survival_rate = db.Column(Float, nullable=True)  # 0.0 to 1.0
    mortality_causes = db.Column(JSON, nullable=True)  # List of mortality factors
    
    # Research Data
    study_references = db.Column(JSON, nullable=True)
    observation_notes = db.Column(Text, nullable=True)
    data_confidence = db.Column(String(20), default='medium')
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pollinator = relationship('Pollinator', back_populates='lifecycle_stages')

class MigrationPattern(db.Model):
    """
    Migration routes, timing, and triggers for mobile pollinators
    """
    __tablename__ = 'migration_patterns'
    
    id = db.Column(Integer, primary_key=True)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Migration Classification
    migration_type = db.Column(Enum(MigrationTypeEnum), nullable=False)
    pattern_name = db.Column(String(200), nullable=True)
    
    # Geographic Information
    origin_latitude = db.Column(Float, nullable=True)
    origin_longitude = db.Column(Float, nullable=True)
    destination_latitude = db.Column(Float, nullable=True)
    destination_longitude = db.Column(Float, nullable=True)
    waypoint_coordinates = db.Column(JSON, nullable=True)  # List of lat/lng pairs
    total_distance_km = db.Column(Float, nullable=True)
    
    # Timing and Duration
    departure_day_of_year = db.Column(Integer, nullable=True)
    arrival_day_of_year = db.Column(Integer, nullable=True)
    migration_duration_days = db.Column(Integer, nullable=True)
    return_migration = db.Column(Boolean, default=False)
    
    # Triggers and Conditions
    temperature_trigger = db.Column(Float, nullable=True)
    photoperiod_trigger = db.Column(Float, nullable=True)
    weather_conditions = db.Column(JSON, nullable=True)
    resource_availability_trigger = db.Column(Text, nullable=True)
    
    # Population Data
    percentage_population_migrating = db.Column(Float, nullable=True)
    survival_rate_migration = db.Column(Float, nullable=True)
    breeding_migration = db.Column(Boolean, default=False)
    
    # Corridor Information
    habitat_corridor_requirements = db.Column(Text, nullable=True)
    stopover_sites = db.Column(JSON, nullable=True)  # Key stopover locations
    threats_along_route = db.Column(JSON, nullable=True)
    
    # Research and Tracking
    tracking_method = db.Column(String(100), nullable=True)  # radar, tagging, citizen science
    study_years = db.Column(JSON, nullable=True)  # Years of study data
    data_source = db.Column(String(200), nullable=True)
    reliability_score = db.Column(Float, default=0.5)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pollinator = relationship('Pollinator', back_populates='migration_patterns')

class OrchidPollinatorRelationship(db.Model):
    """
    Enhanced orchid-pollinator relationships with detailed ecological data
    """
    __tablename__ = 'orchid_pollinator_relationships'
    
    id = db.Column(Integer, primary_key=True)
    
    # Core Relationship
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Relationship Characteristics
    relationship_type = db.Column(Enum(RelationshipTypeEnum), nullable=False)
    pollination_effectiveness = db.Column(Float, nullable=True)  # 0.0 to 1.0
    specificity_level = db.Column(String(50), nullable=True)  # specialist, generalist
    interaction_frequency = db.Column(String(50), nullable=True)
    
    # Temporal Patterns
    seasonal_timing = db.Column(JSON, nullable=True)  # {start_day: X, end_day: Y, peak_day: Z}
    time_of_day_pattern = db.Column(JSON, nullable=True)  # Hourly activity pattern
    weather_dependency = db.Column(JSON, nullable=True)  # Weather conditions required
    
    # Pollination Mechanics
    pollinia_attachment_rate = db.Column(Float, nullable=True)
    pollen_transfer_efficiency = db.Column(Float, nullable=True)
    visit_duration_seconds = db.Column(Integer, nullable=True)
    visits_per_flower = db.Column(Float, nullable=True)
    
    # Floral Rewards and Attraction
    nectar_reward = db.Column(Boolean, default=False)
    pollen_reward = db.Column(Boolean, default=False)
    fragrance_attraction = db.Column(Boolean, default=False)
    visual_attraction = db.Column(Boolean, default=False)
    deceptive_mechanism = db.Column(Text, nullable=True)
    
    # Geographic and Habitat Overlap
    geographic_overlap_percentage = db.Column(Float, nullable=True)
    habitat_overlap_score = db.Column(Float, nullable=True)
    altitude_overlap_range = db.Column(JSON, nullable=True)  # {min: X, max: Y}
    
    # Research Evidence
    evidence_type = db.Column(String(50), nullable=True)  # observed, experimental, literature
    observation_method = db.Column(String(100), nullable=True)
    study_location = db.Column(String(200), nullable=True)
    observation_date = db.Column(DateTime, nullable=True)
    researcher_name = db.Column(String(200), nullable=True)
    reference_citation = db.Column(Text, nullable=True)
    confidence_level = db.Column(String(20), nullable=True)
    
    # Ecosystem Context
    mycorrhizal_connection = db.Column(Text, nullable=True)  # Connection to fungal networks
    plant_community_context = db.Column(Text, nullable=True)
    competition_notes = db.Column(Text, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pollinator = relationship('Pollinator', back_populates='orchid_relationships')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_orchid_pollinator', 'orchid_id', 'pollinator_id'),
        Index('idx_relationship_type', 'relationship_type'),
        Index('idx_effectiveness', 'pollination_effectiveness'),
    )

class PreyPredatorRelationship(db.Model):
    """
    Predator-prey relationships affecting pollinator populations
    """
    __tablename__ = 'prey_predator_relationships'
    
    id = db.Column(Integer, primary_key=True)
    
    # Core Relationship
    predator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    prey_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Relationship Strength
    relationship_strength = db.Column(Float, nullable=True)  # 0.0 to 1.0
    predation_rate = db.Column(Float, nullable=True)  # prey consumed per predator per time
    prey_preference = db.Column(String(50), nullable=True)  # preferred, occasional, rare
    
    # Temporal Patterns
    seasonal_variation = db.Column(JSON, nullable=True)  # Monthly predation rates
    life_stage_specificity = db.Column(JSON, nullable=True)  # Which stages are targeted
    
    # Hunting and Feeding Behavior
    hunting_method = db.Column(String(100), nullable=True)
    attack_success_rate = db.Column(Float, nullable=True)
    feeding_behavior = db.Column(Text, nullable=True)
    
    # Environmental Context
    habitat_specificity = db.Column(Text, nullable=True)
    microhabitat_overlap = db.Column(Float, nullable=True)
    environmental_triggers = db.Column(JSON, nullable=True)
    
    # Population Impact
    population_impact_level = db.Column(String(50), nullable=True)  # low, medium, high
    ecosystem_role = db.Column(Text, nullable=True)
    
    # Research Data
    study_location = db.Column(String(200), nullable=True)
    observation_method = db.Column(String(100), nullable=True)
    data_source = db.Column(String(200), nullable=True)
    reliability_score = db.Column(Float, default=0.5)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    predator = relationship('Pollinator', foreign_keys=[predator_id], back_populates='prey_relationships')
    prey = relationship('Pollinator', foreign_keys=[prey_id], back_populates='predator_relationships')

class EcosystemNetwork(db.Model):
    """
    Network connections between orchids, pollinators, and mycorrhizal fungi
    """
    __tablename__ = 'ecosystem_networks'
    
    id = db.Column(Integer, primary_key=True)
    
    # Network Identification
    network_name = db.Column(String(200), nullable=False)
    network_type = db.Column(String(50), nullable=False)  # pollination, mycorrhizal, tri-partite
    
    # Geographic Scope
    location_name = db.Column(String(200), nullable=True)
    latitude = db.Column(Float, nullable=True)
    longitude = db.Column(Float, nullable=True)
    area_km2 = db.Column(Float, nullable=True)
    habitat_type = db.Column(String(100), nullable=True)
    
    # Network Components (JSON arrays of IDs)
    orchid_species = db.Column(JSON, nullable=True)  # List of orchid_record IDs
    pollinator_species = db.Column(JSON, nullable=True)  # List of pollinator IDs
    mycorrhizal_fungi = db.Column(JSON, nullable=True)  # List of fungal species names
    
    # Network Metrics
    species_richness = db.Column(Integer, nullable=True)
    interaction_count = db.Column(Integer, nullable=True)
    network_density = db.Column(Float, nullable=True)
    modularity_score = db.Column(Float, nullable=True)
    nestedness_score = db.Column(Float, nullable=True)
    
    # Temporal Dynamics
    seasonal_stability = db.Column(Float, nullable=True)
    annual_variation = db.Column(Float, nullable=True)
    phenological_mismatch_risk = db.Column(Float, nullable=True)
    
    # Conservation Status
    threat_level = db.Column(String(20), nullable=True)
    conservation_priority = db.Column(String(20), nullable=True)
    keystone_species = db.Column(JSON, nullable=True)  # Critical species for network stability
    
    # Research Context
    study_duration_years = db.Column(Integer, nullable=True)
    sampling_method = db.Column(String(200), nullable=True)
    research_institution = db.Column(String(200), nullable=True)
    principal_investigator = db.Column(String(200), nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HabitatOverlap(db.Model):
    """
    Spatial and temporal habitat overlap between species
    """
    __tablename__ = 'habitat_overlaps'
    
    id = db.Column(Integer, primary_key=True)
    
    # Species Involved
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=True)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=True)
    
    # Spatial Overlap
    geographic_overlap_percentage = db.Column(Float, nullable=True)
    habitat_similarity_score = db.Column(Float, nullable=True)
    microhabitat_overlap = db.Column(Float, nullable=True)
    
    # Elevation and Climate
    elevation_overlap_range = db.Column(JSON, nullable=True)  # {min: X, max: Y}
    temperature_overlap = db.Column(JSON, nullable=True)
    precipitation_overlap = db.Column(JSON, nullable=True)
    humidity_overlap = db.Column(JSON, nullable=True)
    
    # Temporal Overlap
    phenological_overlap_days = db.Column(Integer, nullable=True)
    peak_activity_synchrony = db.Column(Float, nullable=True)  # 0.0 to 1.0
    seasonal_mismatch_risk = db.Column(Float, nullable=True)
    
    # Quality Metrics
    habitat_quality_score = db.Column(Float, nullable=True)
    fragmentation_impact = db.Column(Float, nullable=True)
    connectivity_index = db.Column(Float, nullable=True)
    
    # Analysis Method
    analysis_method = db.Column(String(100), nullable=True)  # GIS, field_survey, remote_sensing
    resolution_scale = db.Column(String(50), nullable=True)  # fine, medium, coarse
    data_sources = db.Column(JSON, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SeasonalInteraction(db.Model):
    """
    Detailed seasonal timing and interaction patterns
    """
    __tablename__ = 'seasonal_interactions'
    
    id = db.Column(Integer, primary_key=True)
    
    # Core Relationship
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Temporal Specificity
    interaction_month = db.Column(Integer, nullable=False)  # 1-12
    interaction_week = db.Column(Integer, nullable=True)  # 1-52
    peak_interaction_day = db.Column(Integer, nullable=True)  # Day of year
    
    # Activity Patterns
    morning_activity = db.Column(Float, nullable=True)  # 0.0 to 1.0
    midday_activity = db.Column(Float, nullable=True)
    afternoon_activity = db.Column(Float, nullable=True)
    evening_activity = db.Column(Float, nullable=True)
    
    # Weather Dependencies
    temperature_optimum = db.Column(Float, nullable=True)
    temperature_range = db.Column(JSON, nullable=True)  # {min: X, max: Y}
    humidity_preference = db.Column(JSON, nullable=True)
    wind_tolerance = db.Column(Float, nullable=True)
    rain_impact = db.Column(String(50), nullable=True)  # stops, reduces, no_effect
    
    # Interaction Quality
    pollination_success_rate = db.Column(Float, nullable=True)
    resource_availability = db.Column(Float, nullable=True)
    competition_level = db.Column(Float, nullable=True)
    
    # Phenological Context
    orchid_flowering_stage = db.Column(String(50), nullable=True)
    pollinator_activity_stage = db.Column(String(50), nullable=True)
    synchrony_score = db.Column(Float, nullable=True)
    
    # Observation Data
    observation_count = db.Column(Integer, nullable=True)
    study_years = db.Column(JSON, nullable=True)
    location_specificity = db.Column(String(200), nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_seasonal_timing', 'interaction_month', 'peak_interaction_day'),
        Index('idx_orchid_seasonal', 'orchid_id', 'interaction_month'),
        Index('idx_pollinator_seasonal', 'pollinator_id', 'interaction_month'),
    )

# Database initialization and migration helper functions
def create_pollinator_tables():
    """
    Create all pollinator-related tables
    """
    db.create_all()
    print("✅ All pollinator ecosystem tables created successfully")

def get_pollinator_schema_info():
    """
    Return information about the pollinator database schema
    """
    schema_info = {
        'tables': [
            'pollinators',
            'pollinator_lifecycles', 
            'migration_patterns',
            'orchid_pollinator_relationships',
            'prey_predator_relationships',
            'ecosystem_networks',
            'habitat_overlaps',
            'seasonal_interactions'
        ],
        'relationships': {
            'pollinators': ['lifecycle_stages', 'migration_patterns', 'orchid_relationships'],
            'orchid_pollinator_relationships': ['pollinator', 'seasonal_interactions'],
            'ecosystem_networks': ['network-wide connections']
        },
        'enums': ['PollinatorTypeEnum', 'RelationshipTypeEnum', 'LifecycleStageEnum', 'MigrationTypeEnum']
    }
    return schema_info

if __name__ == "__main__":
    print("🐝 Comprehensive Pollinator Ecosystem Database Models")
    print("=" * 60)
    print("Models included:")
    print("• Pollinator - Complete species data with ecology")
    print("• PollinatorLifecycle - Detailed lifecycle stages")
    print("• MigrationPattern - Movement and migration data")
    print("• OrchidPollinatorRelationship - Enhanced relationships")
    print("• PreyPredatorRelationship - Ecological food webs")
    print("• EcosystemNetwork - Network-level analysis")
    print("• HabitatOverlap - Spatial and temporal overlaps")
    print("• SeasonalInteraction - Detailed phenological data")
    print("\n🔗 Ready for integration with existing orchid and mycorrhizal data!")