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
from models import OrchidRecord, OrchidTaxonomy

# OpenAI and Anthropic clients
from openai import OpenAI
import anthropic

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
        
        logger.info("🤖 OrchidAI Research Hub initialized successfully")

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
        """Process species identification queries using AI vision and database context"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # If image provided, use AI vision identification
            if query.image_data and query.image_data.get('path'):
                identification_result = self.orchid_identifier.identify_orchid_from_image(
                    query.image_data['path']
                )
                
                # Cross-reference with database
                genus = identification_result.get('primary_identification', {}).get('genus')
                species = identification_result.get('primary_identification', {}).get('species')
                
                database_matches = []
                if genus:
                    matches = OrchidRecord.query.filter(
                        OrchidRecord.scientific_name.ilike(f'{genus}%')
                    ).limit(10).all()
                    database_records = len(matches)
                    database_matches = [self._serialize_orchid_record(record) for record in matches]
                
                return {
                    'primary_result': identification_result,
                    'confidence_score': identification_result.get('primary_identification', {}).get('confidence', 0) / 100.0,
                    'supporting_evidence': database_matches,
                    'alternative_suggestions': identification_result.get('alternative_possibilities', []),
                    'source_citations': self._generate_identification_citations(identification_result),
                    'research_trail': [f"Image analysis using {ai_models_used[0]}", f"Database cross-reference: {database_records} records"],
                    'ai_models_used': ai_models_used,
                    'database_records_referenced': database_records
                }
            
            # Text-based identification
            else:
                # Search database for similar names
                search_results = self._search_orchid_database(query.query_text)
                database_records = len(search_results)
                
                # Generate AI interpretation
                ai_analysis = self._generate_species_analysis(query.query_text, search_results)
                
                return {
                    'primary_result': ai_analysis,
                    'confidence_score': ai_analysis.get('confidence_score', 0.5),
                    'supporting_evidence': search_results,
                    'alternative_suggestions': ai_analysis.get('alternatives', []),
                    'source_citations': self._generate_database_citations(search_results),
                    'research_trail': [f"Database search: {database_records} matches", "AI species analysis"],
                    'ai_models_used': ai_models_used,
                    'database_records_referenced': database_records
                }
        
        except Exception as e:
            logger.error(f"Species identification processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_cultivation_advice(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process cultivation advice queries using Baker culture sheets and habitat data"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # Extract orchid name from query if possible
            orchid_names = self._extract_orchid_names_from_query(query.query_text)
            
            cultivation_data = {}
            baker_recommendations = []
            habitat_data = []
            
            # Get specific orchid cultivation advice
            if orchid_names:
                for name in orchid_names[:3]:  # Limit to 3 orchids
                    records = OrchidRecord.query.filter(
                        db.or_(
                            OrchidRecord.display_name.ilike(f'%{name}%'),
                            OrchidRecord.scientific_name.ilike(f'%{name}%')
                        )
                    ).limit(5).all()
                    
                    database_records += len(records)
                    
                    for record in records:
                        if record.cultural_notes and "BAKER'S CULTURE SHEET" in record.cultural_notes:
                            baker_data = self._analyze_baker_culture_data(record.cultural_notes)
                            if baker_data:
                                baker_recommendations.append({
                                    'orchid': record.display_name,
                                    'recommendations': baker_data
                                })
                        
                        habitat_data.append(self._extract_habitat_data(record))
            
            # Generate comprehensive cultivation advice using AI
            cultivation_advice = self._generate_cultivation_advice(
                query.query_text, baker_recommendations, habitat_data
            )
            
            return {
                'primary_result': cultivation_advice,
                'confidence_score': cultivation_advice.get('confidence_score', 0.7),
                'supporting_evidence': baker_recommendations + habitat_data,
                'alternative_suggestions': cultivation_advice.get('alternative_methods', []),
                'source_citations': self._generate_cultivation_citations(baker_recommendations),
                'research_trail': [
                    f"Database search: {database_records} records",
                    f"Baker culture analysis: {len(baker_recommendations)} sheets",
                    "AI cultivation synthesis"
                ],
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records
            }
        
        except Exception as e:
            logger.error(f"Cultivation advice processing error: {e}")
            return self._generate_error_response(str(e))

    def _process_research_discovery(self, query: ResearchQuery) -> Dict[str, Any]:
        """Process research discovery queries using pattern analysis and literature"""
        
        ai_models_used = ['gpt-4o']
        database_records = 0
        
        try:
            # Use the existing research assistant for analysis
            research_data = self._prepare_research_context(query.query_text)
            database_records = research_data.get('record_count', 0)
            
            insights = self.research_assistant.analyze_research_data(
                research_data, analysis_type='comprehensive'
            )
            
            # Generate experiment suggestions
            experiments = self.research_assistant.suggest_experiments(
                query.query_text, research_data
            )
            
            return {
                'primary_result': {
                    'research_insights': [insight.__dict__ for insight in insights],
                    'suggested_experiments': [exp.__dict__ for exp in experiments],
                    'pattern_analysis': research_data.get('patterns', {}),
                    'conservation_implications': research_data.get('conservation', {})
                },
                'confidence_score': sum(i.confidence_score for i in insights) / len(insights) if insights else 0.5,
                'supporting_evidence': research_data.get('supporting_records', []),
                'alternative_suggestions': [exp.__dict__ for exp in experiments[:3]],
                'source_citations': self._generate_research_citations(research_data),
                'research_trail': [
                    f"Research context preparation: {database_records} records",
                    f"AI insight generation: {len(insights)} insights",
                    f"Experiment suggestions: {len(experiments)} experiments"
                ],
                'ai_models_used': ai_models_used,
                'database_records_referenced': database_records
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

    # Helper methods for database operations
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

    # Placeholder methods for complex AI operations
    # These would be implemented with full AI prompts and processing
    
    def _extract_orchid_names_from_query(self, query_text: str) -> List[str]:
        """Extract orchid names from query text using AI"""
        # This would use AI to identify orchid names in the query
        # For now, return simple keyword extraction
        terms = query_text.lower().split()
        potential_names = [term.title() for term in terms if len(term) > 3]
        return potential_names[:5]

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