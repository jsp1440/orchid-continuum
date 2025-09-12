/**
 * FCOS Orchid of the Day Widget
 * Self-contained widget that displays one orchid per day from the Orchid Continuum database
 * Embeds with: <script src="orchid-of-the-day.js" defer></script>
 * Target: <div id="orchid-of-the-day"></div>
 */

const CONFIG = {
  timezone: 'America/Los_Angeles',
  containerId: 'orchid-of-the-day',
  DATA_SOURCE: {
    type: 'google_sheet', // 'google_sheet' | 'json' | 'local'
    url: '<<PASTE_YOUR_GOOGLE_SHEET_CSV_URL_HERE>>' // Get from File > Share > Publish to web > CSV
  },
  cacheTtlMinutes: 120,   // cache fetch in sessionStorage
  maxRecentHistory: 30,   // prevent repeats within last N days
  tracking: {
    enabled: true,
    onClick: null // optional callback(urlOrId) to wire analytics later
  },
  brand: {
    bg: '#f4fff4',
    title: '#2e7d32',
    text: '#111'
  }
};

class OrchidOfTheDayWidget {
  constructor(config) {
    this.config = config;
    this.data = null;
    this.container = null;
    this.shadowRoot = null;
    
    // Cache keys
    this.CACHE_KEY = 'orchid_data_cache';
    this.HISTORY_KEY = 'orchid_shown_history';
    this.LAST_DATE_KEY = 'orchid_last_date';
    
    this.init();
  }
  
  async init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }
  
  async setup() {
    // Find container
    this.container = document.getElementById(this.config.containerId);
    if (!this.container) {
      console.error(`Orchid widget: Container #${this.config.containerId} not found`);
      return;
    }
    
    // Create shadow DOM to avoid CSS conflicts
    this.shadowRoot = this.container.attachShadow({ mode: 'open' });
    
    // Load data and render
    try {
      await this.loadData();
      this.render();
    } catch (error) {
      console.error('Orchid widget error:', error);
      this.renderError();
    }
  }
  
  async loadData() {
    const now = Date.now();
    const cached = this.getFromCache();
    
    // Check cache validity
    if (cached && cached.timestamp && (now - cached.timestamp) < (this.config.cacheTtlMinutes * 60 * 1000)) {
      this.data = cached.data;
      return;
    }
    
    // Fetch fresh data based on source type
    let data;
    switch (this.config.DATA_SOURCE.type) {
      case 'google_sheet':
        data = await this.fetchGoogleSheet();
        break;
      case 'json':
        data = await this.fetchJSON();
        break;
      case 'local':
        data = await this.fetchLocal();
        break;
      default:
        throw new Error(`Unknown data source type: ${this.config.DATA_SOURCE.type}`);
    }
    
    // Filter to only entries with images
    this.data = data.filter(item => item.image_url && item.image_url.trim());
    
    // Cache the data
    this.saveToCache(this.data, now);
  }
  
  async fetchGoogleSheet() {
    const url = this.config.DATA_SOURCE.url;
    
    // Ensure the URL is a CSV export URL
    let csvUrl = url;
    if (url.includes('/edit') && !url.includes('/export')) {
      // Convert edit URL to CSV export URL
      const sheetId = url.match(/spreadsheets\/d\/([a-zA-Z0-9-_]+)/)?.[1];
      if (sheetId) {
        csvUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv&gid=0`;
      }
    }
    
    const response = await fetch(csvUrl);
    if (!response.ok) throw new Error(`Failed to fetch sheet: ${response.status} - Make sure sheet is published to web as CSV`);
    
    const csvText = await response.text();
    return this.parseCSV(csvText);
  }
  
  async fetchJSON() {
    const response = await fetch(this.config.DATA_SOURCE.url);
    if (!response.ok) throw new Error(`Failed to fetch JSON: ${response.status}`);
    
    return await response.json();
  }
  
  async fetchLocal() {
    // Sample data for local testing
    return [
      {
        genus: "Cattleya",
        species: "mossiae",
        variety: "",
        hybrid: "",
        grex: "",
        clonal_name: "Easter Sunday",
        infraspecific_rank: "",
        orchid_group: "Cattleya",
        title: "Cattleya mossiae 'Easter Sunday'",
        caption: "The national flower of Venezuela, this spectacular Cattleya blooms in spring with large, fragrant flowers. Native to cloud forests of the Venezuelan mountains.",
        image_url: "/static/images/sample-orchid.jpg",
        photographer: "Sample Photographer",
        credit: "Sample Collection",
        license: "",
        license_url: "",
        native_range: "Venezuela",
        habitat: "Cloud forest epiphyte",
        elevation_m: "800-2000",
        blooming_season: "Spring",
        culture_notes: "Intermediate temperatures, bright filtered light",
        date: "2025-01-01",
        tags: "fragrant,species",
        accession_id: "sample001"
      }
    ];
  }
  
  parseCSV(csvText) {
    const lines = csvText.split('\n').filter(line => line.trim());
    if (lines.length < 2) return [];
    
    // Parse headers (case-insensitive mapping)
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/"/g, ''));
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = this.parseCSVLine(lines[i]);
      if (values.length < headers.length) continue;
      
      const record = {};
      headers.forEach((header, index) => {
        const value = values[index] ? values[index].trim().replace(/"/g, '') : '';
        record[header] = value;
      });
      
      data.push(record);
    }
    
    return data;
  }
  
  parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"' && (i === 0 || line[i-1] !== '\\')) {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current);
        current = '';
      } else {
        current += char;
      }
    }
    
    result.push(current);
    return result;
  }
  
  getTodaysOrchid() {
    if (!this.data || this.data.length === 0) return null;
    
    const today = this.getTodayString();
    const lastDate = localStorage.getItem(this.LAST_DATE_KEY);
    
    // If it's a new day, potentially show a different orchid
    if (lastDate !== today) {
      localStorage.setItem(this.LAST_DATE_KEY, today);
    }
    
    // Get deterministic index for today
    let index = this.hashDate(today) % this.data.length;
    
    // Avoid recent repeats
    const history = this.getHistory();
    let attempts = 0;
    
    while (history.includes(index) && attempts < this.data.length) {
      index = (index + 1) % this.data.length;
      attempts++;
    }
    
    // Update history
    this.addToHistory(index);
    
    return this.data[index];
  }
  
  getTodayString() {
    const now = new Date();
    // Convert to Los Angeles timezone
    const losAngeles = new Intl.DateTimeFormat('en-CA', {
      timeZone: this.config.timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(now);
    
    return losAngeles;
  }
  
  hashDate(dateString) {
    let hash = 0;
    for (let i = 0; i < dateString.length; i++) {
      const char = dateString.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }
  
  getHistory() {
    const stored = localStorage.getItem(this.HISTORY_KEY);
    return stored ? JSON.parse(stored) : [];
  }
  
  addToHistory(index) {
    let history = this.getHistory();
    history.push(index);
    
    // Keep only recent history
    if (history.length > this.config.maxRecentHistory) {
      history = history.slice(-this.config.maxRecentHistory);
    }
    
    localStorage.setItem(this.HISTORY_KEY, JSON.stringify(history));
  }
  
  formatTitle(orchid) {
    const parts = [];
    
    // Scientific name in italics
    if (orchid.genus && orchid.species) {
      parts.push(`<em>${orchid.genus} ${orchid.species}</em>`);
      
      // Add infraspecific rank if present
      if (orchid.infraspecific_rank && orchid.variety) {
        parts.push(`${orchid.infraspecific_rank} ${orchid.variety}`);
      }
    } else if (orchid.hybrid || orchid.grex) {
      // Hybrid name - only italicize if it contains valid botanical epithets
      const hybridName = orchid.hybrid || orchid.grex;
      if (orchid.genus) {
        parts.push(`<em>${orchid.genus}</em> ${hybridName}`);
      } else {
        parts.push(hybridName);
      }
    } else if (orchid.title) {
      parts.push(orchid.title);
    } else {
      parts.push("Unknown Orchid");
    }
    
    // Add clonal name in quotes
    if (orchid.clonal_name) {
      parts.push(`'${orchid.clonal_name}'`);
    }
    
    return parts.join(' ');
  }
  
  formatCaption(orchid) {
    if (orchid.caption) {
      return orchid.caption;
    }
    
    // Build caption from available fields
    const parts = [];
    
    if (orchid.native_range) {
      parts.push(`Native to ${orchid.native_range}`);
    }
    
    if (orchid.habitat) {
      parts.push(`Found in ${orchid.habitat.toLowerCase()}`);
    }
    
    if (orchid.blooming_season) {
      parts.push(`Blooms in ${orchid.blooming_season.toLowerCase()}`);
    }
    
    if (orchid.culture_notes && parts.length < 2) {
      const notes = orchid.culture_notes.length > 100 
        ? orchid.culture_notes.substring(0, 97) + '...' 
        : orchid.culture_notes;
      parts.push(notes);
    }
    
    return parts.length > 0 
      ? parts.join('. ') + '.'
      : 'A beautiful orchid from our collection.';
  }
  
  render() {
    const orchid = this.getTodaysOrchid();
    
    if (!orchid) {
      this.renderError("No orchid data available");
      return;
    }
    
    const title = this.formatTitle(orchid);
    const caption = this.formatCaption(orchid);
    
    // Build chips
    const chips = [];
    if (orchid.orchid_group) {
      chips.push(orchid.orchid_group);
    }
    if (orchid.blooming_season) {
      chips.push(orchid.blooming_season);
    }
    
    const chipHtml = chips.map(chip => 
      `<span class="chip">${this.escapeHtml(chip)}</span>`
    ).join('');
    
    // Credit line
    let creditHtml = '';
    if (orchid.credit || orchid.photographer) {
      const credit = orchid.credit || orchid.photographer;
      creditHtml = `<div class="credit">Photo: ${this.escapeHtml(credit)}</div>`;
    }
    
    // License
    let licenseHtml = '';
    if (orchid.license && orchid.license_url) {
      licenseHtml = `<a href="${orchid.license_url}" class="license" target="_blank" rel="noopener">${this.escapeHtml(orchid.license)}</a>`;
    } else if (orchid.license) {
      licenseHtml = `<span class="license">${this.escapeHtml(orchid.license)}</span>`;
    }
    
    // Alt text for image
    const altText = `${orchid.genus || ''} ${orchid.species || ''} orchid${orchid.native_range ? ' from ' + orchid.native_range : ''}`.trim();
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          line-height: 1.6;
          color: ${this.config.brand.text};
        }
        
        .orchid-card {
          background: ${this.config.brand.bg};
          border: 2px solid ${this.config.brand.title};
          border-radius: 12px;
          padding: 24px;
          max-width: 600px;
          margin: 0 auto;
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .orchid-title {
          font-size: 24px;
          font-weight: 600;
          color: ${this.config.brand.title};
          margin: 0 0 16px 0;
          line-height: 1.3;
        }
        
        .orchid-title em {
          font-style: italic;
          font-weight: inherit;
        }
        
        .chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 20px;
        }
        
        .chip {
          background: white;
          border: 1px solid ${this.config.brand.title};
          color: ${this.config.brand.title};
          padding: 4px 12px;
          border-radius: 16px;
          font-size: 14px;
          font-weight: 500;
        }
        
        .orchid-image {
          width: 100%;
          max-width: 560px;
          height: auto;
          border-radius: 8px;
          margin-bottom: 16px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .orchid-caption {
          font-size: 18px;
          line-height: 1.6;
          margin-bottom: 16px;
          color: ${this.config.brand.text};
        }
        
        .credit {
          font-size: 14px;
          color: #666;
          margin-bottom: 8px;
        }
        
        .license {
          font-size: 12px;
          color: #888;
          text-decoration: none;
          border: 1px solid #ddd;
          padding: 2px 6px;
          border-radius: 4px;
          display: inline-block;
        }
        
        .license:hover {
          background: #f5f5f5;
          text-decoration: underline;
        }
        
        .error {
          background: #fff3cd;
          border: 1px solid #ffeaa7;
          color: #856404;
          padding: 20px;
          border-radius: 8px;
          text-align: center;
          font-size: 18px;
        }
        
        /* Accessibility */
        :focus {
          outline: 2px solid ${this.config.brand.title};
          outline-offset: 2px;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 480px) {
          .orchid-card {
            padding: 16px;
          }
          
          .orchid-title {
            font-size: 20px;
          }
          
          .orchid-caption {
            font-size: 16px;
          }
        }
      </style>
      
      <div class="orchid-card" role="article" aria-live="polite">
        <h1 class="orchid-title">${title}</h1>
        ${chipHtml ? `<div class="chips">${chipHtml}</div>` : ''}
        <img 
          src="${orchid.image_url}" 
          alt="${this.escapeHtml(altText)}"
          class="orchid-image"
          loading="lazy"
          onerror="this.style.display='none'"
        />
        <p class="orchid-caption">${caption}</p>
        ${creditHtml}
        ${licenseHtml}
      </div>
    `;
    
    // Track click if enabled
    if (this.config.tracking.enabled && this.config.tracking.onClick) {
      const card = this.shadowRoot.querySelector('.orchid-card');
      card.style.cursor = 'pointer';
      card.addEventListener('click', () => {
        this.config.tracking.onClick(orchid.accession_id || orchid.id);
      });
    }
  }
  
  renderError(message = "Today's orchid will appear here soon.") {
    this.shadowRoot.innerHTML = `
      <style>
        .error {
          background: #fff3cd;
          border: 1px solid #ffeaa7;
          color: #856404;
          padding: 20px;
          border-radius: 8px;
          text-align: center;
          font-size: 18px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          line-height: 1.6;
          max-width: 600px;
          margin: 0 auto;
        }
      </style>
      <div class="error" role="alert">
        ${this.escapeHtml(message)}
      </div>
    `;
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  getFromCache() {
    try {
      const cached = sessionStorage.getItem(this.CACHE_KEY);
      return cached ? JSON.parse(cached) : null;
    } catch (e) {
      return null;
    }
  }
  
  saveToCache(data, timestamp) {
    try {
      sessionStorage.setItem(this.CACHE_KEY, JSON.stringify({ data, timestamp }));
    } catch (e) {
      console.warn('Could not cache orchid data:', e);
    }
  }
}

// Auto-initialize when script loads
(function() {
  new OrchidOfTheDayWidget(CONFIG);
})();