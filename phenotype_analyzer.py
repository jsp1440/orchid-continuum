#!/usr/bin/env python3
"""
Orchid Phenotypic Variation Analysis System
Uses AI to analyze multiple photos of the same species and detect morphological variations,
mutations, adaptations, and phenotypic traits.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from models import OrchidRecord, db
from app import app
import openai
import base64
import requests
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI client setup
openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

@dataclass
class PhenotypicVariation:
    """Data class for storing phenotypic variation information"""
    trait_name: str
    variation_type: str  # 'color', 'size', 'shape', 'growth_habit', 'flowering', 'mutation'
    description: str
    confidence: float
    specimens_affected: List[int]  # orchid record IDs
    environmental_correlation: Optional[str] = None
    genetic_indicator: Optional[str] = None

@dataclass
class SpeciesAnalysis:
    """Complete analysis results for a species"""
    genus: str
    species: str
    total_specimens: int
    variations: List[PhenotypicVariation]
    morphological_summary: Dict[str, Any]
    mutation_indicators: List[str]
    adaptation_patterns: List[str]
    research_notes: str

class OrchidPhenotypeAnalyzer:
    """Main class for analyzing orchid phenotypic variations"""
    
    def __init__(self):
        self.analysis_cache = {}
        
    def analyze_species_variations(self, genus: str, species: str, max_specimens: int = 50) -> SpeciesAnalysis:
        """
        Analyze all specimens of a given species for phenotypic variations
        """
        logger.info(f"Starting phenotypic analysis for {genus} {species}")
        
        try:
            # Get all specimens of this species
            specimens = OrchidRecord.query.filter(
                func.lower(OrchidRecord.genus) == genus.lower(),
                func.lower(OrchidRecord.species) == species.lower(),
                OrchidRecord.google_drive_id.isnot(None)  # Must have images
            ).limit(max_specimens).all()
            
            if len(specimens) < 2:
                logger.warning(f"Not enough specimens for analysis: {len(specimens)}")
                return None
                
            logger.info(f"Analyzing {len(specimens)} specimens of {genus} {species}")
            
            # Group specimens for comparative analysis
            analysis_groups = self._create_analysis_groups(specimens)
            
            # Perform AI-powered comparative analysis
            variations = []
            for group in analysis_groups:
                group_variations = self._analyze_specimen_group(group)
                variations.extend(group_variations)
            
            # Generate morphological summary
            morphological_summary = self._generate_morphological_summary(specimens, variations)
            
            # Detect potential mutations
            mutation_indicators = self._detect_mutations(specimens, variations)
            
            # Identify adaptation patterns
            adaptation_patterns = self._identify_adaptations(specimens, variations)
            
            # Generate research notes
            research_notes = self._generate_research_notes(genus, species, specimens, variations)
            
            # Create species analysis result
            analysis = SpeciesAnalysis(
                genus=genus,
                species=species,
                total_specimens=len(specimens),
                variations=variations,
                morphological_summary=morphological_summary,
                mutation_indicators=mutation_indicators,
                adaptation_patterns=adaptation_patterns,
                research_notes=research_notes
            )
            
            # Store analysis results in database
            self._store_analysis_results(specimens, analysis)
            
            logger.info(f"Completed analysis: found {len(variations)} variations, {len(mutation_indicators)} potential mutations")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing species {genus} {species}: {e}")
            return None
    
    def _create_analysis_groups(self, specimens: List[OrchidRecord]) -> List[List[OrchidRecord]]:
        """Create groups of specimens for comparative analysis"""
        # Group specimens by similar characteristics for focused comparisons
        groups = []
        
        # Group by collection location if available
        location_groups = {}
        for specimen in specimens:
            location = specimen.country or specimen.region or "unknown"
            if location not in location_groups:
                location_groups[location] = []
            location_groups[location].append(specimen)
        
        # Create comparison groups (compare across locations)
        location_keys = list(location_groups.keys())
        for i, location1 in enumerate(location_keys):
            for j, location2 in enumerate(location_keys[i+1:], i+1):
                if len(location_groups[location1]) > 0 and len(location_groups[location2]) > 0:
                    # Take samples from each location for comparison
                    group = location_groups[location1][:3] + location_groups[location2][:3]
                    groups.append(group)
        
        # Also create a mixed group for general variation analysis
        if len(specimens) > 6:
            mixed_group = specimens[:6]  # Take first 6 for general analysis
            groups.append(mixed_group)
        
        return groups
    
    def _analyze_specimen_group(self, specimens: List[OrchidRecord]) -> List[PhenotypicVariation]:
        """Use AI to analyze a group of specimens for variations"""
        try:
            # Prepare images for AI analysis
            image_data = []
            for specimen in specimens:
                if specimen.google_drive_id:
                    try:
                        image_url = f"https://drive.google.com/uc?export=view&id={specimen.google_drive_id}"
                        response = requests.get(image_url, timeout=30)
                        if response.status_code == 200:
                            image_base64 = base64.b64encode(response.content).decode('utf-8')
                            image_data.append({
                                'id': specimen.id,
                                'base64': image_base64[:100000],  # Limit size
                                'location': specimen.country or specimen.region or 'Unknown',
                                'display_name': specimen.display_name
                            })
                    except Exception as e:
                        logger.warning(f"Could not load image for specimen {specimen.id}: {e}")
            
            if len(image_data) < 2:
                return []
            
            # Create AI prompt for phenotypic analysis
            prompt = self._create_analysis_prompt(specimens, image_data)
            
            # Call OpenAI Vision API
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            *[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img['base64']}"}} for img in image_data[:4]]  # Limit to 4 images
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1  # Low temperature for scientific analysis
            )
            
            # Parse AI response
            analysis_text = response.choices[0].message.content
            variations = self._parse_ai_response(analysis_text, specimens)
            
            return variations
            
        except Exception as e:
            logger.error(f"Error in AI specimen analysis: {e}")
            return []
    
    def _create_analysis_prompt(self, specimens: List[OrchidRecord], image_data: List[Dict]) -> str:
        """Create detailed prompt for AI phenotypic analysis"""
        genus_species = f"{specimens[0].genus} {specimens[0].species}"
        locations = ", ".join(set([img['location'] for img in image_data]))
        
        prompt = f"""
You are a specialized botanist analyzing phenotypic variations in orchids. 
Examine these {len(image_data)} photographs of {genus_species} specimens collected from: {locations}.

ANALYSIS OBJECTIVES:
1. MORPHOLOGICAL VARIATIONS: Compare flower size, shape, color patterns, lip morphology, column structure
2. GROWTH HABITS: Analyze pseudobulb structure, leaf arrangement, root systems if visible
3. FLOWERING CHARACTERISTICS: Compare flower count, inflorescence structure, flower positioning
4. ENVIRONMENTAL ADAPTATIONS: Identify traits that may reflect adaptation to different conditions
5. MUTATION INDICATORS: Spot unusual features that may indicate genetic variations
6. PHENOTYPIC PLASTICITY: Note features that vary within normal species range

For each significant variation found, provide:
- Trait name and type (color/size/shape/growth/flowering/mutation)
- Detailed description of the variation
- Which specimens show this trait (by location or identifying features)
- Confidence level (0.0-1.0)
- Possible biological significance

FORMAT YOUR RESPONSE AS:
VARIATION_1: [trait_type] | [description] | [affected_specimens] | [confidence] | [significance]
VARIATION_2: [trait_type] | [description] | [affected_specimens] | [confidence] | [significance]
...

MORPHOLOGICAL_SUMMARY: [overall morphological diversity assessment]
MUTATION_INDICATORS: [list any potential mutations or unusual features]
ADAPTATION_PATTERNS: [environmental adaptations observed]
RESEARCH_SIGNIFICANCE: [scientific value of these observations]

Focus on scientifically significant variations that would be valuable for orchid research and taxonomy.
"""
        return prompt
    
    def _parse_ai_response(self, response_text: str, specimens: List[OrchidRecord]) -> List[PhenotypicVariation]:
        """Parse AI response into structured phenotypic variations"""
        variations = []
        
        try:
            lines = response_text.split('\n')
            
            for line in lines:
                if line.startswith('VARIATION_'):
                    try:
                        # Parse format: VARIATION_N: type | description | specimens | confidence | significance
                        parts = line.split(':', 1)[1].split('|')
                        if len(parts) >= 4:
                            trait_type = parts[0].strip()
                            description = parts[1].strip()
                            affected_desc = parts[2].strip()
                            confidence = float(parts[3].strip()) if parts[3].strip().replace('.','').isdigit() else 0.7
                            
                            # Map affected specimens (simplified for now)
                            affected_ids = [specimen.id for specimen in specimens[:2]]  # Placeholder logic
                            
                            variation = PhenotypicVariation(
                                trait_name=f"{trait_type.capitalize()} variation",
                                variation_type=trait_type.lower(),
                                description=description,
                                confidence=confidence,
                                specimens_affected=affected_ids
                            )
                            
                            variations.append(variation)
                            
                    except Exception as e:
                        logger.warning(f"Could not parse variation line: {line}, error: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
        
        return variations
    
    def _generate_morphological_summary(self, specimens: List[OrchidRecord], variations: List[PhenotypicVariation]) -> Dict[str, Any]:
        """Generate summary of morphological diversity"""
        return {
            'total_variations': len(variations),
            'variation_types': list(set([v.variation_type for v in variations])),
            'average_confidence': sum([v.confidence for v in variations]) / len(variations) if variations else 0,
            'specimens_analyzed': len(specimens),
            'diversity_score': min(len(variations) * 0.1, 1.0)  # Simple diversity metric
        }
    
    def _detect_mutations(self, specimens: List[OrchidRecord], variations: List[PhenotypicVariation]) -> List[str]:
        """Identify potential mutations from variations"""
        mutations = []
        
        for variation in variations:
            if variation.variation_type == 'mutation' or variation.confidence > 0.8:
                if 'unusual' in variation.description.lower() or 'aberrant' in variation.description.lower():
                    mutations.append(f"{variation.trait_name}: {variation.description}")
        
        return mutations
    
    def _identify_adaptations(self, specimens: List[OrchidRecord], variations: List[PhenotypicVariation]) -> List[str]:
        """Identify environmental adaptations"""
        adaptations = []
        
        # Group specimens by location
        location_groups = {}
        for specimen in specimens:
            location = specimen.country or specimen.region or 'unknown'
            if location not in location_groups:
                location_groups[location] = []
            location_groups[location].append(specimen)
        
        if len(location_groups) > 1:
            adaptations.append(f"Geographic variations observed across {len(location_groups)} locations")
        
        for variation in variations:
            if 'size' in variation.variation_type and variation.confidence > 0.7:
                adaptations.append(f"Size adaptation: {variation.description}")
        
        return adaptations
    
    def _generate_research_notes(self, genus: str, species: str, specimens: List[OrchidRecord], variations: List[PhenotypicVariation]) -> str:
        """Generate comprehensive research notes"""
        notes = []
        
        notes.append(f"Phenotypic analysis of {genus} {species} based on {len(specimens)} specimens.")
        
        if variations:
            notes.append(f"Identified {len(variations)} significant morphological variations.")
            
            # Group by variation type
            type_counts = {}
            for v in variations:
                type_counts[v.variation_type] = type_counts.get(v.variation_type, 0) + 1
            
            for var_type, count in type_counts.items():
                notes.append(f"- {count} {var_type} variations")
        
        # Location diversity
        locations = set([s.country or s.region for s in specimens if s.country or s.region])
        if len(locations) > 1:
            notes.append(f"Specimens collected from {len(locations)} different regions: {', '.join(locations)}.")
        
        notes.append("This analysis contributes to understanding intraspecific variation and potential adaptive responses.")
        
        return " ".join(notes)
    
    def _store_analysis_results(self, specimens: List[OrchidRecord], analysis: SpeciesAnalysis):
        """Store analysis results in the database"""
        try:
            with app.app_context():
                for specimen in specimens:
                    # Update specimen with analysis results
                    specimen.phenotype_variations = [v.trait_name for v in analysis.variations if specimen.id in v.specimens_affected]
                    
                    specimen.morphological_traits = analysis.morphological_summary
                    
                    specimen.variation_analysis = {
                        'analysis_date': datetime.now().isoformat(),
                        'total_variations': len(analysis.variations),
                        'species_analysis_id': f"{analysis.genus}_{analysis.species}",
                        'confidence_scores': [v.confidence for v in analysis.variations if specimen.id in v.specimens_affected]
                    }
                    
                    specimen.mutation_indicators = analysis.mutation_indicators
                    
                    # Calculate overall phenotype confidence
                    relevant_variations = [v for v in analysis.variations if specimen.id in v.specimens_affected]
                    if relevant_variations:
                        specimen.phenotype_confidence = sum([v.confidence for v in relevant_variations]) / len(relevant_variations)
                
                db.session.commit()
                logger.info(f"Stored analysis results for {len(specimens)} specimens")
                
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")
            db.session.rollback()
    
    def get_species_with_multiple_specimens(self, min_specimens: int = 3) -> List[Tuple[str, str, int]]:
        """Get list of species that have multiple specimens for analysis"""
        try:
            with app.app_context():
                results = db.session.query(
                    OrchidRecord.genus,
                    OrchidRecord.species,
                    func.count(OrchidRecord.id).label('count')
                ).filter(
                    OrchidRecord.genus.isnot(None),
                    OrchidRecord.species.isnot(None),
                    OrchidRecord.genus != '',
                    OrchidRecord.species != '',
                    OrchidRecord.google_drive_id.isnot(None)
                ).group_by(
                    OrchidRecord.genus,
                    OrchidRecord.species
                ).having(
                    func.count(OrchidRecord.id) >= min_specimens
                ).order_by(
                    func.count(OrchidRecord.id).desc()
                ).all()
                
                return [(r.genus, r.species, r.count) for r in results]
                
        except Exception as e:
            logger.error(f"Error getting species with multiple specimens: {e}")
            return []

# Global analyzer instance
phenotype_analyzer = OrchidPhenotypeAnalyzer()

def analyze_species_variations(genus: str, species: str) -> Optional[SpeciesAnalysis]:
    """Convenience function to analyze species variations"""
    return phenotype_analyzer.analyze_species_variations(genus, species)

def get_analyzable_species(min_specimens: int = 3) -> List[Tuple[str, str, int]]:
    """Get species suitable for phenotypic analysis"""
    return phenotype_analyzer.get_species_with_multiple_specimens(min_specimens)

if __name__ == "__main__":
    # Test the analyzer
    analyzer = OrchidPhenotypeAnalyzer()
    
    # Get species with multiple specimens
    species_list = analyzer.get_species_with_multiple_specimens(2)
    print(f"Found {len(species_list)} species with multiple specimens:")
    
    for genus, species, count in species_list[:5]:
        print(f"- {genus} {species}: {count} specimens")
        
    # Analyze first species as test
    if species_list:
        genus, species, count = species_list[0]
        print(f"\nAnalyzing {genus} {species}...")
        analysis = analyzer.analyze_species_variations(genus, species)
        if analysis:
            print(f"Found {len(analysis.variations)} variations")
            for variation in analysis.variations[:3]:
                print(f"- {variation.trait_name}: {variation.description} (confidence: {variation.confidence:.2f})")