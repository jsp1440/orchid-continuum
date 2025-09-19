"""
Database Metadata Completeness Tracker
Real-time monitoring of flowering dates and geographic coordinate completeness
"""

from models import OrchidRecord, db
from app import app
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMetadataTracker:
    """Track and report on database metadata completeness"""
    
    def __init__(self):
        self.app = app
        self.stats_history = []

    def get_current_stats(self):
        """Get current database statistics"""
        with self.app.app_context():
            stats = {}
            
            # Basic counts
            stats['total_records'] = db.session.query(OrchidRecord).count()
            stats['with_bloom_time'] = db.session.query(OrchidRecord).filter(
                OrchidRecord.bloom_time.isnot(None)
            ).count()
            stats['with_coordinates'] = db.session.query(OrchidRecord).filter(
                OrchidRecord.decimal_latitude.isnot(None),
                OrchidRecord.decimal_longitude.isnot(None)
            ).count()
            stats['with_both'] = db.session.query(OrchidRecord).filter(
                OrchidRecord.bloom_time.isnot(None),
                OrchidRecord.decimal_latitude.isnot(None)
            ).count()
            
            # Endemic species tracking
            stats['potential_endemic'] = db.session.query(OrchidRecord).filter(
                db.or_(
                    OrchidRecord.native_habitat.contains('endemic'),
                    OrchidRecord.native_habitat.contains('native to'),
                    OrchidRecord.native_habitat.contains('restricted to')
                )
            ).count()
            
            # Genus-level breakdown
            stats['genus_breakdown'] = self.get_genus_metadata_breakdown()
            
            # Cross-latitude candidates
            stats['cross_latitude_candidates'] = self.count_cross_latitude_species()
            
            # Completeness percentages
            if stats['total_records'] > 0:
                stats['bloom_completeness'] = (stats['with_bloom_time'] / stats['total_records']) * 100
                stats['coord_completeness'] = (stats['with_coordinates'] / stats['total_records']) * 100
                stats['both_completeness'] = (stats['with_both'] / stats['total_records']) * 100
            else:
                stats['bloom_completeness'] = 0
                stats['coord_completeness'] = 0
                stats['both_completeness'] = 0
            
            stats['timestamp'] = datetime.utcnow().isoformat()
            
            return stats

    def get_genus_metadata_breakdown(self):
        """Get metadata completeness by genus"""
        with self.app.app_context():
            from sqlalchemy import func
            
            genus_stats = db.session.query(
                OrchidRecord.genus,
                func.count(OrchidRecord.id).label('total'),
                func.count(OrchidRecord.bloom_time).label('with_bloom'),
                func.count(OrchidRecord.decimal_latitude).label('with_coords')
            ).filter(
                OrchidRecord.genus.isnot(None)
            ).group_by(
                OrchidRecord.genus
            ).having(
                func.count(OrchidRecord.id) >= 3
            ).order_by(
                func.count(OrchidRecord.bloom_time).desc()
            ).limit(20).all()
            
            breakdown = []
            for genus, total, with_bloom, with_coords in genus_stats:
                bloom_rate = (with_bloom / total) * 100 if total > 0 else 0
                coord_rate = (with_coords / total) * 100 if total > 0 else 0
                
                breakdown.append({
                    'genus': genus,
                    'total': total,
                    'with_bloom': with_bloom,
                    'with_coords': with_coords,
                    'bloom_rate': round(bloom_rate, 1),
                    'coord_rate': round(coord_rate, 1)
                })
            
            return breakdown

    def count_cross_latitude_species(self):
        """Count species that occur at multiple latitudes"""
        with self.app.app_context():
            from sqlalchemy import func, distinct
            
            # Find species with multiple distinct latitude entries
            # Use CAST to avoid PostgreSQL round function issues
            species_with_multiple_lats = db.session.query(
                OrchidRecord.scientific_name,
                func.count(distinct(func.cast(OrchidRecord.decimal_latitude, db.Integer))).label('lat_count')
            ).filter(
                OrchidRecord.scientific_name.isnot(None),
                OrchidRecord.decimal_latitude.isnot(None),
                OrchidRecord.bloom_time.isnot(None)
            ).group_by(
                OrchidRecord.scientific_name
            ).having(
                func.count(distinct(func.cast(OrchidRecord.decimal_latitude, db.Integer))) >= 2
            ).count()
            
            return species_with_multiple_lats

    def get_high_priority_targets(self):
        """Get genera/species that are high priority for metadata collection"""
        with self.app.app_context():
            from sqlalchemy import func
            
            # Genera with many records but low metadata completeness
            high_priority = db.session.query(
                OrchidRecord.genus,
                func.count(OrchidRecord.id).label('total'),
                func.count(OrchidRecord.bloom_time).label('with_bloom'),
                func.count(OrchidRecord.decimal_latitude).label('with_coords')
            ).filter(
                OrchidRecord.genus.isnot(None)
            ).group_by(
                OrchidRecord.genus
            ).having(
                db.and_(
                    func.count(OrchidRecord.id) >= 10,  # At least 10 records
                    func.count(OrchidRecord.bloom_time) < func.count(OrchidRecord.id) * 0.3  # Less than 30% have bloom time
                )
            ).order_by(
                func.count(OrchidRecord.id).desc()
            ).limit(10).all()
            
            targets = []
            for genus, total, with_bloom, with_coords in high_priority:
                bloom_rate = (with_bloom / total) * 100
                coord_rate = (with_coords / total) * 100
                
                targets.append({
                    'genus': genus,
                    'total_records': total,
                    'bloom_completeness': round(bloom_rate, 1),
                    'coord_completeness': round(coord_rate, 1),
                    'potential_enhancement': total - max(with_bloom, with_coords)
                })
            
            return targets

    def generate_progress_report(self):
        """Generate a comprehensive progress report"""
        stats = self.get_current_stats()
        targets = self.get_high_priority_targets()
        
        report = f"""
{'='*70}
📊 ORCHID DATABASE METADATA COMPLETENESS REPORT
{'='*70}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

📈 OVERALL STATISTICS:
   Total Records: {stats['total_records']:,}
   With Flowering Dates: {stats['with_bloom_time']:,} ({stats['bloom_completeness']:.1f}%)
   With Coordinates: {stats['with_coordinates']:,} ({stats['coord_completeness']:.1f}%)
   With BOTH (Target): {stats['with_both']:,} ({stats['both_completeness']:.1f}%)

🏝️ ENDEMIC SPECIES ANALYSIS:
   Potential Endemic Species: {stats['potential_endemic']}
   Cross-Latitude Species: {stats['cross_latitude_candidates']}

🎯 TOP GENERA BY FLOWERING DATA COMPLETENESS:
"""
        
        for genus_info in stats['genus_breakdown'][:10]:
            report += f"   {genus_info['genus']:<15} {genus_info['total']:>4} records, {genus_info['bloom_rate']:>5.1f}% bloom, {genus_info['coord_rate']:>5.1f}% coords\n"
        
        report += f"""
🔍 HIGH PRIORITY TARGETS FOR ENHANCEMENT:
"""
        
        for target in targets[:5]:
            report += f"   {target['genus']:<15} {target['total_records']:>4} records, {target['bloom_completeness']:>5.1f}% complete, {target['potential_enhancement']:>3} to enhance\n"
        
        report += f"""
{'='*70}
💡 RECOMMENDATIONS:
1. Focus collection efforts on high-volume genera with low completeness
2. Prioritize endemic species identification for cross-latitude analysis
3. Target {stats['cross_latitude_candidates']} cross-latitude species for bloom comparison
4. Current target completion rate: {stats['both_completeness']:.1f}% (Goal: >50%)
{'='*70}
"""
        
        return report

    def track_progress_over_time(self):
        """Track progress changes over time"""
        current_stats = self.get_current_stats()
        self.stats_history.append(current_stats)
        
        # Keep only last 24 hours of data (assuming hourly checks)
        if len(self.stats_history) > 24:
            self.stats_history = self.stats_history[-24:]
        
        return current_stats

    def get_progress_trends(self):
        """Get trends in metadata completeness"""
        if len(self.stats_history) < 2:
            return None
        
        first = self.stats_history[0]
        latest = self.stats_history[-1]
        
        trends = {
            'total_records_change': latest['total_records'] - first['total_records'],
            'bloom_records_change': latest['with_bloom_time'] - first['with_bloom_time'],
            'coord_records_change': latest['with_coordinates'] - first['with_coordinates'],
            'both_records_change': latest['with_both'] - first['with_both'],
            'time_period': f"{first['timestamp']} to {latest['timestamp']}"
        }
        
        return trends

# Global tracker instance
metadata_tracker = DatabaseMetadataTracker()

def get_database_completeness_report():
    """Get current database completeness report"""
    return metadata_tracker.generate_progress_report()

def get_current_metadata_stats():
    """Get current metadata statistics"""
    return metadata_tracker.get_current_stats()

if __name__ == "__main__":
    tracker = DatabaseMetadataTracker()
    report = tracker.generate_progress_report()
    print(report)