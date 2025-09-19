# Orchid Continuum Partner Connect

Minimal partner integration system with API key management, geoprivacy controls, and embeddable widgets.

## Features

- **API Key System**: One key per partner with scopes and rate limiting
- **Partner Endpoints**: JSON/CSV batch upload with upsert capabilities  
- **Widget System**: Search, map, and phenology widgets as UMD bundle
- **Geoprivacy**: Coordinate generalization with uncertainty metadata
- **Partner Kit Generator**: Auto-generates docs, keys, and demo integration

## Quick Start

### 1. Install Dependencies

```bash
# API dependencies
pip install -r requirements.txt

# Widget dependencies  
cd apps/widgets
npm install
```

### 2. Build Widgets

```bash
cd apps/widgets
npm run build
```

### 3. Generate Partner Keys

```bash
cd scripts
python gen_partner_key.py --seed-defaults
```

This creates:
- Partners: `gary-yong-gee` and `roger`
- API keys with full scopes
- Complete documentation kits
- Demo data
- Updated demo.html

### 4. Start API Server

```bash
cd services/api
python main.py
```

### 5. View Demo

Open `http://localhost:8000/demo.html` to see working widgets.

## API Endpoints

All endpoints require `Authorization: Bearer <API_KEY>`

### Partner Upload
- `POST /partner/upload-json` - Batch JSON upload
- `POST /partner/upload-csv` - CSV file upload

### Widget Data (Read-only)
- `GET /widgets/search?q=<query>&page=<num>` - Search records
- `GET /widgets/map?bbox=<bounds>&mode=<public|partner>` - Map data with geoprivacy
- `GET /widgets/phenology?taxon=<name>` - Flowering timeline data

## Widget Integration

### Basic Setup
```html
<script src="/apps/widgets/dist/ocw-widgets.umd.js"
        data-api-base="http://localhost:8000"
        data-api-key="your-api-key"
        data-partner="your-slug"></script>

<ocw-search></ocw-search>
<ocw-map></ocw-map>
<ocw-phenology data-taxon="Cattleya"></ocw-phenology>
```

### Alternative Div-based
```html
<div class="ocw-search"></div>
<div class="ocw-map"></div>
<div class="ocw-phenology" data-taxon="Cattleya"></div>
```

## Data Upload Formats

### JSON Format
```json
{
  "records": [
    {
      "source_id": "unique-per-partner",
      "scientific_name": "Cattleya labiata",
      "image_url": "https://example.org/image.jpg",
      "credit": "Photographer Name",
      "license": "CC-BY-NC",
      "locality": "Brazil, Rio de Janeiro",
      "event_date": "2023-10-14",
      "coords": {"lat": -22.9, "lng": -43.2},
      "geo_visibility": "partner_private",
      "coordinateUncertaintyInMeters": 25000
    }
  ]
}
```

### CSV Format
```csv
source_id,scientific_name,image_url,credit,license,locality,event_date,lat,lng,geo_visibility,coordinate_uncertainty_m
example-001,Cattleya labiata,https://example.org/image.jpg,Photographer,CC-BY-NC,Brazil,-22.9,-43.2,partner_private,25000
```

## Geoprivacy Levels

- **public**: Exact coordinates may be shown publicly
- **partner_private**: Exact coords only with `read:partner_private_geo` scope
- **internal_private**: Always generalized for public display

Public responses automatically generalize coordinates to 25km grid cells and include `coordinateUncertaintyInMeters`.

## Partner Documentation

Each partner gets a complete kit in `docs/partners/<slug>/`:

- `pitch.md` - Partnership proposal
- `faq.md` - Frequently asked questions  
- `checklist.md` - Setup requirements
- `integration_guide.md` - Technical integration with API key
- `mou_geoprivacy.md` - Geoprivacy agreement
- `sample_email.md` - Outreach email template

## Database Schema

```sql
-- Partners with API keys and scopes
partners(id, slug, name, email, api_key_hash, scopes, quota_per_day, active)

-- Records with partner ownership
records(id, partner_id, source_id, scientific_name, image_url, credit, license, locality, event_date)

-- Locations with geoprivacy controls  
locations(id, record_id, lat, lng, elevation_m, geo_visibility, coordinate_uncertainty_m)

-- Phenology (flowering months)
phenology_months(record_id, month)

-- Audit trail
curation_events(id, record_id, action, actor)
```

## Rate Limiting

- 10,000 requests per day per API key
- Sliding window implementation
- Returns 429 with Retry-After header

## Testing Geoprivacy

```python
# Test coordinate generalization
from main import generalize_coords

# Exact coordinates
lat, lng = -22.9068, -43.1729

# Generalized (public display)
gen_lat, gen_lng = generalize_coords(lat, lng, cell_km=25)
print(f"Original: {lat}, {lng}")
print(f"Generalized: {gen_lat}, {gen_lng}")
```

## Production Notes

- Replace SQLite with PostgreSQL + PostGIS
- Use Redis for rate limiting storage
- Add proper logging and monitoring
- Configure CORS for production domains
- Use environment variables for configuration

## File Structure

```
partner-connect/
├── services/api/           # FastAPI backend
├── apps/widgets/          # Vite widget build
├── scripts/               # Partner key generator
├── docs/partners/         # Generated partner kits
├── public/               # Demo page
└── README.md
```