#!/usr/bin/env python3
"""
THE ORCHID CONTINUUM - OPTIMIZED VERSION
========================================
Lightweight server focused on core functionality:
✅ 5,973 orchid photo records
✅ 7,376 Dr. Hassler taxonomy entries
✅ Fast, responsive user interface
❌ No heavy background monitoring (causing crashes)
"""

from flask import Flask, render_template, request, render_template_string
from sqlalchemy import create_engine, text
import os
import logging

# Simple logging only
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Create lightweight Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "orchid-continuum-secret")

# Direct database connection (no heavy ORM)
database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url, pool_pre_ping=True) if database_url else None

@app.route('/')
def home():
    """Main page - The Orchid Continuum homepage"""
    try:
        if not engine:
            return "<h1>🌺 The Orchid Continuum</h1><p>Initializing database...</p>"
        
        with engine.connect() as conn:
            # Quick statistics query
            orchid_count = conn.execute(text("SELECT COUNT(*) FROM orchid_record")).scalar() or 0
            taxonomy_count = conn.execute(text("SELECT COUNT(*) FROM orchid_taxonomy")).scalar() or 0
            
            # Recent orchids with photos
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
        body { background: linear-gradient(135deg, #1a0f0a, #2c1810); color: #e0e0e0; min-height: 100vh; }
        .hero { padding: 4rem 0; }
        .card { background: rgba(45, 45, 45, 0.95); border: 1px solid #6b4226; }
        .orchid-img { height: 200px; object-fit: cover; border-radius: 8px; }
        .stat-card { text-align: center; padding: 2rem; }
        .navbar { background: rgba(44, 24, 16, 0.95) !important; }
        h1 { color: #f4e4bc; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">🌺 The Orchid Continuum</a>
            <ul class="navbar-nav ms-auto">
                <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                <li class="nav-item"><a class="nav-link" href="/gallery">Gallery</a></li>
                <li class="nav-item"><a class="nav-link" href="/search">Search</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="hero" style="margin-top: 80px;">
        <div class="container text-center">
            <h1 class="display-3 mb-4">The Orchid Continuum</h1>
            <p class="lead fs-4">The Global Orchid Experience</p>
            <p class="text-muted">Research-grade digital platform by Jeffery S. Parham</p>
            
            <div class="row mt-5">
                <div class="col-md-6 mb-4">
                    <div class="card stat-card">
                        <h2 class="display-4 text-primary">{{ orchid_count:,}}</h2>
                        <h4>Orchid Photo Records</h4>
                        <p class="text-muted">Visual collection</p>
                    </div>
                </div>
                <div class="col-md-6 mb-4">
                    <div class="card stat-card">
                        <h2 class="display-4 text-success">{{ taxonomy_count:,}}</h2>
                        <h4>Taxonomy Entries</h4>
                        <p class="text-muted">Dr. Hassler's research</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="container my-5">
        <h2 class="text-center mb-4">Recent Orchids</h2>
        <div class="row">
            {% for orchid in recent %}
            <div class="col-md-4 mb-4">
                <div class="card h-100">
                    <img src="{{ orchid.image_url }}" class="card-img-top orchid-img" alt="{{ orchid.display_name }}">
                    <div class="card-body">
                        <h5 class="card-title text-primary">{{ orchid.display_name }}</h5>
                        {% if orchid.genus and orchid.species %}
                        <p class="card-text"><em>{{ orchid.genus }} {{ orchid.species }}</em></p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="text-center mt-4">
            <a href="/gallery" class="btn btn-primary btn-lg">Explore Gallery</a>
        </div>
    </div>
    
    <div class="container my-5">
        <div class="row">
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-body text-center">
                        <h4>📚 Scientific Authority</h4>
                        <p>Dr. Michael Hassler's 40+ years of orchid taxonomy research</p>
                        <p class="small text-success">Citation: Hassler, M. (2025)</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-body text-center">
                        <h4>🌍 Global Coverage</h4>
                        <p>GBIF integration: 8+ million orchid occurrences worldwide</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """, orchid_count=orchid_count, taxonomy_count=taxonomy_count, recent=recent)
        
    except Exception as e:
        logger.error(f"Home error: {e}")
        return f"<h1>🌺 Orchid Continuum</h1><p>Server starting up...</p>", 200

@app.route('/gallery')
def gallery():
    """Photo gallery with simple pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 16
        offset = (page - 1) * per_page
        
        with engine.connect() as conn:
            orchids = conn.execute(text("""
                SELECT display_name, genus, species, image_url
                FROM orchid_record 
                WHERE image_url IS NOT NULL 
                ORDER BY created_at DESC 
                LIMIT :limit OFFSET :offset
            """), {'limit': per_page, 'offset': offset}).fetchall()
            
        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Gallery - Orchid Continuum</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1a0f0a, #2c1810); color: #e0e0e0; }
        .card { background: rgba(45, 45, 45, 0.95); border: 1px solid #6b4226; }
        .orchid-img { height: 220px; object-fit: cover; }
        .navbar { background: rgba(44, 24, 16, 0.95) !important; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">🌺 The Orchid Continuum</a>
            <ul class="navbar-nav">
                <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                <li class="nav-item"><a class="nav-link active" href="/gallery">Gallery</a></li>
                <li class="nav-item"><a class="nav-link" href="/search">Search</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h1>Orchid Gallery</h1>
        <p class="text-muted">Page {{ page }} • {{ orchids|length }} orchids</p>
        
        <div class="row">
            {% for orchid in orchids %}
            <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
                <div class="card h-100">
                    <img src="{{ orchid.image_url }}" class="card-img-top orchid-img" alt="{{ orchid.display_name }}">
                    <div class="card-body">
                        <h6 class="card-title">{{ orchid.display_name }}</h6>
                        {% if orchid.genus and orchid.species %}
                        <p class="card-text small text-muted"><em>{{ orchid.genus }} {{ orchid.species }}</em></p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <nav>
            <ul class="pagination justify-content-center">
                {% if page > 1 %}<li class="page-item"><a class="page-link" href="?page={{ page-1 }}">Previous</a></li>{% endif %}
                <li class="page-item active"><span class="page-link">{{ page }}</span></li>
                {% if orchids|length == 16 %}<li class="page-item"><a class="page-link" href="?page={{ page+1 }}">Next</a></li>{% endif %}
            </ul>
        </nav>
    </div>
</body>
</html>
        """, orchids=orchids, page=page)
        
    except Exception as e:
        return f"Gallery error: {e}", 500

@app.route('/search')
def search():
    """Search both photo records and Dr. Hassler taxonomy"""
    query = request.args.get('q', '').strip()
    results = []
    
    if query and engine:
        try:
            with engine.connect() as conn:
                # Search photo records
                photo_results = conn.execute(text("""
                    SELECT 'photo' as type, display_name, genus, species, image_url
                    FROM orchid_record 
                    WHERE LOWER(display_name) LIKE LOWER(:query) 
                       OR LOWER(genus) LIKE LOWER(:query)
                       OR LOWER(species) LIKE LOWER(:query)
                    LIMIT 10
                """), {'query': f'%{query}%'}).fetchall()
                
                # Search taxonomy
                taxonomy_results = conn.execute(text("""
                    SELECT 'taxonomy' as type, scientific_name as display_name, genus, species, NULL as image_url
                    FROM orchid_taxonomy 
                    WHERE LOWER(scientific_name) LIKE LOWER(:query)
                       OR LOWER(genus) LIKE LOWER(:query)
                    LIMIT 10
                """), {'query': f'%{query}%'}).fetchall()
                
                results = list(photo_results) + list(taxonomy_results)
                
        except Exception as e:
            logger.error(f"Search error: {e}")
    
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Search - Orchid Continuum</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1a0f0a, #2c1810); color: #e0e0e0; }
        .card { background: rgba(45, 45, 45, 0.95); border: 1px solid #6b4226; }
        .navbar { background: rgba(44, 24, 16, 0.95) !important; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">🌺 The Orchid Continuum</a>
            <ul class="navbar-nav">
                <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                <li class="nav-item"><a class="nav-link" href="/gallery">Gallery</a></li>
                <li class="nav-item"><a class="nav-link active" href="/search">Search</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h1>Search Orchids</h1>
        <p class="text-muted">Search 5,973 photos + 7,376 Dr. Hassler entries</p>
        
        <form method="GET" class="mb-4">
            <div class="input-group">
                <input type="text" name="q" class="form-control form-control-lg" placeholder="Search orchids..." value="{{ query }}">
                <button class="btn btn-primary" type="submit">Search</button>
            </div>
        </form>
        
        {% if query %}
            <h3>Results for "{{ query }}" ({{ results|length }})</h3>
            {% for result in results %}
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        {% if result.image_url %}
                        <div class="col-md-3">
                            <img src="{{ result.image_url }}" class="img-fluid rounded" style="height: 80px; object-fit: cover;">
                        </div>
                        <div class="col-md-9">
                        {% else %}
                        <div class="col-md-12">
                        {% endif %}
                            <h5>{{ result.display_name }} 
                                <span class="badge bg-{{ 'success' if result.type == 'taxonomy' else 'primary' }}">
                                    {{ 'Taxonomy' if result.type == 'taxonomy' else 'Photo' }}
                                </span>
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
            <div class="alert alert-info">No results found. Try "Cattleya" or "Phalaenopsis"</div>
            {% endif %}
        {% else %}
            <div class="alert alert-info">
                <h4>Search Tips:</h4>
                <ul>
                    <li>Try popular genera: "Cattleya", "Phalaenopsis", "Dendrobium"</li>
                    <li>Searches both photo collection and Dr. Hassler's taxonomy database</li>
                </ul>
            </div>
        {% endif %}
    </div>
</body>
</html>
    """, query=query, results=results)

if __name__ == "__main__":
    logger.info("🌺 The Orchid Continuum - Fast & Lightweight")
    app.run(host="0.0.0.0", port=5000, debug=False)
