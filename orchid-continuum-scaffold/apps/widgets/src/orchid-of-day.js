/**
 * Orchid of the Day Widget
 * Embeddable web component for displaying featured orchid
 */

class OrchidOfDayWidget extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.apiBase = this.getAttribute('api-base') || 'https://api.orchidcontinuum.org';
        this.theme = this.getAttribute('data-theme') || 'light';
        this.size = this.getAttribute('data-size') || 'medium';
        this.loading = false;
    }

    connectedCallback() {
        this.render();
        this.loadOrchidData();
    }

    getStyles() {
        return `
            <style>
                :host {
                    display: block;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    --primary-color: ${this.theme === 'dark' ? '#8b5cf6' : '#7c3aed'};
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
                    max-width: ${this.size === 'small' ? '280px' : this.size === 'large' ? '400px' : '320px'};
                    margin: 0 auto;
                }
                
                .header {
                    padding: 16px;
                    background: linear-gradient(135deg, var(--primary-color), #ec4899);
                    color: white;
                    text-align: center;
                }
                
                .header h2 {
                    margin: 0;
                    font-size: ${this.size === 'small' ? '16px' : '18px'};
                    font-weight: 600;
                }
                
                .image-container {
                    position: relative;
                    aspect-ratio: 4/3;
                    overflow: hidden;
                }
                
                .orchid-image {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    transition: transform 0.3s ease;
                }
                
                .orchid-image:hover {
                    transform: scale(1.05);
                }
                
                .rights-watermark {
                    position: absolute;
                    bottom: 8px;
                    right: 8px;
                    background: rgba(0, 0, 0, 0.7);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 10px;
                    opacity: 0.8;
                }
                
                .content {
                    padding: 16px;
                }
                
                .orchid-title {
                    font-size: ${this.size === 'small' ? '16px' : '18px'};
                    font-weight: 600;
                    color: var(--text-primary);
                    margin: 0 0 8px 0;
                    font-style: italic;
                }
                
                .orchid-description {
                    font-size: 14px;
                    color: var(--text-secondary);
                    line-height: 1.5;
                    margin: 0 0 12px 0;
                    display: -webkit-box;
                    -webkit-line-clamp: 3;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }
                
                .orchid-credit {
                    font-size: 12px;
                    color: var(--text-secondary);
                    border-top: 1px solid var(--border);
                    padding-top: 8px;
                    margin-top: 8px;
                }
                
                .loading {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 40px;
                    color: var(--text-secondary);
                }
                
                .loading-spinner {
                    width: 20px;
                    height: 20px;
                    border: 2px solid var(--border);
                    border-top: 2px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 8px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .error {
                    padding: 20px;
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
                
                @media (max-width: 480px) {
                    .widget-container {
                        max-width: 100%;
                        border-radius: 8px;
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
                    <h2>🌺 Orchid of the Day</h2>
                </div>
                <div id="content">
                    <div class="loading">
                        <div class="loading-spinner"></div>
                        Loading today's orchid...
                    </div>
                </div>
                <div class="powered-by">
                    Powered by <a href="https://orchidcontinuum.org" target="_blank" rel="noopener">The Orchid Continuum</a>
                </div>
            </div>
        `;
    }

    async loadOrchidData() {
        if (this.loading) return;
        
        this.loading = true;
        const contentEl = this.shadowRoot.getElementById('content');
        
        try {
            const response = await fetch(`${this.apiBase}/orchid-of-day`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const orchid = await response.json();
            this.renderOrchidContent(orchid);
            
        } catch (error) {
            console.error('Failed to load orchid data:', error);
            contentEl.innerHTML = `
                <div class="error">
                    Unable to load today's orchid. Please try again later.
                </div>
            `;
        } finally {
            this.loading = false;
        }
    }

    renderOrchidContent(orchid) {
        const contentEl = this.shadowRoot.getElementById('content');
        
        const imageUrl = orchid.image_url || '/static/images/orchid_placeholder.svg';
        const title = orchid.title || orchid.scientific_name || 'Unknown Orchid';
        const description = orchid.description || orchid.ai_description || 'A beautiful orchid specimen.';
        const photographer = orchid.photographer || 'Unknown';
        const rightsInfo = orchid.rights_info || {};
        
        contentEl.innerHTML = `
            <div class="image-container">
                <img class="orchid-image" 
                     src="${imageUrl}" 
                     alt="${title}"
                     loading="lazy"
                     onerror="this.src='/static/images/orchid_placeholder.svg'">
                ${rightsInfo.watermark ? `<div class="rights-watermark">${rightsInfo.watermark}</div>` : ''}
            </div>
            <div class="content">
                <h3 class="orchid-title">${title}</h3>
                <p class="orchid-description">${description}</p>
                <div class="orchid-credit">
                    📸 Photo by ${photographer}
                </div>
            </div>
        `;
    }

    static get observedAttributes() {
        return ['data-theme', 'data-size', 'api-base'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue !== newValue) {
            if (name === 'data-theme') {
                this.theme = newValue;
            } else if (name === 'data-size') {
                this.size = newValue;
            } else if (name === 'api-base') {
                this.apiBase = newValue;
            }
            
            if (this.shadowRoot) {
                this.render();
                this.loadOrchidData();
            }
        }
    }
}

// Register the custom element
if (!customElements.get('orchid-of-day')) {
    customElements.define('orchid-of-day', OrchidOfDayWidget);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrchidOfDayWidget;
}