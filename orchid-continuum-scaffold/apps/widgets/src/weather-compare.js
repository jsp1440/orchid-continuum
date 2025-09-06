/**
 * Weather/Habitat Compare Widget
 * Embeddable web component for comparing local weather with orchid habitat
 */

class WeatherCompareWidget extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.apiBase = this.getAttribute('api-base') || 'https://api.orchidcontinuum.org';
        this.theme = this.getAttribute('data-theme') || 'light';
        this.orchidId = this.getAttribute('orchid-id');
        this.userLocation = null;
        this.comparisonData = null;
    }

    connectedCallback() {
        this.render();
        this.setupEventListeners();
    }

    getStyles() {
        return `
            <style>
                :host {
                    display: block;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    --primary-color: ${this.theme === 'dark' ? '#10b981' : '#059669'};
                    --background: ${this.theme === 'dark' ? '#1f2937' : '#ffffff'};
                    --text-primary: ${this.theme === 'dark' ? '#f9fafb' : '#1f2937'};
                    --text-secondary: ${this.theme === 'dark' ? '#d1d5db' : '#6b7280'};
                    --border: ${this.theme === 'dark' ? '#374151' : '#e5e7eb'};
                    --success: #10b981;
                    --warning: #f59e0b;
                    --danger: #ef4444;
                }
                
                .widget-container {
                    background: var(--background);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    max-width: 420px;
                    margin: 0 auto;
                }
                
                .header {
                    padding: 16px;
                    background: linear-gradient(135deg, var(--primary-color), #3b82f6);
                    color: white;
                    text-align: center;
                }
                
                .header h2 {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                }
                
                .input-section {
                    padding: 16px;
                    border-bottom: 1px solid var(--border);
                }
                
                .location-input {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 12px;
                }
                
                .location-input input {
                    flex: 1;
                    padding: 10px 12px;
                    border: 1px solid var(--border);
                    border-radius: 6px;
                    font-size: 14px;
                    background: var(--background);
                    color: var(--text-primary);
                }
                
                .location-input button {
                    padding: 10px 16px;
                    background: var(--primary-color);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                
                .location-input button:hover {
                    background: #047857;
                }
                
                .location-input button:disabled {
                    background: var(--text-secondary);
                    cursor: not-allowed;
                }
                
                .comparison-section {
                    padding: 16px;
                }
                
                .comparison-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                    margin-bottom: 16px;
                }
                
                .metric-card {
                    background: ${this.theme === 'dark' ? '#374151' : '#f9fafb'};
                    border-radius: 8px;
                    padding: 12px;
                    text-align: center;
                }
                
                .metric-title {
                    font-size: 12px;
                    color: var(--text-secondary);
                    margin-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .metric-values {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .metric-value {
                    font-size: 16px;
                    font-weight: 600;
                    color: var(--text-primary);
                }
                
                .metric-label {
                    font-size: 10px;
                    color: var(--text-secondary);
                    margin-top: 2px;
                }
                
                .compatibility-gauge {
                    margin: 16px 0;
                    text-align: center;
                }
                
                .gauge-container {
                    position: relative;
                    width: 120px;
                    height: 60px;
                    margin: 0 auto 12px;
                    overflow: hidden;
                }
                
                .gauge-background {
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    background: conic-gradient(
                        var(--danger) 0deg 60deg,
                        var(--warning) 60deg 120deg,
                        var(--success) 120deg 180deg,
                        var(--warning) 180deg 240deg,
                        var(--danger) 240deg 360deg
                    );
                    position: relative;
                }
                
                .gauge-inner {
                    position: absolute;
                    top: 15px;
                    left: 15px;
                    width: 90px;
                    height: 90px;
                    background: var(--background);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-direction: column;
                }
                
                .gauge-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: var(--text-primary);
                }
                
                .gauge-label {
                    font-size: 10px;
                    color: var(--text-secondary);
                    margin-top: 2px;
                }
                
                .recommendations {
                    background: ${this.theme === 'dark' ? '#374151' : '#f0f9ff'};
                    border-radius: 8px;
                    padding: 12px;
                    margin-top: 16px;
                }
                
                .recommendations h4 {
                    margin: 0 0 8px 0;
                    font-size: 14px;
                    color: var(--text-primary);
                }
                
                .recommendations ul {
                    margin: 0;
                    padding-left: 16px;
                    font-size: 12px;
                    color: var(--text-secondary);
                    line-height: 1.4;
                }
                
                .loading, .error {
                    text-align: center;
                    padding: 20px;
                    color: var(--text-secondary);
                    font-size: 14px;
                }
                
                .loading-spinner {
                    width: 20px;
                    height: 20px;
                    border: 2px solid var(--border);
                    border-top: 2px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 8px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
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
                
                @media (max-width: 480px) {
                    .widget-container {
                        max-width: 100%;
                        border-radius: 8px;
                    }
                    
                    .comparison-grid {
                        grid-template-columns: 1fr;
                        gap: 12px;
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
                    <h2>🌡️ Weather & Habitat Compare</h2>
                </div>
                <div class="input-section">
                    <div class="location-input">
                        <input type="text" 
                               id="location-input" 
                               placeholder="Enter ZIP code or city"
                               aria-label="Location input">
                        <button id="compare-button">Compare</button>
                    </div>
                </div>
                <div id="comparison-content">
                    <div class="loading" style="display: none;">
                        <div class="loading-spinner"></div>
                        Analyzing habitat compatibility...
                    </div>
                </div>
                <div class="powered-by">
                    Powered by <a href="https://orchidcontinuum.org" target="_blank" rel="noopener">The Orchid Continuum</a>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        const input = this.shadowRoot.getElementById('location-input');
        const button = this.shadowRoot.getElementById('compare-button');
        
        button.addEventListener('click', () => this.performComparison());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performComparison();
            }
        });
    }

    async performComparison() {
        const input = this.shadowRoot.getElementById('location-input');
        const button = this.shadowRoot.getElementById('compare-button');
        const contentEl = this.shadowRoot.getElementById('comparison-content');
        const loadingEl = contentEl.querySelector('.loading');
        
        const location = input.value.trim();
        if (!location) {
            alert('Please enter a location');
            return;
        }
        
        button.disabled = true;
        loadingEl.style.display = 'block';
        
        try {
            // Fetch comparison data from API
            const response = await fetch(`${this.apiBase}/weather-compare`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    location: location,
                    orchid_id: this.orchidId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            this.comparisonData = await response.json();
            this.renderComparisonResults();
            
        } catch (error) {
            console.error('Comparison failed:', error);
            this.renderError('Unable to compare weather data. Please check your location and try again.');
        } finally {
            button.disabled = false;
            loadingEl.style.display = 'none';
        }
    }

    renderComparisonResults() {
        const contentEl = this.shadowRoot.getElementById('comparison-content');
        const data = this.comparisonData;
        
        // Demo data structure
        const local = data.local_conditions || { temp: 22, humidity: 45 };
        const habitat = data.habitat_conditions || { temp: 24, humidity: 75 };
        const compatibility = data.compatibility_score || 72;
        const recommendations = data.recommendations || [
            'Increase humidity around your orchid',
            'Provide bright, indirect light',
            'Maintain consistent temperatures'
        ];
        
        contentEl.innerHTML = `
            <div class="comparison-section">
                <div class="comparison-grid">
                    <div class="metric-card">
                        <div class="metric-title">Temperature</div>
                        <div class="metric-values">
                            <div>
                                <div class="metric-value">${local.temp}°C</div>
                                <div class="metric-label">Your Area</div>
                            </div>
                            <div>
                                <div class="metric-value">${habitat.temp}°C</div>
                                <div class="metric-label">Native Habitat</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">Humidity</div>
                        <div class="metric-values">
                            <div>
                                <div class="metric-value">${local.humidity}%</div>
                                <div class="metric-label">Your Area</div>
                            </div>
                            <div>
                                <div class="metric-value">${habitat.humidity}%</div>
                                <div class="metric-label">Native Habitat</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="compatibility-gauge">
                    <div class="gauge-container">
                        <div class="gauge-background">
                            <div class="gauge-inner">
                                <div class="gauge-value">${compatibility}%</div>
                                <div class="gauge-label">Compatible</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="recommendations">
                    <h4>🌱 Growing Recommendations</h4>
                    <ul>
                        ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    renderError(message) {
        const contentEl = this.shadowRoot.getElementById('comparison-content');
        contentEl.innerHTML = `<div class="error">${message}</div>`;
    }

    static get observedAttributes() {
        return ['data-theme', 'orchid-id', 'api-base'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue !== newValue) {
            if (name === 'data-theme') {
                this.theme = newValue;
            } else if (name === 'orchid-id') {
                this.orchidId = newValue;
            } else if (name === 'api-base') {
                this.apiBase = newValue;
            }
            
            if (this.shadowRoot) {
                this.render();
                this.setupEventListeners();
            }
        }
    }
}

// Register the custom element
if (!customElements.get('weather-compare')) {
    customElements.define('weather-compare', WeatherCompareWidget);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WeatherCompareWidget;
}