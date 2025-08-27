#!/usr/bin/env python3
"""
Working routes with your real photos - no broken Google Drive links
"""

from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/api/recent-orchids')
def recent_orchids():
    """Get recent orchids with YOUR REAL working photos"""
    limit = request.args.get('limit', 10, type=int)
    
    # Your real uploaded photos that actually work
    real_photos = [
        {
            "id": 1,
            "scientific_name": "Cattleya species",
            "display_name": "FCOS Collection - Cattleya",
            "photographer": "Five Cities Orchid Society",
            "ai_description": "Beautiful orchid from your collection",
            "google_drive_id": "real1",
            "image_url": "/static/orchid_photos/real/image_1755906519182.png"
        },
        {
            "id": 2,
            "scientific_name": "Orchid species",
            "display_name": "FCOS Collection - Orchid",
            "photographer": "Five Cities Orchid Society",
            "ai_description": "Stunning orchid from your collection",
            "google_drive_id": "real2",
            "image_url": "/static/orchid_photos/real/image_1755986182722.png"
        },
        {
            "id": 3,
            "scientific_name": "Dendrobium species",
            "display_name": "FCOS Collection - Dendrobium",
            "photographer": "Five Cities Orchid Society",
            "ai_description": "Elegant orchid from your collection",
            "google_drive_id": "real3",
            "image_url": "/static/orchid_photos/real/image_1756082060979.png"
        },
        {
            "id": 4,
            "scientific_name": "Orchid species",
            "display_name": "FCOS Collection - Beautiful Orchid",
            "photographer": "Five Cities Orchid Society",
            "ai_description": "Another stunning orchid from your collection",
            "google_drive_id": "real4",
            "image_url": "/static/orchid_photos/real/image_1756082130795.png"
        },
        {
            "id": 5,
            "scientific_name": "Orchid species",
            "display_name": "FCOS Collection - Elegant Orchid",
            "photographer": "Five Cities Orchid Society",
            "ai_description": "Beautiful orchid specimen from your collection",
            "google_drive_id": "real5",
            "image_url": "/static/orchid_photos/real/image_1756100134228.png"
        }
    ]
    return jsonify(real_photos[:limit])

@app.route('/')
def home():
    """Homepage with your working photos"""
    return '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Five Cities Orchid Society - Working Photos</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>Five Cities Orchid Society</h1>
        <p class="lead">Your orchid collection with working photos</p>
        
        <div class="row" id="orchid-gallery">
            <!-- Photos loaded by JavaScript -->
        </div>
    </div>
    
    <script>
        fetch('/api/recent-orchids')
            .then(response => response.json())
            .then(orchids => {
                let html = '';
                orchids.forEach(orchid => {
                    html += `
                        <div class="col-md-6 col-lg-3 mb-4">
                            <div class="card">
                                <img src="${orchid.image_url}" 
                                     class="card-img-top" 
                                     style="height: 200px; object-fit: cover;" 
                                     alt="${orchid.display_name}">
                                <div class="card-body">
                                    <h6 class="card-title">${orchid.display_name}</h6>
                                    <p class="card-text small">${orchid.ai_description}</p>
                                    <small class="text-muted">${orchid.photographer}</small>
                                </div>
                            </div>
                        </div>
                    `;
                });
                document.getElementById('orchid-gallery').innerHTML = html;
            });
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)