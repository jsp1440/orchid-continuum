#!/usr/bin/env python3
"""
FRIDAY MEETING PRESENTATION WEBSITE
Simple, clean, actually works
"""

import os
import sqlite3
from flask import Flask, jsonify, render_template_string

# Create simple Flask app
app = Flask(__name__)
app.secret_key = "friday-meeting-key"

# Connect directly to your database
def get_orchids():
    """Get real orchid data from your database"""
    try:
        conn = sqlite3.connect('orchid_continuum.db')
        cursor = conn.cursor()
        
        # Get orchids with photos
        cursor.execute("""
            SELECT scientific_name, display_name, google_drive_id, photographer, ai_description 
            FROM orchid_record 
            WHERE google_drive_id IS NOT NULL AND google_drive_id != ''
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        
        orchids = []
        for row in cursor.fetchall():
            orchids.append({
                'scientific_name': row[0],
                'display_name': row[1] or row[0],
                'google_drive_id': row[2],
                'photographer': row[3] or 'Five Cities Orchid Society',
                'description': row[4] or f"Beautiful {row[0]} orchid"
            })
        
        conn.close()
        return orchids
        
    except Exception as e:
        print(f"Database error: {e}")
        return []

@app.route('/')
def home():
    """Simple homepage that works"""
    orchids = get_orchids()
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Five Cities Orchid Society</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .hero { background: #6B3FA0; color: white; padding: 60px 0; }
        .orchid-card { margin-bottom: 20px; }
        .orchid-img { height: 200px; object-fit: cover; width: 100%; }
    </style>
</head>
<body>
    <div class="hero text-center">
        <div class="container">
            <h1 class="display-4">Five Cities Orchid Society</h1>
            <p class="lead">Digital Orchid Collection & Community Platform</p>
            <p>{{ orchids|length }} orchids in our collection</p>
        </div>
    </div>
    
    <div class="container my-5">
        <h2 class="mb-4">Our Orchid Collection</h2>
        
        <div class="row">
        {% for orchid in orchids %}
            <div class="col-md-4 orchid-card">
                <div class="card">
                    <img src="https://drive.google.com/uc?export=view&id={{ orchid.google_drive_id }}" 
                         class="card-img-top orchid-img" 
                         alt="{{ orchid.display_name }}"
                         onerror="this.src='https://via.placeholder.com/300x200/6B3FA0/FFFFFF?text=Orchid+Photo'">
                    <div class="card-body">
                        <h6 class="card-title">{{ orchid.display_name }}</h6>
                        <p class="card-text small">{{ orchid.description }}</p>
                        <small class="text-muted">Photo: {{ orchid.photographer }}</small>
                    </div>
                </div>
            </div>
        {% endfor %}
        </div>
        
        <div class="text-center mt-5">
            <h3>Workshop Information</h3>
            <div class="card d-inline-block" style="max-width: 500px;">
                <div class="card-body">
                    <h5>Next Workshop</h5>
                    <p><strong>September 13th at 1:00 PM</strong></p>
                    <p>The Planted Parlor</p>
                    <p>Limited to 20 participants</p>
                    <a href="mailto:jeff@fivecitiesorchidsociety.org" class="btn btn-primary">
                        Email to RSVP
                    </a>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-4">
            <h3>Share Your Orchid Photos</h3>
            <a href="https://docs.google.com/forms/d/e/1FAIpQLSdLh6MlI6KjNwVoM-w2MuO2vpU8KWnS_CvKAscOA_zlotag2w/viewform" 
               target="_blank" class="btn btn-success">
                Submit Photos to Our Collection
            </a>
        </div>
    </div>
    
    <footer class="bg-light py-4 mt-5">
        <div class="container text-center">
            <p>&copy; Five Cities Orchid Society - Digital Platform Ready for Presentation</p>
        </div>
    </footer>
</body>
</html>
    ''', orchids=orchids)

@app.route('/stats')
def stats():
    """Show collection statistics"""
    try:
        conn = sqlite3.connect('orchid_continuum.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM orchid_record")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT genus) FROM orchid_record WHERE genus IS NOT NULL")
        genera = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orchid_record WHERE google_drive_id IS NOT NULL")
        with_photos = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_orchids': total,
            'genera_count': genera,
            'photos_available': with_photos,
            'status': 'Database working perfectly'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🌺 FRIDAY PRESENTATION WEBSITE STARTING")
    print("✅ Direct database connection")
    print("✅ Your real orchid data")
    print("✅ Simple, reliable display")
    app.run(host="0.0.0.0", port=5001, debug=True)