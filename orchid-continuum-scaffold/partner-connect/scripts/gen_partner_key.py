#!/usr/bin/env python3
"""
Partner Key Generator for Orchid Continuum Partner Connect
Generates API keys, creates partner documentation, and sets up demo data
"""

import os
import sys
import sqlite3
import hashlib
import secrets
import json
import argparse
from pathlib import Path
from datetime import datetime

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def get_db_connection():
    """Get database connection"""
    db_path = Path(__file__).parent.parent / 'services' / 'api' / 'partner_connect.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def create_partner(slug: str, name: str, email: str) -> str:
    """Create partner and return API key"""
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    scopes = [
        "write:records",
        "read:widgets", 
        "read:analytics",
        "read:partner_private_geo"
    ]
    
    conn = get_db_connection()
    try:
        # Insert or update partner
        conn.execute('''
            INSERT OR REPLACE INTO partners (
                slug, name, email, api_key_hash, scopes, quota_per_day, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (slug, name, email, api_key_hash, json.dumps(scopes), 10000, True))
        
        conn.commit()
        print(f"✅ Created partner: {name} ({slug})")
        return api_key
        
    finally:
        conn.close()

def create_partner_docs(slug: str, name: str, api_key: str):
    """Create partner documentation kit"""
    
    # Configuration
    config = {
        'PARTNER_NAME': name,
        'PARTNER_SLUG': slug,
        'API_KEY': api_key,
        'WIDGET_CDN': 'https://cdn.orchidcontinuum.org/widgets',
        'API_BASE': 'http://localhost:8000'  # Dev mode
    }
    
    # Create docs directory
    docs_dir = Path(__file__).parent.parent / 'docs' / 'partners' / slug
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Pitch document
    pitch_content = f"""# The Orchid Continuum Partnership Proposal

## For {config['PARTNER_NAME']}

The Orchid Continuum adds AI search, interactive maps, and bloom timelines to your site via one embed — with full attribution and backlinks on every record. You keep ownership and control; we never write to your database. Choose a low-maintenance sharing path (export URL, shared folder, or CSV/JSON upload), and we handle the rest.

### What We Offer
- 🔍 **AI-powered search** across your collection
- 🗺️ **Interactive maps** with geoprivacy controls  
- 📊 **Phenology charts** showing flowering patterns
- 🏷️ **Full attribution** and backlinks to your site
- 🔒 **Privacy protection** for sensitive location data

### What We Need
- One-time setup with your unique API key
- Access to your orchid data (via export, folder, or upload)
- Your preferred credit line and optional logo

### Technical Benefits
- Zero database modifications required
- Lightweight embeddable widgets
- Real-time updates and search
- Mobile-responsive design
- Full geoprivacy compliance

Let's build something amazing together for the orchid community!

---
*Generated on {datetime.now().strftime('%Y-%m-%d')} for {config['PARTNER_NAME']}*
"""
    
    # FAQ document  
    faq_content = f"""# Frequently Asked Questions - {config['PARTNER_NAME']}

## Partnership Questions

**Q: Does this touch or change our database?**
A: No. The embed runs in the visitor's browser (like YouTube/Maps). No writes to your system.

**Q: Can we stop later?**
A: Yes. Revoke the key or remove the export; we'll stop ingesting and can remove items on request.

**Q: Do we have to share everything?**
A: No. Share only what you choose; you can omit precise GPS or set geoprivacy per record.

**Q: How is location privacy handled?**
A: Exact GPS is kept private. Public maps show generalized locations with uncertainty, following biodiversity best practices.

**Q: What work is required?**
A: Minimal. Pick one: a read-only export URL, a shared folder, or occasional CSV/JSON upload.

## Technical Questions

**Q: How do the widgets work?**
A: They're web components that load data from our API using your unique key. No server-side integration needed.

**Q: What about mobile users?**
A: All widgets are fully responsive and work on mobile devices.

**Q: Can we customize the appearance?**
A: Yes, widgets support light/dark themes and can be styled with CSS.

**Q: How fast do updates appear?**
A: New data appears in widgets within 24 hours of upload/sync.

## Data Questions

**Q: Who owns the data?**
A: You retain full ownership. We're just displaying it with attribution.

**Q: What image formats are supported?**
A: JPEG, PNG, WebP. We optimize images for web display but don't modify originals.

**Q: How do you handle scientific names?**
A: We support full taxonomic hierarchies and synonym matching for better discoverability.

---
*Generated on {datetime.now().strftime('%Y-%m-%d')} for {config['PARTNER_NAME']}*
"""

    # Checklist document
    checklist_content = f"""# Partnership Checklist - {config['PARTNER_NAME']}

## Required Items

✅ **API Key Provided**
- Your unique key: `{config['API_KEY']}`
- Keep this secure and don't share publicly

✅ **Choose Data Sharing Method**
Pick one option:
- [ ] Export URL (automated, recommended)
- [ ] Shared folder (Google Drive, Dropbox, etc.)
- [ ] Manual CSV/JSON upload (occasional)

✅ **Provide Attribution Details**
- [ ] Preferred credit line: "{config['PARTNER_NAME']}"
- [ ] Logo file (optional, PNG/SVG preferred)
- [ ] Website URL for backlinks

✅ **Contact Information**
- [ ] Primary contact email
- [ ] Technical contact (if different)
- [ ] Preferred communication method

## Optional Enhancements

- [ ] Custom widget styling
- [ ] Specific taxonomic focus
- [ ] Geographic region filtering
- [ ] Seasonal data highlighting
- [ ] Integration with existing search

## Data Preparation

- [ ] Review data for accuracy
- [ ] Set geoprivacy preferences
- [ ] Prepare image credits/licenses
- [ ] Test data export format

## Launch Coordination

- [ ] Review widget placement
- [ ] Test on staging site
- [ ] Plan announcement timing
- [ ] Prepare social media content

---

**Next Steps:**
1. Complete this checklist
2. Reply with your data sharing preference  
3. We'll set up your integration within 48 hours

*Generated on {datetime.now().strftime('%Y-%m-%d')} for {config['PARTNER_NAME']}*
"""

    # MOU Geoprivacy document
    mou_content = f"""# Memorandum of Understanding - Geoprivacy
## Between The Orchid Continuum and {config['PARTNER_NAME']}

### Geoprivacy Commitment

**Partner Responsibilities:**
{config['PARTNER_NAME']} may provide precise coordinates to the Orchid Continuum for research purposes. Partner retains full control over geographic data sharing and may designate records with different privacy levels:

- **Public**: Exact coordinates may be shown publicly
- **Partner Private**: Exact coordinates shared only with authorized partners
- **Internal Private**: Coordinates generalized for all public display

**Orchid Continuum Responsibilities:**
Exact coordinates are stored securely and will not be published without Partner's written consent. Public outputs show generalized locations (e.g., to the nearest 10–25 km or by grid/hex) and include a coordinate uncertainty value.

### Technical Implementation

- All location data encrypted at rest
- API endpoints respect geoprivacy settings
- Public maps show generalized coordinates only
- Partner-scoped access available with proper authentication
- Coordinate uncertainty metadata included in all responses

### Data Rights

- Partner may revoke access at any time
- Partner may request removal of specific records
- Partner retains ownership of all submitted data
- Orchid Continuum provides hosting and discovery services only

### Compliance Standards

This agreement follows GBIF Data Publishing Guidelines and iNaturalist Geoprivacy Standards for biodiversity data protection.

### Contact Information

**Partner:** {config['PARTNER_NAME']}
**Orchid Continuum:** Jeffery S. Parham, Five Cities Orchid Society

**Effective Date:** {datetime.now().strftime('%Y-%m-%d')}

---

By participating in the Orchid Continuum Partner Connect program, both parties agree to these geoprivacy protections and data sharing guidelines.

*This MOU ensures responsible sharing of biodiversity data while protecting sensitive species locations.*
"""

    # Integration guide
    integration_content = f"""# Orchid Continuum – Partner Integration Guide
## {config['PARTNER_NAME']}

### Your Unique API Key
```
{config['API_KEY']}
```
**⚠️ Keep this secure** – treat it like a password

### Quick Setup

**1. Add this once in your page `<head>`:**
```html
<script src="{config['WIDGET_CDN']}/ocw-widgets.umd.js"
        data-api-base="{config['API_BASE']}"
        data-api-key="{config['API_KEY']}"
        data-partner="{config['PARTNER_SLUG']}"></script>
```

**2. Place widgets where you want them:**
```html
<!-- Search widget -->
<ocw-search></ocw-search>

<!-- Map widget -->
<ocw-map></ocw-map>

<!-- Phenology widget -->
<ocw-phenology data-taxon="Cattleya labiata"></ocw-phenology>
```

### Alternative Div-based Setup
If custom elements aren't supported, use divs:
```html
<div class="ocw-search"></div>
<div class="ocw-map"></div>
<div class="ocw-phenology" data-taxon="Cattleya labiata"></div>
```

### Data Upload Options

#### Option 1: JSON Batch Upload
```bash
curl -X POST {config['API_BASE']}/partner/upload-json \\
  -H "Authorization: Bearer {config['API_KEY']}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "records": [
      {{
        "source_id": "{slug}-000123",
        "scientific_name": "Cattleya labiata",
        "image_url": "https://example.org/labiata.jpg",
        "credit": "{config['PARTNER_NAME']}",
        "license": "CC-BY-NC",
        "locality": "Brazil",
        "event_date": "2023-10-14",
        "coords": {{"lat": -23.5, "lng": -46.6}},
        "geo_visibility": "partner_private",
        "coordinateUncertaintyInMeters": 25000
      }}
    ]
  }}'
```

#### Option 2: CSV Upload
```bash
curl -X POST {config['API_BASE']}/partner/upload-csv \\
  -H "Authorization: Bearer {config['API_KEY']}" \\
  -F "file=@orchids.csv"
```

**CSV Format:**
```csv
source_id,scientific_name,image_url,credit,license,locality,event_date,lat,lng,geo_visibility,coordinate_uncertainty_m
{slug}-001,Cattleya labiata,https://example.org/image1.jpg,{config['PARTNER_NAME']},CC-BY-NC,Brazil,2023-10-14,-23.5,-46.6,partner_private,25000
```

### Widget Customization

#### Themes
```html
<ocw-search data-theme="dark"></ocw-search>
<ocw-map data-theme="light"></ocw-map>
```

#### Specific Configuration
```html
<!-- Search with custom placeholder -->
<ocw-search data-placeholder="Search our orchid collection..."></ocw-search>

<!-- Map with specific bounds -->
<ocw-map data-bounds="-25,-50,-20,-45"></ocw-map>

<!-- Phenology for specific taxon -->
<ocw-phenology data-taxon="Dendrobium nobile"></ocw-phenology>
```

### API Endpoints

All endpoints require `Authorization: Bearer {config['API_KEY']}`

- `POST /partner/upload-json` - Batch JSON upload
- `POST /partner/upload-csv` - CSV file upload  
- `GET /widgets/search?q=<query>&page=<num>` - Search data
- `GET /widgets/map?bbox=<bounds>&mode=<public|partner>` - Map data
- `GET /widgets/phenology?taxon=<name>` - Phenology data

### Rate Limits
- 10,000 requests per day
- Automatic retry with exponential backoff recommended

### Testing
Test your integration at: [Demo Page](../../public/demo.html)

### Support
- Documentation: https://docs.orchidcontinuum.org
- Issues: https://github.com/orchid-continuum/partner-connect
- Email: partners@orchidcontinuum.org

---
*Integration guide generated on {datetime.now().strftime('%Y-%m-%d')} for {config['PARTNER_NAME']}*
"""

    # Sample email
    email_content = f"""Subject: Your one-line AI upgrade — key + guide inside

Hi {config['PARTNER_NAME']},

Here's your **Partner Kit** to add AI search, maps, and bloom timelines to your site. It's one embed + one key — no changes to your database.

**Your Details:**
- API key: `{config['API_KEY']}`
- Partner slug: `{config['PARTNER_SLUG']}`
- Documentation: See attached integration guide

**Quick Start:**
1. Add our widget script to your page
2. Place `<ocw-search></ocw-search>` where you want search
3. Upload your data via JSON or CSV (sample formats included)

**What's Included:**
- 🔍 AI-powered search across your collection
- 🗺️ Interactive maps with privacy controls
- 📊 Flowering timeline charts
- 🏷️ Full attribution back to your site

Pick your sharing option (export URL, shared folder, or CSV/JSON upload). Exact GPS stays private; public maps show generalized locations with uncertainty and attribution.

**Demo:** See it working at http://localhost:8000/demo.html

Ready to boost your orchid collection's discoverability? Let's make it happen!

Warmly,  
Jeffery S. Parham  
Five Cities Orchid Society  
The Orchid Continuum

---

**Technical Support:**  
- Email: partners@orchidcontinuum.org
- Documentation: https://docs.orchidcontinuum.org
- GitHub: https://github.com/orchid-continuum/partner-connect

*This email was generated automatically on {datetime.now().strftime('%Y-%m-%d')}*
"""

    # Write all documents
    documents = {
        'pitch.md': pitch_content,
        'faq.md': faq_content, 
        'checklist.md': checklist_content,
        'mou_geoprivacy.md': mou_content,
        'integration_guide.md': integration_content,
        'sample_email.md': email_content
    }
    
    for filename, content in documents.items():
        file_path = docs_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"📄 Created docs in: {docs_dir}")
    return config

def update_demo_html(api_key: str, partner_slug: str):
    """Update demo.html with partner key"""
    demo_path = Path(__file__).parent.parent / 'public' / 'demo.html'
    
    demo_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orchid Continuum Partner Connect - Demo</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
            color: #2c3e50;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 32px;
        }}
        .header p {{
            color: #7f8c8d;
            font-size: 18px;
            margin: 0;
        }}
        .widget-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        .widget-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .widget-section h2 {{
            color: #34495e;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 24px;
        }}
        .widget-section p {{
            color: #7f8c8d;
            margin-bottom: 20px;
        }}
        .code-block {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 12px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        .api-info {{
            background: #e8f4f8;
            border: 1px solid #d4edda;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .api-info h3 {{
            color: #155724;
            margin-top: 0;
        }}
        .api-key {{
            font-family: 'Monaco', 'Consolas', monospace;
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
            word-break: break-all;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-online {{
            background: #27ae60;
        }}
        .status-offline {{
            background: #e74c3c;
        }}
        @media (max-width: 768px) {{
            .widget-grid {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 24px;
            }}
            .header p {{
                font-size: 16px;
            }}
        }}
    </style>
    <script src="/apps/widgets/dist/ocw-widgets.umd.js"
            data-api-base="http://localhost:8000"
            data-api-key="{api_key}"
            data-partner="{partner_slug}"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌺 Orchid Continuum Partner Connect</h1>
            <p>Interactive widgets powered by AI and geoprivacy controls</p>
            <div class="api-info">
                <h3>Demo Configuration</h3>
                <p><strong>Partner:</strong> {partner_slug}</p>
                <p><strong>API Key:</strong> <span class="api-key">{api_key}</span></p>
                <p><strong>API Base:</strong> http://localhost:8000</p>
                <p><span class="status-indicator status-online"></span> API Status: Online</p>
            </div>
        </div>

        <div class="widget-grid">
            <div class="widget-section">
                <h2>🔍 Search Widget</h2>
                <p>AI-powered search across orchid collections with real-time results and detailed metadata.</p>
                <ocw-search></ocw-search>
                <div class="code-block">&lt;ocw-search&gt;&lt;/ocw-search&gt;</div>
            </div>

            <div class="widget-section">
                <h2>🗺️ Map Widget</h2>
                <p>Interactive map with geoprivacy controls. Toggle between public and partner-private data modes.</p>
                <ocw-map></ocw-map>
                <div class="code-block">&lt;ocw-map&gt;&lt;/ocw-map&gt;</div>
            </div>

            <div class="widget-section">
                <h2>📊 Phenology Widget</h2>
                <p>Flowering timeline charts showing seasonal patterns. Try different taxa to see various blooming cycles.</p>
                <ocw-phenology data-taxon="Cattleya"></ocw-phenology>
                <div class="code-block">&lt;ocw-phenology data-taxon="Cattleya"&gt;&lt;/ocw-phenology&gt;</div>
            </div>
        </div>

        <div class="footer">
            <h3>Integration Instructions</h3>
            <p>Copy the widgets above into your website. Each widget is a self-contained web component that works anywhere.</p>
            
            <div class="code-block">
&lt;!-- Include once in your page head --&gt;
&lt;script src="https://cdn.orchidcontinuum.org/widgets/ocw-widgets.umd.js"
        data-api-base="https://api.orchidcontinuum.org"
        data-api-key="{api_key}"
        data-partner="{partner_slug}"&gt;&lt;/script&gt;

&lt;!-- Use anywhere on your page --&gt;
&lt;ocw-search&gt;&lt;/ocw-search&gt;
&lt;ocw-map&gt;&lt;/ocw-map&gt;
&lt;ocw-phenology data-taxon="Your-Taxon"&gt;&lt;/ocw-phenology&gt;
            </div>

            <p><strong>The Orchid Continuum Partner Connect</strong><br>
            Empowering orchid communities through AI and open data</p>
        </div>
    </div>

    <script>
        // Health check for demo
        async function checkApiHealth() {{
            try {{
                const response = await fetch('http://localhost:8000/health');
                const data = await response.json();
                console.log('API Health:', data);
            }} catch (error) {{
                console.warn('API not available:', error);
                document.querySelector('.status-indicator').className = 'status-indicator status-offline';
                document.querySelector('.status-indicator').nextSibling.textContent = ' API Status: Offline';
            }}
        }}
        
        // Check API health on load
        checkApiHealth();
    </script>
</body>
</html>"""

    # Ensure public directory exists
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(demo_path, 'w', encoding='utf-8') as f:
        f.write(demo_content)
    
    print(f"🌐 Updated demo page: {demo_path}")

def seed_demo_data():
    """Seed database with demo records for testing"""
    conn = get_db_connection()
    try:
        # Get partner IDs
        partners = conn.execute("SELECT id, slug FROM partners").fetchall()
        partner_map = {p['slug']: p['id'] for p in partners}
        
        # Demo records for gary-yong-gee
        if 'gary-yong-gee' in partner_map:
            gyg_records = [
                {
                    'source_id': 'gyg-001',
                    'scientific_name': 'Cattleya labiata',
                    'image_url': 'https://example.com/cattleya1.jpg',
                    'credit': 'Gary Yong Gee',
                    'license': 'CC-BY-NC',
                    'locality': 'Brazil, Rio de Janeiro',
                    'event_date': '2023-10-15',
                    'lat': -22.9068, 'lng': -43.1729,
                    'geo_visibility': 'public'
                },
                {
                    'source_id': 'gyg-002', 
                    'scientific_name': 'Dendrobium nobile',
                    'image_url': 'https://example.com/dendrobium1.jpg',
                    'credit': 'Gary Yong Gee',
                    'license': 'CC-BY-NC',
                    'locality': 'Thailand, Chiang Mai',
                    'event_date': '2023-08-22',
                    'lat': 18.7883, 'lng': 98.9853,
                    'geo_visibility': 'partner_private'
                },
                {
                    'source_id': 'gyg-003',
                    'scientific_name': 'Phalaenopsis amabilis',
                    'image_url': 'https://example.com/phal1.jpg', 
                    'credit': 'Gary Yong Gee',
                    'license': 'CC-BY-NC',
                    'locality': 'Indonesia, Java',
                    'event_date': '2023-12-03',
                    'lat': -7.2575, 'lng': 112.7521,
                    'geo_visibility': 'public'
                }
            ]
            
            for record in gyg_records:
                # Insert record
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO records (
                        partner_id, source_id, scientific_name, image_url,
                        credit, license, locality, event_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    partner_map['gary-yong-gee'], record['source_id'],
                    record['scientific_name'], record['image_url'],
                    record['credit'], record['license'],
                    record['locality'], record['event_date']
                ))
                
                record_id = cursor.lastrowid
                
                # Insert location
                conn.execute('''
                    INSERT OR REPLACE INTO locations (
                        record_id, lat, lng, geo_visibility, coordinate_uncertainty_m
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (record_id, record['lat'], record['lng'], record['geo_visibility'], 25000))
                
                # Add phenology data (flowering months)
                flowering_months = {
                    'Cattleya labiata': [10, 11, 12],  # Oct-Dec
                    'Dendrobium nobile': [2, 3, 4],   # Feb-Apr
                    'Phalaenopsis amabilis': [12, 1, 2] # Dec-Feb
                }.get(record['scientific_name'], [])
                
                for month in flowering_months:
                    conn.execute('''
                        INSERT OR IGNORE INTO phenology_months (record_id, month)
                        VALUES (?, ?)
                    ''', (record_id, month))
        
        # Demo records for roger
        if 'roger' in partner_map:
            roger_records = [
                {
                    'source_id': 'roger-001',
                    'scientific_name': 'Oncidium flexuosum',
                    'image_url': 'https://example.com/oncidium1.jpg',
                    'credit': 'Roger',
                    'license': 'CC-BY-SA',
                    'locality': 'Brazil, Minas Gerais',
                    'event_date': '2023-09-18',
                    'lat': -19.9167, 'lng': -43.9345,
                    'geo_visibility': 'public'
                },
                {
                    'source_id': 'roger-002',
                    'scientific_name': 'Vanda coerulea',
                    'image_url': 'https://example.com/vanda1.jpg',
                    'credit': 'Roger',
                    'license': 'CC-BY-SA',
                    'locality': 'Myanmar, Shan State',
                    'event_date': '2023-11-07',
                    'lat': 22.0015, 'lng': 96.4668,
                    'geo_visibility': 'internal_private'
                }
            ]
            
            for record in roger_records:
                # Insert record
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO records (
                        partner_id, source_id, scientific_name, image_url,
                        credit, license, locality, event_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    partner_map['roger'], record['source_id'],
                    record['scientific_name'], record['image_url'],
                    record['credit'], record['license'],
                    record['locality'], record['event_date']
                ))
                
                record_id = cursor.lastrowid
                
                # Insert location
                conn.execute('''
                    INSERT OR REPLACE INTO locations (
                        record_id, lat, lng, geo_visibility, coordinate_uncertainty_m
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (record_id, record['lat'], record['lng'], record['geo_visibility'], 50000))
                
                # Add phenology data
                flowering_months = {
                    'Oncidium flexuosum': [9, 10, 11],  # Sep-Nov
                    'Vanda coerulea': [11, 12, 1]       # Nov-Jan
                }.get(record['scientific_name'], [])
                
                for month in flowering_months:
                    conn.execute('''
                        INSERT OR IGNORE INTO phenology_months (record_id, month)
                        VALUES (?, ?)
                    ''', (record_id, month))
        
        conn.commit()
        print("🌱 Seeded demo data")
        
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Generate partner keys and documentation')
    parser.add_argument('--slug', help='Partner slug (e.g., gary-yong-gee)')
    parser.add_argument('--name', help='Partner name (e.g., Gary Yong Gee)')
    parser.add_argument('--email', help='Partner email')
    parser.add_argument('--seed-defaults', action='store_true', help='Create gary-yong-gee and roger partners')
    
    args = parser.parse_args()
    
    if args.seed_defaults:
        # Create default partners
        partners = [
            ('gary-yong-gee', 'Gary Yong Gee', 'gary@example.com'),
            ('roger', 'Roger', 'roger@example.com')
        ]
        
        api_keys = {}
        for slug, name, email in partners:
            api_key = create_partner(slug, name, email)
            api_keys[slug] = api_key
            config = create_partner_docs(slug, name, api_key)
            print(f"📋 Created partner kit for {name}")
        
        # Update demo with first partner
        if api_keys:
            first_partner = list(api_keys.keys())[0]
            update_demo_html(api_keys[first_partner], first_partner)
        
        # Seed demo data
        seed_demo_data()
        
        print(f"\n✅ Setup complete!")
        print(f"🔗 View demo at: http://localhost:8000/demo.html")
        print(f"📚 Partner docs in: docs/partners/")
        
    elif args.slug and args.name and args.email:
        # Create specific partner
        api_key = create_partner(args.slug, args.name, args.email)
        config = create_partner_docs(args.slug, args.name, api_key)
        update_demo_html(api_key, args.slug)
        
        print(f"\n✅ Created partner: {args.name}")
        print(f"🔑 API Key: {api_key}")
        print(f"📚 Docs: docs/partners/{args.slug}/")
        
    else:
        print("Usage:")
        print("  python gen_partner_key.py --seed-defaults")
        print("  python gen_partner_key.py --slug=partner-name --name='Partner Name' --email=email@example.com")

if __name__ == '__main__':
    main()