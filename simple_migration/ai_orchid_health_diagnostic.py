#!/usr/bin/env python3
"""
AI Orchid Health Diagnostic System
==================================
Advanced orchid health analysis using AI-powered image recognition
Identifies problems, diseases, pests, and provides treatment recommendations
Part of The Orchid Continuum - Specialized grower tools

Features:
- Health problem identification from photos
- Disease and pest detection with confidence scoring
- Treatment recommendations based on problem analysis
- Recovery timeline predictions
- Cross-referencing with successful treatment database
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from PIL import Image
import base64

# OpenAI Vision API integration
from openai import OpenAI

# Database integration  
from app import app, db
from models import OrchidRecord

# Leverage existing AI infrastructure
from ai_orchid_identification import AIOrchidIdentifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIOrchidHealthDiagnostic:
    """
    AI-powered orchid health diagnostic system for identifying and treating problems
    """
    
    def __init__(self):
        # Initialize OpenAI client
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.client = None
        
        if self.openai_key:
            try:
                self.client = OpenAI(api_key=self.openai_key)
                logger.info("✅ OpenAI client initialized for health diagnostics")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI client initialization failed: {e}")
                self.client = None
        else:
            logger.warning("⚠️ OPENAI_API_KEY not set - health diagnostics will have limited functionality")
        
        # Initialize base identifier for species context
        self.species_identifier = AIOrchidIdentifier()
        
        # Health diagnostic expert prompt
        self.health_expert_prompt = """
        You are a world-renowned orchid pathologist and plant health expert with 30+ years of experience treating sick orchids.
        You specialize in identifying orchid health problems, diseases, pests, and environmental stress from photographs.
        
        Your expertise includes:
        - Fungal, bacterial, and viral diseases in orchids
        - Common orchid pests (scale, mealybugs, aphids, spider mites, thrips)
        - Environmental stress symptoms (overwatering, underwatering, light burn, temperature stress)
        - Nutritional deficiencies and fertilizer burn
        - Root rot, crown rot, and other cultural problems
        - Recovery timelines and treatment success rates
        
        Please analyze this orchid photograph for health problems and provide:
        
        1. **Primary Health Assessment**:
           - Overall health status (healthy, mild issues, serious problems, critical condition)
           - Main problem identified (with confidence %)
           - Secondary problems if present
           - Urgency level (low, medium, high, emergency)
        
        2. **Problem Classification**:
           - Problem type (disease, pest, environmental, cultural, nutritional)
           - Specific identification (exact disease/pest name if possible)
           - Affected plant parts (leaves, roots, pseudobulbs, flowers)
           - Severity assessment (1-10 scale)
        
        3. **Symptoms Analysis**:
           - Visible symptoms observed
           - Pattern of damage or discoloration
           - Signs of progression or spreading
           - Environmental indicators visible in photo
        
        4. **Treatment Recommendations**:
           - Immediate actions needed (within 24-48 hours)
           - Specific treatments (fungicides, insecticides, cultural changes)
           - Product recommendations if applicable
           - Isolation requirements
        
        5. **Recovery Prognosis**:
           - Expected recovery timeline
           - Success probability (%)
           - Signs of improvement to watch for
           - When to reassess or seek further help
        
        6. **Prevention Measures**:
           - How to prevent this problem in future
           - Environmental adjustments needed
           - Care routine modifications
           - Early warning signs to monitor
        
        Return your analysis in JSON format:
        {
            "health_assessment": {
                "overall_status": "healthy|mild_issues|serious_problems|critical_condition",
                "primary_problem": "...",
                "confidence": 85,
                "urgency_level": "low|medium|high|emergency",
                "secondary_problems": ["...", "..."]
            },
            "problem_classification": {
                "problem_type": "disease|pest|environmental|cultural|nutritional",
                "specific_identification": "...",
                "affected_parts": ["leaves", "roots", "pseudobulbs"],
                "severity_score": 7
            },
            "symptoms_observed": {
                "primary_symptoms": ["...", "...", "..."],
                "damage_pattern": "...",
                "progression_signs": "...",
                "environmental_factors": "..."
            },
            "treatment_plan": {
                "immediate_actions": ["...", "...", "..."],
                "specific_treatments": ["...", "...", "..."],
                "product_recommendations": ["...", "..."],
                "isolation_needed": true,
                "treatment_frequency": "..."
            },
            "recovery_prognosis": {
                "timeline_days": 14,
                "success_probability": 75,
                "improvement_signs": ["...", "...", "..."],
                "reassessment_date": "2024-01-15"
            },
            "prevention_measures": {
                "environmental_changes": ["...", "...", "..."],
                "care_modifications": ["...", "...", "..."],
                "monitoring_schedule": "...",
                "early_warning_signs": ["...", "...", "..."]
            }
        }
        """
        
        logger.info("🏥 AI Orchid Health Diagnostic system initialized")
    
    def diagnose_orchid_health(self, image_path: str, user_notes: str = "") -> Dict[str, Any]:
        """
        Diagnose orchid health problems from a photo with comprehensive treatment recommendations
        
        Args:
            image_path: Path to the orchid image file showing health issues
            user_notes: Optional user description of symptoms or concerns
            
        Returns:
            Comprehensive health diagnosis and treatment plan
        """
        try:
            logger.info(f"🔍 Analyzing orchid health: {image_path}")
            
            # Check if OpenAI client is available
            if not self.client:
                logger.warning("⚠️ OpenAI client not available - returning limited response")
                return self._create_fallback_response(image_path, user_notes)
            
            # First, try to identify the orchid species for context
            species_context = self._get_species_context(image_path)
            
            # Encode image for OpenAI Vision API
            encoded_image = self._encode_image(image_path)
            
            # Create enhanced prompt with user notes and species context
            enhanced_prompt = self._create_enhanced_prompt(user_notes, species_context)
            
            # Send to OpenAI Vision API for health analysis
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": enhanced_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=2500,
                temperature=0.1  # Low temperature for consistent medical analysis
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            try:
                # Try to parse JSON response
                health_diagnosis = json.loads(ai_response)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured response from text
                health_diagnosis = self._parse_text_health_response(ai_response)
            
            # Enhance diagnosis with database context
            enhanced_diagnosis = self._enhance_with_database_context(health_diagnosis, species_context)
            
            # Add treatment tracking and follow-up scheduling
            treatment_tracking = self._create_treatment_tracking(health_diagnosis)
            
            # Compile final health report
            final_report = {
                "diagnosis_id": self._generate_diagnosis_id(),
                "image_analyzed": image_path,
                "user_notes": user_notes,
                "species_context": species_context,
                "health_diagnosis": enhanced_diagnosis,
                "treatment_tracking": treatment_tracking,
                "analysis_timestamp": datetime.now().isoformat(),
                "follow_up_date": self._calculate_follow_up_date(health_diagnosis),
                "confidence_score": health_diagnosis.get("health_assessment", {}).get("confidence", 0),
                "api_key_available": True
            }
            
            logger.info(f"🏥 Health diagnosis complete - Status: {enhanced_diagnosis.get('health_assessment', {}).get('overall_status', 'unknown')}")
            
            return final_report
            
        except Exception as e:
            logger.error(f"❌ Health diagnosis error: {e}")
            return {
                "error": str(e),
                "success": False,
                "analysis_timestamp": datetime.now().isoformat(),
                "image_analyzed": image_path
            }
    
    def _get_species_context(self, image_path: str) -> Dict[str, Any]:
        """Get orchid species context for more accurate health diagnosis"""
        try:
            identification = self.species_identifier.identify_orchid_from_image(image_path)
            if identification and not identification.get("error"):
                primary_id = identification.get("ai_identification", {}).get("primary_identification", {})
                return {
                    "genus": primary_id.get("genus", "Unknown"),
                    "species": primary_id.get("species", "Unknown"),
                    "full_name": primary_id.get("full_name", "Unknown orchid"),
                    "confidence": primary_id.get("confidence", 0)
                }
        except Exception as e:
            logger.warning(f"Could not identify species for health context: {e}")
        
        return {
            "genus": "Unknown",
            "species": "Unknown", 
            "full_name": "Unknown orchid",
            "confidence": 0
        }
    
    def _create_enhanced_prompt(self, user_notes: str, species_context: Dict[str, Any]) -> str:
        """Create enhanced prompt with user notes and species context"""
        context_info = ""
        if species_context.get("full_name") != "Unknown orchid":
            context_info = f"\n\nOrchid Species Context: This appears to be {species_context['full_name']} (confidence: {species_context['confidence']}%). Please consider species-specific health vulnerabilities in your analysis."
        
        user_info = ""
        if user_notes.strip():
            user_info = f"\n\nUser's Description of Problem: {user_notes.strip()}"
        
        return self.health_expert_prompt + context_info + user_info
    
    def _enhance_with_database_context(self, diagnosis: Dict[str, Any], species_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance diagnosis with database context about similar problems"""
        try:
            with app.app_context():
                genus = species_context.get("genus")
                if genus and genus != "Unknown":
                    # Find similar orchids in database for comparison
                    similar_orchids = OrchidRecord.query.filter_by(genus=genus).limit(5).all()
                    
                    diagnosis["database_context"] = {
                        "similar_orchids_count": len(similar_orchids),
                        "genus_specific_notes": f"Found {len(similar_orchids)} similar {genus} orchids in database",
                        "care_references": [orchid.cultural_notes for orchid in similar_orchids if orchid.cultural_notes][:3]
                    }
                
        except Exception as e:
            logger.warning(f"Could not enhance with database context: {e}")
        
        return diagnosis
    
    def _create_treatment_tracking(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Create treatment tracking schedule based on diagnosis"""
        health_assessment = diagnosis.get("health_assessment", {})
        urgency = health_assessment.get("urgency_level", "medium")
        
        # Calculate check-in schedule based on urgency
        check_intervals = {
            "emergency": [1, 3, 7, 14],      # Days 1, 3, 7, 14
            "high": [2, 5, 10, 21],          # Days 2, 5, 10, 21  
            "medium": [3, 7, 14, 30],        # Days 3, 7, 14, 30
            "low": [7, 14, 30, 60]           # Days 7, 14, 30, 60
        }
        
        intervals = check_intervals.get(urgency, check_intervals["medium"])
        today = datetime.now()
        
        return {
            "tracking_id": self._generate_tracking_id(),
            "urgency_level": urgency,
            "check_in_dates": [
                (today + timedelta(days=interval)).strftime("%Y-%m-%d")
                for interval in intervals
            ],
            "treatment_milestones": {
                "immediate_response": f"Expected within {intervals[0]} days",
                "early_improvement": f"Expected by day {intervals[1]}",
                "significant_progress": f"Expected by day {intervals[2]}",
                "full_recovery": f"Expected by day {intervals[3]}"
            }
        }
    
    def _calculate_follow_up_date(self, diagnosis: Dict[str, Any]) -> str:
        """Calculate recommended follow-up photo date"""
        health_assessment = diagnosis.get("health_assessment", {})
        urgency = health_assessment.get("urgency_level", "medium")
        
        # Follow-up intervals based on urgency
        follow_up_days = {
            "emergency": 1,
            "high": 3, 
            "medium": 7,
            "low": 14
        }
        
        days = follow_up_days.get(urgency, 7)
        follow_up_date = datetime.now() + timedelta(days=days)
        return follow_up_date.strftime("%Y-%m-%d")
    
    def _generate_diagnosis_id(self) -> str:
        """Generate unique diagnosis ID"""
        return f"HEALTH_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(datetime.now()) % 10000:04d}"
    
    def _generate_tracking_id(self) -> str:
        """Generate unique treatment tracking ID"""
        return f"TRACK_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(datetime.now()) % 10000:04d}"
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for OpenAI API"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Image encoding error: {e}")
            raise
    
    def _parse_text_health_response(self, response_text: str) -> Dict[str, Any]:
        """Parse text response into structured format if JSON parsing fails"""
        return {
            "health_assessment": {
                "overall_status": "analysis_pending",
                "primary_problem": "Analysis in progress",
                "confidence": 0,
                "urgency_level": "medium"
            },
            "raw_analysis": response_text,
            "parsing_note": "JSON parsing failed, raw text provided"
        }
    
    def _create_fallback_response(self, image_path: str, user_notes: str) -> Dict[str, Any]:
        """Create fallback response when OpenAI is not available"""
        return {
            "diagnosis_id": self._generate_diagnosis_id(),
            "image_analyzed": image_path,
            "user_notes": user_notes,
            "health_diagnosis": {
                "health_assessment": {
                    "overall_status": "assessment_unavailable",
                    "primary_problem": "AI analysis unavailable - OPENAI_API_KEY not configured",
                    "confidence": 0,
                    "urgency_level": "unknown"
                },
                "limitation": "Full AI health analysis requires OpenAI API key configuration"
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "api_key_available": False
        }

def diagnose_orchid_health_from_photo(image_path: str, user_notes: str = "") -> Dict[str, Any]:
    """
    Main function to diagnose orchid health from a photo
    
    Args:
        image_path: Path to orchid health image
        user_notes: Optional user description of symptoms
        
    Returns:
        Complete health diagnosis and treatment plan
    """
    diagnostic = AIOrchidHealthDiagnostic()
    return diagnostic.diagnose_orchid_health(image_path, user_notes)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        user_notes = sys.argv[2] if len(sys.argv) > 2 else ""
        result = diagnose_orchid_health_from_photo(test_image, user_notes)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python ai_orchid_health_diagnostic.py <image_path> [user_notes]")