/**
 * Five Cities Orchid Society - Embeddable Widget SDK
 * 
 * Usage:
 * <script src="https://your-domain.replit.app/static/orchid-widget.js"></script>
 * <div data-orchid-widget data-limit="6" data-genus="Cattleya" data-theme="dark"></div>
 * <script>OrchidWidget.init();</script>
 */

(function(window, document) {
  'use strict';

  const DEFAULT_CONFIG = {
    apiBaseUrl: window.location.origin,
    theme: 'light',
    limit: 6,
    genus: null,
    width: '100%',
    height: 'auto'
  };

  class OrchidWidget {
    constructor() {
      this.widgets = [];
    }

    init() {
      this.loadStyles();
      const containers = document.querySelectorAll('[data-orchid-widget]');
      containers.forEach(container => this.createWidget(container));
    }

    loadStyles() {
      if (document.getElementById('orchid-widget-styles')) return;

      const style = document.createElement('style');
      style.id = 'orchid-widget-styles';
      style.textContent = `
        .orchid-widget {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          border-radius: 12px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          overflow: hidden;
          background: white;
          color: #111827;
        }
        .orchid-widget.dark {
          background: #1f2937;
          color: #f9fafb;
        }
        .orchid-widget-header {
          text-align: center;
          padding: 24px 24px 0;
        }
        .orchid-widget-title {
          font-size: 24px;
          font-weight: bold;
          margin: 0 0 8px;
        }
        .orchid-widget-subtitle {
          opacity: 0.7;
          margin: 0;
        }
        .orchid-widget-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 16px;
          padding: 24px;
        }
        .orchid-card {
          border-radius: 8px;
          overflow: hidden;
          transition: transform 0.2s ease;
          background: #f9fafb;
        }
        .orchid-widget.dark .orchid-card {
          background: #374151;
        }
        .orchid-card:hover {
          transform: translateY(-2px);
        }
        .orchid-card-image {
          width: 100%;
          height: 200px;
          object-fit: cover;
          background: #e5e7eb;
        }
        .orchid-card-content {
          padding: 16px;
        }
        .orchid-card-title {
          font-weight: 600;
          font-style: italic;
          margin: 0 0 4px;
          font-size: 14px;
        }
        .orchid-card-genus {
          opacity: 0.7;
          margin: 0 0 8px;
          font-size: 12px;
        }
        .orchid-card-description {
          opacity: 0.6;
          font-size: 12px;
          line-height: 1.4;
          margin: 0;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        .orchid-widget-footer {
          text-align: center;
          padding: 0 24px 24px;
        }
        .orchid-widget-button {
          display: inline-flex;
          align-items: center;
          padding: 8px 16px;
          background: #7c3aed;
          color: white;
          text-decoration: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          transition: background-color 0.2s ease;
        }
        .orchid-widget-button:hover {
          background: #6d28d9;
        }
        .orchid-widget-loading {
          padding: 48px 24px;
          text-align: center;
        }
        .orchid-widget-spinner {
          width: 32px;
          height: 32px;
          border: 3px solid #e5e7eb;
          border-top: 3px solid #7c3aed;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 16px;
        }
        .orchid-widget-error {
          padding: 48px 24px;
          text-align: center;
          color: #ef4444;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
          .orchid-widget-grid {
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            padding: 16px;
          }
          .orchid-widget-header {
            padding: 16px 16px 0;
          }
          .orchid-widget-title {
            font-size: 20px;
          }
        }
      `;
      document.head.appendChild(style);
    }

    createWidget(container) {
      const config = this.parseConfig(container);
      const widget = new SingleOrchidWidget(container, config);
      this.widgets.push(widget);
      widget.render();
    }

    parseConfig(container) {
      const dataset = container.dataset;
      return {
        ...DEFAULT_CONFIG,
        theme: dataset.theme || DEFAULT_CONFIG.theme,
        limit: parseInt(dataset.limit) || DEFAULT_CONFIG.limit,
        genus: dataset.genus || null,
        apiBaseUrl: dataset.apiBaseUrl || DEFAULT_CONFIG.apiBaseUrl
      };
    }
  }

  class SingleOrchidWidget {
    constructor(container, config) {
      this.container = container;
      this.config = config;
      this.orchids = [];
      this.loading = true;
      this.error = null;
    }

    async render() {
      this.renderLoading();
      await this.fetchData();
      this.renderContent();
    }

    renderLoading() {
      this.container.innerHTML = `
        <div class="orchid-widget ${this.config.theme}">
          <div class="orchid-widget-loading">
            <div class="orchid-widget-spinner"></div>
            <div>Loading orchid collection...</div>
          </div>
        </div>
      `;
    }

    renderError(message) {
      this.container.innerHTML = `
        <div class="orchid-widget ${this.config.theme}">
          <div class="orchid-widget-error">
            <div style="font-size: 24px; margin-bottom: 8px;">🌺</div>
            <div style="font-weight: 600; margin-bottom: 8px;">Connection Error</div>
            <div style="font-size: 14px;">${message}</div>
          </div>
        </div>
      `;
    }

    async fetchData() {
      try {
        const params = new URLSearchParams({
          limit: this.config.limit.toString(),
          ...(this.config.genus && { genus: this.config.genus })
        });
        
        const response = await fetch(`${this.config.apiBaseUrl}/api/v2/orchids?${params}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        this.orchids = await response.json();
        this.loading = false;
        this.error = null;
      } catch (err) {
        console.error('Failed to fetch orchids:', err);
        this.error = 'Failed to load orchid data. Please check the API connection.';
        this.loading = false;
      }
    }

    renderContent() {
      if (this.error) {
        this.renderError(this.error);
        return;
      }

      const orchidCards = this.orchids.map(orchid => this.renderOrchidCard(orchid)).join('');
      
      this.container.innerHTML = `
        <div class="orchid-widget ${this.config.theme}">
          <div class="orchid-widget-header">
            <h2 class="orchid-widget-title">🌺 Five Cities Orchid Society Collection</h2>
            <p class="orchid-widget-subtitle">
              ${this.config.genus ? `${this.config.genus} species` : 'Featured orchids'} from our digital collection
            </p>
          </div>
          
          ${this.orchids.length === 0 ? `
            <div class="orchid-widget-loading">
              <div style="font-size: 32px; margin-bottom: 16px;">🔍</div>
              <div style="font-weight: 600; margin-bottom: 8px;">No orchids found</div>
              <div style="font-size: 14px; opacity: 0.7;">Try adjusting your search criteria or check back later.</div>
            </div>
          ` : `
            <div class="orchid-widget-grid">
              ${orchidCards}
            </div>
          `}
          
          <div class="orchid-widget-footer">
            <a href="${this.config.apiBaseUrl}/gallery" target="_blank" rel="noopener noreferrer" class="orchid-widget-button">
              View Full Collection →
            </a>
          </div>
        </div>
      `;
    }

    renderOrchidCard(orchid) {
      const photoUrl = orchid.photo_url || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyNCIgZmlsbD0iIzlmYTJhOCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPvCfjLo8L3RleHQ+PC9zdmc+';
      
      return `
        <div class="orchid-card">
          <img 
            class="orchid-card-image" 
            src="${photoUrl}" 
            alt="${orchid.scientific_name || 'Unknown orchid'}"
            onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyNCIgZmlsbD0iIzlmYTJhOCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPvCfjLo8L3RleHQ+PC9zdmc+'"
          />
          <div class="orchid-card-content">
            <h3 class="orchid-card-title">${orchid.scientific_name || 'Unknown species'}</h3>
            <p class="orchid-card-genus">
              ${orchid.genus && orchid.species 
                ? `${orchid.genus} ${orchid.species}`
                : orchid.genus || 'Unknown genus'
              }
            </p>
            ${orchid.description && orchid.description.length > 10 && !orchid.description.includes('Error') ? `
              <p class="orchid-card-description">
                ${orchid.description.substring(0, 100)}${orchid.description.length > 100 ? '...' : ''}
              </p>
            ` : ''}
          </div>
        </div>
      `;
    }
  }

  // Global API
  window.OrchidWidget = new OrchidWidget();

  // Auto-initialize if DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      window.OrchidWidget.init();
    });
  } else {
    window.OrchidWidget.init();
  }

})(window, document);