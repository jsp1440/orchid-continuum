/**
 * Map Viewer Widget
 * Embeddable web component for displaying orchid locations on a map
 */

class MapViewerWidget extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.apiBase = this.getAttribute('api-base') || 'https://api.orchidcontinuum.org';
        this.theme = this.getAttribute('data-theme') || 'light';
        this.defaultZoom = parseInt(this.getAttribute('data-zoom')) || 2;
        this.defaultCenter = [0, 20]; // [lng, lat]
        this.map = null;
        this.markers = [];
    }

    connectedCallback() {
        this.render();
        this.initializeMap();
    }

    disconnectedCallback() {
        if (this.map) {
            this.map.remove();
        }
    }

    getStyles() {
        return `
            <style>
                :host {
                    display: block;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    --primary-color: ${this.theme === 'dark' ? '#6366f1' : '#4f46e5'};
                    --background: ${this.theme === 'dark' ? '#1f2937' : '#ffffff'};
                    --text-primary: ${this.theme === 'dark' ? '#f9fafb' : '#1f2937'};
                    --text-secondary: ${this.theme === 'dark' ? '#d1d5db' : '#6b7280'};
                    --border: ${this.theme === 'dark' ? '#374151' : '#e5e7eb'};
                }
                
                .widget-container {
                    background: var(--background);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    margin: 0 auto;
                }
                
                .header {
                    padding: 16px;
                    background: linear-gradient(135deg, var(--primary-color), #ec4899);
                    color: white;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .header h2 {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                }
                
                .filters {
                    display: flex;
                    gap: 8px;
                    align-items: center;
                }
                
                .filter-select {
                    padding: 6px 10px;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    background: rgba(255, 255, 255, 0.1);
                    color: white;
                    font-size: 12px;
                }
                
                .filter-select option {
                    color: var(--text-primary);
                    background: var(--background);
                }
                
                .map-container {
                    position: relative;
                    height: 400px;
                    background: ${this.theme === 'dark' ? '#374151' : '#f3f4f6'};
                }
                
                .map-canvas {
                    width: 100%;
                    height: 100%;
                    border: none;
                }
                
                .map-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(0, 0, 0, 0.1);
                    z-index: 10;
                }
                
                .loading-spinner {
                    width: 40px;
                    height: 40px;
                    border: 3px solid var(--border);
                    border-top: 3px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .map-info {
                    padding: 12px 16px;
                    background: ${this.theme === 'dark' ? '#374151' : '#f9fafb'};
                    border-top: 1px solid var(--border);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 12px;
                    color: var(--text-secondary);
                }
                
                .location-count {
                    font-weight: 600;
                    color: var(--text-primary);
                }
                
                .map-controls {
                    display: flex;
                    gap: 8px;
                }
                
                .control-button {
                    padding: 4px 8px;
                    background: var(--primary-color);
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 10px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                
                .control-button:hover {
                    background: #3730a3;
                }
                
                .error {
                    padding: 40px 20px;
                    text-align: center;
                    color: #dc2626;
                    font-size: 14px;
                }
                
                .powered-by {
                    text-align: center;
                    padding: 8px;
                    font-size: 10px;
                    color: var(--text-secondary);
                    border-top: 1px solid var(--border);
                    background: ${this.theme === 'dark' ? '#111827' : '#f9fafb'};
                }
                
                .powered-by a {
                    color: var(--primary-color);
                    text-decoration: none;
                }
                
                /* Marker styles */
                .marker {
                    background: var(--primary-color);
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                
                .marker:hover {
                    transform: scale(1.2);
                }
                
                .popup {
                    max-width: 200px;
                    font-size: 12px;
                }
                
                .popup h4 {
                    margin: 0 0 4px 0;
                    font-size: 14px;
                    font-weight: 600;
                    color: var(--text-primary);
                }
                
                .popup p {
                    margin: 0;
                    color: var(--text-secondary);
                    line-height: 1.4;
                }
                
                @media (max-width: 480px) {
                    .widget-container {
                        max-width: 100%;
                        border-radius: 8px;
                    }
                    
                    .header {
                        flex-direction: column;
                        gap: 8px;
                        align-items: stretch;
                    }
                    
                    .filters {
                        justify-content: center;
                    }
                    
                    .map-container {
                        height: 300px;
                    }
                }
            </style>
        `;
    }

    render() {
        this.shadowRoot.innerHTML = `
            ${this.getStyles()}
            <div class="widget-container">
                <div class="header">
                    <h2>🗺️ Orchid Map</h2>
                    <div class="filters">
                        <select class="filter-select" id="genus-filter">
                            <option value="">All Genera</option>
                            <option value="Phalaenopsis">Phalaenopsis</option>
                            <option value="Cattleya">Cattleya</option>
                            <option value="Dendrobium">Dendrobium</option>
                        </select>
                        <select class="filter-select" id="elevation-filter">
                            <option value="">All Elevations</option>
                            <option value="0-500">0-500m</option>
                            <option value="500-1000">500-1000m</option>
                            <option value="1000+">1000m+</option>
                        </select>
                    </div>
                </div>
                <div class="map-container">
                    <div id="map-canvas" class="map-canvas"></div>
                    <div id="map-overlay" class="map-overlay">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
                <div class="map-info">
                    <div>
                        <span class="location-count" id="location-count">0</span> locations shown
                    </div>
                    <div class="map-controls">
                        <button class="control-button" id="reset-zoom">Reset View</button>
                        <button class="control-button" id="reload-data">Reload</button>
                    </div>
                </div>
                <div class="powered-by">
                    Powered by <a href="https://orchidcontinuum.org" target="_blank" rel="noopener">The Orchid Continuum</a>
                </div>
            </div>
        `;
    }

    async initializeMap() {
        try {
            // Initialize with a simple canvas-based map for demo
            // In production, this would use Leaflet, Mapbox, or similar
            await this.loadMapData();
            this.setupEventListeners();
            this.hideOverlay();
            
        } catch (error) {
            console.error('Map initialization failed:', error);
            this.showError('Failed to load map. Please try again later.');
        }
    }

    async loadMapData() {
        try {
            // Get current filter values
            const genusFilter = this.shadowRoot.getElementById('genus-filter').value;
            const elevationFilter = this.shadowRoot.getElementById('elevation-filter').value;
            
            // Build query parameters
            const params = new URLSearchParams();
            if (genusFilter) params.append('genus', genusFilter);
            if (elevationFilter) params.append('elevation', elevationFilter);
            
            // Fetch map data from API
            const response = await fetch(`${this.apiBase}/map/query?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.renderMapData(data);
            
        } catch (error) {
            console.error('Failed to load map data:', error);
            this.showError('Unable to load location data.');
        }
    }

    renderMapData(geoJsonData) {
        const mapCanvas = this.shadowRoot.getElementById('map-canvas');
        const locationCount = this.shadowRoot.getElementById('location-count');
        
        // For demo purposes, create a simple visual representation
        // In production, this would render actual map tiles and markers
        
        const features = geoJsonData.features || [];
        locationCount.textContent = features.length;
        
        // Create simple map visualization
        mapCanvas.innerHTML = `
            <svg width="100%" height="100%" style="background: #e5e7eb;">
                <!-- Simple world map outline -->
                <rect width="100%" height="100%" fill="${this.theme === 'dark' ? '#374151' : '#f3f4f6'}"/>
                <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" 
                      fill="${this.theme === 'dark' ? '#9ca3af' : '#6b7280'}" font-size="14">
                    Interactive Map (${features.length} orchid locations)
                </text>
                ${features.slice(0, 20).map((feature, index) => {
                    // Simple positioning for demo
                    const x = 20 + (index % 10) * 50;
                    const y = 100 + Math.floor(index / 10) * 80;
                    return `
                        <circle cx="${x}" cy="${y}" r="6" 
                               fill="${this.theme === 'dark' ? '#8b5cf6' : '#7c3aed'}" 
                               stroke="white" stroke-width="2"
                               class="map-marker" 
                               data-title="${feature.properties.title || 'Unknown'}"
                               style="cursor: pointer;">
                            <title>${feature.properties.title || 'Unknown'}</title>
                        </circle>
                    `;
                }).join('')}
            </svg>
        `;
        
        // Add click handlers to markers
        this.addMarkerEventListeners();
    }

    addMarkerEventListeners() {
        const markers = this.shadowRoot.querySelectorAll('.map-marker');
        markers.forEach(marker => {
            marker.addEventListener('click', (e) => {
                const title = e.target.getAttribute('data-title');
                this.showMarkerPopup(title, e.target);
            });
        });
    }

    showMarkerPopup(title, element) {
        // Remove existing popups
        const existingPopup = this.shadowRoot.querySelector('.popup-overlay');
        if (existingPopup) {
            existingPopup.remove();
        }
        
        // Create popup
        const popup = document.createElement('div');
        popup.className = 'popup-overlay';
        popup.style.cssText = `
            position: absolute;
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 20;
            max-width: 200px;
            font-size: 12px;
            color: var(--text-primary);
            top: ${element.cy.baseVal.value - 50}px;
            left: ${element.cx.baseVal.value + 10}px;
            pointer-events: none;
        `;
        
        popup.innerHTML = `
            <h4 style="margin: 0 0 4px 0; font-size: 14px; font-weight: 600;">${title}</h4>
            <p style="margin: 0; color: var(--text-secondary);">Click to view details</p>
        `;
        
        this.shadowRoot.querySelector('.map-container').appendChild(popup);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (popup.parentNode) {
                popup.remove();
            }
        }, 3000);
    }

    setupEventListeners() {
        const genusFilter = this.shadowRoot.getElementById('genus-filter');
        const elevationFilter = this.shadowRoot.getElementById('elevation-filter');
        const resetButton = this.shadowRoot.getElementById('reset-zoom');
        const reloadButton = this.shadowRoot.getElementById('reload-data');
        
        genusFilter.addEventListener('change', () => this.loadMapData());
        elevationFilter.addEventListener('change', () => this.loadMapData());
        
        resetButton.addEventListener('click', () => this.resetView());
        reloadButton.addEventListener('click', () => this.reloadData());
    }

    resetView() {
        // Reset filters and reload
        this.shadowRoot.getElementById('genus-filter').value = '';
        this.shadowRoot.getElementById('elevation-filter').value = '';
        this.loadMapData();
    }

    async reloadData() {
        this.showOverlay();
        await this.loadMapData();
        this.hideOverlay();
    }

    showOverlay() {
        const overlay = this.shadowRoot.getElementById('map-overlay');
        overlay.style.display = 'flex';
    }

    hideOverlay() {
        const overlay = this.shadowRoot.getElementById('map-overlay');
        overlay.style.display = 'none';
    }

    showError(message) {
        const mapCanvas = this.shadowRoot.getElementById('map-canvas');
        mapCanvas.innerHTML = `<div class="error">${message}</div>`;
        this.hideOverlay();
    }

    static get observedAttributes() {
        return ['data-theme', 'data-zoom', 'api-base'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue !== newValue) {
            if (name === 'data-theme') {
                this.theme = newValue;
            } else if (name === 'data-zoom') {
                this.defaultZoom = parseInt(newValue) || 2;
            } else if (name === 'api-base') {
                this.apiBase = newValue;
            }
            
            if (this.shadowRoot) {
                this.render();
                this.initializeMap();
            }
        }
    }
}

// Register the custom element
if (!customElements.get('map-viewer')) {
    customElements.define('map-viewer', MapViewerWidget);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MapViewerWidget;
}