#!/usr/bin/env python3
"""
NEW ORCHID GALLERY - Clean Database Solution
Direct PostgreSQL access for all 1,607 real orchid images
"""

import os
import psycopg2
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class OrchidRecord:
    """Clean orchid record class matching actual database schema"""
    def __init__(self, row):
        # Match the exact database schema columns
        self.id = row[0]
        self.display_name = row[1] or 'Unknown Orchid'
        self.scientific_name = row[2] or 'Unknown Species'
        self.genus = row[3] or 'Unknown'
        self.species = row[4] or ''
        self.author = row[5] or ''
        self.region = row[6] or ''
        self.native_habitat = row[7] or ''
        self.bloom_time = row[8] or ''
        self.growth_habit = row[9] or ''
        self.climate_preference = row[10] or ''
        self.google_drive_id = row[11]
        self.photographer = row[12] or 'FCOS Collection'
        self.ai_description = row[13] or f'Beautiful {self.scientific_name} specimen'
        self.created_at = row[14] or datetime.now()
        self.is_featured = row[15] or False
        
        # Computed properties
        self.image_url = f'/api/drive-photo/{self.google_drive_id}' if self.google_drive_id else None
        self.ai_confidence = 0.95
        
    def to_dict(self):
        return {
            'id': self.id,
            'display_name': self.display_name,
            'scientific_name': self.scientific_name,
            'genus': self.genus,
            'species': self.species,
            'photographer': self.photographer,
            'image_url': self.image_url,
            'ai_description': self.ai_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class OrchidPagination:
    """Clean pagination class"""
    def __init__(self, items, total, page, per_page):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = (total + per_page - 1) // per_page if total > 0 else 1
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None

def get_database_connection():
    """Get a fresh database connection"""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

@app.route('/new-gallery')
def new_gallery():
    """Clean gallery showing ALL 1,607 real orchid images"""
    page = request.args.get('page', 1, type=int)
    genus = request.args.get('genus', '')
    climate = request.args.get('climate', '')
    growth_habit = request.args.get('growth_habit', '')
    search_query = request.args.get('search', '')
    
    per_page = 48
    
    try:
        # Get fresh connection
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_conditions = ["google_drive_id IS NOT NULL AND google_drive_id != '' AND google_drive_id != 'None'"]
        params = []
        
        if genus:
            where_conditions.append("genus ILIKE %s")
            params.append(f'%{genus}%')
            
        if climate:
            where_conditions.append("climate_preference = %s")
            params.append(climate)
            
        if growth_habit:
            where_conditions.append("growth_habit = %s")
            params.append(growth_habit)
            
        if search_query:
            where_conditions.append("(display_name ILIKE %s OR scientific_name ILIKE %s OR genus ILIKE %s)")
            search_param = f'%{search_query}%'
            params.extend([search_param, search_param, search_param])
        
        where_clause = " AND ".join(where_conditions)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM orchid_record WHERE {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Get the main data - select only columns that exist
        main_query = f"""
            SELECT id, display_name, scientific_name, genus, species, author, 
                   region, native_habitat, bloom_time, growth_habit, climate_preference,
                   google_drive_id, photographer, ai_description, created_at, is_featured
            FROM orchid_record 
            WHERE {where_clause}
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        
        main_params = params + [per_page, (page - 1) * per_page]
        cursor.execute(main_query, main_params)
        rows = cursor.fetchall()
        
        # Create orchid objects
        orchid_items = [OrchidRecord(row) for row in rows]
        orchids = OrchidPagination(orchid_items, total_count, page, per_page)
        
        # Get filter options
        cursor.execute("SELECT DISTINCT genus FROM orchid_record WHERE genus IS NOT NULL AND genus != '' ORDER BY genus")
        genera = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT climate_preference FROM orchid_record WHERE climate_preference IS NOT NULL AND climate_preference != '' ORDER BY climate_preference")
        climates = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT growth_habit FROM orchid_record WHERE growth_habit IS NOT NULL AND growth_habit != '' ORDER BY growth_habit")
        growth_habits = [row[0] for row in cursor.fetchall()]
        
        # Close connection
        cursor.close()
        conn.close()
        
        logger.info(f"✅ NEW GALLERY: Loaded {len(orchid_items)} from {total_count} total orchids")
        
        return render_template('gallery.html', 
            orchids=orchids,
            page=page,
            pages=orchids.pages,
            total=total_count,
            per_page=per_page,
            search_query=search_query,
            genus_filter=genus,
            climate_filter=climate,
            growth_habit_filter=growth_habit,
            genera=genera,
            climates=climates,
            growth_habits=growth_habits,
            current_genus=genus,
            current_climate=climate,
            current_growth_habit=growth_habit
        )
        
    except Exception as e:
        logger.error(f"❌ New gallery failed: {e}")
        import traceback
        logger.error(f"Full error: {traceback.format_exc()}")
        
        # Return empty gallery if it fails
        empty_orchids = OrchidPagination([], 0, 1, per_page)
        return render_template('gallery.html', 
            orchids=empty_orchids,
            page=1,
            pages=1,
            total=0,
            per_page=per_page,
            search_query=search_query,
            genus_filter='',
            climate_filter='',
            growth_habit_filter='',
            genera=[],
            climates=[],
            growth_habits=[],
            current_genus='',
            current_climate='',
            current_growth_habit=''
        )

@app.route('/api/new-recent-orchids')
def new_recent_orchids():
    """API endpoint for recent orchids using clean database access"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, display_name, scientific_name, google_drive_id, photographer, ai_description
            FROM orchid_record 
            WHERE google_drive_id IS NOT NULL AND google_drive_id != '' AND google_drive_id != 'None'
            ORDER BY created_at DESC 
            LIMIT 6
        """)
        
        rows = cursor.fetchall()
        recent_orchids = []
        
        for row in rows:
            recent_orchids.append({
                'id': row[0],
                'display_name': row[1] or 'Unknown Orchid',
                'scientific_name': row[2] or 'Unknown Species',
                'image_url': f'/api/drive-photo/{row[3]}',
                'photographer': row[4] or 'FCOS Collection',
                'ai_description': row[5] or 'Beautiful orchid specimen'
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'orchids': recent_orchids,
            'total': len(recent_orchids)
        })
        
    except Exception as e:
        logger.error(f"❌ Recent orchids API failed: {e}")
        return jsonify({
            'status': 'error',
            'orchids': [],
            'total': 0,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)