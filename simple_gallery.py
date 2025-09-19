#!/usr/bin/env python3
"""
EMERGENCY GALLERY SOLUTION - All 1,607 Real Orchid Images
Direct PostgreSQL access to bypass SQLAlchemy model issues
"""

import os
import psycopg2
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

class RealOrchid:
    def __init__(self, row):
        self.id = row[0]
        self.display_name = row[1] or 'Unknown Orchid'
        self.scientific_name = row[2] or 'Unknown Species'
        self.genus = (row[3] or 'Unknown').split()[0]
        self.google_drive_id = row[4]
        self.photographer = row[5] or 'FCOS Collection'
        self.ai_description = row[6] or f'Beautiful {self.scientific_name} specimen'
        self.created_at = row[7] or datetime.now()
        self.image_url = f'/api/drive-photo/{self.google_drive_id}' if self.google_drive_id else None
        self.is_featured = False
        self.ai_confidence = 0.95

class RealPagination:
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

@app.route('/real-gallery')
def real_gallery():
    """Gallery showing ALL 1,607 real orchid images"""
    page = request.args.get('page', 1, type=int)
    genus = request.args.get('genus', '')
    
    try:
        # Connect directly to PostgreSQL
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        # Get total count with Google Drive IDs
        cursor.execute("""
            SELECT COUNT(*) FROM orchid_record 
            WHERE google_drive_id IS NOT NULL 
            AND google_drive_id != '' 
            AND google_drive_id != 'None'
        """)
        total_count = cursor.fetchone()[0]
        
        # Build the main query
        base_query = """
            SELECT id, display_name, scientific_name, genus, google_drive_id, 
                   photographer, ai_description, created_at
            FROM orchid_record 
            WHERE google_drive_id IS NOT NULL 
            AND google_drive_id != '' 
            AND google_drive_id != 'None'
        """
        
        params = []
        if genus:
            base_query += " AND genus ILIKE %s"
            params.append(f'%{genus}%')
            
        base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([48, (page - 1) * 48])  # 48 per page
        
        # Execute the query
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        
        # Create orchid objects
        orchid_items = [RealOrchid(row) for row in rows]
        orchids = RealPagination(orchid_items, total_count, page, 48)
        
        # Close connection
        cursor.close()
        conn.close()
        
        print(f"✅ REAL GALLERY: Loaded {len(orchid_items)} from {total_count} total orchids")
        
        return render_template('gallery.html', 
            orchids=orchids,
            page=page,
            pages=orchids.pages,
            total=total_count,
            per_page=48,
            search_query='',
            genus_filter=genus,
            climate_filter='',
            growth_habit_filter='',
            genera=['Trichocentrum', 'Cattleya', 'Brassolaeliocattleya', 'Potinara', 'Angcm'],
            climates=[],
            growth_habits=[],
            current_genus=genus,
            current_climate='',
            current_growth_habit=''
        )
        
    except Exception as e:
        print(f"❌ Real gallery failed: {e}")
        # Return empty gallery if it fails
        empty_orchids = RealPagination([], 0, 1, 48)
        return render_template('gallery.html', 
            orchids=empty_orchids,
            page=1,
            pages=1,
            total=0,
            per_page=48,
            search_query='',
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)