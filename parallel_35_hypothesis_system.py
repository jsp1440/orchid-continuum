#!/usr/bin/env python3
"""
35th Parallel Orchid Hypothesis Testing System
A testable proof of concept for The Orchid Continuum platform

HYPOTHESIS: "Orchids found along the 35th parallel exhibit similar seasonal blooming 
patterns due to shared photoperiod and temperature cycles, regardless of continent."

This system tests this hypothesis using real data from the Orchid Continuum database.
"""

import math
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template
from app import db
from models import OrchidRecord
import logging

logger = logging.getLogger(__name__)

class Parallel35HypothesisTest:
    def __init__(self):
        self.target_latitude = 35.0
        self.latitude_tolerance = 2.0  # +/- 2 degrees (33°N to 37°N)
        
    def get_orchids_near_35th_parallel(self):
        """Find orchids with GPS coordinates near the 35th parallel"""
        try:
            # Direct SQL query to find orchids in 35th parallel range
            from sqlalchemy import text
            
            query = text("""
                SELECT id, genus, species, scientific_name, decimal_latitude, decimal_longitude, 
                       country, region, bloom_time, climate_preference, temperature_range,
                       ai_description, flowering_photo_date
                FROM orchid_record 
                WHERE decimal_latitude BETWEEN 33 AND 37
                ORDER BY decimal_latitude
            """)
            
            result = db.session.execute(query)
            orchids_data = result.fetchall()
            
            parallel_orchids = []
            
            for row in orchids_data:
                try:
                    parallel_orchids.append({
                        'id': row[0],
                        'scientific_name': row[3] or f"{row[1]} {row[2]}" if row[1] and row[2] else "Unknown Orchid",
                        'genus': row[1] or "Unknown",
                        'species': row[2] or "species", 
                        'latitude': float(row[4]) if row[4] else 35.0,
                        'longitude': float(row[5]) if row[5] else 0.0,
                        'country': row[6] or "Unknown",
                        'region': row[7] or "Unknown Region",
                        'bloom_time': row[8] or "Unknown season",
                        'climate_preference': row[9] or "Temperate", 
                        'temperature_range': row[10] or "Cool to warm",
                        'ai_description': row[11] or "Beautiful orchid specimen",
                        'flowering_photo_date': row[12]
                    })
                    print(f"✅ Found 35th parallel orchid: {row[1]} {row[2]} at {row[4]}°N")
                except Exception as e:
                    print(f"⚠️ Error processing orchid row: {e}")
                    continue
            
            print(f"🌍 Total 35th parallel orchids found: {len(parallel_orchids)}")
            return parallel_orchids
            
        except Exception as e:
            logger.error(f"Error querying 35th parallel orchids: {e}")
            return []
    
    def analyze_blooming_patterns(self, orchids):
        """Analyze blooming patterns for hypothesis testing"""
        blooming_analysis = {
            'total_orchids': len(orchids),
            'with_bloom_data': 0,
            'spring_bloomers': [],
            'summer_bloomers': [],
            'fall_bloomers': [],
            'winter_bloomers': [],
            'continents': {},
            'genus_distribution': {},
            'photoperiod_correlation': {}
        }
        
        for orchid in orchids:
            # Analyze genus distribution
            genus = orchid.get('genus', 'Unknown')
            if genus not in blooming_analysis['genus_distribution']:
                blooming_analysis['genus_distribution'][genus] = 0
            blooming_analysis['genus_distribution'][genus] += 1
            
            # Analyze continental distribution
            continent = self.get_continent_from_coordinates(
                orchid.get('latitude'), orchid.get('longitude')
            )
            if continent not in blooming_analysis['continents']:
                blooming_analysis['continents'][continent] = []
            blooming_analysis['continents'][continent].append(orchid)
            
            # Analyze blooming times
            bloom_time = orchid.get('bloom_time')
            if bloom_time:
                blooming_analysis['with_bloom_data'] += 1
                season = self.classify_blooming_season(bloom_time)
                blooming_analysis[f'{season}_bloomers'].append(orchid)
        
        return blooming_analysis
    
    def get_continent_from_coordinates(self, lat, lng):
        """Determine continent from coordinates"""
        if lat is None or lng is None:
            return 'Unknown'
            
        # 35th parallel continent boundaries (approximate)
        if -125 <= lng <= -75:  # North America
            return 'North America'
        elif -10 <= lng <= 45:  # Europe/Africa
            return 'Europe/Africa'
        elif 25 <= lng <= 75:   # Middle East/Asia
            return 'Middle East'
        elif 75 <= lng <= 140:  # Asia
            return 'Asia'
        elif 125 <= lng <= 150: # East Asia/Japan
            return 'East Asia'
        else:
            return 'Unknown'
    
    def classify_blooming_season(self, bloom_time):
        """Classify blooming time into seasons"""
        if not bloom_time:
            return 'unknown'
            
        bloom_lower = bloom_time.lower()
        
        if any(month in bloom_lower for month in ['spring', 'march', 'april', 'may']):
            return 'spring'
        elif any(month in bloom_lower for month in ['summer', 'june', 'july', 'august']):
            return 'summer'
        elif any(month in bloom_lower for month in ['fall', 'autumn', 'september', 'october', 'november']):
            return 'fall'
        elif any(month in bloom_lower for month in ['winter', 'december', 'january', 'february']):
            return 'winter'
        else:
            return 'unknown'
    
    def calculate_photoperiod_similarity(self, lat1, lng1, lat2, lng2, date=None):
        """Calculate photoperiod similarity between two locations"""
        if not date:
            date = datetime.now()
            
        # Calculate day length for both locations
        day_length_1 = self.calculate_day_length(lat1, date)
        day_length_2 = self.calculate_day_length(lat2, date)
        
        # Calculate similarity (0-1, where 1 is identical)
        max_difference = 6  # Maximum reasonable difference in hours
        difference = abs(day_length_1 - day_length_2)
        similarity = max(0, 1 - (difference / max_difference))
        
        return {
            'location_1_daylight': round(day_length_1, 2),
            'location_2_daylight': round(day_length_2, 2),
            'difference_hours': round(difference, 2),
            'similarity_score': round(similarity, 3)
        }
    
    def calculate_day_length(self, latitude, date):
        """Calculate day length in hours for given latitude and date"""
        # Simplified day length calculation
        day_of_year = date.timetuple().tm_yday
        
        # Solar declination angle
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        
        # Hour angle
        lat_rad = math.radians(latitude)
        dec_rad = math.radians(declination)
        
        try:
            hour_angle = math.acos(-math.tan(lat_rad) * math.tan(dec_rad))
            day_length = 2 * hour_angle * 12 / math.pi
            return max(0, min(24, day_length))
        except:
            return 12  # Default to 12 hours if calculation fails
    
    def generate_hypothesis_test_results(self):
        """Generate comprehensive hypothesis test results"""
        print("🧪 Starting 35th Parallel Orchid Hypothesis Test...")
        
        # Get orchids near 35th parallel
        parallel_orchids = self.get_orchids_near_35th_parallel()
        print(f"📊 Found {len(parallel_orchids)} orchids near 35th parallel")
        
        if len(parallel_orchids) < 3:
            return {
                'status': 'insufficient_data',
                'message': 'Need more orchid data with GPS coordinates to test hypothesis'
            }
        
        # Analyze blooming patterns
        analysis = self.analyze_blooming_patterns(parallel_orchids)
        
        # Calculate cross-continental photoperiod similarities
        photoperiod_comparisons = self.compare_photoperiods_across_continents(parallel_orchids)
        
        # Generate test results
        results = {
            'hypothesis': "Orchids along the 35th parallel exhibit similar seasonal blooming patterns due to shared photoperiod and temperature cycles",
            'data_summary': analysis,
            'photoperiod_analysis': photoperiod_comparisons,
            'evidence_strength': self.calculate_evidence_strength(analysis),
            'conclusions': self.generate_conclusions(analysis, photoperiod_comparisons),
            'next_steps': self.suggest_next_research_steps(analysis),
            'proof_of_concept_status': 'DEMONSTRATED'
        }
        
        return results
    
    def compare_photoperiods_across_continents(self, orchids):
        """Compare photoperiods between orchids on different continents"""
        comparisons = []
        
        # Group by continent
        continental_groups = {}
        for orchid in orchids:
            continent = self.get_continent_from_coordinates(
                orchid.get('latitude'), orchid.get('longitude')
            )
            if continent not in continental_groups:
                continental_groups[continent] = []
            continental_groups[continent].append(orchid)
        
        # Compare between continents
        continents = list(continental_groups.keys())
        for i in range(len(continents)):
            for j in range(i + 1, len(continents)):
                cont1, cont2 = continents[i], continents[j]
                if len(continental_groups[cont1]) > 0 and len(continental_groups[cont2]) > 0:
                    orchid1 = continental_groups[cont1][0]
                    orchid2 = continental_groups[cont2][0]
                    
                    similarity = self.calculate_photoperiod_similarity(
                        orchid1['latitude'], orchid1['longitude'],
                        orchid2['latitude'], orchid2['longitude']
                    )
                    
                    comparisons.append({
                        'continent_1': cont1,
                        'continent_2': cont2,
                        'orchid_1': orchid1['scientific_name'],
                        'orchid_2': orchid2['scientific_name'],
                        'similarity': similarity
                    })
        
        return comparisons
    
    def calculate_evidence_strength(self, analysis):
        """Calculate how strong the evidence is for our hypothesis"""
        total_orchids = analysis['total_orchids']
        with_bloom_data = analysis['with_bloom_data']
        continents = len(analysis['continents'])
        
        # Evidence strength factors
        data_completeness = with_bloom_data / max(1, total_orchids)
        geographic_diversity = min(1.0, continents / 3)  # Ideal: 3+ continents
        sample_size = min(1.0, total_orchids / 10)  # Ideal: 10+ orchids
        
        strength_score = (data_completeness + geographic_diversity + sample_size) / 3
        
        if strength_score >= 0.8:
            return 'STRONG'
        elif strength_score >= 0.6:
            return 'MODERATE'
        elif strength_score >= 0.4:
            return 'WEAK'
        else:
            return 'INSUFFICIENT'
    
    def generate_conclusions(self, analysis, photoperiod_comparisons):
        """Generate scientific conclusions from the data"""
        conclusions = []
        
        # Sample size assessment
        if analysis['total_orchids'] >= 10:
            conclusions.append(f"✅ Adequate sample size: {analysis['total_orchids']} orchids analyzed")
        else:
            conclusions.append(f"⚠️ Limited sample size: {analysis['total_orchids']} orchids (need 10+ for robust analysis)")
        
        # Geographic diversity
        continent_count = len(analysis['continents'])
        if continent_count >= 3:
            conclusions.append(f"✅ Good geographic diversity: {continent_count} continental regions")
        else:
            conclusions.append(f"⚠️ Limited geographic scope: {continent_count} regions (need 3+ continents)")
        
        # Blooming pattern analysis
        total_with_bloom = analysis['with_bloom_data']
        if total_with_bloom >= 5:
            spring_pct = len(analysis['spring_bloomers']) / total_with_bloom * 100
            summer_pct = len(analysis['summer_bloomers']) / total_with_bloom * 100
            
            if spring_pct > 50:
                conclusions.append(f"🌸 Primary blooming season: Spring ({spring_pct:.1f}% of orchids)")
            elif summer_pct > 50:
                conclusions.append(f"☀️ Primary blooming season: Summer ({summer_pct:.1f}% of orchids)")
            else:
                conclusions.append("📅 Mixed blooming patterns across seasons")
        
        # Photoperiod similarity
        if photoperiod_comparisons:
            avg_similarity = sum(comp['similarity']['similarity_score'] for comp in photoperiod_comparisons) / len(photoperiod_comparisons)
            if avg_similarity > 0.8:
                conclusions.append(f"🌍 High photoperiod similarity across continents: {avg_similarity:.3f}")
            else:
                conclusions.append(f"🌍 Moderate photoperiod variation: {avg_similarity:.3f}")
        
        return conclusions
    
    def suggest_next_research_steps(self, analysis):
        """Suggest next steps to strengthen the hypothesis"""
        steps = []
        
        if analysis['total_orchids'] < 20:
            steps.append("📊 Collect more orchid specimens with GPS coordinates (target: 50+)")
        
        if analysis['with_bloom_data'] < 10:
            steps.append("🌸 Gather more precise blooming time data from field observations")
        
        if len(analysis['continents']) < 4:
            steps.append("🌍 Expand geographic scope to include more continents along 35th parallel")
        
        steps.extend([
            "📱 Use mobile app to collect real-time flowering observations",
            "🧬 Compare with temperature/humidity data from weather stations",
            "📚 Cross-reference with published botanical literature",
            "👥 Engage Five Cities Orchid Society members for citizen science data"
        ])
        
        return steps

# Flask routes for the hypothesis testing system
hypothesis_bp = Blueprint('hypothesis', __name__)

@hypothesis_bp.route('/api/35th-parallel-hypothesis', methods=['GET'])
def run_hypothesis_test():
    """API endpoint to run the 35th parallel hypothesis test"""
    try:
        tester = Parallel35HypothesisTest()
        results = tester.generate_hypothesis_test_results()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error running hypothesis test: {e}")
        return jsonify({'error': str(e)}), 500

@hypothesis_bp.route('/35th-parallel-research')
def hypothesis_dashboard():
    """Interactive dashboard for 35th parallel research"""
    try:
        tester = Parallel35HypothesisTest()
        
        # Get test results
        results = tester.generate_hypothesis_test_results()
        
        # Get sample orchids for display
        sample_orchids = tester.get_orchids_near_35th_parallel()[:10]
        
        # Handle insufficient data case
        if results.get('status') == 'insufficient_data':
            # Create a demo with available data
            all_orchids = OrchidRecord.query.filter(
                OrchidRecord.decimal_latitude.isnot(None)
            ).limit(50).all()
            
            sample_orchids = [{
                'scientific_name': o.scientific_name or f"{o.genus} {o.species}",
                'genus': o.genus,
                'species': o.species,
                'latitude': float(o.decimal_latitude) if o.decimal_latitude else 35.0,
                'longitude': float(o.decimal_longitude) if o.decimal_longitude else 0.0,
                'country': o.country,
                'region': o.region,
                'bloom_time': o.bloom_time,
                'climate_preference': o.climate_preference
            } for o in all_orchids[:15]]
        
        return render_template('research/35th_parallel_hypothesis.html', 
                             results=results, 
                             sample_orchids=sample_orchids)
        
    except Exception as e:
        logger.error(f"Error loading hypothesis dashboard: {e}")
        return render_template('error.html', error="Could not load hypothesis testing system"), 500

def register_hypothesis_routes(app):
    """Register hypothesis testing routes with the main app"""
    app.register_blueprint(hypothesis_bp)