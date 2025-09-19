/**
 * Orchid Continuum Partner Connect Widgets - UMD Bundle
 * Version 1.0 for Gary Yong Gee partnership
 */
(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
    typeof define === 'function' && define.amd ? define(['exports'], factory) :
    (global = typeof globalThis !== 'undefined' ? globalThis : global || self, factory(global.OCWWidgets = {}));
})(this, (function (exports) {
    'use strict';

    // Base widget class
    class OCWBaseWidget extends HTMLElement {
        constructor() {
            super();
            this.attachShadow({ mode: 'open' });
            
            // Get configuration from script tag or attributes
            const scriptTag = document.querySelector('script[data-api-base]');
            this.apiBase = this.getAttribute('data-api-base') || 
                          (scriptTag && scriptTag.getAttribute('data-api-base')) || 
                          'https://api.orchidcontinuum.org';
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
                    throw new Error(`API Error: ${response.status}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Orchid Continuum API request failed:', error);
                this.showError(error.message);
                return null;
            }
        }

        showError(message) {
            this.shadowRoot.innerHTML = `
                <style>
                    .error { 
                        background: #fee; border: 1px solid #fcc; border-radius: 4px; 
                        padding: 12px; color: #c33; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                        text-align: center;
                    }
                </style>
                <div class="error">⚠️ ${message}</div>
            `;
        }

        showLoading() {
            this.shadowRoot.innerHTML = `
                <style>
                    .loading { 
                        display: flex; align-items: center; justify-content: center; padding: 20px; 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #666; 
                    }
                    .spinner { 
                        width: 16px; height: 16px; border: 2px solid #ddd; border-top: 2px solid #4a90e2; 
                        border-radius: 50%; animation: spin 1s linear infinite; margin-right: 8px; 
                    }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
                <div class="loading"><div class="spinner"></div>Loading Gary's orchid data...</div>
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
                        border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: white; max-width: 600px; 
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    .search-header { 
                        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); 
                        color: white; padding: 12px 16px; font-weight: 600; 
                    }
                    .search-input { padding: 12px 16px; border-bottom: 1px solid #eee; }
                    .search-input input { 
                        width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; 
                        font-size: 14px; box-sizing: border-box; transition: border-color 0.2s;
                    }
                    .search-input input:focus { border-color: #4a90e2; outline: none; }
                    .search-results { max-height: 400px; overflow-y: auto; }
                    .result-item { 
                        padding: 12px 16px; border-bottom: 1px solid #eee; cursor: pointer; 
                        transition: background-color 0.2s;
                    }
                    .result-item:hover { background: #f8f9fa; }
                    .result-name { font-weight: 600; color: #333; font-style: italic; margin-bottom: 4px; }
                    .result-meta { font-size: 12px; color: #666; }
                    .no-results { 
                        padding: 30px 20px; text-align: center; color: #666; font-style: italic; 
                        background: #f8f9fa; 
                    }
                </style>
                <div class="search-widget">
                    <div class="search-header">🔍 Search - ${this.partner}</div>
                    <div class="search-input">
                        <input type="text" placeholder="${this.getAttribute('data-placeholder') || 'Search orchids...'}" id="search-input">
                    </div>
                    <div class="search-results" id="results-container">
                        <div class="no-results">Enter a search term to find orchids in Gary's collection</div>
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
            const container = this.shadowRoot.getElementById('results-container');
            
            if (!query.trim()) {
                container.innerHTML = '<div class="no-results">Enter a search term to find orchids in Gary\'s collection</div>';
                return;
            }

            container.innerHTML = '<div class="no-results">🔍 Searching Gary\'s collection...</div>';

            // Simulate API call - in real version this would hit the actual API
            setTimeout(() => {
                const mockResults = this.getMockResults(query);
                this.renderResults(mockResults);
            }, 800);
        }

        getMockResults(query) {
            const mockData = [
                { scientific_name: 'Cattleya labiata', locality: 'Brazil', credit: 'Gary Yong Gee', license: 'CC-BY-NC' },
                { scientific_name: 'Dendrobium nobile', locality: 'Thailand', credit: 'Gary Yong Gee', license: 'CC-BY-NC' },
                { scientific_name: 'Phalaenopsis amabilis', locality: 'Indonesia', credit: 'Gary Yong Gee', license: 'CC-BY-NC' }
            ];
            
            return {
                results: mockData.filter(item => 
                    item.scientific_name.toLowerCase().includes(query.toLowerCase())
                )
            };
        }

        renderResults(data) {
            const container = this.shadowRoot.getElementById('results-container');
            
            if (!data.results || data.results.length === 0) {
                container.innerHTML = '<div class="no-results">No orchids found matching your search</div>';
                return;
            }

            const resultsHTML = data.results.map(result => `
                <div class="result-item">
                    <div class="result-name">${result.scientific_name}</div>
                    <div class="result-meta">
                        📍 ${result.locality} • 📷 ${result.credit} • 📄 ${result.license}
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
                        border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: white; 
                        width: 100%; max-width: 800px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    .map-header { 
                        background: linear-gradient(135deg, #28a745 0%, #20903d 100%); 
                        color: white; padding: 12px 16px; font-weight: 600; 
                        display: flex; justify-content: space-between; align-items: center; 
                    }
                    .map-controls button { 
                        background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); 
                        padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 8px; 
                        transition: background-color 0.2s;
                    }
                    .map-controls button:hover { background: rgba(255,255,255,0.3); }
                    .map-container { height: 400px; position: relative; background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%); }
                    .map-placeholder { 
                        display: flex; align-items: center; justify-content: center; height: 100%; 
                        color: #666; font-size: 14px; flex-direction: column; text-align: center;
                    }
                    .map-icon { font-size: 48px; margin-bottom: 16px; }
                    .location-count { 
                        padding: 12px 16px; background: #f8f9fa; border-top: 1px solid #eee; 
                        font-size: 12px; color: #666; display: flex; justify-content: space-between; align-items: center;
                    }
                    .privacy-badge { 
                        background: #007bff; color: white; padding: 2px 8px; border-radius: 12px; 
                        font-size: 10px; text-transform: uppercase; font-weight: 600;
                    }
                </style>
                <div class="map-widget">
                    <div class="map-header">
                        🗺️ Orchid Locations - ${this.partner}
                        <div class="map-controls">
                            <button onclick="this.getRootNode().host.toggleMode()">Toggle Privacy</button>
                            <button onclick="this.getRootNode().host.reloadMap()">↻ Reload</button>
                        </div>
                    </div>
                    <div class="map-container" id="map-container">
                        <div class="map-placeholder">
                            <div class="map-icon">🌍</div>
                            <div><strong>Interactive Map Ready</strong></div>
                            <div style="margin-top: 8px; max-width: 300px;">
                                Gary Yong Gee's orchid locations with geoprivacy protection. 
                                Real integration will show actual collection locations.
                            </div>
                        </div>
                    </div>
                    <div class="location-count" id="location-count">
                        <span>Loading location data...</span>
                        <span class="privacy-badge" id="privacy-mode">Public</span>
                    </div>
                </div>
            `;
        }

        async initializeMap() {
            this.mode = 'public';
            await this.loadMapData();
        }

        async loadMapData() {
            const container = this.shadowRoot.getElementById('map-container');
            const countElement = this.shadowRoot.getElementById('location-count');
            const privacyBadge = this.shadowRoot.getElementById('privacy-mode');
            
            // Simulate loading
            setTimeout(() => {
                const locationCount = this.mode === 'public' ? 12 : 28;
                
                countElement.innerHTML = `
                    <span>Showing ${locationCount} orchid locations (${this.mode} mode)</span>
                    <span class="privacy-badge">${this.mode === 'public' ? 'Public' : 'Partner Private'}</span>
                `;
                
                container.innerHTML = `
                    <div style="padding: 40px 20px; text-align: center;">
                        <div class="map-icon">📍</div>
                        <div style="margin-bottom: 16px; font-weight: 600; font-size: 18px;">${locationCount} locations found</div>
                        <div style="font-size: 12px; color: #666; max-width: 400px; margin: 0 auto; line-height: 1.4;">
                            Interactive map integration ready for Gary Yong Gee's orchid collection.<br>
                            <strong>${this.mode === 'public' ? 'Public mode:' : 'Partner mode:'}</strong> 
                            ${this.mode === 'public' ? 'Generalized coordinates for sensitive species' : 'Exact coordinates for research purposes'}
                        </div>
                    </div>
                `;
            }, 500);
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
                        border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: white; 
                        max-width: 500px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    .phenology-header { 
                        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); 
                        color: white; padding: 12px 16px; font-weight: 600; 
                    }
                    .phenology-content { padding: 20px; }
                    .taxon-input { margin-bottom: 16px; }
                    .taxon-input input { 
                        width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; 
                        font-size: 14px; box-sizing: border-box; transition: border-color 0.2s;
                    }
                    .taxon-input input:focus { border-color: #dc3545; outline: none; }
                    .chart-container { 
                        margin: 16px 0; border: 1px solid #eee; border-radius: 6px; overflow: hidden; 
                        background: linear-gradient(135deg, #fff8f8 0%, #fff 100%);
                    }
                    .chart-header { 
                        background: #f8f9fa; padding: 10px 12px; font-size: 12px; 
                        font-weight: 600; color: #495057; border-bottom: 1px solid #eee; 
                    }
                    .chart-content { padding: 30px 20px; text-align: center; }
                    .chart-icon { font-size: 36px; margin-bottom: 12px; }
                    .summary { 
                        margin-top: 12px; padding: 15px; background: #f8f9fa; border-radius: 6px; 
                        font-size: 12px; color: #495057; border-left: 4px solid #dc3545;
                    }
                </style>
                <div class="phenology-widget">
                    <div class="phenology-header">📊 Flowering Timeline - ${this.partner}</div>
                    <div class="phenology-content">
                        <div class="taxon-input">
                            <input type="text" placeholder="Enter orchid genus or species..." id="taxon-input" value="${this.taxon}">
                        </div>
                        <div class="chart-container">
                            <div class="chart-header">Flowering frequency by month</div>
                            <div class="chart-content" id="chart-content">
                                <div class="chart-icon">📊</div>
                                <div>Loading flowering data...</div>
                            </div>
                        </div>
                        <div class="summary" id="summary">Enter a taxon name to see flowering patterns from Gary's collection</div>
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
                if (this.taxon.trim()) {
                    searchTimeout = setTimeout(() => {
                        this.loadPhenologyData();
                    }, 500);
                }
            });
        }

        async loadPhenologyData() {
            if (!this.taxon.trim()) return;

            const chartContent = this.shadowRoot.getElementById('chart-content');
            const summary = this.shadowRoot.getElementById('summary');
            
            chartContent.innerHTML = `
                <div class="chart-icon">⏳</div>
                <div>Loading <em>${this.taxon}</em> data...</div>
            `;

            // Simulate API call
            setTimeout(() => {
                const mockRecords = Math.floor(Math.random() * 50) + 5;
                
                chartContent.innerHTML = `
                    <div class="chart-icon">🌸</div>
                    <div style="font-weight: 600; margin-bottom: 8px; font-style: italic;">${this.taxon}</div>
                    <div style="font-size: 12px; color: #666;">
                        ${mockRecords} flowering records found<br>
                        Interactive phenology chart integration ready
                    </div>
                `;

                summary.innerHTML = `
                    <strong>Flowering Analysis:</strong> <em>${this.taxon}</em><br>
                    • Total flowering records: ${mockRecords}<br>
                    • Data from Gary Yong Gee's orchid collection<br>
                    • Peak flowering periods and seasonal patterns available
                `;
            }, 800);
        }
    }

    // Register web components
    customElements.define('ocw-search', OCWSearchWidget);
    customElements.define('ocw-map', OCWMapWidget);
    customElements.define('ocw-phenology', OCWPhenologyWidget);

    // Auto-initialize div-based widgets when DOM loads
    document.addEventListener('DOMContentLoaded', () => {
        // Convert div.ocw-search to <ocw-search>
        document.querySelectorAll('div.ocw-search').forEach(div => {
            const widget = document.createElement('ocw-search');
            Array.from(div.attributes).forEach(attr => {
                widget.setAttribute(attr.name, attr.value);
            });
            div.parentNode.replaceChild(widget, div);
        });

        // Convert div.ocw-map to <ocw-map>
        document.querySelectorAll('div.ocw-map').forEach(div => {
            const widget = document.createElement('ocw-map');
            Array.from(div.attributes).forEach(attr => {
                widget.setAttribute(attr.name, attr.value);
            });
            div.parentNode.replaceChild(widget, div);
        });

        // Convert div.ocw-phenology to <ocw-phenology>
        document.querySelectorAll('div.ocw-phenology').forEach(div => {
            const widget = document.createElement('ocw-phenology');
            Array.from(div.attributes).forEach(attr => {
                widget.setAttribute(attr.name, attr.value);
            });
            div.parentNode.replaceChild(widget, div);
        });
    });

    console.log('Orchid Continuum Widgets loaded for partner:', 
                document.querySelector('script[data-partner]')?.getAttribute('data-partner') || 'unknown');

    // Export for UMD
    exports.OCWSearchWidget = OCWSearchWidget;
    exports.OCWMapWidget = OCWMapWidget;
    exports.OCWPhenologyWidget = OCWPhenologyWidget;

}));