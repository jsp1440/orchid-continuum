#!/usr/bin/env python3
"""
MINIMAL ORCHID CONTINUUM SERVER
===============================
Lightweight version focusing on core functionality:
- 5,973 orchid photo records
- 7,376 Dr. Hassler taxonomy entries  
- Basic search and gallery features
- No heavy background monitoring
"""

from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import os
import logging

# Minimal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "orchid-continuum-secret")

# Database connection
database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url, pool_pre_ping=True) if database_url else None

@app.route('/')
def home():
    """Main home page with orchid statistics"""
    try:
        if not engine:
            return render_template_string("""
            <h1>🌺 Orchid Continuum</h1>
            <p>Database connection not available</p>
            """)
        
        with engine.connect() as conn:
            # Get basic statistics
            orchid_count = conn.execute(text("SELECT COUNT(*) FROM orchid_record")).scalar() or 0
            taxonomy_count = conn.execute(text("SELECT COUNT(*) FROM orchid_taxonomy")).scalar() or 0
            
            # Get recent orchids
            recent = conn.execute(text("""
                SELECT display_name, genus, species, image_url 
                FROM orchid_record 
                WHERE image_url IS NOT NULL 
                ORDER BY created_at DESC 
                LIMIT 6
            """)).fetchall()
            
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>The Orchid Continuum</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background-color: #1a1a1a; color: #e0e0e0; }
                .hero { background: linear-gradient(135deg, #2c1810, #1a0f0a); padding: 3rem 0; }
                .card { background-color: #2d2d2d; border: 1px solid #404040; }
                .orchid-img { height: 200px; object-fit: cover; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="hero">
                <div class="container text-center">
                    <h1 class="display-4">🌺 The Orchid Continuum</h1>
                    <p class="lead">The Global Orchid Experience</p>
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h3>{{ orchid_count:,}}</h3>
                                    <p>Orchid Photo Records</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h3>{{ taxonomy_count:,}}</h3>
                                    <p>Dr. Hassler Taxonomy Entries</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container mt-5">
                <h2>Recent Orchids</h2>
                <div class="row">
                    {% for orchid in recent %}
                    <div class="col-md-4 mb-4">
                        <div class="card">
                            {% if orchid.image_url %}
                            <img src="{{ orchid.image_url }}" class="card-img-top orchid-img" alt="{{ orchid.display_name }}">
                            {% endif %}
                            <div class="card-body">
                                <h5 class="card-title">{{ orchid.display_name }}</h5>
                                {% if orchid.genus and orchid.species %}
                                <p class="card-text"><em>{{ orchid.genus }} {{ orchid.species }}</em></p>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="container mt-5">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">📚 Scientific Attribution</h5>
                                <p class="card-text">Taxonomy database includes Dr. Michael Hassler's 40+ years of orchid research</p>
                                <p class="small text-muted">Citation: Hassler, M. (2025). World Orchids Database.</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">🌍 Global Coverage</h5>
                                <p class="card-text">Integrated with GBIF biodiversity data representing 8+ million orchid occurrences worldwide</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """, orchid_count=orchid_count, taxonomy_count=taxonomy_count, recent=recent)
        
    except Exception as e:
        logger.error(f"Home page error: {e}")
        return f"<h1>🌺 Orchid Continuum</h1><p>Error: {e}</p>", 500

@app.route('/gallery')
def gallery():
    """Gallery of orchid photos"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 12
        offset = (page - 1) * per_page
        
        with engine.connect() as conn:
            # Get orchids with images
            orchids = conn.execute(text("""
                SELECT display_name, genus, species, image_url, scientific_name
                FROM orchid_record 
                WHERE image_url IS NOT NULL 
                ORDER BY created_at DESC 
                LIMIT :limit OFFSET :offset
            """), {'limit': per_page, 'offset': offset}).fetchall()
            
            # Get total count for pagination
            total = conn.execute(text("SELECT COUNT(*) FROM orchid_record WHERE image_url IS NOT NULL")).scalar()
            
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Orchid Gallery - The Orchid Continuum</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background-color: #1a1a1a; color: #e0e0e0; }
                .card { background-color: #2d2d2d; border: 1px solid #404040; margin-bottom: 2rem; }
                .orchid-img { height: 250px; object-fit: cover; }
                .navbar { background-color: #2c1810 !important; }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark">
                <div class="container">
                    <a class="navbar-brand" href="/">🌺 Orchid Continuum</a>
                    <ul class="navbar-nav">
                        <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                        <li class="nav-item"><a class="nav-link active" href="/gallery">Gallery</a></li>
                        <li class="nav-item"><a class="nav-link" href="/search">Search</a></li>
                    </ul>
                </div>
            </nav>
            
            <div class="container mt-4">
                <h1>Orchid Photo Gallery</h1>
                <p class="text-muted">Showing {{ orchids|length }} of {{ total:,}} orchids with photos</p>
                
                <div class="row">
                    {% for orchid in orchids %}
                    <div class="col-md-4 mb-4">
                        <div class="card">
                            <img src="{{ orchid.image_url }}" class="card-img-top orchid-img" alt="{{ orchid.display_name }}">
                            <div class="card-body">
                                <h5 class="card-title">{{ orchid.display_name }}</h5>
                                {% if orchid.genus and orchid.species %}
                                <p class="card-text"><em>{{ orchid.genus }} {{ orchid.species }}</em></p>
                                {% endif %}
                                {% if orchid.scientific_name %}
                                <p class="card-text small text-muted">{{ orchid.scientific_name }}</p>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Simple pagination -->
                <nav>
                    <ul class="pagination justify-content-center">
                        {% if page > 1 %}
                        <li class="page-item"><a class="page-link" href="?page={{ page-1 }}">Previous</a></li>
                        {% endif %}
                        <li class="page-item active"><span class="page-link">{{ page }}</span></li>
                        {% if orchids|length == 12 %}
                        <li class="page-item"><a class="page-link" href="?page={{ page+1 }}">Next</a></li>
                        {% endif %}
                    </ul>
                </nav>
            </div>
        </body>
        </html>
        """, orchids=orchids, total=total, page=page)
        
    except Exception as e:
        return f"Gallery error: {e}", 500

@app.route('/search')
def search():
    """Search orchids and taxonomy"""
    query = request.args.get('q', '').strip()
    results = []
    
    if query and engine:
        try:
            with engine.connect() as conn:
                # Search both orchid records and taxonomy
                orchid_results = conn.execute(text("""
                    SELECT 'photo' as type, display_name, genus, species, image_url, scientific_name
                    FROM orchid_record 
                    WHERE LOWER(display_name) LIKE LOWER(:query) 
                       OR LOWER(genus) LIKE LOWER(:query)
                       OR LOWER(species) LIKE LOWER(:query)
                       OR LOWER(scientific_name) LIKE LOWER(:query)
                    LIMIT 20
                """), {'query': f'%{query}%'}).fetchall()
                
                taxonomy_results = conn.execute(text("""
                    SELECT 'taxonomy' as type, scientific_name as display_name, genus, species, NULL as image_url, scientific_name
                    FROM orchid_taxonomy 
                    WHERE LOWER(scientific_name) LIKE LOWER(:query)
                       OR LOWER(genus) LIKE LOWER(:query) 
                       OR LOWER(species) LIKE LOWER(:query)
                    LIMIT 20
                """), {'query': f'%{query}%'}).fetchall()
                
                results = list(orchid_results) + list(taxonomy_results)
                
        except Exception as e:
            logger.error(f"Search error: {e}")
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search - The Orchid Continuum</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #1a1a1a; color: #e0e0e0; }
            .card { background-color: #2d2d2d; border: 1px solid #404040; margin-bottom: 1rem; }
            .navbar { background-color: #2c1810 !important; }
            .search-result { padding: 1rem; border-bottom: 1px solid #404040; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🌺 Orchid Continuum</a>
                <ul class="navbar-nav">
                    <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                    <li class="nav-item"><a class="nav-link" href="/gallery">Gallery</a></li>
                    <li class="nav-item"><a class="nav-link active" href="/search">Search</a></li>
                </ul>
            </div>
        </nav>
        
        <div class="container mt-4">
            <h1>Search Orchids</h1>
            
            <form method="GET" class="mb-4">
                <div class="input-group">
                    <input type="text" name="q" class="form-control" placeholder="Search by name, genus, or species..." value="{{ query }}">
                    <button class="btn btn-primary" type="submit">Search</button>
                </div>
            </form>
            
            {% if query %}
                <p class="text-muted">Found {{ results|length }} results for "{{ query }}"</p>
                
                {% for result in results %}
                <div class="card">
                    <div class="card-body">
                        <div class="row">
                            {% if result.image_url %}
                            <div class="col-md-3">
                                <img src="{{ result.image_url }}" class="img-fluid rounded" style="height: 120px; object-fit: cover;">
                            </div>
                            <div class="col-md-9">
                            {% else %}
                            <div class="col-md-12">
                            {% endif %}
                                <h5>{{ result.display_name }}
                                    {% if result.type == 'taxonomy' %}
                                    <span class="badge bg-success">Dr. Hassler Taxonomy</span>
                                    {% else %}
                                    <span class="badge bg-primary">Photo Record</span>
                                    {% endif %}
                                </h5>
                                {% if result.genus and result.species %}
                                <p class="text-muted"><em>{{ result.genus }} {{ result.species }}</em></p>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
                
                {% if not results %}
                <div class="alert alert-info">No results found for "{{ query }}". Try searching for genus names like "Cattleya" or "Phalaenopsis".</div>
                {% endif %}
            {% else %}
                <div class="alert alert-info">
                    <h4>Search Tips:</h4>
                    <ul>
                        <li>Search by genus (e.g., "Cattleya", "Dendrobium")</li>
                        <li>Search by species name</li>
                        <li>Search includes both photo records and Dr. Hassler's taxonomy database</li>
                    </ul>
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    """, query=query, results=results)

if __name__ == "__main__":
    logger.info("🌺 Starting Minimal Orchid Continuum Server")
    logger.info(f"📊 Database available: {engine is not None}")
    app.run(host="0.0.0.0", port=5000, debug=False)