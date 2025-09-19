"""
Orchid Interaction Explorer API Routes
Serves canonical ecosystem data for the interactive widget
"""

from flask import Blueprint, jsonify, request, render_template_string
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Create blueprint
orchid_interaction_bp = Blueprint('orchid_interaction', __name__)

# Load ecosystem data
ECOSYSTEM_DATA = {}

def load_ecosystem_data():
    """Load canonical ecosystem data from exports"""
    global ECOSYSTEM_DATA
    
    ecosystem_file = Path("exports/ecosystem/canonical/orchid_ecosystem_complete.json")
    if ecosystem_file.exists():
        with open(ecosystem_file, 'r') as f:
            ECOSYSTEM_DATA = json.load(f)
        print(f"✅ Loaded {len(ECOSYSTEM_DATA)} orchid ecosystem records")
    else:
        print("⚠️ Ecosystem data not found - run orchid_ecosystem_integrator.py first")

def find_species_by_taxon_key(taxon_key: str) -> Optional[Dict[str, Any]]:
    """Find species data by GBIF taxon key"""
    
    # Search through ecosystem data
    for gbif_id, record in ECOSYSTEM_DATA.items():
        if str(record.get('taxon', {}).get('acceptedTaxonKey', '')) == str(taxon_key):
            return record
    
    # If not found by taxon key, try by GBIF ID
    if taxon_key in ECOSYSTEM_DATA:
        return ECOSYSTEM_DATA[taxon_key]
    
    return None

def enhance_species_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance species data for widget display"""
    
    if not record:
        return {}
    
    # Ensure all required sections exist
    enhanced = {
        'taxon': record.get('taxon', {}),
        'distribution': record.get('distribution', {}),
        'interactions': {
            'pollinators': record.get('interactions', {}).get('pollinators', []),
            'mycorrhiza': record.get('interactions', {}).get('mycorrhiza', []),
            'mimicry': record.get('interactions', {}).get('mimicry', [])
        },
        'uses': {
            'food': record.get('uses', {}).get('food', []),
            'medicine': record.get('uses', {}).get('medicine', []),
            'trade': record.get('uses', {}).get('trade', [])
        },
        'attribution': record.get('attribution', {
            'gbifDatasets': [],
            'interactionSources': [],
            'ethnobotanySources': [],
            'lastUpdated': ''
        })
    }
    
    return enhanced

@orchid_interaction_bp.route('/api/continuum/species/<taxon_key>.json')
def get_species_data(taxon_key):
    """API endpoint for species ecosystem data"""
    
    try:
        # Find species in ecosystem data
        record = find_species_by_taxon_key(taxon_key)
        
        if not record:
            return jsonify({
                'error': 'Species not found',
                'taxonKey': taxon_key,
                'message': 'No ecosystem data available for this taxon key'
            }), 404
        
        # Enhance data for widget
        enhanced_data = enhance_species_data(record)
        
        return jsonify(enhanced_data)
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@orchid_interaction_bp.route('/orchid-explorer')
def orchid_explorer_widget():
    """Serve the Orchid Interaction Explorer widget"""
    
    # Load the widget HTML template
    widget_html = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Orchid Interaction Explorer - Five Cities Orchid Society</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #f8f9fa; }
    header { padding: 16px 20px; border-bottom: 2px solid #2d5aa0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .header-content { max-width: 1200px; margin: 0 auto; }
    .logo { font-size: 24px; font-weight: 700; color: #2d5aa0; margin-bottom: 8px; }
    .wrap { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .search-section { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .row { display: grid; grid-template-columns: 1fr; gap: 20px; margin-top: 20px; }
    @media (min-width: 1000px){ .row { grid-template-columns: 2fr 1fr; } }
    #map { height: 450px; border: 1px solid #e5e5e5; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h2 { margin: 0 0 16px; font-size: 20px; color: #2d5aa0; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; }
    h3 { margin: 16px 0 8px; font-size: 16px; color: #495057; }
    small.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: #666; background: #f8f9fa; padding: 4px 8px; border-radius: 4px; }
    .card { border: 1px solid #e9ecef; border-radius: 12px; padding: 20px; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .interaction-item { margin-bottom: 16px; padding: 12px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #2d5aa0; }
    .interaction-item strong { color: #2d5aa0; }
    .pill { display:inline-block; padding:4px 12px; border:1px solid #2d5aa0; border-radius:20px; margin:2px 4px 2px 0; font-size:12px; background:#e8f0fe; color:#2d5aa0; font-weight:600; }
    .evidence-list { margin-top: 8px; }
    .evidence-list li { margin-bottom: 4px; font-size: 13px; color: #6c757d; }
    footer { margin-top: 24px; padding: 20px; background: white; border-radius: 12px; font-size: 13px; color: #6c757d; border: 1px solid #e9ecef; }
    .footer-links { margin-top: 12px; }
    a { color: #2d5aa0; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .search-input { width: 300px; padding: 12px 16px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 16px; }
    .search-input:focus { outline: none; border-color: #2d5aa0; box-shadow: 0 0 0 3px rgba(45, 90, 160, 0.1); }
    .load-btn { padding: 12px 24px; background: #2d5aa0; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin-left: 12px; }
    .load-btn:hover { background: #1e3a6f; }
    .no-data { color: #6c757d; font-style: italic; padding: 16px; text-align: center; background: #f8f9fa; border-radius: 8px; }
    .species-info { margin-top: 12px; }
    .species-info h1 { margin: 0; color: #2d5aa0; font-size: 28px; }
    .species-info .rank { color: #6c757d; font-size: 16px; margin-top: 4px; }
  </style>
  <!-- MapLibre (lightweight, open) -->
  <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
  <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
</head>
<body>
  <header>
    <div class="header-content">
      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <div>
          <div class="logo">🌺 Orchid Interaction Explorer</div>
          <div style="color: #6c757d;">Five Cities Orchid Society - Ecosystem Relationships Database</div>
          <div style="margin-top: 8px;">
            <a href="/static/docs/orchid_interaction_explorer_guide.md" target="_blank" 
               style="color: #6B3FA0; text-decoration: none; font-size: 14px;">
              📖 User Guide & FAQ
            </a>
          </div>
        </div>
        <div style="display: flex; gap: 12px;">
          <a href="/" style="background: #6B3FA0; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px;">
            🏠 Home
          </a>
          <a href="/gallery" style="background: #28a745; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px;">
            🖼️ Gallery
          </a>
        </div>
      </div>
    </div>
  </header>

  <div class="wrap">
    <div class="search-section">
      <h2>🔍 Explore Orchid Ecosystem Relationships</h2>
      <div style="display: flex; align-items: center; flex-wrap: wrap;">
        <label style="display: block; margin-right: 16px;">
          <strong>Enter Orchid Genus or Species Name:</strong><br>
          <input id="taxonKey" class="search-input" placeholder="e.g., Cattleya, Orchis mascula, Dendrobium" />
        </label>
        <button id="load" class="load-btn">🔍 Explore Species</button>
      </div>
      <div class="species-info" id="speciesInfo" style="display: none;">
        <h1 id="sciName"></h1>
        <div class="rank" id="rankInfo"></div>
      </div>
      <div style="margin-top: 12px; font-size: 14px; color: #6c757d;">
        💡 <strong>Try these examples:</strong> 
        <a href="#" onclick="searchByName('Cattleya')">Cattleya</a> • 
        <a href="#" onclick="searchByName('Orchis mascula')">Orchis mascula</a> • 
        <a href="#" onclick="searchByName('Dendrobium')">Dendrobium</a> •
        <a href="#" onclick="searchByName('Phalaenopsis')">Phalaenopsis</a>
      </div>
    </div>

    <div class="row" id="mainContent" style="display: none;">
      <div class="card">
        <h2>🗺️ Distribution Map</h2>
        <div id="map"></div>
        <div style="margin-top: 12px; font-size: 13px; color: #6c757d;">
          Map shows GBIF occurrence density overlay. Darker areas indicate higher observation density.
        </div>
      </div>
      
      <div class="card">
        <h2>🐝 Ecosystem Interactions</h2>
        
        <h3>Pollinators</h3>
        <div id="pollinators"></div>
        
        <h3>🍄 Mycorrhizal Associations</h3>
        <div id="myco"></div>
        
        <h3>🎭 Mimicry Strategies</h3>
        <div id="mimicry"></div>
      </div>
    </div>

    <div class="card" id="usesSection" style="margin-top: 20px; display: none;">
      <h2>🌿 Traditional Uses & Applications</h2>
      <div id="uses"></div>
    </div>
    
    <div class="card" id="refsSection" style="margin-top: 20px; display: none;">
      <h2>📚 Data Sources & Attribution</h2>
      <div id="refs"></div>
    </div>
    
    <footer>
      <div>
        <strong>🌺 Five Cities Orchid Society - Orchid Interaction Explorer</strong><br>
        Built on GBIF occurrence data, Global Biotic Interactions (GloBI), and peer-reviewed literature. 
        This tool integrates orchid distribution, pollination networks, mycorrhizal relationships, and traditional uses.
      </div>
      <div class="footer-links">
        <a href="/">← Back to Main Site</a> • 
        <a href="/gallery">Orchid Gallery</a> • 
        <a href="/compare">Compare Orchids</a> • 
        <a href="/weather-widget">Weather Widget</a>
      </div>
    </footer>
  </div>

  <script>
    const API_BASE = '/api/continuum/species';

    const map = new maplibregl.Map({
      container: 'map',
      style: {
        "version": 8,
        "sources": {
          "basemap": {
            "type": "raster",
            "tiles": [
              "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            ],
            "tileSize": 256,
            "attribution": "© OpenStreetMap contributors"
          }
        },
        "layers": [
          { "id": "basemap", "type": "raster", "source": "basemap" }
        ]
      },
      center: [0, 20],
      zoom: 2
    });

    function addDensityLayer(taxonKey){
      const id = 'density';
      if (map.getSource(id)) { 
        map.removeLayer(id); 
        map.removeSource(id); 
      }
      
      map.addSource(id, {
        "type": "raster",
        "tiles": [
          `https://api.gbif.org/v2/map/occurrence/density/{z}/{x}/{y}.png?taxonKey=${taxonKey}&style=classic-v2.point`
        ],
        "tileSize": 256
      });
      
      map.addLayer({ 
        "id": id, 
        "type": "raster", 
        "source": id, 
        "paint": { "raster-opacity": 0.7 } 
      });
    }

    function pill(text, type = 'default'){
      const span = document.createElement('span'); 
      span.className = 'pill'; 
      span.textContent = text;
      if (type === 'food') span.style.background = '#e8f5e8';
      if (type === 'medicine') span.style.background = '#ffe8e8';
      if (type === 'trade') span.style.background = '#fff3e0';
      return span;
    }

    function citeList(arr){
      if (!arr || !arr.length) return '<div class="no-data">No citations available</div>';
      const ul = document.createElement('ul');
      ul.className = 'evidence-list';
      arr.forEach(e => {
        const li = document.createElement('li');
        if (e.type && e.value) {
          li.innerHTML = `<strong>${e.type.toUpperCase()}:</strong> ${e.value}`;
          if (e.verbatim) li.innerHTML += ` <em>(${e.verbatim})</em>`;
        } else {
          li.textContent = typeof e === 'string' ? e : JSON.stringify(e);
        }
        ul.appendChild(li);
      });
      return ul.outerHTML;
    }

    async function loadSpecies(taxonKey){
      try {
        const res = await fetch(`${API_BASE}/${taxonKey}.json`);
        if(!res.ok){ 
          alert(`Species data not found for taxon key: ${taxonKey}\\nPlease check the taxon key and try again.`); 
          return; 
        }
        
        const data = await res.json();
        console.log('Loaded species data:', data);

        // Show main content
        document.getElementById('mainContent').style.display = 'grid';
        document.getElementById('usesSection').style.display = 'block';
        document.getElementById('refsSection').style.display = 'block';
        
        // Update species info
        const sciName = data.taxon?.acceptedScientificName || data.taxon?.scientificName || 'Unknown Species';
        const rank = data.taxon?.taxonRank || 'Unknown Rank';
        
        document.getElementById('sciName').textContent = sciName;
        document.getElementById('rankInfo').textContent = `Taxonomic Rank: ${rank.charAt(0).toUpperCase() + rank.slice(1).toLowerCase()}`;
        document.getElementById('speciesInfo').style.display = 'block';

        // Map layer - use the taxon key for GBIF density
        const gbifTaxonKey = data.taxon?.acceptedTaxonKey || taxonKey;
        addDensityLayer(gbifTaxonKey);

        // Pollinators
        const pol = document.getElementById('pollinators'); 
        pol.innerHTML = '';
        const pollinators = data.interactions?.pollinators || [];
        
        if (pollinators.length > 0) {
          pollinators.forEach(p => {
            const div = document.createElement('div'); 
            div.className = 'interaction-item';
            const title = p.pollinatorTaxon?.name || 'Unknown pollinator';
            const interaction = p.interactionType || 'pollination';
            const confidence = p.confidence || 'unknown';
            
            div.innerHTML = `
              <strong>🐝 ${title}</strong> 
              <small style="background: #e8f0fe; padding: 2px 8px; border-radius: 12px; margin-left: 8px;">
                ${interaction} • confidence: ${confidence}
              </small>
              ${citeList(p.evidence)}
            `;
            pol.appendChild(div);
          });
        } else {
          pol.innerHTML = '<div class="no-data">🔍 No pollinator interactions documented yet. Check back as we expand our database!</div>';
        }

        // Mycorrhiza
        const my = document.getElementById('myco'); 
        my.innerHTML = '';
        const mycorrhiza = data.interactions?.mycorrhiza || [];
        
        if (mycorrhiza.length > 0) {
          mycorrhiza.forEach(m => {
            const title = m.fungusTaxon?.name || 'Unknown fungus';
            const relationship = m.relationship || 'mycorrhizal association';
            const lifeStage = m.lifeStage || 'all stages';
            const confidence = m.confidence || 'medium';
            
            const div = document.createElement('div');
            div.className = 'interaction-item';
            div.innerHTML = `
              <strong>🍄 ${title}</strong>
              <small style="background: #f0f8e8; padding: 2px 8px; border-radius: 12px; margin-left: 8px;">
                ${relationship} • ${lifeStage} • confidence: ${confidence}
              </small>
              ${citeList(m.evidence)}
            `;
            my.appendChild(div);
          });
        } else {
          my.innerHTML = '<div class="no-data">🔬 No mycorrhizal associations documented yet.</div>';
        }

        // Mimicry strategies
        const mim = document.getElementById('mimicry');
        mim.innerHTML = '';
        const mimicry = data.interactions?.mimicry || [];
        
        if (mimicry.length > 0) {
          mimicry.forEach(m => {
            const div = document.createElement('div');
            div.className = 'interaction-item';
            div.innerHTML = `
              <strong>🎭 ${m.class || 'Mimicry Strategy'}</strong>
              <div style="margin-top: 8px;">
                <strong>Signals:</strong> ${(m.signal || []).join(', ')}<br>
                <strong>Model:</strong> ${m.modelSpecies || 'Unknown'}<br>
                <strong>Notes:</strong> ${m.notes || 'No additional notes'}
              </div>
              ${citeList(m.evidence)}
            `;
            mim.appendChild(div);
          });
        } else {
          mim.innerHTML = '<div class="no-data">🎭 No mimicry strategies documented yet.</div>';
        }

        // Traditional uses
        const uses = document.getElementById('uses'); 
        uses.innerHTML = '';
        let hasUses = false;
        
        ['food', 'medicine', 'trade'].forEach(useType => {
          const useData = data.uses?.[useType] || [];
          useData.forEach(u => {
            hasUses = true;
            const div = document.createElement('div');
            div.className = 'interaction-item';
            div.appendChild(pill(useType, useType));
            
            let details = '';
            if (useType === 'food' && u.part) details += `Part used: ${u.part} • `;
            if (u.preparation) details += `Preparation: ${u.preparation} • `;
            if (u.status) details += `Status: ${u.status} • `;
            if (u.region) details += `Regions: ${u.region.join(', ')}`;
            
            div.innerHTML += `<div style="margin-top: 8px;">${details}</div>${citeList(u.evidence)}`;
            uses.appendChild(div);
          });
        });
        
        if (!hasUses) {
          uses.innerHTML = '<div class="no-data">🌿 No traditional uses or trade information documented yet.</div>';
        }

        // References & attribution
        const refs = document.getElementById('refs');
        const gbifList = (data.attribution?.gbifDatasets || [])
          .map(d => `<li><strong>${d.title || 'Unnamed Dataset'}</strong> — <em>${d.license || 'License not specified'}</em></li>`).join('');
        const intList = (data.attribution?.interactionSources || [])
          .map(s => `<li>${s}</li>`).join('');
        const ethList = (data.attribution?.ethnobotanySources || [])
          .map(s => `<li>${s}</li>`).join('');
          
        const lastUpdated = data.attribution?.lastUpdated ? 
          new Date(data.attribution.lastUpdated).toLocaleDateString() : 'Unknown';
        
        refs.innerHTML = `
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
            <div>
              <h3>🗄️ GBIF Datasets</h3>
              <ul class="evidence-list">${gbifList || '<li>No GBIF datasets listed</li>'}</ul>
            </div>
            <div>
              <h3>🔗 Interaction Sources</h3>
              <ul class="evidence-list">${intList || '<li>Literature review and expert knowledge</li>'}</ul>
            </div>
            <div>
              <h3>🌿 Ethnobotany Sources</h3>
              <ul class="evidence-list">${ethList || '<li>No ethnobotanical sources listed</li>'}</ul>
            </div>
          </div>
          <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e9ecef; color: #6c757d;">
            <small><strong>Last Updated:</strong> ${lastUpdated} • <strong>Data Integrated:</strong> GBIF Foundation Layer + Ecosystem Cross-linking</small>
          </div>
        `;
        
      } catch (error) {
        console.error('Error loading species:', error);
        alert(`Error loading species data: ${error.message}`);
      }
    }

    // Search by species/genus name
    async function searchByName(speciesName) {
      try {
        document.getElementById('taxonKey').value = speciesName;
        
        // First try to search our database for matching species
        const response = await fetch(`/api/continuum/search?q=${encodeURIComponent(speciesName)}`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
          // Use the first match
          const match = data.results[0];
          if (match.taxonKey) {
            loadSpecies(match.taxonKey);
            return;
          }
        }
        
        // If no matches in our database, try using the name directly as a GBIF search
        // This is a fallback that may work for some common species
        loadSpeciesByName(speciesName);
        
      } catch (error) {
        console.error('Search error:', error);
        alert(`Search failed: ${error.message}`);
      }
    }
    
    // Enhanced search that handles both taxon keys and species names
    async function searchSpecies() {
      const input = document.getElementById('taxonKey').value.trim();
      if (!input) {
        alert('Please enter an orchid genus or species name');
        return;
      }
      
      // Check if input looks like a number (GBIF taxon key)
      if (/^\d+$/.test(input)) {
        loadSpecies(input);
      } else {
        // Treat as species name
        searchByName(input);
      }
    }
    
    // Fallback function for direct name searches  
    async function loadSpeciesByName(speciesName) {
      try {
        // Show loading state
        document.getElementById('mainContent').style.display = 'none';
        document.getElementById('speciesInfo').style.display = 'block';
        document.getElementById('sciName').textContent = `Searching for "${speciesName}"...`;
        document.getElementById('rankInfo').textContent = 'Please wait...';
        
        // For now, show a helpful message about the limitation
        setTimeout(() => {
          document.getElementById('sciName').textContent = speciesName;
          document.getElementById('rankInfo').textContent = 'Species lookup by name';
          
          // Show limited content explaining the limitation
          document.getElementById('mainContent').style.display = 'grid';
          document.getElementById('pollinators').innerHTML = 
            '<div class="no-data">🔍 Direct name search requires GBIF taxon keys for ecosystem data. Try browsing our <a href="/gallery">Gallery</a> for detailed orchid information!</div>';
          document.getElementById('myco').innerHTML = 
            '<div class="no-data">🔬 Mycorrhizal data requires specific taxon identifiers.</div>';
          document.getElementById('mimicry').innerHTML = 
            '<div class="no-data">🎭 For detailed ecosystem interactions, please use the main <a href="/search">Search</a> tool.</div>';
        }, 1000);
        
      } catch (error) {
        console.error('Name search error:', error);
        alert(`Species search failed: ${error.message}`);
      }
    }

    function loadExample(taxonKey) {
      document.getElementById('taxonKey').value = taxonKey;
      loadSpecies(taxonKey);
    }

    document.getElementById('load').addEventListener('click', () => {
      searchSpecies();
    });

    // Allow Enter key to trigger search
    document.getElementById('taxonKey').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        searchSpecies();
      }
    });

    // Load example on page load for demonstration
    document.addEventListener('DOMContentLoaded', () => {
      console.log('Orchid Interaction Explorer loaded');
      // Auto-load a demo species
      setTimeout(() => {
        if (window.location.hash === '#demo') {
          loadExample('1101138636'); // Monadenia (Disa)
        }
      }, 1000);
    });
  </script>
</body>
</html>'''
    
    return render_template_string(widget_html)

@orchid_interaction_bp.route('/api/continuum/search')
def search_species():
    """Search endpoint for species by name or partial match"""
    
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify({'results': []})
    
    results = []
    for gbif_id, record in ECOSYSTEM_DATA.items():
        taxon = record.get('taxon', {})
        sci_name = taxon.get('acceptedScientificName', '').lower()
        
        # Extract genus from scientific name (first word)
        genus = ''
        if sci_name:
            genus_part = sci_name.split(' ')[0] if ' ' in sci_name else sci_name
            genus = genus_part.lower()
        
        if query in sci_name or query in genus:
            results.append({
                'gbifID': gbif_id,
                'taxonKey': gbif_id,  # Use gbifID as taxonKey since our API uses gbifID
                'scientificName': taxon.get('acceptedScientificName', ''),
                'genus': genus,
                'rank': taxon.get('taxonRank', '')
            })
    
    return jsonify({'results': results[:20]})  # Limit to 20 results

# Initialize data when blueprint is registered
load_ecosystem_data()

print("🔗 Orchid Interaction Explorer routes registered successfully")