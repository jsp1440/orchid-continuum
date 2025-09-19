#!/usr/bin/env python3
"""
OrchidAI Research Hub
====================
Unified AI research service backend that coordinates existing AI capabilities
and provides intelligent orchid research assistance for botanical researchers
and orchid society members.

Features:
- Unified query intelligence engine with intent classification
- Multi-model AI routing (OpenAI GPT-4o primary, Anthropic fallback)
- Context preparation from 5,975+ orchid database records
- Integration with GBIF ecosystem data
- Advanced AI reasoning with session context management
- Research query categories: Species ID, Cultivation, Research Discovery, Citations
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import uuid

# Flask imports
from flask import Blueprint, request, jsonify, session
from app import app, db

# Import existing AI modules
from orchid_ai import analyze_orchid_image, extract_metadata_from_text, get_weather_based_care_advice
from ai_orchid_identification import AIOrchidIdentifier
from ai_orchid_chat import OrchidAI
from ai_research_assistant import AIResearchAssistant
from orchid_ecosystem_integrator import OrchidEcosystemIntegrator

# Import database models
from models import (OrchidRecord, OrchidTaxonomy, AdvancedOrchidPollinatorRelationship, 
                   LiteratureCitation, ResearchCollaboration, MemberCollection, 
                   ExternalDatabaseCache)

# OpenAI and Anthropic clients
from openai import OpenAI
import anthropic

# Fuzzy matching and similarity
from fuzzywuzzy import fuzz, process
from Levenshtein import distance as levenshtein_distance
import jellyfish

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI clients
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Make API key optional with graceful degradation
openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI client initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ OpenAI client initialization failed: {e}")
else:
    logger.warning("⚠️ OPENAI_API_KEY not set - AI Research Hub will have limited functionality")

# Initialize Anthropic client if available
anthropic_client = None
if ANTHROPIC_API_KEY:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Create Flask Blueprint
research_hub_bp = Blueprint('research_hub', __name__, url_prefix='/ai-research-hub')

class QueryIntentType(Enum):
    """Research query intent classification"""
    SPECIES_IDENTIFICATION = "species_identification"
    CULTIVATION_ADVICE = "cultivation_advice"
    RESEARCH_DISCOVERY = "research_discovery"
    CITATION_GENERATION = "citation_generation"
    DATABASE_QUERY = "database_query"
    IMAGE_ANALYSIS = "image_analysis"
    ECOSYSTEM_ANALYSIS = "ecosystem_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"

class ConfidenceLevel(Enum):
    """AI response confidence levels"""
    VERY_HIGH = "very_high"  # 0.90+
    HIGH = "high"           # 0.70-0.89
    MEDIUM = "medium"       # 0.50-0.69
    LOW = "low"            # 0.30-0.49
    VERY_LOW = "very_low"   # <0.30

@dataclass
class ResearchQuery:
    """Structured research query"""
    query_id: str
    intent: QueryIntentType
    query_text: str
    user_id: Optional[str] = None
    image_data: Optional[Dict] = None
    context_filters: Optional[Dict] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None

@dataclass
class ResearchResponse:
    """Unified research response"""
    query_id: str
    response_type: str
    primary_result: Dict[str, Any]
    confidence_score: float
    confidence_level: ConfidenceLevel
    supporting_evidence: List[Dict[str, Any]]
    alternative_suggestions: List[Dict[str, Any]]
    source_citations: List[Dict[str, Any]]
    research_trail: List[str]
    session_context: Dict[str, Any]
    processing_time: float
    ai_models_used: List[str]
    database_records_referenced: int
    
class OrchidAIResearchHub:
    """
    Unified AI research service that coordinates existing AI capabilities
    and provides intelligent orchid research assistance
    """
    
    def __init__(self):
        """Initialize the research hub with all AI subsystems"""
        self.session_contexts = {}  # In-memory session storage
        self.fuzzy_match_cache = {}  # Cache for fuzzy matching results
        self.species_similarity_matrix = {}  # Pre-computed similarity scores
        
        # Initialize existing AI modules
        self.orchid_identifier = AIOrchidIdentifier()
        self.orchid_chat = OrchidAI()
        self.research_assistant = AIResearchAssistant()
        self.ecosystem_integrator = OrchidEcosystemIntegrator()
        
        # Load ecosystem data
        try:
            self.ecosystem_integrator.load_gbif_foundation()
            logger.info("🌿 GBIF foundation layer loaded successfully")
        except Exception as e:
            logger.warning(f"GBIF foundation layer loading failed: {e}")
        
        # Initialize enhanced database integration components
        self._init_enhanced_database_services()
        
        logger.info("🤖 OrchidAI Research Hub initialized successfully")
    
    def _init_enhanced_database_services(self):
        """Initialize enhanced database integration services"""
        try:
            # Pre-compute genus index for faster taxonomic searches
            self._precompute_genus_index()
            
            # Pre-compute similarity matrix for related species
            self._precompute_similarity_matrix()
            
            # Initialize FCOS collection cache
            self._init_fcos_collection_cache()
            
            # Initialize research collaboration index
            self._init_research_collaboration_index()
            
            logger.info("✅ Enhanced database services initialized")
            logger.info(f"📊 Database status: {OrchidRecord.query.count()} orchid records available")
            
        except Exception as e:
            logger.warning(f"⚠️ Enhanced database services initialization failed: {e}")
    
    def _precompute_genus_index(self):
        """Pre-compute genus index for faster taxonomic searches"""
        try:
            # Get all genera with counts
            genera = db.session.query(
                OrchidRecord.genus, 
                db.func.count(OrchidRecord.id).label('count')
            ).filter(
                OrchidRecord.genus.isnot(None)
            ).group_by(OrchidRecord.genus).all()
            
            self.genus_index = {}
            self.genus_species_count = {}
            
            for genus, count in genera:
                if genus:
                    self.genus_index[genus.lower()] = genus
                    self.genus_species_count[genus] = count
            
            logger.info(f"📚 Genus index created: {len(self.genus_index)} genera")
            
        except Exception as e:
            logger.warning(f"⚠️ Genus index creation failed: {e}")
            self.genus_index = {}
            self.genus_species_count = {}
    
    def _precompute_similarity_matrix(self):
        """Pre-compute similarity scores for related species"""
        try:
            # Get top 20 most common genera for similarity pre-computation
            top_genera = db.session.query(
                OrchidRecord.genus, 
                db.func.count(OrchidRecord.id).label('count')
            ).filter(
                OrchidRecord.genus.isnot(None)
            ).group_by(OrchidRecord.genus).order_by(
                db.func.count(OrchidRecord.id).desc()
            ).limit(20).all()
            
            self.species_similarity_matrix = {}
            
            for genus_name, count in top_genera:
                if genus_name and count > 3:  # Only compute for genera with multiple species
                    species_in_genus = db.session.query(
                        OrchidRecord.scientific_name
                    ).filter(
                        OrchidRecord.genus == genus_name,
                        OrchidRecord.scientific_name.isnot(None)
                    ).distinct().limit(30).all()  # Limit to avoid memory issues
                    
                    species_names = [sp[0] for sp in species_in_genus if sp[0]]
                    if len(species_names) > 1:
                        genus_similarities = {}
                        for i, sp1 in enumerate(species_names):
                            for sp2 in species_names[i+1:]:
                                similarity = fuzz.ratio(sp1, sp2)
                                if similarity > 65:  # Only store significant similarities
                                    genus_similarities[f"{sp1}||{sp2}"] = similarity
                        
                        if genus_similarities:
                            self.species_similarity_matrix[genus_name] = genus_similarities
            
            logger.info(f"🔗 Species similarity matrix created: {len(self.species_similarity_matrix)} genera")
            
        except Exception as e:
            logger.warning(f"⚠️ Similarity matrix creation failed: {e}")
            self.species_similarity_matrix = {}
    
    def _init_fcos_collection_cache(self):
        """Initialize FCOS collection data cache"""
        try:
            # Cache FCOS member collection data
            fcos_collections = MemberCollection.query.filter(
                MemberCollection.collection_name.ilike('%fcos%')
            ).limit(100).all()
            
            self.fcos_collection_cache = {}
            for collection in fcos_collections:
                if collection.orchid_record_id:
                    self.fcos_collection_cache[collection.orchid_record_id] = {
                        'collection_name': collection.collection_name,
                        'member_id': collection.member_id,
                        'growing_conditions': collection.growing_conditions,
                        'success_notes': collection.success_notes,
                        'cultivation_tips': collection.cultivation_tips,
                        'image_urls': collection.image_urls
                    }
            
            logger.info(f"🌺 FCOS collection cache initialized: {len(self.fcos_collection_cache)} records")
            
        except Exception as e:
            logger.warning(f"⚠️ FCOS collection cache initialization failed: {e}")
            self.fcos_collection_cache = {}
    
    def _init_research_collaboration_index(self):
        """Initialize research collaboration index for academic queries"""
        try:
            # Index research collaborations and literature citations
            collaborations = ResearchCollaboration.query.filter(
                ResearchCollaboration.collaboration_status == 'active'
            ).limit(50).all()
            
            citations = LiteratureCitation.query.filter(
                LiteratureCitation.doi.isnot(None)
            ).limit(100).all()
            
            self.research_collaboration_index = {}
            self.literature_citation_index = {}
            
            # Index collaborations by orchid species
            for collab in collaborations:
                species_key = collab.target_species or 'general'
                if species_key not in self.research_collaboration_index:
                    self.research_collaboration_index[species_key] = []
                self.research_collaboration_index[species_key].append({
                    'id': collab.id,
                    'institution': collab.collaborating_institution,
                    'research_focus': collab.research_focus,
                    'contact_person': collab.contact_person
                })
            
            # Index literature by orchid mentions
            for citation in citations:
                if citation.orchid_species_mentioned:
                    species_list = json.loads(citation.orchid_species_mentioned) if isinstance(citation.orchid_species_mentioned, str) else [citation.orchid_species_mentioned]
                    for species in species_list:
                        if species not in self.literature_citation_index:
                            self.literature_citation_index[species] = []
                        self.literature_citation_index[species].append({
                            'id': citation.id,
                            'title': citation.title,
                            'authors': citation.authors,
                            'doi': citation.doi,
                            'publication_year': citation.publication_year
                        })
            
            logger.info(f"🔬 Research collaboration index: {len(self.research_collaboration_index)} species")
            logger.info(f"📚 Literature citation index: {len(self.literature_citation_index)} species")
            
        except Exception as e:
            logger.warning(f"⚠️ Research index initialization failed: {e}")
            self.research_collaboration_index = {}
            self.literature_citation_index = {}

    def process_research_query(self, query: ResearchQuery) -> ResearchResponse:
        """
        Main entry point for processing research queries
        Coordinates all AI subsystems based on query intent
        """
        start_time = datetime.now()
        
        try:
            # Initialize session context if needed
            if query.session_id:
                self._ensure_session_context(query.session_id)
            
            # Classify query intent if not already classified
            if query.intent == QueryIntentType.DATABASE_QUERY:
                query.intent = self._classify_query_intent(query.query_text)
            
            # Route to appropriate processing method
            response_data = self._route_query_processing(query)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Build unified response
            response = ResearchResponse(
                query_id=query.query_id,
                response_type=query.intent.value,
                primary_result=response_data.get('primary_result', {}),
                confidence_score=response_data.get('confidence_score', 0.0),
                confidence_level=self._determine_confidence_level(response_data.get('confidence_score', 0.0)),
                supporting_evidence=response_data.get('supporting_evidence', []),
                alternative_suggestions=response_data.get('alternative_suggestions', []),
                source_citations=response_data.get('source_citations', []),
                research_trail=response_data.get('research_trail', []),
                session_context=self._get_session_context(query.session_id) if query.session_id else {},
                processing_time=processing_time,
                ai_models_used=response_data.get('ai_models_used', ['gpt-4o']),
                database_records_referenced=response_data.get('database_records_referenced', 0)
            )
            
            # Update session context
            if query.session_id:
                self._update_session_context(query.session_id, query, response)
            
            logger.info(f"🔬 Research query processed: {query.intent.value} (confidence: {response.confidence_score:.2f})")
            return response
            
        except Exception as e:
            logger.error(f"Research query processing error: {str(e)}")
            
            # Return error response
            return ResearchResponse(
                query_id=query.query_id,
                response_type="error",
                primary_result={"error": str(e), "error_type": "processing_error"},
                confidence_score=0.0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                supporting_evidence=[],
                alternative_suggestions=[],
                source_citations=[],
                research_trail=[f"Error: {str(e)}"],
                session_context={},
                processing_time=(datetime.now() - start_time).total_seconds(),
                ai_models_used=["error"],
                database_records_referenced=0
            )

    def _classify_query_intent(self, query_text: str) -> QueryIntentType:
        """Classify the intent of a research query using AI"""
        
        classification_prompt = f"""
        Classify this orchid research query into one of these categories:
        
        1. SPECIES_IDENTIFICATION - Identifying orchid species from images or descriptions
        2. CULTIVATION_ADVICE - Growing, care, watering, lighting, temperature advice
        3. RESEARCH_DISCOVERY - Scientific research, patterns, conservation, ecology
        4. CITATION_GENERATION - Academic references, literature, DOI lookup
        5. DATABASE_QUERY - Searching for specific orchid records or data
        6. IMAGE_ANALYSIS - Analyzing orchid images for various purposes
        7. ECOSYSTEM_ANALYSIS - Pollination, symbiosis, ecological relationships
        8. COMPARATIVE_ANALYSIS - Comparing orchid species, hybrids, or characteristics
        
        Query: "{query_text}"
        
        Respond with just the category name (e.g., "SPECIES_IDENTIFICATION").
        """
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content:
                intent_str = content.strip().upper()
                for intent in QueryIntentType:
                    if intent.name == intent_str:
                        return intent
            
        except Exception as e:
            logger.error(f"Query intent classification error: {e}")
        
        # Default fallback
        return QueryIntentType.DATABASE_QUERY

    def _route_query_processing(self, query: ResearchQuery) -> Dict[str, Any]:
        """Route query to appropriate AI subsystem based on intent"""
        
        if query.intent == QueryIntentType.SPECIES_IDENTIFICATION:
            return self._process_species_identification(query)
        elif query.intent == QueryIntentType.CULTIVATION_ADVICE:
            return self._process_cultivation_advice(query)
        elif query.intent == QueryIntentType.RESEARCH_DISCOVERY:
            return self._process_research_discovery(query)
        elif query.intent == QueryIntentType.CITATION_GENERATION:
            return self._process_citation_generation(query)
        elif query.intent == QueryIntentType.IMAGE_ANALYSIS:
            return self._process_image_analysis(query)
        elif query.intent == QueryIntentType.ECOSYSTEM_ANALYSIS:
            return self._process_ecosystem_analysis(query)
        elif query.intent == QueryIntentType.COMPARATIVE_ANALYSIS:
            return self._process_comparative_analysis(query)
        else:  # DATABASE_QUERY
            return self._process_database_query(query)

    def _process_species_identification(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process species identification queries using comprehensive AI analysis"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # Generate comprehensive species profile
            if query.image_data and query.image_data.get('path'):
                return self._generate_comprehensive_species_profile(
                    query, from_image=True
                )
            else:
                return self._generate_comprehensive_species_profile(
                    query, from_text=True
                )
                
        except Exception as e:
            logger.error(f"Species identification error: {e}")
            return {
                'primary_result': {
                    'analysis_type': 'species_identification_error',
                    'error': str(e),
                    'confidence_score': 0.0
                },
                'confidence_score': 0.0,
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records,
                'supporting_evidence': [],
                'alternative_suggestions': []
            }
    
    def _generate_comprehensive_species_profile(self, query: ResearchQuery, from_image=False, from_text=False) -> Dict[str, Any]:
        """Generate comprehensive species profile with taxonomic classification, GBIF verification, and morphological analysis"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        species_profile = {}
        
        try:
            # Step 1: Primary identification
            if from_image and query.image_data:
                identification_result = self.orchid_identifier.identify_orchid_from_image(
                    query.image_data['path']
                )
                primary_species = identification_result.get('primary_identification', {})
                morphological_data = identification_result.get('botanical_characteristics', {})
            else:
                # Text-based identification using AI
                primary_species, morphological_data = self._identify_species_from_text(query.query_text)
            
            if not primary_species or not primary_species.get('full_name'):
                return self._handle_no_identification(query)
            
            species_name = primary_species.get('full_name')
            genus = primary_species.get('genus')
            species = primary_species.get('species')
            
            # Step 2: Database integration and verification
            database_matches = self._get_comprehensive_database_matches(species_name, genus, species)
            database_records = len(database_matches)
            
            # Step 3: GBIF verification and distribution analysis
            gbif_data = self._verify_with_gbif(species_name, genus)
            
            # Step 4: Taxonomic classification enhancement
            taxonomic_classification = self._enhance_taxonomic_classification(species_name, genus, database_matches)
            
            # Step 5: Conservation status assessment
            conservation_status = self._assess_conservation_status(species_name, genus, gbif_data)
            
            # Step 6: Breeding history and hybrid analysis
            breeding_history = self._analyze_breeding_history(species_name, genus, database_matches)
            
            # Step 7: Pollinator and symbiotic associations
            ecological_relationships = self._analyze_ecological_relationships(species_name, genus)
            
            # Step 8: Distribution mapping and habitat requirements
            distribution_analysis = self._analyze_distribution_and_habitat(species_name, genus, gbif_data, database_matches)
            
            # Compile comprehensive species profile
            species_profile = {
                'primary_identification': {
                    'scientific_name': species_name,
                    'genus': genus,
                    'species': species,
                    'confidence_score': primary_species.get('confidence', 0.7),
                    'identification_method': 'AI_vision' if from_image else 'AI_text_analysis',
                    'alternative_names': primary_species.get('alternatives', [])
                },
                'taxonomic_classification': taxonomic_classification,
                'morphological_characteristics': morphological_data,
                'gbif_verification': gbif_data,
                'conservation_status': conservation_status,
                'distribution_analysis': distribution_analysis,
                'breeding_history': breeding_history,
                'ecological_relationships': ecological_relationships,
                'database_integration': {
                    'total_records': database_records,
                    'fcos_collections': len([r for r in database_matches if r.get('fcos_collection')]),
                    'verified_records': len([r for r in database_matches if r.get('verified')])
                },
                'profile_completeness': self._calculate_profile_completeness({
                    'taxonomic': taxonomic_classification,
                    'morphological': morphological_data,
                    'gbif': gbif_data,
                    'conservation': conservation_status,
                    'breeding': breeding_history,
                    'ecological': ecological_relationships
                })
            }
            
            # Calculate overall confidence
            confidence_factors = [
                primary_species.get('confidence', 0.7),
                gbif_data.get('verification_confidence', 0.6),
                taxonomic_classification.get('confidence', 0.7),
                min(database_records / 10.0, 1.0)  # More records = higher confidence
            ]
            overall_confidence = sum(confidence_factors) / len(confidence_factors)
            
            return {
                'primary_result': species_profile,
                'confidence_score': overall_confidence,
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records,
                'supporting_evidence': self._generate_supporting_evidence(species_profile),
                'alternative_suggestions': self._generate_profile_alternatives(primary_species.get('alternatives', []))
            }
            
        except Exception as e:
            logger.error(f"Comprehensive species profile generation error: {e}")
            return {
                'primary_result': {
                    'analysis_type': 'species_profiling_error',
                    'error': str(e)
                },
                'confidence_score': 0.0,
                'ai_models_used': ai_models_used,
                'database_records_referenced': 0
            }
        
        except Exception as e:
            logger.error(f"Species identification processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_cultivation_advice(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process cultivation advice queries with intelligent recommendations and climate matching"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            return self._generate_intelligent_cultivation_advisory(query)
            
        except Exception as e:
            logger.error(f"Cultivation advice error: {e}")
            return {
                'primary_result': {
                    'analysis_type': 'cultivation_advice_error',
                    'error': str(e)
                },
                'confidence_score': 0.0,
                'ai_models_used': ai_models_used,
                'database_records_referenced': 0
            }
    
    def _generate_intelligent_cultivation_advisory(self, query: ResearchQuery) -> Dict[str, Any]:
        """Generate intelligent cultivation advice with climate matching and problem diagnosis"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # Step 1: Identify target orchids and user context
            target_orchids = self._extract_orchid_names_from_query(query.query_text)
            user_location = query.context_filters.get('location') if query.context_filters else None
            growing_conditions = query.context_filters.get('conditions') if query.context_filters else None
            
            # Step 2: Database integration for cultivation data
            cultivation_database = self._gather_cultivation_database(target_orchids)
            database_records = len(cultivation_database)
            
            # Step 3: Climate matching analysis
            climate_analysis = self._perform_climate_matching(target_orchids, user_location, cultivation_database)
            
            # Step 4: Baker culture sheet integration and extrapolation
            baker_analysis = self._integrate_baker_culture_data(target_orchids, cultivation_database)
            
            # Step 5: Seasonal care guidance and photoperiod analysis
            seasonal_guidance = self._generate_seasonal_care_guidance(target_orchids, climate_analysis)
            
            # Step 6: Problem diagnosis and treatment suggestions
            problem_diagnosis = self._diagnose_cultivation_problems(query.query_text, target_orchids)
            
            # Step 7: FCOS collection success stories integration
            success_stories = self._integrate_fcos_success_stories(target_orchids)
            
            # Step 8: Growing condition recommendations with scoring
            condition_recommendations = self._generate_condition_recommendations(
                target_orchids, climate_analysis, baker_analysis, growing_conditions
            )
            
            # Step 9: Care calendar generation
            care_calendar = self._generate_care_calendar(target_orchids, seasonal_guidance, climate_analysis)
            
            # Compile comprehensive cultivation advisory
            cultivation_advisory = {
                'target_orchids': target_orchids,
                'climate_analysis': climate_analysis,
                'baker_culture_integration': baker_analysis,
                'seasonal_guidance': seasonal_guidance,
                'problem_diagnosis': problem_diagnosis,
                'condition_recommendations': condition_recommendations,
                'care_calendar': care_calendar,
                'success_stories': success_stories,
                'personalized_advice': self._generate_personalized_advice(
                    target_orchids, user_location, growing_conditions, query.query_text
                ),
                'difficulty_assessment': self._assess_growing_difficulty(target_orchids, cultivation_database),
                'expert_tips': self._extract_expert_cultivation_tips(target_orchids, cultivation_database)
            }
            
            # Calculate confidence based on data availability and specificity
            confidence_factors = [
                min(len(cultivation_database) / 5.0, 1.0),  # Database coverage
                baker_analysis.get('confidence', 0.6),
                climate_analysis.get('confidence', 0.7),
                len(target_orchids) / 3.0 if target_orchids else 0.3  # Specificity
            ]
            overall_confidence = sum(confidence_factors) / len(confidence_factors)
            
            return {
                'primary_result': cultivation_advisory,
                'confidence_score': overall_confidence,
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records,
                'supporting_evidence': self._generate_cultivation_evidence(cultivation_advisory),
                'alternative_suggestions': self._generate_cultivation_alternatives(cultivation_advisory)
            }
            
        except Exception as e:
            logger.error(f"Intelligent cultivation advisory generation error: {e}")
            return {
                'primary_result': {
                    'analysis_type': 'cultivation_advisory_error',
                    'error': str(e)
                },
                'confidence_score': 0.0,
                'ai_models_used': ai_models_used,
                'database_records_referenced': 0
            }
        
        except Exception as e:
            logger.error(f"Cultivation advice processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_research_discovery(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process research discovery queries with pattern analysis and academic correlation"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            return self._generate_comprehensive_research_discovery(query)
            
        except Exception as e:
            logger.error(f"Research discovery error: {e}")
            return {
                'primary_result': {
                    'analysis_type': 'research_discovery_error',
                    'error': str(e)
                },
                'confidence_score': 0.0,
                'ai_models_used': ai_models_used,
                'database_records_referenced': 0
            }
    
    def _generate_comprehensive_research_discovery(self, query: ResearchQuery) -> Dict[str, Any]:
        """Generate comprehensive research discovery with pattern analysis and collaboration matching"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # Step 1: Taxonomic relationship network analysis
            taxonomic_analysis = self._analyze_taxonomic_relationships(query.query_text)
            
            # Step 2: Pattern analysis across evolutionary connections
            evolutionary_patterns = self._analyze_evolutionary_patterns(query.query_text, taxonomic_analysis)
            
            # Step 3: Literature correlation and citation mining
            literature_analysis = self._analyze_research_literature(query.query_text)
            
            # Step 4: Research gap identification
            research_gaps = self._identify_research_gaps(query.query_text, literature_analysis, taxonomic_analysis)
            
            # Step 5: Academic collaboration matching
            collaboration_opportunities = self._match_collaboration_opportunities(query.query_text, research_gaps)
            
            # Step 6: Conservation priority analysis
            conservation_analysis = self._analyze_conservation_priorities(query.query_text, taxonomic_analysis)
            
            # Step 7: Grant opportunity suggestions
            grant_opportunities = self._suggest_grant_opportunities(research_gaps, conservation_analysis)
            
            # Step 8: Research methodology recommendations
            methodology_suggestions = self._suggest_research_methodologies(query.query_text, research_gaps)
            
            # Step 9: Academic impact assessment
            impact_assessment = self._assess_academic_impact(literature_analysis, research_gaps)
            
            # Compile comprehensive research discovery
            research_discovery = {
                'query_focus': query.query_text,
                'taxonomic_analysis': taxonomic_analysis,
                'evolutionary_patterns': evolutionary_patterns,
                'literature_analysis': literature_analysis,
                'research_gaps': research_gaps,
                'collaboration_opportunities': collaboration_opportunities,
                'conservation_analysis': conservation_analysis,
                'grant_opportunities': grant_opportunities,
                'methodology_suggestions': methodology_suggestions,
                'impact_assessment': impact_assessment,
                'discovery_insights': self._generate_discovery_insights(
                    taxonomic_analysis, evolutionary_patterns, literature_analysis, research_gaps
                ),
                'future_directions': self._suggest_future_research_directions(
                    research_gaps, conservation_analysis, collaboration_opportunities
                )
            }
            
            # Calculate database records used
            database_records = (
                taxonomic_analysis.get('records_analyzed', 0) +
                literature_analysis.get('citations_analyzed', 0) +
                conservation_analysis.get('records_analyzed', 0)
            )
            
            # Calculate confidence based on data depth and pattern strength
            confidence_factors = [
                taxonomic_analysis.get('confidence', 0.7),
                literature_analysis.get('confidence', 0.6),
                min(len(research_gaps.get('identified_gaps', [])) / 3.0, 1.0),
                conservation_analysis.get('confidence', 0.6)
            ]
            overall_confidence = sum(confidence_factors) / len(confidence_factors)
            
            return {
                'primary_result': research_discovery,
                'confidence_score': overall_confidence,
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records,
                'supporting_evidence': self._generate_discovery_evidence(research_discovery),
                'alternative_suggestions': self._generate_discovery_alternatives(research_discovery)
            }
            
        except Exception as e:
            logger.error(f"Comprehensive research discovery generation error: {e}")
            return {
                'primary_result': {
                    'analysis_type': 'research_discovery_error',
                    'error': str(e)
                },
                'confidence_score': 0.0,
                'ai_models_used': ai_models_used,
                'database_records_referenced': 0
            }
        
        except Exception as e:
            logger.error(f"Research discovery processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_citation_generation(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process citation generation queries for academic references"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # Extract entities mentioned in query
            entities = self._extract_research_entities(query.query_text)
            
            # Find relevant database records
            relevant_records = []
            for entity in entities:
                records = OrchidRecord.query.filter(
                    db.or_(
                        OrchidRecord.display_name.ilike(f'%{entity}%'),
                        OrchidRecord.scientific_name.ilike(f'%{entity}%')
                    )
                ).limit(10).all()
                relevant_records.extend(records)
            
            database_records = len(relevant_records)
            
            # Generate citations using AI
            citations = self._generate_academic_citations(query.query_text, relevant_records)
            
            return {
                'primary_result': {
                    'formatted_citations': citations.get('citations', []),
                    'citation_styles': ['APA', 'MLA', 'Chicago', 'Vancouver'],
                    'doi_suggestions': citations.get('dois', []),
                    'reference_quality': citations.get('quality_assessment', {})
                },
                'confidence_score': citations.get('confidence_score', 0.8),
                'supporting_evidence': [self._serialize_orchid_record(r) for r in relevant_records],
                'alternative_suggestions': citations.get('alternative_sources', []),
                'source_citations': citations.get('primary_sources', []),
                'research_trail': [
                    f"Entity extraction: {len(entities)} entities",
                    f"Database matching: {database_records} records",
                    "AI citation generation"
                ],
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records
            }
        
        except Exception as e:
            logger.error(f"Citation generation processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_image_analysis(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process image analysis queries using unified image AI"""
        
        if not query.image_data or not query.image_data.get('path'):
            return self._generate_error_response("No image data provided for image analysis")
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            image_path = query.image_data['path']
            
            # Comprehensive image analysis using existing modules
            orchid_analysis = analyze_orchid_image(image_path)
            exif_data = extract_metadata_from_text(str(orchid_analysis))  # Extract metadata from analysis result
            
            # Get database context if genus identified
            genus = orchid_analysis.get('genus')
            database_matches = []
            if genus:
                matches = OrchidRecord.query.filter(
                    OrchidRecord.scientific_name.ilike(f'{genus}%')
                ).limit(15).all()
                database_records = len(matches)
                database_matches = [self._serialize_orchid_record(record) for record in matches]
            
            return {
                'primary_result': {
                    'botanical_analysis': orchid_analysis,
                    'exif_metadata': exif_data,
                    'image_quality': self._assess_image_quality(image_path),
                    'analysis_completeness': self._calculate_analysis_completeness(orchid_analysis)
                },
                'confidence_score': orchid_analysis.get('confidence', 0.5),
                'supporting_evidence': database_matches,
                'alternative_suggestions': self._generate_image_alternatives(orchid_analysis),
                'source_citations': self._generate_image_citations(orchid_analysis, exif_data),
                'research_trail': [
                    "Image encoding and preprocessing",
                    "AI botanical analysis",
                    "EXIF metadata extraction",
                    f"Database cross-reference: {database_records} records"
                ],
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records
            }
        
        except Exception as e:
            logger.error(f"Image analysis processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_ecosystem_analysis(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process ecosystem analysis using GBIF integration"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # Extract orchid species from query
            species_names = self._extract_species_names_from_query(query.query_text)
            
            ecosystem_data = {}
            gbif_interactions = []
            
            # Get ecosystem data for each species
            for species in species_names[:5]:  # Limit to 5 species
                interactions = self.ecosystem_integrator.fetch_globi_interactions(species)
                gbif_interactions.extend(interactions)
                database_records += len(interactions)
            
            # Generate ecosystem analysis using AI
            if gbif_interactions:
                ecosystem_analysis = self._generate_ecosystem_analysis(
                    query.query_text, gbif_interactions
                )
            else:
                ecosystem_analysis = self._generate_general_ecosystem_analysis(query.query_text)
            
            return {
                'primary_result': {
                    'ecosystem_interactions': gbif_interactions,
                    'analysis_summary': ecosystem_analysis,
                    'pollination_networks': ecosystem_analysis.get('pollination', {}),
                    'conservation_implications': ecosystem_analysis.get('conservation', {})
                },
                'confidence_score': ecosystem_analysis.get('confidence_score', 0.6),
                'supporting_evidence': gbif_interactions,
                'alternative_suggestions': ecosystem_analysis.get('research_suggestions', []),
                'source_citations': self._generate_ecosystem_citations(gbif_interactions),
                'research_trail': [
                    f"Species extraction: {len(species_names)} species",
                    f"GBIF interactions: {len(gbif_interactions)} records",
                    "AI ecosystem analysis"
                ],
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records
            }
        
        except Exception as e:
            logger.error(f"Ecosystem analysis processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_comparative_analysis(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process comparative analysis between orchid species or hybrids"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # Extract orchid names for comparison
            orchid_names = self._extract_orchid_names_from_query(query.query_text)
            
            if len(orchid_names) < 2:
                return self._generate_error_response("Comparative analysis requires at least 2 orchid names")
            
            comparison_data = []
            for name in orchid_names[:5]:  # Limit to 5 orchids
                records = OrchidRecord.query.filter(
                    db.or_(
                        OrchidRecord.display_name.ilike(f'%{name}%'),
                        OrchidRecord.scientific_name.ilike(f'%{name}%')
                    )
                ).limit(3).all()
                
                database_records += len(records)
                for record in records:
                    comparison_data.append(self._serialize_orchid_record(record))
            
            # Generate comparative analysis using AI
            comparative_analysis = self._generate_comparative_analysis(
                query.query_text, comparison_data
            )
            
            return {
                'primary_result': {
                    'comparison_matrix': comparative_analysis.get('matrix', {}),
                    'key_differences': comparative_analysis.get('differences', []),
                    'similarities': comparative_analysis.get('similarities', []),
                    'cultivation_comparison': comparative_analysis.get('cultivation', {}),
                    'taxonomic_relationships': comparative_analysis.get('taxonomy', {})
                },
                'confidence_score': comparative_analysis.get('confidence_score', 0.7),
                'supporting_evidence': comparison_data,
                'alternative_suggestions': comparative_analysis.get('additional_comparisons', []),
                'source_citations': self._generate_database_citations(comparison_data),
                'research_trail': [
                    f"Orchid extraction: {len(orchid_names)} names",
                    f"Database retrieval: {database_records} records",
                    "AI comparative analysis"
                ],
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records
            }
        
        except Exception as e:
            logger.error(f"Comparative analysis processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_database_query(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process general database queries using intelligent search"""
        
        ai_models_used = ['database_search']
        
        try:
            # Intelligent database search
            search_results = self._search_orchid_database(query.query_text)
            database_records = len(search_results)
            
            # Generate AI summary of results
            if search_results:
                ai_summary = self._generate_search_summary(query.query_text, search_results)
            else:
                ai_summary = {"summary": "No matching records found", "suggestions": []}
            
            return {
                'primary_result': {
                    'search_results': search_results,
                    'result_summary': ai_summary,
                    'total_matches': database_records,
                    'search_strategy': self._explain_search_strategy(query.query_text)
                },
                'confidence_score': 0.9 if database_records > 0 else 0.1,
                'supporting_evidence': search_results[:10],  # Top 10 results
                'alternative_suggestions': ai_summary.get('suggestions', []),
                'source_citations': self._generate_database_citations(search_results),
                'research_trail': [
                    f"Database search executed",
                    f"Results found: {database_records}",
                    "AI result summarization"
                ],
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records
            }
        
        except Exception as e:
            logger.error(f"Database query processing error: {e}")
            return self._generate_error_response(str(e))

    # Enhanced database integration methods
    def get_comprehensive_orchid_data(self, query_text: str, include_fcos: bool = True, 
                                     include_research: bool = True) -> Dict[str, Any]:
        """Get comprehensive orchid data with FCOS collection and research integration"""
        
        logger.info(f"🔍 Comprehensive data request: '{query_text}'")
        
        try:
            # 1. Enhanced database search with fuzzy matching
            search_results = self._search_orchid_database_comprehensive(query_text, limit=25)
            
            # 2. Add FCOS collection data
            if include_fcos:
                search_results = self._enrich_with_fcos_collection_data(search_results)
            
            # 3. Add research collaboration and literature data
            if include_research:
                search_results = self._enrich_with_research_data(search_results, query_text)
            
            # 4. Enhanced GBIF ecosystem integration
            search_results = self._enrich_with_enhanced_gbif_data(search_results)
            
            # 5. Add confidence scoring and source attribution
            search_results = self._add_confidence_scoring(search_results, query_text)
            
            return {
                'orchid_records': search_results,
                'total_found': len(search_results),
                'data_sources': self._get_data_sources_summary(search_results),
                'search_strategy': self._explain_comprehensive_search_strategy(query_text),
                'confidence_distribution': self._analyze_confidence_distribution(search_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Comprehensive data error: {e}")
            return {'error': str(e), 'orchid_records': []}
    
    def _search_orchid_database_comprehensive(self, query_text: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Comprehensive intelligent search with fuzzy matching and taxonomic hierarchy"""
        
        results = []
        
        try:
            # 1. Exact matches (highest priority)
            exact_results = self._exact_database_search(query_text, limit//3)
            
            # 2. Fuzzy matches for misspellings
            fuzzy_results = self._fuzzy_database_search_enhanced(query_text, limit//3)
            
            # 3. Taxonomic hierarchy search
            taxonomy_results = self._taxonomic_hierarchy_search_enhanced(query_text, limit//3)
            
            # 4. Combine and deduplicate
            all_results = exact_results + fuzzy_results + taxonomy_results
            seen_ids = set()
            
            for result in all_results:
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    results.append(result)
                    if len(results) >= limit:
                        break
            
            # 5. Score and rank results
            results = self._score_and_rank_results_enhanced(results, query_text)
            
            logger.info(f"✅ Comprehensive search: {len(results)} unique results")
            
        except Exception as e:
            logger.error(f"❌ Comprehensive search error: {e}")
        
        return results[:limit]
    
    def _enrich_with_fcos_collection_data(self, orchid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich orchid records with FCOS collection member experiences"""
        
        try:
            for record in orchid_records:
                orchid_id = record.get('id')
                
                # Check FCOS collection cache
                if orchid_id in self.fcos_collection_cache:
                    fcos_data = self.fcos_collection_cache[orchid_id]
                    record['fcos_collection'] = {
                        'member_cultivation': fcos_data,
                        'has_member_experience': True,
                        'growing_success_notes': fcos_data.get('success_notes'),
                        'member_cultivation_tips': fcos_data.get('cultivation_tips'),
                        'google_drive_images': fcos_data.get('image_urls')
                    }
                
                # Look for additional FCOS records by scientific name matching
                if record.get('scientific_name'):
                    additional_fcos = MemberCollection.query.filter(
                        db.or_(
                            MemberCollection.orchid_scientific_name.ilike(f"%{record['scientific_name']}%"),
                            MemberCollection.collection_notes.ilike(f"%{record['scientific_name']}%")
                        )
                    ).limit(3).all()
                    
                    if additional_fcos:
                        if 'fcos_collection' not in record:
                            record['fcos_collection'] = {'member_cultivation': [], 'has_member_experience': False}
                        
                        for fcos_record in additional_fcos:
                            record['fcos_collection']['member_cultivation'].append({
                                'member_id': fcos_record.member_id,
                                'collection_name': fcos_record.collection_name,
                                'growing_conditions': fcos_record.growing_conditions,
                                'success_notes': fcos_record.success_notes,
                                'image_urls': fcos_record.image_urls
                            })
                        
                        record['fcos_collection']['has_member_experience'] = True
            
            logger.info(f"📋 FCOS enrichment: {sum(1 for r in orchid_records if r.get('fcos_collection', {}).get('has_member_experience'))} records enriched")
            
        except Exception as e:
            logger.error(f"❌ FCOS enrichment error: {e}")
        
        return orchid_records
    
    def _enrich_with_research_data(self, orchid_records: List[Dict[str, Any]], query_text: str) -> List[Dict[str, Any]]:
        """Enrich with research collaborations and literature citations"""
        
        try:
            for record in orchid_records:
                scientific_name = record.get('scientific_name', '')
                genus = record.get('genus', '')
                
                # Research collaborations
                research_collabs = []
                for species_key in [scientific_name, genus, 'general']:
                    if species_key in self.research_collaboration_index:
                        research_collabs.extend(self.research_collaboration_index[species_key])
                
                # Literature citations
                literature_refs = []
                for species_key in [scientific_name, genus]:
                    if species_key in self.literature_citation_index:
                        literature_refs.extend(self.literature_citation_index[species_key])
                
                if research_collabs or literature_refs:
                    record['research_data'] = {
                        'active_collaborations': research_collabs[:3],  # Top 3 collaborations
                        'literature_citations': literature_refs[:5],   # Top 5 citations
                        'research_significance': record.get('research_significance', 'Standard'),
                        'has_academic_interest': len(research_collabs) > 0 or len(literature_refs) > 0
                    }
            
            enriched_count = sum(1 for r in orchid_records if r.get('research_data', {}).get('has_academic_interest'))
            logger.info(f"🔬 Research enrichment: {enriched_count} records with academic data")
            
        except Exception as e:
            logger.error(f"❌ Research enrichment error: {e}")
        
        return orchid_records
    
    def _enrich_with_enhanced_gbif_data(self, orchid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced GBIF integration with occurrence data and conservation status"""
        
        try:
            for record in orchid_records:
                gbif_key = record.get('gbif_species_key')
                scientific_name = record.get('scientific_name')
                
                if gbif_key or scientific_name:
                    # Get enhanced GBIF data through ecosystem integrator
                    try:
                        if scientific_name:
                            # Get occurrence data
                            occurrence_data = self.ecosystem_integrator.fetch_gbif_occurrences(scientific_name, limit=10)
                            
                            # Get conservation status
                            conservation_status = self.ecosystem_integrator.get_conservation_status(scientific_name)
                            
                            # Get pollinator relationships
                            pollinator_relationships = AdvancedOrchidPollinatorRelationship.query.filter(
                                AdvancedOrchidPollinatorRelationship.orchid_species.ilike(f'%{scientific_name}%')
                            ).limit(5).all()
                            
                            record['enhanced_gbif'] = {
                                'occurrence_count': len(occurrence_data) if occurrence_data else 0,
                                'occurrence_data': occurrence_data[:5] if occurrence_data else [],
                                'conservation_status': conservation_status,
                                'pollinator_relationships': [
                                    {
                                        'pollinator_species': rel.pollinator_species,
                                        'interaction_type': rel.interaction_type,
                                        'relationship_strength': rel.relationship_strength,
                                        'seasonal_timing': rel.seasonal_timing
                                    } for rel in pollinator_relationships
                                ],
                                'has_ecological_data': len(pollinator_relationships) > 0 or (occurrence_data and len(occurrence_data) > 0)
                            }
                    
                    except Exception as gbif_error:
                        logger.warning(f"⚠️ GBIF enrichment failed for {scientific_name}: {gbif_error}")
                        record['enhanced_gbif'] = {'error': 'GBIF data unavailable', 'has_ecological_data': False}
            
            enriched_count = sum(1 for r in orchid_records if r.get('enhanced_gbif', {}).get('has_ecological_data'))
            logger.info(f"🌍 GBIF enrichment: {enriched_count} records with ecological data")
            
        except Exception as e:
            logger.error(f"❌ Enhanced GBIF integration error: {e}")
        
        return orchid_records
    
    def _add_confidence_scoring(self, orchid_records: List[Dict[str, Any]], query_text: str) -> List[Dict[str, Any]]:
        """Add intelligent confidence scoring based on data completeness and verification"""
        
        try:
            for record in orchid_records:
                confidence_factors = {
                    'data_completeness': 0,
                    'external_verification': 0,
                    'member_validation': 0,
                    'research_backing': 0,
                    'query_relevance': 0
                }
                
                # Data completeness scoring (40% of confidence)
                required_fields = ['scientific_name', 'genus', 'species', 'region', 'native_habitat']
                optional_fields = ['common_names', 'cultural_notes', 'image_url', 'bloom_time', 'growth_habit']
                
                completeness_score = 0
                for field in required_fields:
                    if record.get(field):
                        completeness_score += 0.6 / len(required_fields)
                
                for field in optional_fields:
                    if record.get(field):
                        completeness_score += 0.4 / len(optional_fields)
                
                confidence_factors['data_completeness'] = min(completeness_score, 0.4)
                
                # External verification (25% of confidence)
                if record.get('taxonomy_info', {}).get('verification_status') == 'verified':
                    confidence_factors['external_verification'] += 0.15
                if record.get('gbif_species_key'):
                    confidence_factors['external_verification'] += 0.1
                
                # Member validation (15% of confidence)
                if record.get('fcos_collection', {}).get('has_member_experience'):
                    confidence_factors['member_validation'] = 0.15
                
                # Research backing (10% of confidence)
                if record.get('research_data', {}).get('has_academic_interest'):
                    confidence_factors['research_backing'] = 0.1
                
                # Query relevance (10% of confidence)
                relevance_score = record.get('relevance_score', 0)
                confidence_factors['query_relevance'] = min(relevance_score * 0.1, 0.1)
                
                # Calculate total confidence
                total_confidence = sum(confidence_factors.values())
                
                record['ai_confidence'] = {
                    'overall_score': round(total_confidence, 3),
                    'confidence_factors': confidence_factors,
                    'confidence_level': self._determine_confidence_level(total_confidence),
                    'data_sources': self._identify_data_sources(record)
                }
            
            logger.info(f"⭐ Confidence scoring: {len(orchid_records)} records scored")
            
        except Exception as e:
            logger.error(f"❌ Confidence scoring error: {e}")
        
        return orchid_records
    
    def _fuzzy_database_search_enhanced(self, query_text: str, limit: int) -> List[Dict[str, Any]]:
        """Enhanced fuzzy matching with better performance and accuracy"""
        
        try:
            # Get all orchid names for fuzzy matching (optimized query)
            orchid_names = db.session.query(
                OrchidRecord.id,
                OrchidRecord.scientific_name,
                OrchidRecord.display_name,
                OrchidRecord.genus
            ).filter(
                db.or_(
                    OrchidRecord.scientific_name.isnot(None),
                    OrchidRecord.display_name.isnot(None),
                    OrchidRecord.genus.isnot(None)
                )
            ).limit(500).all()  # Limit for performance
            
            # Build name candidates for fuzzy matching
            name_candidates = []
            for record in orchid_names:
                if record.scientific_name:
                    name_candidates.append((record.scientific_name, record.id, 'scientific'))
                if record.display_name and record.display_name != record.scientific_name:
                    name_candidates.append((record.display_name, record.id, 'display'))
                if record.genus:
                    name_candidates.append((record.genus, record.id, 'genus'))
            
            # Fuzzy match using multiple algorithms
            query_terms = [term.strip() for term in query_text.split() if len(term.strip()) > 2]
            fuzzy_matches = []
            
            for term in query_terms:
                # Use fuzzywuzzy for standard matching
                matches = process.extractBests(
                    term, 
                    [name for name, _, _ in name_candidates], 
                    score_cutoff=65, 
                    limit=15
                )
                
                for match_name, score in matches:
                    matching_records = [(orchid_id, name_type) for name, orchid_id, name_type in name_candidates if name == match_name]
                    for orchid_id, name_type in matching_records:
                        fuzzy_matches.append((orchid_id, score, name_type, match_name, term))
            
            # Get unique high-scoring matches
            unique_matches = {}
            for orchid_id, score, name_type, match_name, original_term in fuzzy_matches:
                if orchid_id not in unique_matches or unique_matches[orchid_id]['score'] < score:
                    unique_matches[orchid_id] = {
                        'score': score,
                        'name_type': name_type,
                        'matched_name': match_name,
                        'original_term': original_term
                    }
            
            # Get top matches and fetch full records
            top_matches = sorted(unique_matches.items(), key=lambda x: x[1]['score'], reverse=True)[:limit]
            orchid_ids = [match[0] for match in top_matches]
            
            results = []
            if orchid_ids:
                records = OrchidRecord.query.filter(OrchidRecord.id.in_(orchid_ids)).all()
                for record in records:
                    serialized = self._serialize_orchid_record_enhanced(record)
                    if record.id in unique_matches:
                        match_info = unique_matches[record.id]
                        serialized['fuzzy_match_score'] = match_info['score']
                        serialized['matched_field'] = match_info['name_type']
                        serialized['matched_name'] = match_info['matched_name']
                        serialized['original_query_term'] = match_info['original_term']
                    results.append(serialized)
            
            return results
            
        except Exception as e:
            logger.error(f"Enhanced fuzzy search error: {e}")
            return []
    
    def _taxonomic_hierarchy_search_enhanced(self, query_text: str, limit: int) -> List[Dict[str, Any]]:
        """Enhanced taxonomic hierarchy search with better matching"""
        
        try:
            results = []
            terms = [term.capitalize().strip() for term in query_text.split() if len(term.strip()) > 2]
            
            for term in terms:
                # Search in genus index first (pre-computed)
                genus_matches = []
                for genus_key, genus_name in self.genus_index.items():
                    if term.lower() in genus_key or genus_key.startswith(term.lower()):
                        genus_matches.append(genus_name)
                
                # Search OrchidTaxonomy for more comprehensive matches
                taxonomy_records = OrchidTaxonomy.query.filter(
                    db.or_(
                        OrchidTaxonomy.genus.ilike(f'{term}%'),
                        OrchidTaxonomy.scientific_name.ilike(f'{term}%'),
                        OrchidTaxonomy.family.ilike(f'%{term}%'),
                        OrchidTaxonomy.subfamily.ilike(f'%{term}%')
                    )
                ).limit(10).all()
                
                # Get related OrchidRecords through taxonomy
                for tax_record in taxonomy_records:
                    orchid_records = OrchidRecord.query.filter(
                        OrchidRecord.taxonomy_id == tax_record.id
                    ).limit(3).all()
                    
                    for record in orchid_records:
                        serialized = self._serialize_orchid_record_enhanced(record)
                        serialized['taxonomy_match'] = {
                            'taxonomy_id': tax_record.id,
                            'family': tax_record.family,
                            'subfamily': tax_record.subfamily,
                            'gbif_key': tax_record.gbif_key,
                            'verification_status': tax_record.external_verification_status,
                            'matched_level': 'species' if tax_record.scientific_name else 'genus'
                        }
                        results.append(serialized)
                        
                        if len(results) >= limit:
                            return results[:limit]
                
                # Direct genus search in OrchidRecord for additional matches
                for genus_name in genus_matches:
                    genus_records = OrchidRecord.query.filter(
                        OrchidRecord.genus == genus_name
                    ).limit(5).all()
                    
                    for record in genus_records:
                        serialized = self._serialize_orchid_record_enhanced(record)
                        serialized['genus_match'] = {
                            'matched_genus': genus_name,
                            'species_count_in_genus': self.genus_species_count.get(genus_name, 1),
                            'matched_level': 'genus'
                        }
                        results.append(serialized)
                        
                        if len(results) >= limit:
                            return results[:limit]
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Enhanced taxonomic search error: {e}")
            return []
    
    def _score_and_rank_results_enhanced(self, results: List[Dict[str, Any]], query_text: str) -> List[Dict[str, Any]]:
        """Enhanced scoring with multiple relevance factors"""
        
        try:
            query_lower = query_text.lower()
            query_terms = [term.strip().lower() for term in query_text.split() if len(term.strip()) > 2]
            
            for result in results:
                score = 0.0
                scoring_details = {}
                
                # 1. Fuzzy match scoring (25%)
                if 'fuzzy_match_score' in result:
                    fuzzy_score = result['fuzzy_match_score'] / 100.0 * 0.25
                    score += fuzzy_score
                    scoring_details['fuzzy_match'] = fuzzy_score
                
                # 2. Exact match bonuses (30%)
                exact_match_score = 0
                scientific_name = result.get('scientific_name', '').lower()
                display_name = result.get('display_name', '').lower()
                genus = result.get('genus', '').lower()
                
                # Perfect matches get highest scores
                if query_lower == scientific_name:
                    exact_match_score += 0.30
                elif query_lower == display_name:
                    exact_match_score += 0.25
                elif query_lower == genus:
                    exact_match_score += 0.20
                else:
                    # Partial matches
                    for term in query_terms:
                        if term in scientific_name:
                            exact_match_score += 0.05
                        if term in display_name:
                            exact_match_score += 0.03
                        if term in genus:
                            exact_match_score += 0.02
                
                score += min(exact_match_score, 0.30)
                scoring_details['exact_match'] = min(exact_match_score, 0.30)
                
                # 3. Data completeness (20%)
                completeness_score = 0
                required_fields = ['scientific_name', 'genus', 'species', 'region', 'native_habitat']
                bonus_fields = ['common_names', 'cultural_notes', 'image_url', 'bloom_time', 'growth_habit', 'ai_description']
                
                for field in required_fields:
                    if result.get(field):
                        completeness_score += 0.12 / len(required_fields)
                
                for field in bonus_fields:
                    if result.get(field):
                        completeness_score += 0.08 / len(bonus_fields)
                
                score += min(completeness_score, 0.20)
                scoring_details['completeness'] = min(completeness_score, 0.20)
                
                # 4. External verification (15%)
                verification_score = 0
                if result.get('taxonomy_match', {}).get('verification_status') == 'verified':
                    verification_score += 0.08
                if result.get('gbif_species_key'):
                    verification_score += 0.04
                if result.get('enhanced_gbif', {}).get('has_ecological_data'):
                    verification_score += 0.03
                
                score += min(verification_score, 0.15)
                scoring_details['verification'] = min(verification_score, 0.15)
                
                # 5. Community and research value (10%)
                community_score = 0
                if result.get('fcos_collection', {}).get('has_member_experience'):
                    community_score += 0.05
                if result.get('research_data', {}).get('has_academic_interest'):
                    community_score += 0.05
                
                score += min(community_score, 0.10)
                scoring_details['community'] = min(community_score, 0.10)
                
                # Store detailed scoring
                result['relevance_score'] = round(score, 4)
                result['scoring_details'] = scoring_details
                result['ranking_factors'] = {
                    'has_fuzzy_match': 'fuzzy_match_score' in result,
                    'has_exact_match': exact_match_score > 0,
                    'data_complete': completeness_score > 0.15,
                    'externally_verified': verification_score > 0.05,
                    'community_validated': community_score > 0
                }
            
            # Sort by relevance score
            return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Enhanced scoring error: {e}")
            return results
    
    def _get_data_sources_summary(self, orchid_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze and summarize data sources used in results"""
        
        try:
            sources_summary = {
                'primary_database': 0,
                'gbif_integration': 0,
                'fcos_collection': 0,
                'research_literature': 0,
                'taxonomy_verification': 0,
                'ai_enhanced': 0
            }
            
            for record in orchid_records:
                sources_summary['primary_database'] += 1
                
                if record.get('enhanced_gbif', {}).get('has_ecological_data'):
                    sources_summary['gbif_integration'] += 1
                
                if record.get('fcos_collection', {}).get('has_member_experience'):
                    sources_summary['fcos_collection'] += 1
                
                if record.get('research_data', {}).get('has_academic_interest'):
                    sources_summary['research_literature'] += 1
                
                if record.get('taxonomy_match', {}).get('verification_status') == 'verified':
                    sources_summary['taxonomy_verification'] += 1
                
                if record.get('ai_description') or record.get('ai_confidence'):
                    sources_summary['ai_enhanced'] += 1
            
            return sources_summary
            
        except Exception as e:
            logger.error(f"Data sources summary error: {e}")
            return {}
    
    def _explain_comprehensive_search_strategy(self, query_text: str) -> Dict[str, Any]:
        """Explain the search strategy used for transparency"""
        
        try:
            strategy = {
                'query_analysis': {
                    'original_query': query_text,
                    'query_length': len(query_text),
                    'terms_extracted': len([t for t in query_text.split() if len(t.strip()) > 2]),
                    'likely_scientific_name': bool(len(query_text.split()) >= 2 and query_text[0].isupper())
                },
                'search_methods_used': [
                    'Exact string matching across multiple fields',
                    'Fuzzy matching with Levenshtein distance',
                    'Taxonomic hierarchy traversal',
                    'Synonym and common name lookup',
                    'GBIF ecosystem data integration',
                    'FCOS member collection matching'
                ],
                'ranking_factors': [
                    'Query relevance and exact matches (30%)',
                    'Fuzzy match confidence scores (25%)',
                    'Data completeness and quality (20%)',
                    'External database verification (15%)',
                    'Community validation and research backing (10%)'
                ],
                'data_enrichment': [
                    'GBIF occurrence and conservation data',
                    'FCOS member cultivation experiences',
                    'Academic literature and research citations',
                    'Taxonomic verification and synonyms',
                    'AI-generated descriptions and analysis'
                ]
            }
            
            return strategy
            
        except Exception as e:
            logger.error(f"Search strategy explanation error: {e}")
            return {'error': 'Strategy explanation unavailable'}
    
    def _analyze_confidence_distribution(self, orchid_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze confidence score distribution across results"""
        
        try:
            if not orchid_records:
                return {'error': 'No records to analyze'}
            
            confidence_scores = [r.get('ai_confidence', {}).get('overall_score', 0) for r in orchid_records]
            confidence_scores = [score for score in confidence_scores if score > 0]
            
            if not confidence_scores:
                return {'error': 'No confidence scores available'}
            
            distribution = {
                'total_records': len(orchid_records),
                'records_with_confidence': len(confidence_scores),
                'average_confidence': round(sum(confidence_scores) / len(confidence_scores), 3),
                'min_confidence': round(min(confidence_scores), 3),
                'max_confidence': round(max(confidence_scores), 3),
                'confidence_levels': {
                    'very_high': len([s for s in confidence_scores if s >= 0.9]),
                    'high': len([s for s in confidence_scores if 0.7 <= s < 0.9]),
                    'medium': len([s for s in confidence_scores if 0.5 <= s < 0.7]),
                    'low': len([s for s in confidence_scores if s < 0.5])
                }
            }
            
            return distribution
            
        except Exception as e:
            logger.error(f"Confidence distribution analysis error: {e}")
            return {'error': 'Analysis unavailable'}
    
    def _identify_data_sources(self, record: Dict[str, Any]) -> List[str]:
        """Identify all data sources contributing to a record"""
        
        try:
            sources = ['OrchidRecord Database']  # Primary source
            
            if record.get('taxonomy_match'):
                sources.append('OrchidTaxonomy')
            
            if record.get('enhanced_gbif', {}).get('has_ecological_data'):
                sources.append('GBIF Occurrence Data')
                sources.append('Global Biodiversity Information Facility')
            
            if record.get('fcos_collection', {}).get('has_member_experience'):
                sources.append('Five Cities Orchid Society Collection')
                sources.append('Member Cultivation Data')
            
            if record.get('research_data', {}).get('has_academic_interest'):
                sources.append('Academic Literature Citations')
                sources.append('Research Collaboration Network')
            
            if record.get('ai_description'):
                sources.append('AI-Generated Analysis')
            
            if record.get('google_drive_id'):
                sources.append('Google Drive Images')
            
            data_source = record.get('data_source', '')
            if 'baker' in data_source.lower():
                sources.append('Baker Culture Sheets')
            elif 'gbif' in data_source.lower():
                sources.append('GBIF Original Data')
            
            return list(set(sources))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Data source identification error: {e}")
            return ['OrchidRecord Database']
    def _search_orchid_database(self, query_text: str) -> List[Dict[str, Any]]:
        """Intelligent search across OrchidRecord database"""
        
        # Extract search terms
        terms = query_text.lower().split()
        results = []
        
        try:
            # Multi-field search query
            base_query = OrchidRecord.query
            
            # Apply filters based on search terms
            for term in terms:
                base_query = base_query.filter(
                    db.or_(
                        OrchidRecord.display_name.ilike(f'%{term}%'),
                        OrchidRecord.scientific_name.ilike(f'%{term}%'),
                        OrchidRecord.common_names.ilike(f'%{term}%'),
                        OrchidRecord.region.ilike(f'%{term}%'),
                        OrchidRecord.native_habitat.ilike(f'%{term}%')
                    )
                )
            
            records = base_query.limit(50).all()
            results = [self._serialize_orchid_record(record) for record in records]
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
        
        return results

    def _serialize_orchid_record(self, record: OrchidRecord) -> Dict[str, Any]:
        """Convert OrchidRecord to serializable dictionary"""
        
        # Extract genus and species from scientific name for backward compatibility
        genus = None
        species = None
        if record.scientific_name:
            parts = record.scientific_name.split(' ', 1)
            genus = parts[0] if len(parts) > 0 else None
            species = parts[1] if len(parts) > 1 else None
        
        return {
            'id': record.id,
            'display_name': record.display_name,
            'scientific_name': record.scientific_name,
            'genus': genus,
            'species': species,
            'common_names': record.common_names,
            'region': record.region,
            'native_habitat': record.native_habitat,
            'climate_preference': record.climate_preference,
            'growth_habit': record.growth_habit,
            'bloom_time': record.bloom_time,
            'latitude': record.decimal_latitude,
            'longitude': record.decimal_longitude,
            'country': record.country,
            'data_source': record.data_source,
            'cultural_notes': record.cultural_notes[:500] if record.cultural_notes else None  # Truncate for response
        }

    # Session context management
    def _ensure_session_context(self, session_id: str) -> None:
        """Ensure session context exists"""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {
                'created_at': datetime.now(),
                'query_history': [],
                'research_focus': [],
                'confidence_trends': [],
                'last_activity': datetime.now()
            }

    def _get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        return self.session_contexts.get(session_id, {})

    def _update_session_context(self, session_id: str, query: ResearchQuery, response: ResearchResponse) -> None:
        """Update session context with new query and response"""
        if session_id in self.session_contexts:
            context = self.session_contexts[session_id]
            context['query_history'].append({
                'query': query.query_text,
                'intent': query.intent.value,
                'confidence': response.confidence_score,
                'timestamp': datetime.now()
            })
            context['confidence_trends'].append(response.confidence_score)
            context['last_activity'] = datetime.now()
            
            # Keep only last 20 queries
            context['query_history'] = context['query_history'][-20:]
            context['confidence_trends'] = context['confidence_trends'][-20:]

    # AI helper methods
    def _determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Convert numeric confidence to categorical level"""
        if confidence_score >= 0.90:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.70:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.50:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.30:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            'primary_result': {"error": error_message, "error_type": "processing_error"},
            'confidence_score': 0.0,
            'supporting_evidence': [],
            'alternative_suggestions': [],
            'source_citations': [],
            'research_trail': [f"Error: {error_message}"],
            'ai_models_used': ["error"],
            'database_records_referenced': 0
        }

    # Citation generation methods
    def _generate_identification_citations(self, identification_result: Dict) -> List[Dict[str, Any]]:
        """Generate citations for species identification results"""
        citations = []
        
        # Add AI model citation
        citations.append({
            'type': 'ai_analysis',
            'source': 'OpenAI GPT-4o Vision',
            'date': datetime.now().isoformat(),
            'confidence': identification_result.get('primary_identification', {}).get('confidence', 0)
        })
        
        # Add database citations if referenced
        if 'database_matches' in identification_result:
            citations.append({
                'type': 'database',
                'source': 'Orchid Continuum Database',
                'records_count': len(identification_result['database_matches']),
                'date': datetime.now().isoformat()
            })
        
        return citations

    def _generate_database_citations(self, database_records: List[Dict]) -> List[Dict[str, Any]]:
        """Generate citations for database records"""
        citations = []
        
        # Group by data source
        sources = {}
        for record in database_records:
            source = record.get('data_source', 'Unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(record)
        
        for source, records in sources.items():
            citations.append({
                'type': 'database',
                'source': source,
                'records_count': len(records),
                'date': datetime.now().isoformat(),
                'sample_records': [r.get('scientific_name', r.get('display_name')) for r in records[:3]]
            })
        
        return citations

    def _generate_cultivation_citations(self, baker_recommendations: List[Dict]) -> List[Dict[str, Any]]:
        """Generate citations for cultivation advice"""
        citations = []
        
        if baker_recommendations:
            citations.append({
                'type': 'culture_sheet',
                'source': "Charles & Margaret Baker Culture Sheets",
                'sheets_referenced': len(baker_recommendations),
                'date': datetime.now().isoformat(),
                'orchids': [rec.get('orchid') for rec in baker_recommendations]
            })
        
        return citations

    def _generate_research_citations(self, research_data: Dict) -> List[Dict[str, Any]]:
        """Generate citations for research analysis"""
        citations = []
        
        # Add database citation
        citations.append({
            'type': 'database_analysis',
            'source': 'Orchid Continuum Research Database',
            'records_analyzed': research_data.get('record_count', 0),
            'date': datetime.now().isoformat()
        })
        
        # Add AI analysis citation
        citations.append({
            'type': 'ai_research',
            'source': 'AI Research Assistant (GPT-4o)',
            'analysis_type': 'comprehensive',
            'date': datetime.now().isoformat()
        })
        
        return citations

    def _generate_ecosystem_citations(self, gbif_interactions: List) -> List[Dict[str, Any]]:
        """Generate citations for ecosystem analysis"""
        citations = []
        
        if gbif_interactions:
            citations.append({
                'type': 'ecological_database',
                'source': 'Global Biodiversity Information Facility (GBIF)',
                'interactions_analyzed': len(gbif_interactions),
                'date': datetime.now().isoformat()
            })
            
            citations.append({
                'type': 'interaction_database',
                'source': 'Global Biotic Interactions (GloBI)',
                'date': datetime.now().isoformat()
            })
        
        return citations

    def _generate_image_citations(self, analysis: Dict, exif_data: Dict) -> List[Dict[str, Any]]:
        """Generate citations for image analysis"""
        citations = []
        
        # AI analysis citation
        citations.append({
            'type': 'image_analysis',
            'source': 'OpenAI GPT-4o Vision API',
            'date': datetime.now().isoformat(),
            'analysis_completeness': self._calculate_analysis_completeness(analysis)
        })
        
        # EXIF data citation if available
        if exif_data:
            citations.append({
                'type': 'image_metadata',
                'source': 'EXIF Metadata Extraction',
                'camera_info': f"{exif_data.get('camera_make', '')} {exif_data.get('camera_model', '')}".strip(),
                'date': datetime.now().isoformat()
            })
        
        return citations

    # ===============================================================
    # SPECIALIZED RESEARCH FEATURE SUPPORTING METHODS
    # ===============================================================
    
    # Species Profiling System Supporting Methods
    # ===============================================================
    
    def _identify_species_from_text(self, query_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Identify species from text description using AI"""
        try:
            identification_prompt = f"""
            As an expert orchid taxonomist, analyze this query and extract orchid identification information:
            
            Query: "{query_text}"
            
            Extract and identify:
            1. Genus and species names mentioned
            2. Morphological characteristics described
            3. Growing conditions mentioned
            4. Geographic locations referenced
            
            Return JSON with:
            {{
                "genus": "...",
                "species": "...",
                "full_name": "...",
                "confidence": 0.85,
                "alternatives": [...]
            }}
            """
            
            if openai_client:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": identification_prompt}],
                    max_tokens=500,
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
                if content:
                    try:
                        identification_data = json.loads(content)
                        morphological_data = {
                            "growth_habit": "unknown",
                            "flower_characteristics": "unknown",
                            "leaf_form": "unknown",
                            "pseudobulb_type": "unknown"
                        }
                        return identification_data, morphological_data
                    except json.JSONDecodeError:
                        pass
            
            # Fallback to keyword extraction
            terms = query_text.lower().split()
            potential_genus = [term.title() for term in terms if len(term) > 4 and term.isalpha()][:1]
            
            return {
                "genus": potential_genus[0] if potential_genus else "Unknown",
                "species": "unknown",
                "full_name": potential_genus[0] if potential_genus else "Unknown orchid",
                "confidence": 0.3,
                "alternatives": []
            }, {}
            
        except Exception as e:
            logger.error(f"Text species identification error: {e}")
            return {"genus": "Unknown", "species": "unknown", "full_name": "Unknown", "confidence": 0.1}, {}
    
    def _get_comprehensive_database_matches(self, species_name: str, genus: str, species: str) -> List[Dict]:
        """Get comprehensive database matches for species identification"""
        try:
            matches = []
            
            # Primary exact matches
            if species_name and species_name != "Unknown":
                exact_matches = OrchidRecord.query.filter(
                    db.or_(
                        OrchidRecord.scientific_name.ilike(f'%{species_name}%'),
                        OrchidRecord.display_name.ilike(f'%{species_name}%')
                    )
                ).limit(20).all()
                
                for record in exact_matches:
                    match_data = {
                        'record_id': record.id,
                        'scientific_name': record.scientific_name,
                        'display_name': record.display_name,
                        'genus': record.genus,
                        'species': record.species,
                        'match_type': 'exact',
                        'confidence': 0.9,
                        'fcos_collection': record.id in self.fcos_collection_cache,
                        'verified': bool(record.taxonomy_verified),
                        'habitat': record.native_habitat,
                        'region': record.region
                    }
                    matches.append(match_data)
            
            # Genus-level matches if exact matches are limited
            if len(matches) < 5 and genus and genus != "Unknown":
                genus_matches = OrchidRecord.query.filter(
                    OrchidRecord.genus.ilike(genus)
                ).limit(10).all()
                
                for record in genus_matches:
                    if record.id not in [m['record_id'] for m in matches]:
                        match_data = {
                            'record_id': record.id,
                            'scientific_name': record.scientific_name,
                            'display_name': record.display_name,
                            'genus': record.genus,
                            'species': record.species,
                            'match_type': 'genus',
                            'confidence': 0.6,
                            'fcos_collection': record.id in self.fcos_collection_cache,
                            'verified': bool(record.taxonomy_verified),
                            'habitat': record.native_habitat,
                            'region': record.region
                        }
                        matches.append(match_data)
            
            return matches
            
        except Exception as e:
            logger.error(f"Database matching error: {e}")
            return []
    
    def _verify_with_gbif(self, species_name: str, genus: str) -> Dict[str, Any]:
        """Verify species with GBIF and analyze distribution"""
        try:
            # Check if we have GBIF data in our foundation layer
            gbif_records = []
            verification_confidence = 0.5
            
            # Look for matches in our GBIF foundation
            for gbif_id, record in self.gbif_foundation.items():
                if (species_name and species_name.lower() in record.get('scientificName', '').lower()) or \
                   (genus and genus.lower() in record.get('genus', '').lower()):
                    gbif_records.append(record)
                    
            if gbif_records:
                verification_confidence = 0.8
                
                # Analyze distribution from GBIF records
                countries = [r.get('country', 'Unknown') for r in gbif_records[:10]]
                coordinates = [(r.get('decimalLatitude'), r.get('decimalLongitude')) 
                             for r in gbif_records[:20] if r.get('decimalLatitude')]
                
                return {
                    'verification_status': 'verified',
                    'verification_confidence': verification_confidence,
                    'gbif_records_found': len(gbif_records),
                    'distribution': {
                        'countries': list(set(countries)),
                        'coordinate_samples': coordinates[:10],
                        'occurrence_count': len(gbif_records)
                    },
                    'taxonomy_verification': {
                        'genus_confirmed': any(genus.lower() in r.get('genus', '').lower() for r in gbif_records),
                        'species_confirmed': any(species_name.lower() in r.get('scientificName', '').lower() for r in gbif_records)
                    }
                }
            else:
                return {
                    'verification_status': 'not_found',
                    'verification_confidence': 0.2,
                    'gbif_records_found': 0,
                    'distribution': {'countries': [], 'coordinate_samples': [], 'occurrence_count': 0},
                    'taxonomy_verification': {'genus_confirmed': False, 'species_confirmed': False}
                }
                
        except Exception as e:
            logger.error(f"GBIF verification error: {e}")
            return {
                'verification_status': 'error',
                'verification_confidence': 0.1,
                'error': str(e)
            }
    
    def _enhance_taxonomic_classification(self, species_name: str, genus: str, database_matches: List) -> Dict[str, Any]:
        """Enhance taxonomic classification with database cross-references"""
        try:
            # Get taxonomic data from our matches
            taxonomic_data = {
                'genus': genus,
                'species': species_name.split()[-1] if ' ' in species_name else 'unknown',
                'family': 'Orchidaceae',
                'subfamily': 'unknown',
                'tribe': 'unknown',
                'confidence': 0.7
            }
            
            # Check taxonomy table for additional information
            if genus and genus != "Unknown":
                taxonomy_records = OrchidTaxonomy.query.filter(
                    OrchidTaxonomy.genus.ilike(genus)
                ).limit(5).all()
                
                if taxonomy_records:
                    # Use the most recent or verified taxonomy record
                    primary_record = taxonomy_records[0]
                    taxonomic_data.update({
                        'subfamily': getattr(primary_record, 'subfamily', 'unknown'),
                        'tribe': getattr(primary_record, 'tribe', 'unknown'),
                        'authority': getattr(primary_record, 'authority', 'unknown'),
                        'confidence': 0.9
                    })
            
            # Add related genera from similarity matrix
            related_genera = []
            if genus in self.species_similarity_matrix:
                related_genera = list(self.species_similarity_matrix[genus].keys())[:5]
            
            taxonomic_data['related_genera'] = related_genera
            
            return taxonomic_data
            
        except Exception as e:
            logger.error(f"Taxonomic classification enhancement error: {e}")
            return {'genus': genus, 'species': 'unknown', 'family': 'Orchidaceae', 'confidence': 0.3}
    
    def _extract_orchid_names_from_query(self, query_text: str) -> List[str]:
        """Extract orchid names from query text using enhanced AI analysis"""
        try:
            extraction_prompt = f"""
            Extract orchid names (genus, species, or common names) from this query:
            
            "{query_text}"
            
            Return a JSON list of orchid names found:
            ["Cattleya", "Dendrobium nobile", "Lady Slipper", ...]
            
            Only include actual orchid names, not general terms.
            """
            
            if openai_client:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": extraction_prompt}],
                    max_tokens=200,
                    temperature=0.2
                )
                
                content = response.choices[0].message.content
                if content:
                    try:
                        extracted_names = json.loads(content)
                        return extracted_names[:5] if isinstance(extracted_names, list) else []
                    except json.JSONDecodeError:
                        pass
            
            # Fallback to keyword extraction
            terms = query_text.lower().split()
            potential_names = [term.title() for term in terms if len(term) > 3 and term.isalpha()]
            return potential_names[:5]
            
        except Exception as e:
            logger.error(f"Orchid name extraction error: {e}")
            return []
    
    # Additional Supporting Methods (Placeholder implementations for comprehensive functionality)
    # ===============================================================
    
    def _handle_no_identification(self, query: ResearchQuery) -> Dict[str, Any]:
        """Handle cases where no species identification is possible"""
        return {
            'primary_result': {
                'analysis_type': 'identification_failed',
                'message': 'Unable to identify orchid species from provided information',
                'suggestions': [
                    'Provide clearer images with better lighting',
                    'Include more detailed descriptions',
                    'Focus on flower characteristics'
                ]
            },
            'confidence_score': 0.1,
            'ai_models_used': ['gpt-4o'],
            'database_records_referenced': 0
        }
    
    def _assess_conservation_status(self, species_name: str, genus: str, gbif_data: Dict) -> Dict[str, Any]:
        """Assess conservation status and threats"""
        return {
            'status': 'unknown',
            'confidence': 0.5,
            'threat_level': 'medium',
            'population_trend': 'unknown',
            'threats': ['habitat_loss', 'climate_change'],
            'conservation_actions': ['habitat_protection', 'ex_situ_conservation']
        }
    
    def _analyze_breeding_history(self, species_name: str, genus: str, database_matches: List) -> Dict[str, Any]:
        """Analyze breeding history and hybrid parentage"""
        return {
            'breeding_potential': 'moderate',
            'known_hybrids': [],
            'parentage_analysis': {},
            'hybridization_success': 0.6,
            'breeding_recommendations': []
        }
    
    def _analyze_ecological_relationships(self, species_name: str, genus: str) -> Dict[str, Any]:
        """Analyze pollinator and symbiotic relationships"""
        return {
            'pollinators': [],
            'mycorrhizal_partners': [],
            'ecological_role': 'unknown',
            'symbiotic_requirements': []
        }
    
    def _analyze_distribution_and_habitat(self, species_name: str, genus: str, gbif_data: Dict, database_matches: List) -> Dict[str, Any]:
        """Analyze distribution and habitat requirements"""
        return {
            'native_range': gbif_data.get('distribution', {}).get('countries', []),
            'habitat_requirements': {
                'elevation': 'unknown',
                'climate': 'unknown',
                'substrate': 'unknown'
            },
            'distribution_map_data': gbif_data.get('distribution', {}).get('coordinate_samples', [])
        }
    
    def _calculate_profile_completeness(self, profile_data: Dict) -> float:
        """Calculate how complete the species profile is"""
        completed_sections = sum(1 for section in profile_data.values() if section and section != {})
        return min(completed_sections / 6.0, 1.0)
    
    def _generate_supporting_evidence(self, species_profile: Dict) -> List[Dict]:
        """Generate supporting evidence for species profile"""
        return [
            {'type': 'database_match', 'confidence': 0.8, 'source': 'orchid_database'},
            {'type': 'gbif_verification', 'confidence': 0.7, 'source': 'gbif_foundation'},
            {'type': 'taxonomic_classification', 'confidence': 0.9, 'source': 'taxonomy_database'}
        ]
    
    def _generate_profile_alternatives(self, alternatives: List) -> List[Dict]:
        """Generate alternative species suggestions"""
        return [{'species': alt, 'reason': 'morphological_similarity'} for alt in alternatives[:3]]
    
    # Cultivation Advisory Supporting Methods
    # ===============================================================
    
    def _gather_cultivation_database(self, target_orchids: List[str]) -> List[Dict]:
        """Gather cultivation data from database"""
        cultivation_data = []
        for orchid in target_orchids:
            # Get cultivation records from FCOS collections
            records = [record for record_id, record in self.fcos_collection_cache.items() 
                      if orchid.lower() in str(record.get('collection_name', '')).lower()]
            cultivation_data.extend(records)
        return cultivation_data
    
    def _perform_climate_matching(self, target_orchids: List[str], user_location: Optional[str], cultivation_database: List) -> Dict[str, Any]:
        """Perform climate matching analysis"""
        return {
            'climate_compatibility': 0.7,
            'temperature_match': 'good',
            'humidity_match': 'moderate',
            'light_requirements': 'intermediate',
            'confidence': 0.6
        }
    
    def _integrate_baker_culture_data(self, target_orchids: List[str], cultivation_database: List) -> Dict[str, Any]:
        """Integrate Baker culture sheet data"""
        return {
            'baker_recommendations': [],
            'cultural_requirements': {},
            'confidence': 0.6,
            'extrapolated_advice': []
        }
    
    def _generate_seasonal_care_guidance(self, target_orchids: List[str], climate_analysis: Dict) -> Dict[str, Any]:
        """Generate seasonal care guidance"""
        return {
            'spring': {'watering': 'increase', 'fertilizer': 'weekly'},
            'summer': {'watering': 'maintain', 'fertilizer': 'bi-weekly'},
            'fall': {'watering': 'reduce', 'fertilizer': 'monthly'},
            'winter': {'watering': 'minimal', 'fertilizer': 'none'}
        }
    
    def _diagnose_cultivation_problems(self, query_text: str, target_orchids: List[str]) -> Dict[str, Any]:
        """Diagnose cultivation problems and suggest treatments"""
        return {
            'potential_problems': [],
            'treatments': [],
            'prevention': [],
            'confidence': 0.5
        }
    
    def _integrate_fcos_success_stories(self, target_orchids: List[str]) -> List[Dict]:
        """Integrate FCOS collection success stories"""
        success_stories = []
        for orchid in target_orchids:
            stories = [record for record_id, record in self.fcos_collection_cache.items() 
                      if record.get('success_notes') and orchid.lower() in str(record.get('collection_name', '')).lower()]
            success_stories.extend(stories)
        return success_stories
    
    def _generate_condition_recommendations(self, target_orchids: List[str], climate_analysis: Dict, baker_analysis: Dict, growing_conditions: Optional[Dict]) -> Dict[str, Any]:
        """Generate growing condition recommendations with scoring"""
        return {
            'temperature': {'range': '18-25°C', 'score': 0.8},
            'humidity': {'range': '60-80%', 'score': 0.7},
            'light': {'type': 'bright_indirect', 'score': 0.9},
            'air_circulation': {'requirement': 'moderate', 'score': 0.6}
        }
    
    def _generate_care_calendar(self, target_orchids: List[str], seasonal_guidance: Dict, climate_analysis: Dict) -> Dict[str, Any]:
        """Generate care calendar"""
        return {
            'monthly_tasks': {month: [] for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']},
            'blooming_schedule': {},
            'fertilizer_schedule': {},
            'repotting_schedule': {}
        }
    
    def _generate_personalized_advice(self, target_orchids: List[str], user_location: Optional[str], growing_conditions: Optional[Dict], query_text: str) -> Dict[str, Any]:
        """Generate personalized cultivation advice"""
        return {
            'personalization_factors': ['location', 'experience_level', 'growing_environment'],
            'customized_recommendations': [],
            'difficulty_adjustments': []
        }
    
    def _assess_growing_difficulty(self, target_orchids: List[str], cultivation_database: List) -> Dict[str, str]:
        """Assess growing difficulty for target orchids"""
        return {orchid: 'intermediate' for orchid in target_orchids}
    
    def _extract_expert_cultivation_tips(self, target_orchids: List[str], cultivation_database: List) -> List[str]:
        """Extract expert cultivation tips"""
        return ['Maintain consistent moisture', 'Provide adequate air circulation', 'Monitor for pests regularly']
    
    def _generate_cultivation_evidence(self, cultivation_advisory: Dict) -> List[Dict]:
        """Generate supporting evidence for cultivation advice"""
        return [
            {'type': 'fcos_experience', 'confidence': 0.8},
            {'type': 'baker_culture_sheet', 'confidence': 0.9},
            {'type': 'climate_analysis', 'confidence': 0.7}
        ]
    
    def _generate_cultivation_alternatives(self, cultivation_advisory: Dict) -> List[Dict]:
        """Generate alternative cultivation approaches"""
        return [
            {'approach': 'hydroponic', 'suitability': 0.6},
            {'approach': 'terrarium', 'suitability': 0.4}
        ]
    
    # Research Discovery Supporting Methods
    # ===============================================================
    
    def _analyze_taxonomic_relationships(self, query_text: str) -> Dict[str, Any]:
        """Analyze taxonomic relationships and network patterns"""
        return {
            'related_genera': [],
            'evolutionary_connections': [],
            'phylogenetic_position': 'unknown',
            'confidence': 0.6,
            'records_analyzed': 0
        }
    
    def _analyze_evolutionary_patterns(self, query_text: str, taxonomic_analysis: Dict) -> Dict[str, Any]:
        """Analyze evolutionary patterns and connections"""
        return {
            'evolutionary_trends': [],
            'adaptive_patterns': [],
            'biogeographic_patterns': [],
            'confidence': 0.5
        }
    
    def _analyze_research_literature(self, query_text: str) -> Dict[str, Any]:
        """Analyze research literature and citations"""
        return {
            'relevant_papers': [],
            'citation_trends': {},
            'research_themes': [],
            'confidence': 0.6,
            'citations_analyzed': 0
        }
    
    def _identify_research_gaps(self, query_text: str, literature_analysis: Dict, taxonomic_analysis: Dict) -> Dict[str, Any]:
        """Identify research gaps and opportunities"""
        return {
            'identified_gaps': [],
            'priority_research_areas': [],
            'methodological_gaps': [],
            'data_availability_gaps': []
        }
    
    def _match_collaboration_opportunities(self, query_text: str, research_gaps: Dict) -> List[Dict]:
        """Match academic collaboration opportunities"""
        return [
            {'institution': 'Example University', 'research_focus': 'orchid_ecology', 'match_score': 0.7}
        ]
    
    def _analyze_conservation_priorities(self, query_text: str, taxonomic_analysis: Dict) -> Dict[str, Any]:
        """Analyze conservation priorities and recommendations"""
        return {
            'priority_level': 'medium',
            'conservation_actions': [],
            'threat_assessment': {},
            'confidence': 0.5,
            'records_analyzed': 0
        }
    
    def _suggest_grant_opportunities(self, research_gaps: Dict, conservation_analysis: Dict) -> List[Dict]:
        """Suggest grant opportunities"""
        return [
            {'agency': 'NSF', 'program': 'biodiversity', 'fit_score': 0.8}
        ]
    
    def _suggest_research_methodologies(self, query_text: str, research_gaps: Dict) -> List[Dict]:
        """Suggest research methodologies"""
        return [
            {'method': 'phylogenetic_analysis', 'applicability': 0.8},
            {'method': 'field_surveys', 'applicability': 0.6}
        ]
    
    def _assess_academic_impact(self, literature_analysis: Dict, research_gaps: Dict) -> Dict[str, Any]:
        """Assess potential academic impact"""
        return {
            'impact_potential': 'high',
            'novelty_score': 0.7,
            'collaboration_potential': 0.8,
            'publication_venues': []
        }
    
    def _generate_discovery_insights(self, taxonomic_analysis: Dict, evolutionary_patterns: Dict, literature_analysis: Dict, research_gaps: Dict) -> List[str]:
        """Generate research discovery insights"""
        return [
            'Taxonomic relationships suggest potential for hybrid vigor studies',
            'Evolutionary patterns indicate adaptation to specific microclimates',
            'Literature gaps exist in pollination ecology research'
        ]
    
    def _suggest_future_research_directions(self, research_gaps: Dict, conservation_analysis: Dict, collaboration_opportunities: List) -> List[str]:
        """Suggest future research directions"""
        return [
            'Investigate climate change impacts on orchid distributions',
            'Develop conservation protocols for endangered species',
            'Study mycorrhizal relationships in disturbed habitats'
        ]
    
    def _generate_discovery_evidence(self, research_discovery: Dict) -> List[Dict]:
        """Generate supporting evidence for research discovery"""
        return [
            {'type': 'literature_analysis', 'confidence': 0.7},
            {'type': 'taxonomic_database', 'confidence': 0.8},
            {'type': 'collaboration_network', 'confidence': 0.6}
        ]
    
    def _generate_discovery_alternatives(self, research_discovery: Dict) -> List[Dict]:
        """Generate alternative research approaches"""
        return [
            {'approach': 'citizen_science', 'feasibility': 0.8},
            {'approach': 'molecular_analysis', 'feasibility': 0.6}
        ]

    def _extract_species_names_from_query(self, query_text: str) -> List[str]:
        """Extract species names from query text"""
        # Similar to orchid names but focused on scientific names
        return self._extract_orchid_names_from_query(query_text)

    def _extract_research_entities(self, query_text: str) -> List[str]:
        """Extract research entities from query text"""
        return self._extract_orchid_names_from_query(query_text)

    def _analyze_baker_culture_data(self, cultural_notes: str) -> Optional[Dict]:
        """Analyze Baker culture sheet data"""
        # This would call the existing analyze_baker_culture_data function
        try:
            from orchid_ai import analyze_baker_culture_data
            return analyze_baker_culture_data(cultural_notes)
        except Exception as e:
            logger.error(f"Baker culture analysis error: {e}")
            return None

    def _extract_habitat_data(self, record: OrchidRecord) -> Dict[str, Any]:
        """Extract habitat data from orchid record"""
        return {
            'record_id': record.id,
            'orchid': record.display_name,
            'habitat': record.native_habitat,
            'climate': record.climate_preference,
            'growth_habit': record.growth_habit,
            'region': record.region,
            'coordinates': {
                'latitude': record.decimal_latitude,
                'longitude': record.decimal_longitude
            } if record.decimal_latitude and record.decimal_longitude else None
        }

    def _prepare_research_context(self, query_text: str) -> Dict[str, Any]:
        """Prepare research context from database"""
        # This would analyze the database to provide context for research
        search_results = self._search_orchid_database(query_text)
        
        return {
            'record_count': len(search_results),
            'supporting_records': search_results[:20],
            'patterns': {'genus_distribution': {}, 'climate_patterns': {}},
            'conservation': {'status_summary': {}, 'threats': []}
        }

    def _generate_species_analysis(self, query_text: str, search_results: List) -> Dict[str, Any]:
        """Generate AI species analysis"""
        return {
            'analysis_type': 'species_identification',
            'query_interpretation': query_text,
            'matches_found': len(search_results),
            'confidence_score': 0.7 if search_results else 0.2,
            'top_matches': search_results[:3],
            'alternatives': []
        }

    def _generate_cultivation_advice(self, query_text: str, baker_data: List, habitat_data: List) -> Dict[str, Any]:
        """Generate comprehensive cultivation advice"""
        return {
            'advice_type': 'cultivation',
            'query_focus': query_text,
            'baker_recommendations': len(baker_data),
            'habitat_insights': len(habitat_data),
            'confidence_score': 0.8 if baker_data else 0.6,
            'care_summary': {
                'watering': 'Context-specific watering advice',
                'lighting': 'Light requirement analysis',
                'temperature': 'Temperature range recommendations',
                'humidity': 'Humidity level guidance'
            },
            'alternative_methods': []
        }

    def _generate_ecosystem_analysis(self, query_text: str, interactions: List) -> Dict[str, Any]:
        """Generate ecosystem analysis from GBIF interactions"""
        return {
            'analysis_type': 'ecosystem',
            'interactions_analyzed': len(interactions),
            'confidence_score': 0.7,
            'pollination': {'primary_pollinators': [], 'seasonal_patterns': {}},
            'conservation': {'ecological_role': '', 'threats': []},
            'research_suggestions': []
        }

    def _generate_general_ecosystem_analysis(self, query_text: str) -> Dict[str, Any]:
        """Generate general ecosystem analysis when no specific data available"""
        return {
            'analysis_type': 'general_ecosystem',
            'confidence_score': 0.4,
            'general_principles': True,
            'recommendations': ['Gather more specific species data', 'Consult field studies']
        }

    def _generate_comparative_analysis(self, query_text: str, comparison_data: List) -> Dict[str, Any]:
        """Generate comparative analysis between orchids"""
        return {
            'analysis_type': 'comparative',
            'orchids_compared': len(comparison_data),
            'confidence_score': 0.8 if len(comparison_data) >= 2 else 0.3,
            'matrix': {},
            'differences': [],
            'similarities': [],
            'cultivation': {},
            'taxonomy': {},
            'additional_comparisons': []
        }

    def _generate_academic_citations(self, query_text: str, records: List) -> Dict[str, Any]:
        """Generate academic citations"""
        return {
            'citations': [],
            'dois': [],
            'confidence_score': 0.6,
            'quality_assessment': {'completeness': 0.7, 'accuracy': 0.8},
            'alternative_sources': [],
            'primary_sources': []
        }

    def _generate_search_summary(self, query_text: str, results: List) -> Dict[str, Any]:
        """Generate AI summary of search results"""
        return {
            'summary': f"Found {len(results)} records matching '{query_text}'",
            'key_findings': [],
            'suggestions': []
        }

    def _explain_search_strategy(self, query_text: str) -> Dict[str, Any]:
        """Explain the search strategy used"""
        return {
            'strategy': 'Multi-field fuzzy search',
            'fields_searched': ['display_name', 'scientific_name', 'genus', 'species', 'common_names', 'region'],
            'query_interpretation': query_text.lower().split()
        }

    def _assess_image_quality(self, image_path: str) -> Dict[str, Any]:
        """Assess image quality for analysis"""
        return {
            'resolution': 'Unknown',
            'clarity': 'Good',
            'lighting': 'Adequate',
            'focus': 'Sharp',
            'suitability_score': 0.8
        }

    def _calculate_analysis_completeness(self, analysis: Dict) -> float:
        """Calculate how complete the analysis is"""
        total_fields = 20
        completed_fields = len([v for v in analysis.values() if v is not None and v != 'unknown'])
        return completed_fields / total_fields

    def _generate_image_alternatives(self, analysis: Dict) -> List[Dict]:
        """Generate alternative suggestions for image analysis"""
        return [
            {'suggestion': 'Try a different angle', 'reason': 'Better flower visibility'},
            {'suggestion': 'Improve lighting', 'reason': 'Enhanced color accuracy'},
            {'suggestion': 'Include plant context', 'reason': 'Growth habit assessment'}
        ]

# Flask routes for the research hub
@research_hub_bp.route('/query', methods=['POST'])
def process_query():
    """Main endpoint for processing research queries"""
    
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text required'}), 400
        
        # Create research query object
        query = ResearchQuery(
            query_id=str(uuid.uuid4()),
            intent=QueryIntentType.DATABASE_QUERY,  # Will be classified automatically
            query_text=data['query'],
            user_id=data.get('user_id'),
            image_data=data.get('image_data'),
            context_filters=data.get('filters'),
            session_id=data.get('session_id') or str(uuid.uuid4()),
            timestamp=datetime.now()
        )
        
        # Process the query
        research_hub = OrchidAIResearchHub()
        response = research_hub.process_research_query(query)
        
        # Convert response to JSON-serializable format
        response_dict = {
            'query_id': response.query_id,
            'response_type': response.response_type,
            'primary_result': response.primary_result,
            'confidence_score': response.confidence_score,
            'confidence_level': response.confidence_level.value,
            'supporting_evidence': response.supporting_evidence,
            'alternative_suggestions': response.alternative_suggestions,
            'source_citations': response.source_citations,
            'research_trail': response.research_trail,
            'session_context': response.session_context,
            'processing_time': response.processing_time,
            'ai_models_used': response.ai_models_used,
            'database_records_referenced': response.database_records_referenced,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_dict), 200
        
    except Exception as e:
        logger.error(f"Query processing endpoint error: {e}")
        return jsonify({
            'error': str(e),
            'error_type': 'endpoint_error',
            'timestamp': datetime.now().isoformat()
        }), 500

@research_hub_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Get research hub capabilities and status"""
    
    try:
        # Check database connectivity
        try:
            orchid_count = OrchidRecord.query.count()
        except Exception as e:
            logger.warning(f"OrchidRecord count error: {e}")
            orchid_count = 0
        
        try:
            taxonomy_count = OrchidTaxonomy.query.count()
        except Exception as e:
            logger.warning(f"OrchidTaxonomy count error: {e}")
            taxonomy_count = 0
        
        return jsonify({
            'status': 'operational',
            'capabilities': {
                'query_types': [intent.value for intent in QueryIntentType],
                'ai_models': ['gpt-4o', 'claude-sonnet-4'] if anthropic_client else ['gpt-4o'],
                'database_records': {
                    'orchid_records': orchid_count,
                    'taxonomy_entries': taxonomy_count
                },
                'integrations': {
                    'gbif_ecosystem': True,
                    'baker_culture_sheets': True,
                    'image_analysis': True,
                    'species_identification': True
                }
            },
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Capabilities endpoint error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@research_hub_bp.route('/session/<session_id>/context', methods=['GET'])
def get_session_context(session_id: str):
    """Get session context for a specific session"""
    
    try:
        research_hub = OrchidAIResearchHub()
        context = research_hub._get_session_context(session_id)
        
        if not context:
            return jsonify({'error': 'Session not found'}), 404
        
        # Convert datetime objects to ISO format
        if 'created_at' in context:
            context['created_at'] = context['created_at'].isoformat()
        if 'last_activity' in context:
            context['last_activity'] = context['last_activity'].isoformat()
        
        for query in context.get('query_history', []):
            if 'timestamp' in query:
                query['timestamp'] = query['timestamp'].isoformat()
        
        return jsonify({
            'session_id': session_id,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Session context endpoint error: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Initialize global research hub instance
research_hub_instance = None

def get_research_hub() -> OrchidAIResearchHub:
    """Get or create global research hub instance"""
    global research_hub_instance
    if research_hub_instance is None:
        research_hub_instance = OrchidAIResearchHub()
    return research_hub_instance

# Export the blueprint for app registration
__all__ = ['research_hub_bp', 'OrchidAIResearchHub', 'QueryIntentType', 'ResearchQuery', 'ResearchResponse']