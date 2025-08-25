#!/usr/bin/env python3
"""
Professor BloomBot - AI Discovery Alert System
Automatically detects and flags important orchid discoveries and correlations
"""

from app import app, db
from models import OrchidRecord, ScrapingLog
from sqlalchemy import func, and_, or_
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfessorBloomBot:
    """AI system for discovering interesting orchid patterns and correlations"""
    
    def __init__(self):
        self.discoveries = []
        self.importance_threshold = 0.7  # Minimum importance score to generate alert
    
    def discover_patterns(self):
        """Main discovery engine - analyzes database for interesting patterns"""
        logger.info("🔬 Professor BloomBot starting discovery analysis...")
        
        with app.app_context():
            # Discovery 1: New species with research potential
            self._discover_research_candidates()
            
            # Discovery 2: Geographic correlations
            self._discover_geographic_patterns()
            
            # Discovery 3: Recent significant additions
            self._discover_recent_additions()
            
            # Discovery 4: Rare genus discoveries
            self._discover_rare_genera()
            
            # Discovery 5: Hybrid parentage patterns
            self._discover_hybrid_patterns()
            
            # Discovery 6: Collector insights
            self._discover_collector_patterns()
            
            return self.discoveries
    
    def _discover_research_candidates(self):
        """Find species that just became good research candidates"""
        all_records = OrchidRecord.query.all()
        species_groups = defaultdict(list)
        
        for record in all_records:
            if record.display_name and len(record.display_name.strip()) > 2:
                species_key = record.display_name.strip().lower()
                species_groups[species_key].append(record)
        
        # Find species that recently reached comparison threshold
        new_candidates = []
        for species, records in species_groups.items():
            if len(records) >= 3:  # Good for comparison research
                photos = sum(1 for r in records if r.google_drive_id)
                photo_percentage = (photos / len(records)) * 100 if len(records) > 0 else 0
                
                if photo_percentage >= 50:  # Good visual data
                    research_score = len(records) * 2 + photos * 3
                    if research_score >= 15:  # High research value
                        new_candidates.append({
                            'species': species.title(),
                            'specimens': len(records),
                            'photos': photos,
                            'research_score': research_score
                        })
        
        if new_candidates:
            # Sort by research value
            new_candidates.sort(key=lambda x: x['research_score'], reverse=True)
            top_candidate = new_candidates[0]
            
            discovery = {
                'type': 'research_breakthrough',
                'title': f"🔬 Research Breakthrough: {top_candidate['species']}!",
                'message': f"Professor BloomBot discovered {top_candidate['species']} now has {top_candidate['specimens']} specimens with {top_candidate['photos']} photos - perfect for comparing different growing conditions!",
                'importance': 0.9,
                'action_url': f"/compare/{top_candidate['species'].lower()}",
                'action_text': "Start Research Comparison",
                'icon': 'trending-up',
                'category': 'research'
            }
            self.discoveries.append(discovery)
    
    def _discover_geographic_patterns(self):
        """Discover interesting geographic distribution patterns"""
        records_with_regions = OrchidRecord.query.filter(
            OrchidRecord.region.isnot(None)
        ).all()
        
        if len(records_with_regions) > 10:
            region_diversity = Counter(r.region for r in records_with_regions)
            most_diverse = region_diversity.most_common(1)[0] if region_diversity else None
            
            if most_diverse and most_diverse[1] >= 5:
                discovery = {
                    'type': 'geographic_insight',
                    'title': f"🌍 Geographic Discovery: {most_diverse[0]} Hotspot!",
                    'message': f"Professor BloomBot found {most_diverse[1]} orchid species from {most_diverse[0]} - this region shows remarkable biodiversity in our collection!",
                    'importance': 0.75,
                    'action_url': f"/gallery?region={most_diverse[0]}",
                    'action_text': "Explore Region",
                    'icon': 'globe',
                    'category': 'geography'
                }
                self.discoveries.append(discovery)
    
    def _discover_recent_additions(self):
        """Find significant recent database additions"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_records = OrchidRecord.query.filter(
            OrchidRecord.created_at >= yesterday
        ).all()
        
        if len(recent_records) >= 5:  # Significant addition
            with_photos = sum(1 for r in recent_records if r.google_drive_id)
            photo_percentage = (with_photos / len(recent_records)) * 100
            
            discovery = {
                'type': 'database_growth',
                'title': f"📈 Database Expansion: {len(recent_records)} New Orchids!",
                'message': f"Professor BloomBot noticed {len(recent_records)} new orchids added recently, including {with_photos} with photos ({photo_percentage:.0f}% photo coverage)!",
                'importance': 0.8,
                'action_url': "/gallery?sort=newest",
                'action_text': "View Recent Additions",
                'icon': 'plus-circle',
                'category': 'growth'
            }
            self.discoveries.append(discovery)
    
    def _discover_rare_genera(self):
        """Find rare or newly discovered genera"""
        all_records = OrchidRecord.query.all()
        genus_counts = Counter()
        
        for record in all_records:
            if record.scientific_name:
                genus = record.scientific_name.split()[0] if ' ' in record.scientific_name else record.scientific_name
                genus_counts[genus] += 1
            elif record.display_name and len(record.display_name) > 2:
                first_word = record.display_name.split()[0]
                if len(first_word) > 2:  # Likely a genus name
                    genus_counts[first_word] += 1
        
        # Find rare genera (only 1-2 specimens)
        rare_genera = [(genus, count) for genus, count in genus_counts.items() 
                      if 1 <= count <= 2 and len(genus) > 3]
        
        if rare_genera:
            rare_genus = rare_genera[0]  # Pick first rare genus
            
            discovery = {
                'type': 'rare_discovery',
                'title': f"💎 Rare Discovery: {rare_genus[0]} Orchid!",
                'message': f"Professor BloomBot spotted {rare_genus[0]} - a rare genus with only {rare_genus[1]} specimen{'s' if rare_genus[1] > 1 else ''} in our collection!",
                'importance': 0.85,
                'action_url': f"/gallery?search={rare_genus[0]}",
                'action_text': "View Rare Orchid",
                'icon': 'star',
                'category': 'rarity'
            }
            self.discoveries.append(discovery)
    
    def _discover_hybrid_patterns(self):
        """Discover interesting hybrid parentage patterns"""
        hybrids = OrchidRecord.query.filter(
            or_(
                OrchidRecord.pod_parent.isnot(None),
                OrchidRecord.pollen_parent.isnot(None)
            )
        ).all()
        
        if len(hybrids) >= 3:
            discovery = {
                'type': 'hybrid_insight',
                'title': f"🧬 Hybrid Collection: {len(hybrids)} Breeding Records!",
                'message': f"Professor BloomBot identified {len(hybrids)} orchids with recorded parentage - valuable for understanding breeding patterns and genetic diversity!",
                'importance': 0.7,
                'action_url': "/gallery?filter=hybrids",
                'action_text': "Explore Hybrids",
                'icon': 'shuffle',
                'category': 'genetics'
            }
            self.discoveries.append(discovery)
    
    def _discover_collector_patterns(self):
        """Find patterns in photographer/collector data"""
        records_with_photographers = OrchidRecord.query.filter(
            OrchidRecord.photographer.isnot(None)
        ).all()
        
        if records_with_photographers:
            photographer_counts = Counter(r.photographer for r in records_with_photographers)
            top_contributor = photographer_counts.most_common(1)[0] if photographer_counts else None
            
            if top_contributor and top_contributor[1] >= 10:
                discovery = {
                    'type': 'contributor_highlight',
                    'title': f"👥 Top Contributor: {top_contributor[0]}!",
                    'message': f"Professor BloomBot recognizes {top_contributor[0]} as a major contributor with {top_contributor[1]} orchid specimens in our research database!",
                    'importance': 0.65,
                    'action_url': f"/gallery?photographer={top_contributor[0]}",
                    'action_text': "View Collection",
                    'icon': 'user',
                    'category': 'contributors'
                }
                self.discoveries.append(discovery)
    
    def get_discovery_alerts(self, limit=5):
        """Get top discovery alerts for display"""
        # Sort by importance and recency
        sorted_discoveries = sorted(
            self.discoveries, 
            key=lambda x: x['importance'], 
            reverse=True
        )
        
        return sorted_discoveries[:limit]
    
    def generate_daily_discovery_report(self):
        """Generate a daily discovery report"""
        discoveries = self.discover_patterns()
        
        if not discoveries:
            return {
                'title': "🔬 Professor BloomBot Daily Report",
                'message': "All systems monitoring orchid patterns. More discoveries expected as the database grows!",
                'discoveries': []
            }
        
        top_discoveries = self.get_discovery_alerts(3)
        
        report = {
            'title': "🔬 Professor BloomBot Daily Discoveries",
            'message': f"Found {len(discoveries)} interesting patterns and correlations today!",
            'discoveries': top_discoveries,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return report

if __name__ == "__main__":
    # Test the discovery system
    print("🤖 Professor BloomBot Discovery System")
    print("=" * 50)
    
    bot = ProfessorBloomBot()
    report = bot.generate_daily_discovery_report()
    
    print(f"📊 {report['title']}")
    print(f"💡 {report['message']}\n")
    
    for i, discovery in enumerate(report['discoveries'], 1):
        print(f"{i}. {discovery['title']}")
        print(f"   {discovery['message']}")
        print(f"   Category: {discovery['category'].title()}")
        print()
