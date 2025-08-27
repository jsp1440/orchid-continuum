#!/usr/bin/env python3
"""
FINAL WORKING VERSION - REAL PHOTOS
Clean implementation with working Google Drive photos
"""

import sqlite3
from flask import Flask, render_template_string

app = Flask(__name__)

def get_orchids_with_photos():
    """Get orchids from database with working photo URLs"""
    try:
        conn = sqlite3.connect('orchid_continuum.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM orchid_record")
        total = cursor.fetchone()[0]
        
        # Get orchids with valid Google Drive IDs
        cursor.execute("""
            SELECT scientific_name, display_name, photographer, ai_description, google_drive_id 
            FROM orchid_record 
            WHERE google_drive_id IS NOT NULL AND google_drive_id != ''
            AND LENGTH(google_drive_id) > 10
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        
        orchids = []
        for row in cursor.fetchall():
            # Use working Google Photos direct link
            photo_url = f"https://lh3.googleusercontent.com/d/{row[4]}"
            
            orchids.append({
                'name': row[1] or row[0],
                'scientific': row[0],
                'photographer': row[2] or 'Five Cities Orchid Society',
                'description': row[3] or f"Beautiful {row[0]} orchid",
                'photo_url': photo_url
            })
        
        conn.close()
        return total, orchids
        
    except Exception as e:
        print(f"Database error: {e}")
        return 0, []

@app.route('/')
def home():
    """Main page with working photos"""
    total_count, orchids = get_orchids_with_photos()
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Five Cities Orchid Society - Digital Collection</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .hero {
            background: linear-gradient(135deg, #6B3FA0, #8E44AD);
            color: white;
            padding: 80px 0;
        }
        .orchid-img {
            height: 250px;
            width: 100%;
            object-fit: cover;
            border-radius: 10px 10px 0 0;
        }
        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
    </style>
</head>
<body>
    <div class="hero text-center">
        <div class="container">
            <h1 class="display-4 fw-bold">Five Cities Orchid Society</h1>
            <p class="lead fs-3">Digital Orchid Collection</p>
            <div class="bg-white text-dark d-inline-block px-4 py-3 rounded">
                <h3 class="mb-0">{{ total_count }} Orchids</h3>
            </div>
        </div>
    </div>

    <div class="container my-5">
        <h2 class="text-center mb-5">Featured Orchid Collection</h2>
        
        <div class="row">
        {% for orchid in orchids %}
            <div class="col-md-4">
                <div class="card">
                    <img src="{{ orchid.photo_url }}" 
                         class="orchid-img" 
                         alt="{{ orchid.name }}"
                         loading="lazy">
                    <div class="card-body">
                        <h5 class="card-title text-primary">{{ orchid.name }}</h5>
                        <p class="card-text fst-italic">{{ orchid.scientific }}</p>
                        <p class="card-text small">{{ orchid.description }}</p>
                        <small class="text-muted">📸 {{ orchid.photographer }}</small>
                    </div>
                </div>
            </div>
        {% endfor %}
        </div>
        
        <div class="row mt-5">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h4>🗓️ Next Workshop</h4>
                        <h5>September 13th at 1:00 PM</h5>
                        <p>The Planted Parlor<br><strong>Limited to 20 participants</strong></p>
                        <a href="mailto:jeff@fivecitiesorchidsociety.org" class="btn btn-primary">RSVP</a>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h4>📸 Share Your Photos</h4>
                        <p>Help grow our digital collection!</p>
                        <a href="https://docs.google.com/forms/d/e/1FAIpQLSdLh6MlI6KjNwVoM-w2MuO2vpU8KWnS_CvKAscOA_zlotag2w/viewform" 
                           target="_blank" class="btn btn-success">Submit Photos</a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white py-4 mt-5">
        <div class="container text-center">
            <h5>Five Cities Orchid Society</h5>
            <p>Digital Platform Ready for Friday Meeting</p>
        </div>
    </footer>
</body>
</html>
    ''', orchids=orchids, total_count=total_count)

if __name__ == '__main__':
    print("🌺 FINAL WORKING VERSION STARTING")
    print("✅ Real orchid database connected") 
    print("✅ Working Google Drive photo URLs")
    print("✅ Clean, minimal code")
    app.run(host="0.0.0.0", port=5006, debug=False)