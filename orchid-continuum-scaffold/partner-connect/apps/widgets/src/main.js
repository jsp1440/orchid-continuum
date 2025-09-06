/**
 * Orchid Continuum Partner Connect Widgets
 * Web Components for embedding search, map, and phenology data
 */

// Import Leaflet for maps
import L from 'leaflet';

// Base widget class
class OCWBaseWidget extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        
        // Get configuration from script tag or attributes
        const scriptTag = document.querySelector('script[data-api-base]');
        this.apiBase = this.getAttribute('data-api-base') || 
                      (scriptTag && scriptTag.getAttribute('data-api-base')) || 
                      'http://localhost:8000';
        this.apiKey = this.getAttribute('data-api-key') || 
                     (scriptTag && scriptTag.getAttribute('data-api-key')) || '';
        this.partner = this.getAttribute('data-partner') || 
                      (scriptTag && scriptTag.getAttribute('data-partner')) || '';
    }

    async apiRequest(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const headers = {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        try {
            const response = await fetch(url, { ...options, headers });
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    showError(message) {
        this.shadowRoot.innerHTML = `
            <style>
                .error {
                    background: #fee;
                    border: 1px solid #fcc;
                    border-radius: 4px;
                    padding: 12px;
                    color: #c33;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                }
            </style>
            <div class="error">Error: ${message}</div>
        `;
    }

    showLoading() {
        this.shadowRoot.innerHTML = `
            <style>
                .loading {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    color: #666;
                }
                .spinner {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #ddd;
                    border-top: 2px solid #4a90e2;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 8px;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
            <div class="loading">
                <div class="spinner"></div>
                Loading...
            </div>
        `;
    }
}

// Search widget
class OCWSearchWidget extends OCWBaseWidget {
    connectedCallback() {
        this.render();
        this.setupEventListeners();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                .search-widget {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                    background: white;
                    max-width: 600px;
                }
                .search-header {
                    background: #4a90e2;
                    color: white;
                    padding: 12px 16px;
                    font-weight: 600;
                }
                .search-input {
                    padding: 12px 16px;
                    border-bottom: 1px solid #eee;
                }
                .search-input input {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                    box-sizing: border-box;
                }
                .search-results {
                    max-height: 400px;
                    overflow-y: auto;
                }
                .result-item {
                    padding: 12px 16px;
                    border-bottom: 1px solid #eee;
                    cursor: pointer;
                }
                .result-item:hover {
                    background: #f5f5f5;
                }
                .result-item:last-child {
                    border-bottom: none;
                }
                .result-name {
                    font-weight: 600;
                    color: #333;
                    font-style: italic;
                }
                .result-meta {
                    font-size: 12px;
                    color: #666;
                    margin-top: 4px;
                }
                .no-results {
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-style: italic;
                }
                .pagination {
                    padding: 12px 16px;
                    text-align: center;
                    background: #f9f9f9;
                    border-top: 1px solid #eee;
                }
                .pagination button {
                    background: #4a90e2;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    margin: 0 4px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }
                .pagination button:disabled {
                    background: #ccc;
                    cursor: not-allowed;
                }
            </style>
            <div class="search-widget">
                <div class="search-header">🔍 Orchid Search</div>
                <div class="search-input">
                    <input type="text" placeholder="Search by scientific name or location..." id="search-input">
                </div>
                <div class="search-results" id="results-container">
                    <div class="no-results">Enter a search term to find orchids</div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        const input = this.shadowRoot.getElementById('search-input');
        let searchTimeout;

        input.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });
    }

    async performSearch(query) {
        if (!query.trim()) {
            this.shadowRoot.getElementById('results-container').innerHTML = 
                '<div class="no-results">Enter a search term to find orchids</div>';
            return;
        }

        const container = this.shadowRoot.getElementById('results-container');
        container.innerHTML = '<div class="no-results">Searching...</div>';

        try {
            const data = await this.apiRequest(`/widgets/search?q=${encodeURIComponent(query)}&page=1`);
            this.renderResults(data);
        } catch (error) {
            container.innerHTML = '<div class="no-results">Search failed. Please try again.</div>';
        }
    }

    renderResults(data) {
        const container = this.shadowRoot.getElementById('results-container');
        
        if (!data.results || data.results.length === 0) {
            container.innerHTML = '<div class="no-results">No orchids found for your search</div>';
            return;
        }

        const resultsHTML = data.results.map(result => `
            <div class="result-item" onclick="window.open('${result.image_url || '#'}', '_blank')">
                <div class="result-name">${result.scientific_name || 'Unknown species'}</div>
                <div class="result-meta">
                    📍 ${result.locality || 'Unknown location'} • 
                    📷 ${result.credit || result.partner_name} • 
                    📄 ${result.license || 'License unknown'}
                </div>
            </div>
        `).join('');

        container.innerHTML = resultsHTML;
    }
}

// Map widget
class OCWMapWidget extends OCWBaseWidget {
    connectedCallback() {
        this.render();
        this.initializeMap();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                .map-widget {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                    background: white;
                    width: 100%;
                    max-width: 800px;
                }
                .map-header {
                    background: #28a745;
                    color: white;
                    padding: 12px 16px;
                    font-weight: 600;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .map-controls {
                    display: flex;
                    gap: 8px;
                }
                .map-controls button {
                    background: rgba(255,255,255,0.2);
                    color: white;
                    border: 1px solid rgba(255,255,255,0.3);
                    padding: 4px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }
                .map-controls button:hover {
                    background: rgba(255,255,255,0.3);
                }
                .map-container {
                    height: 400px;
                    position: relative;
                    background: #f0f8f0;
                }
                .map-placeholder {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    color: #666;
                    font-size: 14px;
                    flex-direction: column;
                }
                .location-count {
                    padding: 8px 16px;
                    background: #f9f9f9;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                }
            </style>
            <div class="map-widget">
                <div class="map-header">
                    🗺️ Orchid Locations
                    <div class="map-controls">
                        <button onclick="this.getRootNode().host.toggleMode()">Toggle Private</button>
                        <button onclick="this.getRootNode().host.reloadMap()">Reload</button>
                    </div>
                </div>
                <div class="map-container" id="map-container">
                    <div class="map-placeholder">
                        <div>🌍</div>
                        <div>Interactive map will load here</div>
                        <div style="margin-top: 12px; font-size: 11px;">
                            Leaflet map with orchid locations<br>
                            Generalized coordinates for geoprivacy
                        </div>
                    </div>
                </div>
                <div class="location-count" id="location-count">
                    Loading location data...
                </div>
            </div>
        `;
    }

    async initializeMap() {
        this.mode = 'public';
        await this.loadMapData();
    }

    async loadMapData() {
        try {
            const data = await this.apiRequest(`/widgets/map?mode=${this.mode}`);
            this.renderMapData(data);
        } catch (error) {
            this.shadowRoot.getElementById('location-count').textContent = 'Failed to load locations';
        }
    }

    renderMapData(geoJsonData) {
        const container = this.shadowRoot.getElementById('map-container');
        const countElement = this.shadowRoot.getElementById('location-count');
        
        const locationCount = geoJsonData.features.length;
        countElement.textContent = `Showing ${locationCount} orchid locations (${this.mode} mode)`;
        
        // Simple map visualization for demo
        const features = geoJsonData.features.slice(0, 10); // Show first 10
        
        const mapHTML = `
            <div style="padding: 20px; text-align: center;">
                <div style="margin-bottom: 16px; font-weight: 600;">
                    📍 ${locationCount} locations found
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; max-height: 320px; overflow-y: auto;">
                    ${features.map(feature => `
                        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px; text-align: left;">
                            <div style="font-weight: 600; font-style: italic; color: #495057; margin-bottom: 4px;">
                                ${feature.properties.scientific_name || 'Unknown species'}
                            </div>
                            <div style="font-size: 12px; color: #6c757d;">
                                📍 ${feature.properties.locality || 'Unknown location'}<br>
                                📷 ${feature.properties.credit || feature.properties.partner_name}<br>
                                📐 ±${feature.properties.coordinateUncertaintyInMeters || 'Unknown'}m
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${locationCount > 10 ? `<div style="margin-top: 12px; font-size: 12px; color: #6c757d;">Showing first 10 of ${locationCount} locations</div>` : ''}
            </div>
        `;
        
        container.innerHTML = mapHTML;
    }

    toggleMode() {
        this.mode = this.mode === 'public' ? 'partner' : 'public';
        this.loadMapData();
    }

    reloadMap() {
        this.loadMapData();
    }
}

// Phenology widget
class OCWPhenologyWidget extends OCWBaseWidget {
    connectedCallback() {
        this.taxon = this.getAttribute('data-taxon') || 'Cattleya';
        this.render();
        this.loadPhenologyData();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                .phenology-widget {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                    background: white;
                    max-width: 500px;
                }
                .phenology-header {
                    background: #dc3545;
                    color: white;
                    padding: 12px 16px;
                    font-weight: 600;
                }
                .phenology-content {
                    padding: 16px;
                }
                .taxon-input {
                    margin-bottom: 16px;
                }
                .taxon-input input {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                    box-sizing: border-box;
                }
                .chart-container {
                    margin: 16px 0;
                    border: 1px solid #eee;
                    border-radius: 4px;
                    overflow: hidden;
                }
                .chart-header {
                    background: #f8f9fa;
                    padding: 8px 12px;
                    font-size: 12px;
                    font-weight: 600;
                    color: #495057;
                }
                .chart-bars {
                    display: grid;
                    grid-template-columns: repeat(12, 1fr);
                    gap: 1px;
                    background: #eee;
                    padding: 1px;
                }
                .month-bar {
                    background: white;
                    padding: 8px 4px;
                    text-align: center;
                    font-size: 10px;
                    position: relative;
                    min-height: 80px;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-end;
                }
                .month-name {
                    font-weight: 600;
                    color: #495057;
                    margin-bottom: 4px;
                }
                .month-value {
                    font-size: 8px;
                    color: #6c757d;
                }
                .bar-fill {
                    background: #dc3545;
                    margin: 2px;
                    border-radius: 2px;
                    min-height: 2px;
                    display: flex;
                    align-items: flex-end;
                    justify-content: center;
                    color: white;
                    font-size: 8px;
                    font-weight: 600;
                }
                .summary {
                    margin-top: 12px;
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    font-size: 12px;
                    color: #495057;
                }
            </style>
            <div class="phenology-widget">
                <div class="phenology-header">📊 Flowering Timeline</div>
                <div class="phenology-content">
                    <div class="taxon-input">
                        <input type="text" placeholder="Enter taxon name..." id="taxon-input" value="${this.taxon}">
                    </div>
                    <div class="chart-container" id="chart-container">
                        <div class="chart-header">Flowering frequency by month</div>
                        <div id="chart-content">Loading...</div>
                    </div>
                    <div class="summary" id="summary">
                        Enter a taxon name to see flowering patterns
                    </div>
                </div>
            </div>
        `;

        this.setupEventListeners();
    }

    setupEventListeners() {
        const input = this.shadowRoot.getElementById('taxon-input');
        let searchTimeout;

        input.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            this.taxon = e.target.value;
            searchTimeout = setTimeout(() => {
                this.loadPhenologyData();
            }, 500);
        });
    }

    async loadPhenologyData() {
        if (!this.taxon.trim()) return;

        const chartContent = this.shadowRoot.getElementById('chart-content');
        chartContent.innerHTML = 'Loading...';

        try {
            const data = await this.apiRequest(`/widgets/phenology?taxon=${encodeURIComponent(this.taxon)}`);
            this.renderChart(data);
        } catch (error) {
            chartContent.innerHTML = 'Failed to load data';
            this.shadowRoot.getElementById('summary').textContent = 'Error loading phenology data';
        }
    }

    renderChart(data) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        const maxValue = Math.max(...Object.values(data.months || {}), 1);
        
        const barsHTML = months.map(month => {
            const value = data.months[month] || 0;
            const height = (value / maxValue) * 60; // Max height 60px
            
            return `
                <div class="month-bar">
                    <div class="month-name">${month}</div>
                    <div class="bar-fill" style="height: ${height}px;">
                        ${value > 0 ? value : ''}
                    </div>
                    <div class="month-value">${value}</div>
                </div>
            `;
        }).join('');

        this.shadowRoot.getElementById('chart-content').innerHTML = `
            <div class="chart-bars">${barsHTML}</div>
        `;

        this.shadowRoot.getElementById('summary').innerHTML = `
            <strong>${data.taxon}</strong><br>
            Total flowering records: ${data.total_records || 0}<br>
            Peak months: ${this.findPeakMonths(data.months)}
        `;
    }

    findPeakMonths(monthData) {
        if (!monthData || Object.keys(monthData).length === 0) return 'No data';
        
        const maxValue = Math.max(...Object.values(monthData));
        const peakMonths = Object.keys(monthData).filter(month => monthData[month] === maxValue);
        
        return peakMonths.length > 0 ? peakMonths.join(', ') : 'No peak detected';
    }
}

// Register web components
customElements.define('ocw-search', OCWSearchWidget);
customElements.define('ocw-map', OCWMapWidget);
customElements.define('ocw-phenology', OCWPhenologyWidget);

// Export for UMD
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OCWSearchWidget, OCWMapWidget, OCWPhenologyWidget };
}

// Auto-initialize widgets
document.addEventListener('DOMContentLoaded', () => {
    // Look for div elements with OCW classes and convert them to custom elements
    document.querySelectorAll('div.ocw-search').forEach(div => {
        const widget = document.createElement('ocw-search');
        // Copy attributes
        for (const attr of div.attributes) {
            widget.setAttribute(attr.name, attr.value);
        }
        div.parentNode.replaceChild(widget, div);
    });

    document.querySelectorAll('div.ocw-map').forEach(div => {
        const widget = document.createElement('ocw-map');
        for (const attr of div.attributes) {
            widget.setAttribute(attr.name, attr.value);
        }
        div.parentNode.replaceChild(widget, div);
    });

    document.querySelectorAll('div.ocw-phenology').forEach(div => {
        const widget = document.createElement('ocw-phenology');
        for (const attr of div.attributes) {
            widget.setAttribute(attr.name, attr.value);
        }
        div.parentNode.replaceChild(widget, div);
    });
});