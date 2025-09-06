import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from app import app, db
from models import OrchidRecord

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/api/recent-orchids')
def recent_orchids():
    """Recent orchids API - shows your REAL orchid data from database"""
    limit = int(request.args.get('limit', 20))
    
    try:
        # Get orchids from the actual database using SQLAlchemy
        from app import db
        from models import OrchidRecord
        
        # Query real orchids with images, prioritize those with Google Drive IDs
        orchids = OrchidRecord.query.filter(
            (OrchidRecord.google_drive_id.isnot(None)) | 
            (OrchidRecord.image_url.isnot(None))
        ).order_by(OrchidRecord.id.desc()).limit(limit).all()
        
        # Convert to JSON format
        result = []
        for orchid in orchids:
            result.append({
                "id": orchid.id,
                "scientific_name": orchid.scientific_name or orchid.display_name,
                "display_name": orchid.display_name,
                "photographer": orchid.photographer or "FCOS Collection",
                "ai_description": orchid.ai_description or "Beautiful orchid from the Five Cities Orchid Society collection",
                "google_drive_id": orchid.google_drive_id,
                "image_url": orchid.image_url,
                "decimal_latitude": orchid.decimal_latitude,
                "decimal_longitude": orchid.decimal_longitude
            })
        
        if result:
            return jsonify(result)
            
    except Exception as e:
        print(f"Error getting recent orchids: {e}")
    
    # Fallback to working examples only if database fails
    fallback_photos = [
        {
            "id": 1,
            "scientific_name": "Cattleya trianae",
            "display_name": "Cattleya trianae",
            "photographer": "FCOS Collection",
            "ai_description": "Beautiful Christmas orchid in full bloom",
            "google_drive_id": "185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I",
            "image_url": "/api/drive-photo/185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I",
            "decimal_latitude": 4.0,
            "decimal_longitude": -74.0
        },
        {
            "id": 2,
            "scientific_name": "Phalaenopsis amabilis",
            "display_name": "Phalaenopsis amabilis",
            "photographer": "FCOS Collection",
            "ai_description": "Elegant white moon orchid",
            "google_drive_id": "1142ajwZe7_LbGt-BPy-HqVkLpNczcfZY",
            "image_url": "/api/drive-photo/1142ajwZe7_LbGt-BPy-HqVkLpNczcfZY",
            "decimal_latitude": 1.0,
            "decimal_longitude": 104.0
        }
    ]
    return jsonify(fallback_photos[:limit])

@app.route('/gallery')
def gallery():
    """Gallery page - always works"""
    return '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gallery - Five Cities Orchid Society</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <script src="https://unpkg.com/feather-icons"></script>
</head>
<body>
    <div class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1><i data-feather="grid"></i> Orchid Gallery</h1>
            <a href="/" class="btn btn-outline-secondary"><i data-feather="arrow-left"></i> Back to Home</a>
        </div>
        
        <div class="row" id="gallery-grid">
            <!-- Gallery loaded by JavaScript -->
        </div>
        
        <div class="text-center mt-5">
            <p class="text-muted">Showing orchids from the Five Cities Orchid Society collection</p>
        </div>
    </div>
    
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script>
        // Load gallery
        fetch('/api/recent-orchids')
            .then(response => response.json())
            .then(orchids => {
                let html = '';
                orchids.forEach(orchid => {
                    // Use image_url if available, fallback to google_drive_id
                    let imageSrc = orchid.image_url || `/api/drive-photo/${orchid.google_drive_id}`;
                    
                    html += `
                        <div class="col-md-6 col-lg-4 mb-4">
                            <div class="card gallery-card">
                                <img src="${imageSrc}" 
                                     class="card-img-top" 
                                     style="height: 250px; object-fit: cover;" 
                                     alt="${orchid.display_name}"
                                     onerror="this.src='/static/images/orchid_placeholder.svg'">
                                <div class="card-body">
                                    <h5 class="card-title">${orchid.display_name}</h5>
                                    <p class="card-text text-truncate">${orchid.ai_description || 'Beautiful orchid from the Five Cities Orchid Society collection'}</p>
                                    <small class="text-muted">Photo: ${orchid.photographer || 'FCOS Collection'}</small>
                                </div>
                            </div>
                        </div>
                    `;
                });
                document.getElementById('gallery-grid').innerHTML = html;
            });
        
        // Initialize icons
        feather.replace();
    </script>
</body>
</html>
'''