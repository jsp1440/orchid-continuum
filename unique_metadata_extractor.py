"""
Enhanced AI-powered unique metadata extraction system
Focuses on finding hard-to-get information like registration dates, awards, breeding history, etc.
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

class UniqueMetadataExtractor:
    """Extract unique, valuable metadata that users can't easily find elsewhere"""
    
    def __init__(self):
        self.openai_client = None
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def extract_comprehensive_unique_metadata(self, orchid_name: str, existing_data: Dict[str, Any] = None, image_url: str = None) -> Dict[str, Any]:
        """
        Extract unique metadata that provides real value to orchid enthusiasts
        
        Args:
            orchid_name: Name of the orchid (display name or scientific name)
            existing_data: Any existing data about the orchid
            image_url: URL of orchid photo for visual analysis
            
        Returns:
            Dictionary containing unique metadata fields
        """
        if not self.openai_client:
            return {'error': 'OpenAI client not available'}
            
        try:
            # Create comprehensive analysis prompt
            unique_metadata_prompt = f"""
            CRITICAL: You are analyzing the orchid "{orchid_name}". 
            Your goal is to extract UNIQUE, HARD-TO-FIND metadata that serious orchid collectors and researchers need.
            
            DO NOT provide generic descriptions like "beautiful orchid with large flowers".
            
            FOCUS EXCLUSIVELY ON finding these specific data points:
            
            1. REGISTRATION INFORMATION:
            - RHS (Royal Horticultural Society) registration number and date
            - AOS (American Orchid Society) registration details
            - Original registrant/hybridizer name
            - Registration year and documentation
            
            2. AWARDS AND RECOGNITION:
            - Specific awards: AM (Award of Merit), HCC (Highly Commended Certificate), FCC (First Class Certificate), etc.
            - Award dates and judging locations
            - Point scores if available
            - Show awards and exhibition recognition
            
            3. BREEDING AND PARENTAGE:
            - Specific parent plants (pod parent × pollen parent)
            - Breeding dates and hybridizer details
            - Generation information (F1, F2, backcross, etc.)
            - Notable offspring or breeding significance
            
            4. CLONE AND NURSERY INFORMATION:
            - Clone designations ('Alba', 'Coerulea', specific cultivar names)
            - Original nursery or grower
            - Notable collections this clone has been in
            - Propagation history if significant
            
            5. HISTORICAL AND COMMERCIAL SIGNIFICANCE:
            - First discovery date and location
            - Historical importance in orchid development
            - Commercial availability and rarity
            - Price history for significant specimens
            
            6. TAXONOMIC UPDATES:
            - Former names or synonyms
            - Recent taxonomic changes
            - Type specimen information
            
            RETURN ONLY factual, specific information. If you cannot find definitive information about any category, mark it as "Not found in available sources" rather than making generic statements.
            
            Format your response as JSON with the following structure:
            {{
                "registration": {{
                    "rhs_number": "string or null",
                    "registration_date": "YYYY-MM-DD or null",
                    "registrant": "string or null",
                    "aos_details": "string or null"
                }},
                "awards": [
                    {{
                        "award_type": "string",
                        "date": "YYYY-MM-DD",
                        "location": "string",
                        "score": "number or null",
                        "details": "string"
                    }}
                ],
                "breeding": {{
                    "pod_parent": "string or null",
                    "pollen_parent": "string or null",
                    "hybridizer": "string or null",
                    "breeding_date": "YYYY or null",
                    "generation": "string or null"
                }},
                "clone_info": {{
                    "clone_name": "string or null",
                    "original_nursery": "string or null",
                    "notable_collections": "array or null",
                    "cultivar_designation": "string or null"
                }},
                "historical_significance": {{
                    "discovery_date": "YYYY-MM-DD or null",
                    "discoverer": "string or null",
                    "significance": "string or null",
                    "commercial_status": "string or null"
                }},
                "taxonomy": {{
                    "former_names": "array or null",
                    "recent_changes": "string or null",
                    "type_specimen": "string or null"
                }},
                "confidence_score": "0.0 to 1.0",
                "sources_available": "boolean",
                "unique_insights_found": "number"
            }}
            """
            
            # Build message content
            messages = [{"role": "user", "content": unique_metadata_prompt}]
            
            # Add image if available for visual confirmation
            if image_url:
                messages[0]["content"] = [
                    {"type": "text", "text": unique_metadata_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            
            # Get AI analysis
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=2000,
                temperature=0.1  # Low temperature for factual accuracy
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse JSON response
            try:
                metadata = json.loads(ai_response)
                
                # Validate and clean the response
                cleaned_metadata = self._validate_and_clean_metadata(metadata, orchid_name)
                
                # Add processing information
                cleaned_metadata['processing_info'] = {
                    'processed_at': datetime.now().isoformat(),
                    'orchid_name': orchid_name,
                    'image_analyzed': image_url is not None,
                    'extraction_success': True
                }
                
                return cleaned_metadata
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                
                # Try to extract structured information from text response
                fallback_metadata = self._extract_metadata_from_text(ai_response, orchid_name)
                return fallback_metadata
                
        except Exception as e:
            logger.error(f"Error in unique metadata extraction: {e}")
            return {
                'error': f'Metadata extraction failed: {str(e)}',
                'processing_info': {
                    'processed_at': datetime.now().isoformat(),
                    'orchid_name': orchid_name,
                    'extraction_success': False
                }
            }
    
    def _validate_and_clean_metadata(self, metadata: Dict[str, Any], orchid_name: str) -> Dict[str, Any]:
        """Validate and clean extracted metadata"""
        
        # Ensure all required sections exist
        required_sections = ['registration', 'awards', 'breeding', 'clone_info', 'historical_significance', 'taxonomy']
        for section in required_sections:
            if section not in metadata:
                metadata[section] = {}
        
        # Clean up null/empty values
        def clean_section(section):
            if isinstance(section, dict):
                return {k: v for k, v in section.items() if v not in [None, "", "null", "Not found", "Unknown"]}
            elif isinstance(section, list):
                return [item for item in section if item not in [None, "", "null", "Not found", "Unknown"]]
            return section
        
        for section in required_sections:
            metadata[section] = clean_section(metadata[section])
        
        # Calculate value score based on unique information found
        unique_insights = 0
        
        # Check for valuable registration info
        if metadata['registration'].get('rhs_number') or metadata['registration'].get('aos_details'):
            unique_insights += 3
            
        # Check for awards
        if metadata['awards'] and len(metadata['awards']) > 0:
            unique_insights += len(metadata['awards']) * 2
            
        # Check for breeding info
        if metadata['breeding'].get('hybridizer') or (metadata['breeding'].get('pod_parent') and metadata['breeding'].get('pollen_parent')):
            unique_insights += 2
            
        # Check for clone information
        if metadata['clone_info'].get('original_nursery') or metadata['clone_info'].get('clone_name'):
            unique_insights += 2
            
        # Check for historical significance
        if metadata['historical_significance'].get('discoverer') or metadata['historical_significance'].get('discovery_date'):
            unique_insights += 2
        
        metadata['unique_insights_found'] = unique_insights
        metadata['value_score'] = min(unique_insights / 10.0, 1.0)  # Normalize to 0-1 scale
        
        return metadata
    
    def _extract_metadata_from_text(self, text_response: str, orchid_name: str) -> Dict[str, Any]:
        """Fallback method to extract metadata from text response if JSON parsing fails"""
        
        metadata = {
            'registration': {},
            'awards': [],
            'breeding': {},
            'clone_info': {},
            'historical_significance': {},
            'taxonomy': {},
            'processing_info': {
                'processed_at': datetime.now().isoformat(),
                'orchid_name': orchid_name,
                'extraction_method': 'text_fallback',
                'extraction_success': True
            },
            'raw_response': text_response[:500]  # Store first 500 chars for debugging
        }
        
        # Use regex to find specific patterns
        patterns = {
            'rhs_registration': r'RHS\s+(?:registration\s+)?(?:number\s+)?:?\s*([A-Z0-9\-]+)',
            'registration_date': r'(?:registered|registration)\s+(?:in\s+)?(\d{4})',
            'award_am': r'AM\s*(?:\(|\s)+(\d{2,3})\s*(?:pts|points)',
            'award_hcc': r'HCC\s*(?:\(|\s)+(\d{2,3})\s*(?:pts|points)',
            'award_fcc': r'FCC\s*(?:\(|\s)+(\d{2,3})\s*(?:pts|points)',
            'hybridizer': r'(?:hybridized|bred|created)\s+by\s+([A-Za-z\s\.]+)',
            'parents': r'([A-Za-z\s\.]+)\s*[×x]\s*([A-Za-z\s\.]+)',
            'clone_name': r"(?:clone\s+|cv\.\s*)'([^']+)'",
            'nursery': r'(?:grown|bred|from)\s+([A-Z][A-Za-z\s]+(?:Nursery|Orchids|Gardens))'
        }
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, text_response, re.IGNORECASE)
            if matches:
                if pattern_name == 'rhs_registration':
                    metadata['registration']['rhs_number'] = matches[0].strip()
                elif pattern_name == 'registration_date':
                    metadata['registration']['registration_date'] = matches[0]
                elif pattern_name.startswith('award_'):
                    award_type = pattern_name.split('_')[1].upper()
                    metadata['awards'].append({
                        'award_type': award_type,
                        'score': int(matches[0]),
                        'details': f'{award_type} {matches[0]} points'
                    })
                elif pattern_name == 'hybridizer':
                    metadata['breeding']['hybridizer'] = matches[0].strip()
                elif pattern_name == 'parents':
                    metadata['breeding']['pod_parent'] = matches[0][0].strip()
                    metadata['breeding']['pollen_parent'] = matches[0][1].strip()
                elif pattern_name == 'clone_name':
                    metadata['clone_info']['clone_name'] = matches[0].strip()
                elif pattern_name == 'nursery':
                    metadata['clone_info']['original_nursery'] = matches[0].strip()
        
        return metadata
    
    def generate_unique_description(self, metadata: Dict[str, Any], orchid_name: str) -> str:
        """Generate a description focused on unique metadata rather than generic characteristics"""
        
        if metadata.get('error'):
            return f"Analysis of {orchid_name} is pending enhanced metadata extraction."
        
        unique_points = []
        
        # Registration information
        if metadata.get('registration', {}).get('rhs_number'):
            reg_info = metadata['registration']
            reg_text = f"RHS registration {reg_info['rhs_number']}"
            if reg_info.get('registration_date'):
                reg_text += f" ({reg_info['registration_date']})"
            if reg_info.get('registrant'):
                reg_text += f" by {reg_info['registrant']}"
            unique_points.append(reg_text)
        
        # Awards
        awards = metadata.get('awards', [])
        if awards:
            award_text = "Awards: " + ", ".join([
                f"{award['award_type']}" + (f" {award['score']}pts" if award.get('score') else "")
                for award in awards[:3]  # Show up to 3 awards
            ])
            unique_points.append(award_text)
        
        # Breeding information
        breeding = metadata.get('breeding', {})
        if breeding.get('pod_parent') and breeding.get('pollen_parent'):
            breeding_text = f"Cross: {breeding['pod_parent']} × {breeding['pollen_parent']}"
            if breeding.get('hybridizer'):
                breeding_text += f" by {breeding['hybridizer']}"
            unique_points.append(breeding_text)
        
        # Clone information
        clone_info = metadata.get('clone_info', {})
        if clone_info.get('clone_name'):
            clone_text = f"Clone '{clone_info['clone_name']}'"
            if clone_info.get('original_nursery'):
                clone_text += f" from {clone_info['original_nursery']}"
            unique_points.append(clone_text)
        
        # Historical significance
        historical = metadata.get('historical_significance', {})
        if historical.get('discoverer') or historical.get('significance'):
            hist_text = ""
            if historical.get('discoverer'):
                hist_text += f"Discovered by {historical['discoverer']}"
            if historical.get('discovery_date'):
                hist_text += f" ({historical['discovery_date']})"
            if historical.get('significance'):
                hist_text += f". {historical['significance']}"
            unique_points.append(hist_text.strip())
        
        # Generate final description
        if unique_points:
            description = f"{orchid_name}: " + " | ".join(unique_points)
            return description[:500]  # Limit length
        else:
            # If no unique metadata found, indicate this clearly
            confidence = metadata.get('confidence_score', 0.0)
            if confidence < 0.3:
                return f"{orchid_name}: Comprehensive metadata analysis in progress. Unique registration, award, and breeding details will be added as they become available."
            else:
                return f"{orchid_name}: Research-grade specimen with detailed analysis pending specialized orchid databases."

if __name__ == "__main__":
    # Test the extractor
    extractor = UniqueMetadataExtractor()
    test_result = extractor.extract_comprehensive_unique_metadata(
        "Laeliacattleya Love",
        existing_data={},
        image_url=None
    )
    
    print("Test result:")
    print(json.dumps(test_result, indent=2))
    
    description = extractor.generate_unique_description(test_result, "Laeliacattleya Love")
    print(f"\nGenerated description: {description}")