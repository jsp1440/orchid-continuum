#!/usr/bin/env python3
"""
Breeding Compatibility Predictor
===============================
AI-powered orchid breeding compatibility analysis and success rate prediction
Using comprehensive orchid database, genetic lineage, and botanical characteristics

Features:
- Genetic compatibility analysis between orchid pairs
- Breeding success rate prediction using AI models
- Hybrid vigor assessment and trait inheritance prediction
- Breeding difficulty scoring and timeline estimation
- Parent selection optimization for desired traits
- Historical breeding data analysis and pattern recognition
- Chromosome compatibility and fertility prediction
- Seasonal breeding recommendations and care protocols
"""

import os
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import re

# Flask and database imports
from app import app, db
from models import OrchidRecord, OrchidTaxonomy

# AI integration for advanced breeding analysis
try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

# Configure logging
logger = logging.getLogger(__name__)

class CompatibilityLevel(Enum):
    """Breeding compatibility levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    INCOMPATIBLE = "incompatible"

class BreedingDifficulty(Enum):
    """Breeding difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT_ONLY = "expert_only"
    RESEARCH_GRADE = "research_grade"

class HybridVigor(Enum):
    """Hybrid vigor assessment"""
    EXCEPTIONAL = "exceptional"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"

@dataclass
class GeneticProfile:
    """Genetic characteristics of an orchid"""
    genus: str
    species: str
    chromosome_count: Optional[int] = None
    ploidy_level: str = "diploid"  # diploid, triploid, tetraploid, etc.
    fertility_status: str = "fertile"  # fertile, semi_fertile, sterile
    breeding_group: str = "standard"  # standard, miniature, species, complex
    growth_habit: str = "sympodial"  # sympodial, monopodial
    blooming_season: List[str] = None
    temperature_preference: str = "intermediate"  # cool, intermediate, warm
    known_hybrids: List[str] = None
    breeding_barriers: List[str] = None
    
    def __post_init__(self):
        if self.blooming_season is None:
            self.blooming_season = []
        if self.known_hybrids is None:
            self.known_hybrids = []
        if self.breeding_barriers is None:
            self.breeding_barriers = []

@dataclass
class BreedingPrediction:
    """Breeding compatibility prediction results"""
    parent1: OrchidRecord
    parent2: OrchidRecord
    compatibility_score: float  # 0-100
    success_probability: float  # 0-100
    compatibility_level: CompatibilityLevel
    breeding_difficulty: BreedingDifficulty
    hybrid_vigor: HybridVigor
    estimated_timeline: Dict[str, int]  # germination_days, flowering_years
    predicted_traits: Dict[str, Any]
    potential_challenges: List[str]
    breeding_advantages: List[str]
    care_requirements: Dict[str, str]
    fertility_prediction: str
    ai_analysis: Optional[str] = None

class BreedingCompatibilityPredictor:
    """
    Main class for predicting orchid breeding compatibility and success rates
    """
    
    def __init__(self):
        # Initialize AI client for advanced breeding analysis
        self.openai_client = None
        if openai_available:
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                try:
                    self.openai_client = OpenAI(api_key=openai_key)
                    logger.info("✅ OpenAI client initialized for breeding analysis")
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI client initialization failed: {e}")
        
        # Load genetic compatibility matrices
        self.compatibility_matrices = self._load_compatibility_data()
        
        # Breeding difficulty factors
        self.difficulty_factors = {
            'intergeneric': {'multiplier': 2.5, 'base_difficulty': 4},
            'interspecific': {'multiplier': 1.5, 'base_difficulty': 2},
            'intraspecific': {'multiplier': 1.0, 'base_difficulty': 1},
            'complex_hybrid': {'multiplier': 2.0, 'base_difficulty': 3},
            'species_cross': {'multiplier': 1.3, 'base_difficulty': 2},
            'chromosome_mismatch': {'penalty': 30, 'difficulty_increase': 2},
            'ploidy_mismatch': {'penalty': 25, 'difficulty_increase': 1},
            'temperature_mismatch': {'penalty': 15, 'difficulty_increase': 0},
            'growth_habit_mismatch': {'penalty': 10, 'difficulty_increase': 0}
        }
        
        # Known successful breeding combinations
        self.successful_crosses = self._load_breeding_history()
        
        logger.info("🧬 Breeding Compatibility Predictor initialized")
    
    def predict_breeding_compatibility(self, parent1_id: int, parent2_id: int, 
                                     include_ai_analysis: bool = True) -> Optional[BreedingPrediction]:
        """
        Predict breeding compatibility between two orchids
        
        Args:
            parent1_id: ID of first parent orchid
            parent2_id: ID of second parent orchid
            include_ai_analysis: Whether to include AI-powered analysis
            
        Returns:
            Comprehensive breeding prediction analysis
        """
        try:
            with app.app_context():
                # Get orchid records
                parent1 = OrchidRecord.query.get(parent1_id)
                parent2 = OrchidRecord.query.get(parent2_id)
                
                if not parent1 or not parent2:
                    logger.error(f"Orchid not found: {parent1_id} or {parent2_id}")
                    return None
                
                logger.info(f"🧬 Analyzing breeding compatibility: {parent1.display_name} × {parent2.display_name}")
                
                # Create genetic profiles
                profile1 = self._create_genetic_profile(parent1)
                profile2 = self._create_genetic_profile(parent2)
                
                # Calculate compatibility metrics
                compatibility_score = self._calculate_compatibility_score(profile1, profile2)
                success_probability = self._calculate_success_probability(profile1, profile2, compatibility_score)
                compatibility_level = self._determine_compatibility_level(compatibility_score)
                breeding_difficulty = self._assess_breeding_difficulty(profile1, profile2)
                hybrid_vigor = self._predict_hybrid_vigor(profile1, profile2)
                
                # Generate predictions
                estimated_timeline = self._estimate_breeding_timeline(profile1, profile2, breeding_difficulty)
                predicted_traits = self._predict_offspring_traits(profile1, profile2)
                challenges = self._identify_breeding_challenges(profile1, profile2)
                advantages = self._identify_breeding_advantages(profile1, profile2)
                care_requirements = self._generate_care_requirements(profile1, profile2)
                fertility_prediction = self._predict_fertility(profile1, profile2)
                
                # AI-powered analysis (if available and requested)
                ai_analysis = None
                if include_ai_analysis and self.openai_client:
                    ai_analysis = self._generate_ai_breeding_analysis(parent1, parent2, compatibility_score)
                
                prediction = BreedingPrediction(
                    parent1=parent1,
                    parent2=parent2,
                    compatibility_score=round(compatibility_score, 1),
                    success_probability=round(success_probability, 1),
                    compatibility_level=compatibility_level,
                    breeding_difficulty=breeding_difficulty,
                    hybrid_vigor=hybrid_vigor,
                    estimated_timeline=estimated_timeline,
                    predicted_traits=predicted_traits,
                    potential_challenges=challenges,
                    breeding_advantages=advantages,
                    care_requirements=care_requirements,
                    fertility_prediction=fertility_prediction,
                    ai_analysis=ai_analysis
                )
                
                logger.info(f"✅ Breeding analysis complete: {compatibility_score}% compatibility")
                return prediction
                
        except Exception as e:
            logger.error(f"❌ Error predicting breeding compatibility: {e}")
            return None
    
    def find_optimal_breeding_partners(self, orchid_id: int, desired_traits: List[str] = None, 
                                     max_suggestions: int = 10) -> List[BreedingPrediction]:
        """
        Find the best breeding partners for a specific orchid
        
        Args:
            orchid_id: Target orchid ID
            desired_traits: List of desired traits in offspring
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of breeding predictions ranked by compatibility
        """
        try:
            with app.app_context():
                target_orchid = OrchidRecord.query.get(orchid_id)
                if not target_orchid:
                    return []
                
                logger.info(f"🔍 Finding breeding partners for: {target_orchid.display_name}")
                
                # Get potential breeding partners
                candidates = self._get_breeding_candidates(target_orchid, desired_traits)
                predictions = []
                
                for candidate in candidates[:50]:  # Limit to prevent timeout
                    if candidate.id != orchid_id:  # Don't breed with itself
                        prediction = self.predict_breeding_compatibility(
                            orchid_id, candidate.id, include_ai_analysis=False
                        )
                        if prediction and prediction.compatibility_score >= 30:  # Minimum threshold
                            predictions.append(prediction)
                
                # Sort by compatibility score and success probability
                predictions.sort(
                    key=lambda p: (p.compatibility_score * 0.6 + p.success_probability * 0.4),
                    reverse=True
                )
                
                return predictions[:max_suggestions]
                
        except Exception as e:
            logger.error(f"Error finding breeding partners: {e}")
            return []
    
    def analyze_breeding_program(self, orchid_ids: List[int]) -> Dict[str, Any]:
        """
        Analyze a breeding program with multiple orchids
        
        Args:
            orchid_ids: List of orchid IDs in the breeding program
            
        Returns:
            Comprehensive breeding program analysis
        """
        try:
            with app.app_context():
                orchids = [OrchidRecord.query.get(oid) for oid in orchid_ids]
                orchids = [o for o in orchids if o is not None]
                
                if len(orchids) < 2:
                    return {"error": "At least 2 orchids required for breeding program analysis"}
                
                logger.info(f"📊 Analyzing breeding program with {len(orchids)} orchids")
                
                # Analyze all possible breeding combinations
                combinations = []
                for i in range(len(orchids)):
                    for j in range(i + 1, len(orchids)):
                        prediction = self.predict_breeding_compatibility(
                            orchids[i].id, orchids[j].id, include_ai_analysis=False
                        )
                        if prediction:
                            combinations.append(prediction)
                
                # Generate program insights
                analysis = {
                    "program_overview": {
                        "total_orchids": len(orchids),
                        "possible_crosses": len(combinations),
                        "avg_compatibility": sum(c.compatibility_score for c in combinations) / len(combinations) if combinations else 0,
                        "high_potential_crosses": len([c for c in combinations if c.compatibility_score >= 70])
                    },
                    "top_combinations": sorted(combinations, key=lambda c: c.compatibility_score, reverse=True)[:10],
                    "genetic_diversity": self._analyze_genetic_diversity(orchids),
                    "breeding_timeline": self._create_program_timeline(combinations),
                    "resource_requirements": self._estimate_program_resources(combinations),
                    "recommendations": self._generate_program_recommendations(orchids, combinations)
                }
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error analyzing breeding program: {e}")
            return {"error": str(e)}
    
    def _create_genetic_profile(self, orchid: OrchidRecord) -> GeneticProfile:
        """Create genetic profile from orchid record"""
        try:
            # Extract genetic information from available data
            genus = orchid.genus
            species = orchid.species or "hybrid"
            
            # Determine characteristics based on genus and available information
            profile_data = {
                'genus': genus,
                'species': species,
                'chromosome_count': self._estimate_chromosome_count(genus),
                'ploidy_level': self._determine_ploidy(orchid),
                'fertility_status': self._assess_fertility_status(orchid),
                'breeding_group': self._determine_breeding_group(orchid),
                'growth_habit': self._determine_growth_habit(genus),
                'blooming_season': self._extract_blooming_season(orchid),
                'temperature_preference': self._determine_temperature_preference(genus),
                'known_hybrids': self._get_known_hybrids(orchid),
                'breeding_barriers': self._identify_breeding_barriers(orchid)
            }
            
            return GeneticProfile(**profile_data)
            
        except Exception as e:
            logger.error(f"Error creating genetic profile: {e}")
            return GeneticProfile(genus=orchid.genus, species=orchid.species or "hybrid")
    
    def _calculate_compatibility_score(self, profile1: GeneticProfile, profile2: GeneticProfile) -> float:
        """Calculate breeding compatibility score between two genetic profiles"""
        try:
            score = 50.0  # Base compatibility score
            
            # Genus compatibility
            if profile1.genus == profile2.genus:
                score += 30  # Same genus - high compatibility
                
                # Species compatibility within genus
                if profile1.species == profile2.species:
                    score += 15  # Same species - very high compatibility
                elif profile1.species != "hybrid" and profile2.species != "hybrid":
                    score += 10  # Both species, different - good compatibility
                else:
                    score += 5   # One or both hybrids - moderate compatibility
            else:
                # Intergeneric crosses - check known compatibility
                intergeneric_bonus = self._get_intergeneric_compatibility(profile1.genus, profile2.genus)
                score += intergeneric_bonus
            
            # Chromosome and ploidy compatibility
            if profile1.chromosome_count and profile2.chromosome_count:
                if profile1.chromosome_count == profile2.chromosome_count:
                    score += 15
                elif abs(profile1.chromosome_count - profile2.chromosome_count) <= 2:
                    score += 5
                else:
                    score -= 10
            
            if profile1.ploidy_level == profile2.ploidy_level:
                score += 10
            else:
                score -= 5
            
            # Fertility compatibility
            if profile1.fertility_status == "fertile" and profile2.fertility_status == "fertile":
                score += 10
            elif "fertile" in [profile1.fertility_status, profile2.fertility_status]:
                score += 5
            else:
                score -= 15
            
            # Growth habit compatibility
            if profile1.growth_habit == profile2.growth_habit:
                score += 5
            
            # Temperature compatibility
            temp_compatibility = self._calculate_temperature_compatibility(
                profile1.temperature_preference, profile2.temperature_preference
            )
            score += temp_compatibility
            
            # Blooming season overlap
            season_overlap = self._calculate_season_overlap(profile1.blooming_season, profile2.blooming_season)
            score += season_overlap
            
            # Historical breeding success bonus
            historical_bonus = self._get_historical_breeding_success(profile1, profile2)
            score += historical_bonus
            
            # Apply breeding barriers penalties
            barrier_penalties = self._calculate_barrier_penalties(profile1.breeding_barriers, profile2.breeding_barriers)
            score -= barrier_penalties
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating compatibility score: {e}")
            return 50.0
    
    def _calculate_success_probability(self, profile1: GeneticProfile, profile2: GeneticProfile, 
                                     compatibility_score: float) -> float:
        """Calculate breeding success probability"""
        try:
            # Base probability from compatibility score
            base_probability = compatibility_score * 0.7
            
            # Adjust for known successful combinations
            if self._has_successful_precedent(profile1, profile2):
                base_probability += 15
            
            # Adjust for fertility status
            if profile1.fertility_status == "sterile" or profile2.fertility_status == "sterile":
                base_probability *= 0.1
            elif profile1.fertility_status == "semi_fertile" or profile2.fertility_status == "semi_fertile":
                base_probability *= 0.7
            
            # Adjust for breeding group compatibility
            if profile1.breeding_group == profile2.breeding_group:
                base_probability += 5
            
            # Genus-specific adjustments
            genus_modifier = self._get_genus_breeding_modifier(profile1.genus, profile2.genus)
            base_probability *= genus_modifier
            
            return max(5, min(95, base_probability))
            
        except Exception as e:
            logger.error(f"Error calculating success probability: {e}")
            return 50.0
    
    def _determine_compatibility_level(self, score: float) -> CompatibilityLevel:
        """Determine compatibility level from score"""
        if score >= 85:
            return CompatibilityLevel.EXCELLENT
        elif score >= 70:
            return CompatibilityLevel.GOOD
        elif score >= 50:
            return CompatibilityLevel.MODERATE
        elif score >= 30:
            return CompatibilityLevel.POOR
        else:
            return CompatibilityLevel.INCOMPATIBLE
    
    def _assess_breeding_difficulty(self, profile1: GeneticProfile, profile2: GeneticProfile) -> BreedingDifficulty:
        """Assess breeding difficulty level"""
        try:
            base_difficulty = 1
            
            # Genus crossing difficulty
            if profile1.genus != profile2.genus:
                base_difficulty += 2  # Intergeneric is harder
            
            # Species vs hybrid complexity
            if "hybrid" in [profile1.species, profile2.species]:
                base_difficulty += 1
            
            # Chromosome mismatch
            if (profile1.chromosome_count and profile2.chromosome_count and 
                abs(profile1.chromosome_count - profile2.chromosome_count) > 2):
                base_difficulty += 2
            
            # Fertility issues
            if "sterile" in [profile1.fertility_status, profile2.fertility_status]:
                base_difficulty += 3
            elif "semi_fertile" in [profile1.fertility_status, profile2.fertility_status]:
                base_difficulty += 1
            
            # Breeding barriers
            barrier_count = len(profile1.breeding_barriers) + len(profile2.breeding_barriers)
            base_difficulty += barrier_count * 0.5
            
            # Map to difficulty enum
            if base_difficulty <= 2:
                return BreedingDifficulty.BEGINNER
            elif base_difficulty <= 4:
                return BreedingDifficulty.INTERMEDIATE
            elif base_difficulty <= 6:
                return BreedingDifficulty.ADVANCED
            elif base_difficulty <= 8:
                return BreedingDifficulty.EXPERT_ONLY
            else:
                return BreedingDifficulty.RESEARCH_GRADE
                
        except Exception as e:
            logger.error(f"Error assessing breeding difficulty: {e}")
            return BreedingDifficulty.INTERMEDIATE
    
    def _predict_hybrid_vigor(self, profile1: GeneticProfile, profile2: GeneticProfile) -> HybridVigor:
        """Predict hybrid vigor in offspring"""
        try:
            # Base vigor assessment
            if profile1.genus != profile2.genus:
                # Intergeneric crosses often show exceptional vigor if successful
                return HybridVigor.EXCEPTIONAL if self._has_successful_precedent(profile1, profile2) else HybridVigor.LOW
            elif profile1.species != profile2.species and "hybrid" not in [profile1.species, profile2.species]:
                # Species crosses typically show high vigor
                return HybridVigor.HIGH
            elif "hybrid" in [profile1.species, profile2.species]:
                # Hybrid crosses show moderate vigor
                return HybridVigor.MODERATE
            else:
                # Intraspecific crosses show low but stable vigor
                return HybridVigor.LOW
                
        except Exception as e:
            logger.error(f"Error predicting hybrid vigor: {e}")
            return HybridVigor.UNKNOWN
    
    def _estimate_breeding_timeline(self, profile1: GeneticProfile, profile2: GeneticProfile, 
                                  difficulty: BreedingDifficulty) -> Dict[str, int]:
        """Estimate breeding timeline milestones"""
        try:
            # Base timelines by difficulty
            timelines = {
                BreedingDifficulty.BEGINNER: {
                    'pollination_window_days': 30,
                    'seed_development_months': 6,
                    'germination_days': 90,
                    'seedling_establishment_months': 12,
                    'first_flowering_years': 3
                },
                BreedingDifficulty.INTERMEDIATE: {
                    'pollination_window_days': 21,
                    'seed_development_months': 8,
                    'germination_days': 120,
                    'seedling_establishment_months': 18,
                    'first_flowering_years': 4
                },
                BreedingDifficulty.ADVANCED: {
                    'pollination_window_days': 14,
                    'seed_development_months': 10,
                    'germination_days': 150,
                    'seedling_establishment_months': 24,
                    'first_flowering_years': 5
                },
                BreedingDifficulty.EXPERT_ONLY: {
                    'pollination_window_days': 10,
                    'seed_development_months': 12,
                    'germination_days': 180,
                    'seedling_establishment_months': 30,
                    'first_flowering_years': 6
                },
                BreedingDifficulty.RESEARCH_GRADE: {
                    'pollination_window_days': 7,
                    'seed_development_months': 15,
                    'germination_days': 240,
                    'seedling_establishment_months': 36,
                    'first_flowering_years': 8
                }
            }
            
            return timelines.get(difficulty, timelines[BreedingDifficulty.INTERMEDIATE])
            
        except Exception as e:
            logger.error(f"Error estimating breeding timeline: {e}")
            return {'first_flowering_years': 4}
    
    def _predict_offspring_traits(self, profile1: GeneticProfile, profile2: GeneticProfile) -> Dict[str, Any]:
        """Predict traits in offspring"""
        try:
            traits = {
                'growth_habit': self._predict_dominant_trait([profile1.growth_habit, profile2.growth_habit]),
                'temperature_preference': self._predict_intermediate_trait(profile1.temperature_preference, profile2.temperature_preference),
                'expected_ploidy': self._predict_offspring_ploidy(profile1.ploidy_level, profile2.ploidy_level),
                'fertility_expectation': self._predict_offspring_fertility(profile1.fertility_status, profile2.fertility_status),
                'blooming_seasons': list(set(profile1.blooming_season + profile2.blooming_season)),
                'size_category': self._predict_size_inheritance(profile1.breeding_group, profile2.breeding_group),
                'vigor_expectation': self._predict_hybrid_vigor(profile1, profile2).value
            }
            
            return traits
            
        except Exception as e:
            logger.error(f"Error predicting offspring traits: {e}")
            return {'growth_habit': 'intermediate'}
    
    def _generate_ai_breeding_analysis(self, parent1: OrchidRecord, parent2: OrchidRecord, 
                                     compatibility_score: float) -> Optional[str]:
        """Generate AI-powered breeding analysis with timeout"""
        try:
            if not self.openai_client:
                return None
            
            parent1_name = parent1.display_name or f"{parent1.genus} {parent1.species or 'hybrid'}"
            parent2_name = parent2.display_name or f"{parent2.genus} {parent2.species or 'hybrid'}"
            
            prompt = f"""As an expert orchid breeder and geneticist, analyze this breeding combination:

Parent 1: {parent1_name} ({parent1.genus} {parent1.species or 'hybrid'})
Parent 2: {parent2_name} ({parent2.genus} {parent2.species or 'hybrid'})

Compatibility Score: {compatibility_score}%

Cultural notes available:
Parent 1: {parent1.cultural_notes[:200] if parent1.cultural_notes else 'No cultural notes available'}
Parent 2: {parent2.cultural_notes[:200] if parent2.cultural_notes else 'No cultural notes available'}

Please provide a concise expert analysis focusing on:
1. Genetic compatibility and breeding viability
2. Expected offspring characteristics and vigor
3. Potential breeding challenges and solutions  
4. Timeline and care requirements for success
5. Expected trait inheritance patterns

Limit response to 3-4 paragraphs maximum."""

            # Add timeout for OpenAI request
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("OpenAI request timed out")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(15)  # 15 second timeout
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
        except TimeoutError:
            logger.warning("AI breeding analysis timed out, skipping")
            return None
        except Exception as e:
            logger.error(f"Error generating AI breeding analysis: {e}")
            return None
    
    # Helper methods for genetic analysis
    def _load_compatibility_data(self) -> Dict[str, Any]:
        """Load genetic compatibility matrices with fallback"""
        try:
            # This would ideally load from a database or external source
            # For now, return basic compatibility data with error handling
            return {
                'intergeneric_compatibility': {
                    ('Cattleya', 'Laelia'): 0.85,
                    ('Cattleya', 'Brassavola'): 0.75,
                    ('Cattleya', 'Sophronitis'): 0.70,
                    ('Phalaenopsis', 'Doritis'): 0.90,
                    ('Dendrobium', 'Epidendrum'): 0.60,
                    ('Oncidium', 'Odontoglossum'): 0.80,
                    ('Oncidium', 'Miltonia'): 0.75,
                    ('Vanda', 'Ascocentrum'): 0.85,
                    ('Vanda', 'Renanthera'): 0.70
                },
                'genus_breeding_modifiers': {
                    'Phalaenopsis': 1.2,
                    'Cattleya': 1.1,
                    'Dendrobium': 1.0,
                    'Oncidium': 1.1,
                    'Cymbidium': 0.9,
                    'Paphiopedilum': 0.8,
                    'Masdevallia': 0.7,
                    'Vanda': 1.0,
                    'Laelia': 1.1
                }
            }
        except Exception as e:
            logger.warning(f"Error loading compatibility data: {e}, using minimal fallback")
            return {
                'intergeneric_compatibility': {},
                'genus_breeding_modifiers': {}
            }
    
    def _load_breeding_history(self) -> Dict[str, Any]:
        """Load historical breeding success data with fallback"""
        try:
            return {
                'successful_crosses': [
                    ('Cattleya', 'Laelia'),
                    ('Cattleya', 'Brassavola'),
                    ('Phalaenopsis', 'Doritis'),
                    ('Vanda', 'Ascocentrum'),
                    ('Oncidium', 'Odontoglossum'),
                    ('Oncidium', 'Miltonia'),
                    ('Dendrobium', 'Epidendrum')
                ]
            }
        except Exception as e:
            logger.warning(f"Error loading breeding history: {e}, using minimal fallback")
            return {
                'successful_crosses': []
            }
    
    def _get_breeding_candidates(self, target_orchid: OrchidRecord, desired_traits: List[str] = None) -> List[OrchidRecord]:
        """Get potential breeding partner candidates"""
        try:
            # Start with orchids from compatible genera
            compatible_genera = self._get_compatible_genera(target_orchid.genus)
            
            query = OrchidRecord.query.filter(
                OrchidRecord.genus.in_(compatible_genera)
            )
            
            # Filter by desired traits if specified
            if desired_traits:
                for trait in desired_traits:
                    if trait.lower() in ['compact', 'miniature', 'small']:
                        query = query.filter(OrchidRecord.cultural_notes.ilike(f'%{trait}%'))
            
            candidates = query.limit(100).all()
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error getting breeding candidates: {e}")
            return []
    
    def _get_compatible_genera(self, genus: str) -> List[str]:
        """Get list of genera compatible for breeding"""
        compatibility_map = {
            'Cattleya': ['Cattleya', 'Laelia', 'Brassavola', 'Sophronitis'],
            'Phalaenopsis': ['Phalaenopsis', 'Doritis'],
            'Dendrobium': ['Dendrobium', 'Epidendrum'],
            'Oncidium': ['Oncidium', 'Odontoglossum', 'Miltonia'],
            'Vanda': ['Vanda', 'Ascocentrum', 'Renanthera'],
            'Cymbidium': ['Cymbidium'],
            'Paphiopedilum': ['Paphiopedilum']
        }
        
        return compatibility_map.get(genus, [genus])
    
    def _estimate_chromosome_count(self, genus: str) -> Optional[int]:
        """Estimate chromosome count based on genus"""
        chromosome_estimates = {
            'Phalaenopsis': 38,
            'Cattleya': 40,
            'Dendrobium': 38,
            'Oncidium': 56,
            'Cymbidium': 40,
            'Paphiopedilum': 28,
            'Vanda': 38,
            'Masdevallia': 60
        }
        return chromosome_estimates.get(genus)
    
    def _determine_ploidy(self, orchid: OrchidRecord) -> str:
        """Determine ploidy level"""
        # Most orchids are diploid unless specified otherwise
        if orchid.cultural_notes and ('triploid' in orchid.cultural_notes.lower() or 'tetraploid' in orchid.cultural_notes.lower()):
            if 'triploid' in orchid.cultural_notes.lower():
                return 'triploid'
            elif 'tetraploid' in orchid.cultural_notes.lower():
                return 'tetraploid'
        return 'diploid'
    
    def _assess_fertility_status(self, orchid: OrchidRecord) -> str:
        """Assess fertility status"""
        if orchid.cultural_notes:
            notes_lower = orchid.cultural_notes.lower()
            if 'sterile' in notes_lower:
                return 'sterile'
            elif 'semi-fertile' in notes_lower or 'semifertile' in notes_lower:
                return 'semi_fertile'
        return 'fertile'
    
    def _determine_breeding_group(self, orchid: OrchidRecord) -> str:
        """Determine breeding group"""
        if orchid.cultural_notes:
            notes_lower = orchid.cultural_notes.lower()
            if any(word in notes_lower for word in ['miniature', 'compact', 'small']):
                return 'miniature'
            elif 'species' in notes_lower:
                return 'species'
            elif 'complex' in notes_lower:
                return 'complex'
        return 'standard'
    
    def _determine_growth_habit(self, genus: str) -> str:
        """Determine growth habit based on genus"""
        monopodial_genera = ['Phalaenopsis', 'Vanda', 'Ascocentrum', 'Renanthera']
        return 'monopodial' if genus in monopodial_genera else 'sympodial'
    
    def _extract_blooming_season(self, orchid: OrchidRecord) -> List[str]:
        """Extract blooming season information"""
        seasons = []
        if orchid.cultural_notes:
            notes_lower = orchid.cultural_notes.lower()
            season_keywords = {
                'spring': ['spring'],
                'summer': ['summer'],
                'fall': ['fall', 'autumn'],
                'winter': ['winter']
            }
            
            for season, keywords in season_keywords.items():
                if any(keyword in notes_lower for keyword in keywords):
                    seasons.append(season)
        
        return seasons if seasons else ['year_round']
    
    def _determine_temperature_preference(self, genus: str) -> str:
        """Determine temperature preference"""
        temperature_preferences = {
            'Masdevallia': 'cool',
            'Cymbidium': 'cool',
            'Odontoglossum': 'cool',
            'Cattleya': 'intermediate',
            'Phalaenopsis': 'warm',
            'Vanda': 'warm',
            'Dendrobium': 'intermediate'
        }
        return temperature_preferences.get(genus, 'intermediate')
    
    def _get_known_hybrids(self, orchid: OrchidRecord) -> List[str]:
        """Get list of known hybrids"""
        # This would query the database for known hybrids
        # For now, return empty list
        return []
    
    def _identify_breeding_barriers(self, orchid: OrchidRecord) -> List[str]:
        """Identify potential breeding barriers"""
        barriers = []
        if orchid.cultural_notes:
            notes_lower = orchid.cultural_notes.lower()
            if 'difficult' in notes_lower:
                barriers.append('difficult_cultivation')
            if 'rare' in notes_lower:
                barriers.append('limited_availability')
            if 'slow' in notes_lower:
                barriers.append('slow_growth')
        return barriers
    
    def _get_intergeneric_compatibility(self, genus1: str, genus2: str) -> float:
        """Get intergeneric breeding compatibility score"""
        compatibility = self.compatibility_matrices.get('intergeneric_compatibility', {})
        key = (genus1, genus2) if (genus1, genus2) in compatibility else (genus2, genus1)
        return compatibility.get(key, 0) * 20  # Convert to score adjustment
    
    def _calculate_temperature_compatibility(self, temp1: str, temp2: str) -> float:
        """Calculate temperature preference compatibility"""
        temp_order = {'cool': 1, 'intermediate': 2, 'warm': 3}
        diff = abs(temp_order.get(temp1, 2) - temp_order.get(temp2, 2))
        
        if diff == 0:
            return 10  # Perfect match
        elif diff == 1:
            return 5   # Close match
        else:
            return -5  # Poor match
    
    def _calculate_season_overlap(self, seasons1: List[str], seasons2: List[str]) -> float:
        """Calculate blooming season overlap"""
        if not seasons1 or not seasons2:
            return 0
        
        overlap = len(set(seasons1) & set(seasons2))
        total_seasons = len(set(seasons1) | set(seasons2))
        
        return (overlap / total_seasons) * 10 if total_seasons > 0 else 0
    
    def _get_historical_breeding_success(self, profile1: GeneticProfile, profile2: GeneticProfile) -> float:
        """Get historical breeding success bonus"""
        successful_crosses = self.successful_crosses.get('successful_crosses', [])
        genus_pair = (profile1.genus, profile2.genus)
        reverse_pair = (profile2.genus, profile1.genus)
        
        if genus_pair in successful_crosses or reverse_pair in successful_crosses:
            return 15
        return 0
    
    def _calculate_barrier_penalties(self, barriers1: List[str], barriers2: List[str]) -> float:
        """Calculate penalties from breeding barriers"""
        all_barriers = barriers1 + barriers2
        barrier_penalties = {
            'difficult_cultivation': 5,
            'limited_availability': 3,
            'slow_growth': 2
        }
        
        total_penalty = 0
        for barrier in all_barriers:
            total_penalty += barrier_penalties.get(barrier, 1)
        
        return total_penalty
    
    def _has_successful_precedent(self, profile1: GeneticProfile, profile2: GeneticProfile) -> bool:
        """Check if similar crosses have been successful"""
        genus_pair = (profile1.genus, profile2.genus)
        reverse_pair = (profile2.genus, profile1.genus)
        successful_crosses = self.successful_crosses.get('successful_crosses', [])
        
        return genus_pair in successful_crosses or reverse_pair in successful_crosses
    
    def _get_genus_breeding_modifier(self, genus1: str, genus2: str) -> float:
        """Get genus-specific breeding success modifier"""
        modifiers = self.compatibility_matrices.get('genus_breeding_modifiers', {})
        avg_modifier = (modifiers.get(genus1, 1.0) + modifiers.get(genus2, 1.0)) / 2
        return avg_modifier
    
    def _predict_dominant_trait(self, traits: List[str]) -> str:
        """Predict dominant trait inheritance"""
        # Simplified dominant trait prediction
        trait_counter = Counter(traits)
        return trait_counter.most_common(1)[0][0] if traits else 'unknown'
    
    def _predict_intermediate_trait(self, trait1: str, trait2: str) -> str:
        """Predict intermediate trait inheritance"""
        temp_order = {'cool': 0, 'intermediate': 1, 'warm': 2}
        if trait1 == trait2:
            return trait1
        
        avg = (temp_order.get(trait1, 1) + temp_order.get(trait2, 1)) / 2
        reverse_order = {0: 'cool', 1: 'intermediate', 2: 'warm'}
        return reverse_order.get(round(avg), 'intermediate')
    
    def _predict_offspring_ploidy(self, ploidy1: str, ploidy2: str) -> str:
        """Predict offspring ploidy"""
        if ploidy1 == ploidy2 == 'diploid':
            return 'diploid'
        elif 'triploid' in [ploidy1, ploidy2]:
            return 'mostly_sterile'
        else:
            return 'variable'
    
    def _predict_offspring_fertility(self, fertility1: str, fertility2: str) -> str:
        """Predict offspring fertility"""
        if fertility1 == fertility2 == 'fertile':
            return 'high_fertility'
        elif 'sterile' in [fertility1, fertility2]:
            return 'reduced_fertility'
        else:
            return 'moderate_fertility'
    
    def _predict_size_inheritance(self, group1: str, group2: str) -> str:
        """Predict size category inheritance"""
        if 'miniature' in [group1, group2]:
            return 'compact_to_standard'
        else:
            return 'standard'
    
    def _identify_breeding_challenges(self, profile1: GeneticProfile, profile2: GeneticProfile) -> List[str]:
        """Identify potential breeding challenges"""
        challenges = []
        
        if profile1.genus != profile2.genus:
            challenges.append("Intergeneric cross - requires advanced techniques and patience")
        
        if profile1.fertility_status != 'fertile' or profile2.fertility_status != 'fertile':
            challenges.append("Fertility issues may reduce success rates and require multiple attempts")
        
        if profile1.chromosome_count and profile2.chromosome_count:
            if abs(profile1.chromosome_count - profile2.chromosome_count) > 2:
                challenges.append("Chromosome mismatch may cause reduced fertility in offspring")
        
        if profile1.temperature_preference != profile2.temperature_preference:
            challenges.append("Different temperature preferences may complicate care during breeding")
        
        barriers = profile1.breeding_barriers + profile2.breeding_barriers
        if barriers:
            challenges.append("Cultural difficulties may impact breeding success")
        
        return challenges[:5]  # Limit to top 5 challenges
    
    def _identify_breeding_advantages(self, profile1: GeneticProfile, profile2: GeneticProfile) -> List[str]:
        """Identify breeding advantages"""
        advantages = []
        
        if profile1.genus == profile2.genus:
            advantages.append("Same genus cross - higher compatibility and success rates")
        
        if profile1.fertility_status == 'fertile' and profile2.fertility_status == 'fertile':
            advantages.append("Both parents fertile - excellent breeding potential")
        
        if self._has_successful_precedent(profile1, profile2):
            advantages.append("Similar crosses have been successful - good precedent")
        
        if profile1.growth_habit == profile2.growth_habit:
            advantages.append("Matching growth habits - predictable offspring characteristics")
        
        # Check for complementary traits
        if (profile1.temperature_preference != profile2.temperature_preference and 
            'intermediate' in [profile1.temperature_preference, profile2.temperature_preference]):
            advantages.append("Temperature preferences may produce adaptable offspring")
        
        return advantages[:4]  # Limit to top 4 advantages
    
    def _generate_care_requirements(self, profile1: GeneticProfile, profile2: GeneticProfile) -> Dict[str, str]:
        """Generate care requirements for breeding"""
        return {
            'temperature': self._predict_intermediate_trait(profile1.temperature_preference, profile2.temperature_preference),
            'pollination_timing': 'Early morning when flowers are fresh and pollen is viable',
            'seed_development': '6-12 months in pod on mother plant',
            'germination_medium': 'Sterile agar medium with appropriate nutrients',
            'seedling_care': 'High humidity, filtered light, sterile conditions for first year',
            'transplant_timing': 'When seedlings have 2-3 leaves and established roots'
        }
    
    def _predict_fertility(self, profile1: GeneticProfile, profile2: GeneticProfile) -> str:
        """Predict fertility of offspring"""
        if profile1.genus != profile2.genus:
            return "Variable - intergeneric hybrids may have reduced fertility"
        elif profile1.species != profile2.species:
            return "Good - species crosses typically maintain fertility"
        else:
            return "Excellent - intraspecific crosses maintain high fertility"
    
    def _analyze_genetic_diversity(self, orchids: List[OrchidRecord]) -> Dict[str, Any]:
        """Analyze genetic diversity in breeding program"""
        genera = [o.genus for o in orchids]
        species = [f"{o.genus} {o.species}" for o in orchids if o.species]
        
        return {
            'genus_diversity': len(set(genera)),
            'species_diversity': len(set(species)),
            'genus_distribution': dict(Counter(genera)),
            'diversity_score': len(set(genera)) / len(orchids) if orchids else 0
        }
    
    def _create_program_timeline(self, combinations: List[BreedingPrediction]) -> Dict[str, Any]:
        """Create breeding program timeline"""
        if not combinations:
            return {}
        
        avg_timeline = combinations[0].estimated_timeline
        return {
            'recommended_start': 'Spring (optimal pollination conditions)',
            'first_results_expected': f"{avg_timeline.get('first_flowering_years', 4)} years",
            'program_duration': f"{avg_timeline.get('first_flowering_years', 4) + 2} years for evaluation",
            'peak_productivity': f"Years {avg_timeline.get('first_flowering_years', 4)}-{avg_timeline.get('first_flowering_years', 4) + 5}"
        }
    
    def _estimate_program_resources(self, combinations: List[BreedingPrediction]) -> Dict[str, str]:
        """Estimate resource requirements"""
        return {
            'space_requirements': 'Medium - dedicated growing area with controlled conditions',
            'equipment_needed': 'Basic pollination tools, sterile germination setup, growing supplies',
            'time_commitment': '2-4 hours weekly for active breeding season',
            'skill_level': 'Intermediate to Advanced depending on crosses selected',
            'estimated_cost': 'Moderate - supplies and equipment investment required'
        }
    
    def _generate_program_recommendations(self, orchids: List[OrchidRecord], 
                                        combinations: List[BreedingPrediction]) -> List[str]:
        """Generate breeding program recommendations"""
        recommendations = []
        
        if len(orchids) < 5:
            recommendations.append("Consider adding more genetic diversity to breeding stock")
        
        high_success = [c for c in combinations if c.success_probability >= 70]
        if high_success:
            recommendations.append(f"Focus on {len(high_success)} high-probability crosses first")
        
        beginner_crosses = [c for c in combinations if c.breeding_difficulty == BreedingDifficulty.BEGINNER]
        if beginner_crosses:
            recommendations.append("Start with beginner-level crosses to gain experience")
        
        recommendations.append("Maintain detailed breeding records for future reference")
        recommendations.append("Plan for 3-5 year timeline to see first flowering results")
        
        return recommendations

def predict_orchid_breeding_compatibility(parent1_id: int, parent2_id: int, 
                                        include_ai_analysis: bool = True) -> Dict[str, Any]:
    """
    Main function to predict breeding compatibility between two orchids
    
    Args:
        parent1_id: ID of first parent orchid
        parent2_id: ID of second parent orchid
        include_ai_analysis: Whether to include AI analysis
        
    Returns:
        Breeding compatibility prediction results
    """
    try:
        predictor = BreedingCompatibilityPredictor()
        prediction = predictor.predict_breeding_compatibility(parent1_id, parent2_id, include_ai_analysis)
        
        if prediction:
            # Convert to JSON-serializable format
            result = {
                'success': True,
                'prediction': {
                    'parent1': {
                        'id': prediction.parent1.id,
                        'name': prediction.parent1.display_name or f"{prediction.parent1.genus} {prediction.parent1.species}",
                        'scientific_name': prediction.parent1.scientific_name or f"{prediction.parent1.genus} {prediction.parent1.species}",
                        'genus': prediction.parent1.genus,
                        'species': prediction.parent1.species or "hybrid",
                        'image_id': prediction.parent1.google_drive_id
                    },
                    'parent2': {
                        'id': prediction.parent2.id,
                        'name': prediction.parent2.display_name or f"{prediction.parent2.genus} {prediction.parent2.species}",
                        'scientific_name': prediction.parent2.scientific_name or f"{prediction.parent2.genus} {prediction.parent2.species}",
                        'genus': prediction.parent2.genus,
                        'species': prediction.parent2.species or "hybrid",
                        'image_id': prediction.parent2.google_drive_id
                    },
                    'compatibility_analysis': {
                        'compatibility_score': float(prediction.compatibility_score),
                        'success_probability': float(prediction.success_probability),
                        'compatibility_level': prediction.compatibility_level.value,
                        'breeding_difficulty': prediction.breeding_difficulty.value,
                        'hybrid_vigor': prediction.hybrid_vigor.value
                    },
                    'predictions': {
                        'estimated_timeline': dict(prediction.estimated_timeline),
                        'predicted_traits': dict(prediction.predicted_traits),
                        'fertility_prediction': prediction.fertility_prediction
                    },
                    'guidance': {
                        'breeding_advantages': list(prediction.breeding_advantages),
                        'potential_challenges': list(prediction.potential_challenges),
                        'care_requirements': dict(prediction.care_requirements)
                    },
                    'ai_analysis': prediction.ai_analysis,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            return result
        else:
            return {
                'success': False,
                'error': 'Unable to analyze breeding compatibility'
            }
            
    except Exception as e:
        logger.error(f"Error in breeding compatibility prediction: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def find_breeding_partners(orchid_id: int, desired_traits: List[str] = None, 
                          max_suggestions: int = 10) -> Dict[str, Any]:
    """
    Find optimal breeding partners for a specific orchid
    
    Args:
        orchid_id: Target orchid ID
        desired_traits: List of desired traits
        max_suggestions: Maximum number of suggestions
        
    Returns:
        List of breeding partner suggestions
    """
    try:
        predictor = BreedingCompatibilityPredictor()
        predictions = predictor.find_optimal_breeding_partners(orchid_id, desired_traits, max_suggestions)
        
        if predictions:
            formatted_results = []
            for pred in predictions:
                formatted_results.append({
                    'partner': {
                        'id': pred.parent2.id,
                        'name': pred.parent2.display_name,
                        'genus': pred.parent2.genus,
                        'species': pred.parent2.species,
                        'image_id': pred.parent2.google_drive_id
                    },
                    'compatibility_score': pred.compatibility_score,
                    'success_probability': pred.success_probability,
                    'breeding_difficulty': pred.breeding_difficulty.value,
                    'advantages': pred.breeding_advantages[:2],  # Top 2 advantages
                    'timeline': f"{pred.estimated_timeline.get('first_flowering_years', 4)} years to flowering"
                })
            
            return {
                'success': True,
                'target_orchid_id': orchid_id,
                'partner_suggestions': formatted_results,
                'total_candidates_analyzed': len(predictions),
                'analysis_timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': 'No suitable breeding partners found'
            }
            
    except Exception as e:
        logger.error(f"Error finding breeding partners: {e}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        parent1_id = int(sys.argv[1])
        parent2_id = int(sys.argv[2])
        result = predict_orchid_breeding_compatibility(parent1_id, parent2_id)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python breeding_compatibility_predictor.py <parent1_id> <parent2_id>")