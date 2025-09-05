"""
AI-Powered Pattern Analysis and Hypothesis Generation System
Identifies interesting patterns in orchid data and suggests research directions
"""

import os
import openai
import json
import numpy as np
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from app import db
from models import OrchidRecord

logger = logging.getLogger(__name__)

class AIPatternAnalyzer:
    """AI system that identifies patterns and suggests research hypotheses"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        
        # Pattern detection thresholds
        self.geographic_cluster_threshold = 3  # Min species in same region
        self.correlation_threshold = 0.6       # Min correlation strength
        self.ecosystem_similarity_threshold = 0.7
        
    def analyze_data_patterns(self, filters: Dict = None) -> Dict[str, Any]:
        """
        Comprehensive pattern analysis across all orchid data
        Returns interesting patterns with AI-generated research suggestions
        """
        logger.info("🔍 Starting AI pattern analysis...")
        
        try:
            # Get orchid data
            orchid_data = self._get_analysis_data(filters)
            
            if len(orchid_data) < 3:
                return {
                    'error': 'Insufficient data for pattern analysis',
                    'minimum_required': 3,
                    'current_count': len(orchid_data)
                }
            
            patterns = {
                'data_summary': {
                    'total_specimens': len(orchid_data),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'filters_applied': filters or {}
                },
                'geographic_patterns': self._analyze_geographic_patterns(orchid_data),
                'phylogenetic_patterns': self._analyze_phylogenetic_patterns(orchid_data),
                'ecological_patterns': self._analyze_ecological_patterns(orchid_data),
                'temporal_patterns': self._analyze_temporal_patterns(orchid_data),
                'cross_ecosystem_patterns': self._analyze_cross_ecosystem_patterns(orchid_data),
                'ai_insights': {},
                'research_hypotheses': {},
                'interesting_observations': []
            }
            
            # Generate AI insights and hypotheses
            if self.openai_client:
                patterns['ai_insights'] = self._generate_ai_insights(patterns)
                patterns['research_hypotheses'] = self._generate_research_hypotheses(patterns)
                patterns['interesting_observations'] = self._find_interesting_observations(patterns)
            
            logger.info(f"✅ Pattern analysis complete: {len(patterns['interesting_observations'])} interesting patterns found")
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return {'error': str(e)}
    
    def _get_analysis_data(self, filters: Dict = None) -> List[Dict]:
        """Retrieve orchid data optimized for pattern analysis"""
        try:
            query = db.session.query(OrchidRecord)
            
            # Apply filters if provided
            if filters:
                if filters.get('genus'):
                    query = query.filter(OrchidRecord.genus.ilike(f"%{filters['genus']}%"))
                if filters.get('region'):
                    query = query.filter(OrchidRecord.region.ilike(f"%{filters['region']}%"))
                if filters.get('latitude_min'):
                    query = query.filter(OrchidRecord.decimal_latitude >= float(filters['latitude_min']))
                if filters.get('latitude_max'):
                    query = query.filter(OrchidRecord.decimal_latitude <= float(filters['latitude_max']))
            
            orchids = query.all()
            
            # Convert to analysis format
            data = []
            for orchid in orchids:
                data.append({
                    'id': orchid.id,
                    'scientific_name': orchid.scientific_name or f"{orchid.genus} {orchid.species}",
                    'genus': orchid.genus,
                    'species': orchid.species,
                    'latitude': orchid.decimal_latitude,
                    'longitude': orchid.decimal_longitude,
                    'country': orchid.country,
                    'region': orchid.region,
                    'bloom_time': orchid.bloom_time,
                    'growth_habit': orchid.growth_habit,
                    'climate_preference': orchid.climate_preference,
                    'temperature_range': orchid.temperature_range,
                    'elevation': getattr(orchid, 'elevation_indicators', None),
                    'flowering_photo_date': getattr(orchid, 'flowering_photo_date', None),
                    'habitat_description': getattr(orchid, 'native_habitat', None),
                    'cultural_notes': getattr(orchid, 'cultural_notes', None),
                    'created_at': orchid.created_at
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Data retrieval error: {e}")
            return []
    
    def _analyze_geographic_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Find geographic clustering and distribution patterns"""
        patterns = {
            'regional_clusters': {},
            'latitudinal_bands': {},
            'continental_distribution': {},
            'island_biogeography': [],
            'range_overlaps': []
        }
        
        # Group by geographic regions
        regional_groups = defaultdict(list)
        latitudinal_groups = defaultdict(list)
        
        for orchid in data:
            if orchid.get('region'):
                regional_groups[orchid['region']].append(orchid)
            
            if orchid.get('latitude'):
                lat_band = int(orchid['latitude'] / 5) * 5  # 5-degree bands
                latitudinal_groups[lat_band].append(orchid)
        
        # Analyze regional clustering
        for region, orchids in regional_groups.items():
            if len(orchids) >= self.geographic_cluster_threshold:
                genera = set(o['genus'] for o in orchids if o.get('genus'))
                patterns['regional_clusters'][region] = {
                    'specimen_count': len(orchids),
                    'genus_diversity': len(genera),
                    'genera': list(genera),
                    'dominant_genus': max(genera, key=lambda g: sum(1 for o in orchids if o.get('genus') == g)) if genera else None
                }
        
        # Analyze latitudinal patterns
        for lat_band, orchids in latitudinal_groups.items():
            if len(orchids) >= self.geographic_cluster_threshold:
                patterns['latitudinal_bands'][f"{lat_band}°N to {lat_band+5}°N"] = {
                    'specimen_count': len(orchids),
                    'genus_diversity': len(set(o['genus'] for o in orchids if o.get('genus'))),
                    'bloom_seasons': [o.get('bloom_time') for o in orchids if o.get('bloom_time')]
                }
        
        return patterns
    
    def _analyze_phylogenetic_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze genus and species relationships"""
        patterns = {
            'genus_distribution': {},
            'species_richness': {},
            'endemic_candidates': [],
            'widespread_species': []
        }
        
        # Genus analysis
        genus_data = defaultdict(lambda: {
            'species_count': 0,
            'geographic_range': set(),
            'climate_preferences': [],
            'bloom_patterns': []
        })
        
        for orchid in data:
            genus = orchid.get('genus')
            if not genus:
                continue
                
            genus_data[genus]['species_count'] += 1
            if orchid.get('region'):
                genus_data[genus]['geographic_range'].add(orchid['region'])
            if orchid.get('climate_preference'):
                genus_data[genus]['climate_preferences'].append(orchid['climate_preference'])
            if orchid.get('bloom_time'):
                genus_data[genus]['bloom_patterns'].append(orchid['bloom_time'])
        
        # Convert to analysis format
        for genus, info in genus_data.items():
            patterns['genus_distribution'][genus] = {
                'species_count': info['species_count'],
                'geographic_range_size': len(info['geographic_range']),
                'regions': list(info['geographic_range']),
                'climate_diversity': len(set(info['climate_preferences']))
            }
        
        # Identify endemic candidates (single region)
        patterns['endemic_candidates'] = [
            genus for genus, info in patterns['genus_distribution'].items()
            if info['geographic_range_size'] == 1 and info['species_count'] >= 2
        ]
        
        # Identify widespread genera (multiple regions)
        patterns['widespread_species'] = [
            genus for genus, info in patterns['genus_distribution'].items()
            if info['geographic_range_size'] >= 3
        ]
        
        return patterns
    
    def _analyze_ecological_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Find ecological niche and adaptation patterns"""
        patterns = {
            'climate_associations': {},
            'elevation_patterns': {},
            'substrate_preferences': {},
            'growth_habit_correlations': {}
        }
        
        # Climate pattern analysis
        climate_groups = defaultdict(list)
        for orchid in data:
            climate = orchid.get('climate_preference')
            if climate:
                climate_groups[climate].append(orchid)
        
        for climate, orchids in climate_groups.items():
            genera = [o['genus'] for o in orchids if o.get('genus')]
            patterns['climate_associations'][climate] = {
                'specimen_count': len(orchids),
                'genus_diversity': len(set(genera)),
                'dominant_genera': self._get_top_items(genera, 3)
            }
        
        # Elevation analysis
        elevation_data = [o.get('elevation') for o in data if o.get('elevation')]
        if elevation_data:
            try:
                numeric_elevations = [float(str(e).split()[0]) for e in elevation_data if str(e).replace('.','').isdigit()]
                if numeric_elevations:
                    patterns['elevation_patterns'] = {
                        'range': f"{min(numeric_elevations):.0f}m - {max(numeric_elevations):.0f}m",
                        'mean': f"{np.mean(numeric_elevations):.0f}m",
                        'distribution': 'lowland' if np.mean(numeric_elevations) < 500 else 'montane'
                    }
            except:
                patterns['elevation_patterns'] = {'note': 'Elevation data requires standardization'}
        
        return patterns
    
    def _analyze_temporal_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze blooming and temporal patterns"""
        patterns = {
            'bloom_seasonality': {},
            'flowering_synchrony': {},
            'phenology_patterns': {}
        }
        
        # Bloom season analysis
        bloom_seasons = [o.get('bloom_time') for o in data if o.get('bloom_time')]
        if bloom_seasons:
            season_counts = defaultdict(int)
            for season in bloom_seasons:
                # Normalize season names
                if 'spring' in season.lower():
                    season_counts['spring'] += 1
                elif 'summer' in season.lower():
                    season_counts['summer'] += 1
                elif 'fall' in season.lower() or 'autumn' in season.lower():
                    season_counts['fall'] += 1
                elif 'winter' in season.lower():
                    season_counts['winter'] += 1
            
            patterns['bloom_seasonality'] = dict(season_counts)
            
            # Find peak blooming season
            if season_counts:
                peak_season = max(season_counts.keys(), key=lambda k: season_counts[k])
                patterns['peak_bloom_season'] = {
                    'season': peak_season,
                    'percentage': (season_counts[peak_season] / len(bloom_seasons)) * 100
                }
        
        return patterns
    
    def _analyze_cross_ecosystem_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Find patterns across different ecosystem types"""
        patterns = {
            'multi_region_species': [],
            'ecosystem_similarities': {},
            'adaptation_patterns': {},
            'biogeographic_connections': []
        }
        
        # Find species occurring in multiple regions
        species_regions = defaultdict(set)
        for orchid in data:
            scientific_name = orchid.get('scientific_name')
            region = orchid.get('region')
            if scientific_name and region:
                species_regions[scientific_name].add(region)
        
        # Multi-region species (potential for ecosystem comparison)
        patterns['multi_region_species'] = [
            {
                'species': species,
                'regions': list(regions),
                'region_count': len(regions)
            }
            for species, regions in species_regions.items()
            if len(regions) > 1
        ]
        
        return patterns
    
    def _generate_ai_insights(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to generate insights from detected patterns"""
        if not self.openai_client:
            return {'note': 'AI analysis requires OpenAI API key'}
        
        try:
            prompt = f"""
            As a botanical research AI, analyze these orchid distribution patterns and provide insights:
            
            GEOGRAPHIC PATTERNS:
            - Regional clusters: {len(patterns['geographic_patterns']['regional_clusters'])} regions with significant diversity
            - Latitudinal bands: {len(patterns['geographic_patterns']['latitudinal_bands'])} bands with clustering
            
            PHYLOGENETIC PATTERNS:
            - Endemic candidates: {patterns['phylogenetic_patterns']['endemic_candidates']}
            - Widespread genera: {patterns['phylogenetic_patterns']['widespread_species']}
            
            ECOLOGICAL PATTERNS:
            - Climate associations: {list(patterns['ecological_patterns']['climate_associations'].keys())}
            
            MULTI-REGION SPECIES:
            - Species in multiple regions: {len(patterns['cross_ecosystem_patterns']['multi_region_species'])}
            
            Please provide:
            1. Key insights about biogeographic patterns
            2. Potential evolutionary or ecological explanations
            3. What these patterns suggest about orchid adaptation strategies
            4. Any surprising or noteworthy findings
            
            Be specific and reference the actual data patterns shown above.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a botanical research specialist with expertise in orchid biogeography, evolution, and ecology. Provide scientific insights based on data patterns."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return {
                'ai_analysis': response.choices[0].message.content,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI insight generation error: {e}")
            return {'error': str(e)}
    
    def _generate_research_hypotheses(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate testable research hypotheses based on patterns"""
        hypotheses = []
        
        # Geographic hypotheses
        if len(patterns['geographic_patterns']['regional_clusters']) > 1:
            hypotheses.append({
                'type': 'biogeographic',
                'hypothesis': 'Orchid diversity hotspots are correlated with specific environmental factors',
                'testable_prediction': 'Regions with high orchid diversity will share similar climate, elevation, or geological characteristics',
                'data_needed': ['climate data', 'soil types', 'elevation profiles', 'geological maps'],
                'statistical_test': 'correlation analysis, cluster analysis'
            })
        
        # Multi-region species hypotheses
        multi_region_count = len(patterns['cross_ecosystem_patterns']['multi_region_species'])
        if multi_region_count > 0:
            hypotheses.append({
                'type': 'ecological_adaptation',
                'hypothesis': f'{multi_region_count} species found in multiple regions show adaptive flexibility',
                'testable_prediction': 'Multi-region orchid species will show phenotypic variation corresponding to local environmental conditions',
                'data_needed': ['morphometric measurements', 'local climate data', 'soil analyses'],
                'statistical_test': 'ANOVA, principal component analysis'
            })
        
        # Endemic species hypothesis
        endemic_count = len(patterns['phylogenetic_patterns']['endemic_candidates'])
        if endemic_count > 0:
            hypotheses.append({
                'type': 'evolutionary',
                'hypothesis': f'{endemic_count} potential endemic genera suggest localized speciation events',
                'testable_prediction': 'Endemic orchid genera will show recent evolutionary divergence and unique adaptations to local conditions',
                'data_needed': ['phylogenetic analysis', 'geological history', 'pollinator surveys'],
                'statistical_test': 'molecular phylogeny, divergence time estimation'
            })
        
        # Bloom timing hypothesis
        if patterns.get('temporal_patterns', {}).get('peak_bloom_season'):
            peak_info = patterns['temporal_patterns']['peak_bloom_season']
            hypotheses.append({
                'type': 'phenological',
                'hypothesis': f'Concentrated blooming in {peak_info["season"]} ({peak_info["percentage"]:.1f}% of species) suggests environmental trigger',
                'testable_prediction': 'Bloom timing will correlate with photoperiod, temperature, or precipitation patterns',
                'data_needed': ['detailed flowering dates', 'weather data', 'photoperiod calculations'],
                'statistical_test': 'time series analysis, correlation analysis'
            })
        
        return {
            'generated_hypotheses': hypotheses,
            'total_count': len(hypotheses),
            'priority_ranking': self._rank_hypotheses_by_testability(hypotheses)
        }
    
    def _find_interesting_observations(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify the most interesting patterns for researcher attention"""
        observations = []
        
        # High-diversity regions
        regional_clusters = patterns['geographic_patterns']['regional_clusters']
        if regional_clusters:
            highest_diversity = max(regional_clusters.items(), key=lambda x: x[1]['genus_diversity'])
            observations.append({
                'type': 'biodiversity_hotspot',
                'title': f"Exceptional orchid diversity in {highest_diversity[0]}",
                'details': f"Found {highest_diversity[1]['specimen_count']} specimens from {highest_diversity[1]['genus_diversity']} different genera",
                'significance': 'High',
                'follow_up_questions': [
                    "What environmental factors make this region favorable for orchid diversity?",
                    "Are there undescribed species in this hotspot?",
                    "How does this compare to other tropical/temperate regions?"
                ]
            })
        
        # Unusual distribution patterns
        multi_region_species = patterns['cross_ecosystem_patterns']['multi_region_species']
        if multi_region_species:
            wide_ranging = [s for s in multi_region_species if s['region_count'] >= 3]
            if wide_ranging:
                observations.append({
                    'type': 'wide_distribution',
                    'title': f"{len(wide_ranging)} species found across 3+ regions",
                    'details': f"Species like {wide_ranging[0]['species']} occur in: {', '.join(wide_ranging[0]['regions'])}",
                    'significance': 'Medium',
                    'follow_up_questions': [
                        "What adaptations allow these orchids to thrive in different ecosystems?",
                        "Do populations show local adaptation or phenotypic plasticity?",
                        "Could these be cryptic species complexes?"
                    ]
                })
        
        # Endemic patterns
        endemic_candidates = patterns['phylogenetic_patterns']['endemic_candidates']
        if endemic_candidates:
            observations.append({
                'type': 'endemism',
                'title': f"Potential endemic genera identified: {len(endemic_candidates)}",
                'details': f"Genera restricted to single regions: {', '.join(endemic_candidates[:3])}{'...' if len(endemic_candidates) > 3 else ''}",
                'significance': 'High',
                'follow_up_questions': [
                    "What historical factors led to this geographic isolation?",
                    "Are these genera at risk due to habitat loss?",
                    "Could these represent ancient relict lineages?"
                ]
            })
        
        return observations
    
    def _get_top_items(self, items: List, n: int = 3) -> List[Tuple[str, int]]:
        """Get top N most frequent items with counts"""
        counts = defaultdict(int)
        for item in items:
            if item:
                counts[item] += 1
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def _rank_hypotheses_by_testability(self, hypotheses: List[Dict]) -> List[str]:
        """Rank hypotheses by how testable they are with current data"""
        # Simple ranking based on data requirements and statistical methods
        testability_scores = {}
        
        for i, hyp in enumerate(hypotheses):
            score = 0
            # Fewer data requirements = more testable
            score += 10 - len(hyp.get('data_needed', []))
            # Standard statistical tests = more testable  
            if 'correlation' in hyp.get('statistical_test', ''):
                score += 3
            if 'ANOVA' in hyp.get('statistical_test', ''):
                score += 2
            
            testability_scores[f"Hypothesis {i+1}"] = score
        
        return sorted(testability_scores.keys(), key=lambda k: testability_scores[k], reverse=True)


# Factory function for easy use
def analyze_orchid_patterns(filters: Dict = None) -> Dict[str, Any]:
    """Convenience function to run complete pattern analysis"""
    analyzer = AIPatternAnalyzer()
    return analyzer.analyze_data_patterns(filters)


def suggest_research_directions(genus: str = None, region: str = None) -> Dict[str, Any]:
    """Get AI suggestions for research directions based on specific criteria"""
    filters = {}
    if genus:
        filters['genus'] = genus
    if region:
        filters['region'] = region
    
    analyzer = AIPatternAnalyzer()
    patterns = analyzer.analyze_data_patterns(filters)
    
    return {
        'focus_area': f"Genus: {genus}" if genus else f"Region: {region}" if region else "Global",
        'key_patterns': patterns.get('interesting_observations', []),
        'research_hypotheses': patterns.get('research_hypotheses', {}),
        'recommended_next_steps': patterns.get('ai_insights', {})
    }