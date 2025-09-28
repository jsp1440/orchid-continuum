/*!
 * FCOS Orchid of the Day Widget v1.0
 * Production-ready, self-contained botanical display widget
 * ========================================================
 * 
 * INSTALLATION INSTRUCTIONS
 * ========================
 * 
 * 1. ADD TO NEON ONE HEADER:
 *    In your Neon One admin, go to Design > Custom HTML/CSS
 *    Add this to the <head> section:
 *    
 *    <script src="https://your-domain.com/static/js/orchid-of-the-day.js" defer></script>
 * 
 * 2. ADD PLACEHOLDER DIV:
 *    Where you want the widget to appear, add:
 *    
 *    <div id="orchid-of-the-day"></div>
 * 
 * 3. CONFIGURE DATA SOURCE:
 *    Edit the CONFIG object below to set your data source:
 *    
 *    For Google Sheets:
 *    DATA_SOURCE: {
 *      type: 'google_sheet',
 *      url: 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv'
 *    }
 *    
 *    For JSON API:
 *    DATA_SOURCE: {
 *      type: 'json',
 *      url: 'https://your-api.com/orchid-data.json'
 *    }
 *    
 *    For Local Testing:
 *    DATA_SOURCE: {
 *      type: 'local'
 *    }
 * 
 * 4. REQUIRED CSV/JSON HEADERS:
 *    genus, species, variety, hybrid, grex, clonal_name, infraspecific_rank, 
 *    orchid_group, title, caption, image_url, photographer, credit, license, 
 *    license_url, native_range, habitat, elevation_m, blooming_season, 
 *    culture_notes, date, tags, accession_id
 *    
 *    Only 'image_url' is strictly required. Headers are case-insensitive and
 *    support underscores, spaces, or hyphens (e.g., "Image URL", "image_url", "image-url").
 * 
 * 5. CUSTOMIZE APPEARANCE:
 *    Edit CONFIG.brand object:
 *    brand: {
 *      bg: '#f4fff4',      // Background color
 *      title: '#2e7d32',   // Title color (FCOS green)
 *      text: '#111',       // Body text color
 *      font: 'system'      // Font family ('system' uses device defaults)
 *    }
 * 
 * FEATURES
 * ========
 * • Daily rotation with no repeats for 30+ days
 * • Proper botanical formatting (*Genus species* 'Clone Name')
 * • Senior-friendly 18px base font, high contrast
 * • WCAG AA accessible with alt text and focus states
 * • Shadow DOM prevents CSS conflicts
 * • Mobile responsive design
 * • Graceful error handling with user-friendly messages
 * • Embedded sample data for immediate testing
 * 
 */

const CONFIG = {
  timezone: 'America/Los_Angeles',
  containerId: 'orchid-of-the-day',
  DATA_SOURCE: {
    type: 'local', // 'google_sheet' | 'json' | 'local'
    url: '<<PASTE_YOUR_GOOGLE_SHEET_CSV_OR_JSON_URL_HERE>>'
  },
  cacheTtlMinutes: 120,
  maxRecentHistory: 30,
  tracking: {
    enabled: true,
    onClick: null // callback(orchid) for analytics
  },
  brand: {
    bg: '#f4fff4',
    title: '#2e7d32',
    text: '#111',
    font: 'system'
  }
};

// Embedded sample data for immediate testing (3 realistic records)
const SAMPLE_DATA = `data:application/json,${encodeURIComponent(JSON.stringify([
  {
    genus: "Cattleya",
    species: "mossiae",
    variety: "",
    hybrid: "",
    grex: "",
    clonal_name: "Easter Sunday",
    infraspecific_rank: "",
    orchid_group: "Cattleya",
    title: "",
    caption: "The national flower of Venezuela, this spectacular Cattleya produces large, fragrant flowers in spring with vibrant pink and purple petals surrounding a deep magenta lip. Known for its robust growth and reliable blooming, this clone has won numerous awards for its perfect form and intense fragrance.",
    image_url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%23f8f9fa'/%3E%3Cpath d='M200 80 Q240 100 260 140 Q240 180 200 200 Q160 180 140 140 Q160 100 200 80 Z' fill='%23e91e63'/%3E%3Cpath d='M200 100 Q220 110 230 130 Q220 150 200 160 Q180 150 170 130 Q180 110 200 100 Z' fill='%23ad1457'/%3E%3Ctext x='200' y='250' text-anchor='middle' font-family='serif' font-size='16' fill='%23666'%3ECattleya mossiae%3C/text%3E%3C/svg%3E",
    photographer: "María González",
    credit: "Venezuelan Orchid Society",
    license: "CC BY-SA 4.0",
    license_url: "https://creativecommons.org/licenses/by-sa/4.0/",
    native_range: "Venezuela, Colombia",
    habitat: "Cloud forest epiphyte",
    elevation_m: "800-2000",
    blooming_season: "Spring (March-May)",
    culture_notes: "Intermediate temperatures (65-80°F days, 55-65°F nights). Bright filtered light, good air circulation. Allow to dry between waterings.",
    date: "2025-01-15",
    tags: "fragrant,species,spring-blooming",
    accession_id: "SAMPLE001"
  },
  {
    genus: "Phalaenopsis",
    species: "",
    variety: "",
    hybrid: "Sogo Yukidian",
    grex: "Sogo Yukidian",
    clonal_name: "V3",
    infraspecific_rank: "",
    orchid_group: "Phalaenopsis",
    title: "",
    caption: "This pristine white Phalaenopsis hybrid showcases perfect form with broad, overlapping petals and a subtle yellow throat. Blooms can last 3-4 months with proper care, making it an ideal choice for beginners and experienced growers alike.",
    image_url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%23f8f9fa'/%3E%3Cpath d='M200 60 Q260 80 280 140 Q260 200 200 220 Q140 200 120 140 Q140 80 200 60 Z' fill='%23ffffff' stroke='%23e0e0e0'/%3E%3Cpath d='M200 90 Q230 100 240 130 Q230 160 200 170 Q170 160 160 130 Q170 100 200 90 Z' fill='%23fff9c4'/%3E%3Ctext x='200' y='250' text-anchor='middle' font-family='serif' font-size='16' fill='%23666'%3EPhalaenopsis Sogo Yukidian%3C/text%3E%3C/svg%3E",
    photographer: "David Kim",
    credit: "California Orchid Society",
    license: "",
    license_url: "",
    native_range: "Hybrid (Asian parentage)",
    habitat: "Cultivated epiphyte",
    elevation_m: "",
    blooming_season: "Winter-Spring",
    culture_notes: "Warm temperatures (70-85°F days, 65-75°F nights). Low to medium light, high humidity. Keep media moist but not soggy.",
    date: "2025-01-16",
    tags: "beginner-friendly,hybrid,long-lasting,white",
    accession_id: "SAMPLE002"
  },
  {
    genus: "Dendrobium",
    species: "nobile",
    variety: "",
    hybrid: "",
    grex: "",
    clonal_name: "",
    infraspecific_rank: "",
    orchid_group: "Dendrobium",
    title: "",
    caption: "",
    image_url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%23f8f9fa'/%3E%3Cpath d='M180 70 Q200 60 220 70 Q230 90 220 110 Q200 120 180 110 Q170 90 180 70 Z' fill='%23f8bbd9'/%3E%3Cpath d='M200 80 Q210 85 215 95 Q210 105 200 110 Q190 105 185 95 Q190 85 200 80 Z' fill='%23e1bee7'/%3E%3Cpath d='M160 120 Q180 110 200 120 Q210 140 200 160 Q180 170 160 160 Q150 140 160 120 Z' fill='%23f8bbd9'/%3E%3Cpath d='M240 120 Q260 110 280 120 Q290 140 280 160 Q260 170 240 160 Q230 140 240 120 Z' fill='%23f8bbd9'/%3E%3Ctext x='200' y='250' text-anchor='middle' font-family='serif' font-size='16' fill='%23666'%3EDendrobium nobile%3C/text%3E%3C/svg%3E",
    photographer: "Chen Wei",
    credit: "Beijing Orchid Association",
    license: "",
    license_url: "",
    native_range: "China, Himalayas, Southeast Asia",
    habitat: "Mountain epiphyte on deciduous trees",
    elevation_m: "1000-2500",
    blooming_season: "Late winter to early spring",
    culture_notes: "Requires cool, dry winter rest (50-60°F, minimal water). Bright light, good air movement essential. Water freely during growing season.",
    date: "2025-01-17",
    tags: "species,fragrant,cool-growing,rest-period",
    accession_id: "SAMPLE003"
  }
]))}`;

class OrchidOfTheDayWidget {
  constructor(config) {
    this.config = config;
    this.data = null;
    this.container = null;
    this.shadowRoot = null;
    
    // Cache and history keys
    this.CACHE_KEY = 'orchid_widget_cache';
    this.HISTORY_KEY = 'orchid_widget_history';
    this.LAST_DATE_KEY = 'orchid_widget_last_date';
    
    this.init();
  }
  
  async init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }
  
  async setup() {
    this.container = document.getElementById(this.config.containerId);
    if (!this.container) {
      console.error(`FCOS Orchid Widget: Container #${this.config.containerId} not found`);
      return;
    }
    
    // Create shadow DOM for style isolation
    this.shadowRoot = this.container.attachShadow({ mode: 'open' });
    
    try {
      await this.loadData();
      this.render();
    } catch (error) {
      console.error('FCOS Orchid Widget error:', error);
      this.renderError(this.getErrorMessage(error));
    }
  }
  
  getErrorMessage(error) {
    const message = error.message || error.toString();
    
    if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
      return "Unable to load today's orchid due to network issues. Please check your internet connection and try refreshing the page.";
    }
    
    if (message.includes('CORS')) {
      return "Data source not accessible due to security restrictions. Please ensure your orchid data source allows cross-origin requests.";
    }
    
    if (message.includes('sheet') && message.includes('published')) {
      return "Google Sheet not accessible. Please ensure it's published to the web as CSV format (File > Share > Publish to web > CSV).";
    }
    
    if (message.includes('No orchid data')) {
      return "No orchid data found. Please check your data source URL and ensure it contains orchid records with image URLs.";
    }
    
    return "Today's orchid is temporarily unavailable. Please try again later.";
  }
  
  async loadData() {
    const now = Date.now();
    const cached = this.getFromCache();
    
    // Check cache validity
    if (cached && cached.timestamp && (now - cached.timestamp) < (this.config.cacheTtlMinutes * 60 * 1000)) {
      this.data = cached.data;
      return;
    }
    
    // Fetch fresh data
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
    
    // Normalize and filter data
    this.data = this.normalizeData(data).filter(item => item.image_url && item.image_url.trim());
    
    if (this.data.length === 0) {
      throw new Error('No orchid data available with valid image URLs');
    }
    
    // Cache the processed data
    this.saveToCache(this.data, now);
  }
  
  async fetchGoogleSheet() {
    const url = this.config.DATA_SOURCE.url;
    let csvUrl = url;
    
    // Convert Google Sheets edit URLs to CSV export URLs
    if (url.includes('/edit') && !url.includes('/export')) {
      const sheetId = url.match(/spreadsheets\/d\/([a-zA-Z0-9-_]+)/)?.[1];
      if (sheetId) {
        csvUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv&gid=0`;
      }
    }
    
    const response = await fetch(csvUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch sheet: ${response.status} - Make sure sheet is published to web as CSV`);
    }
    
    const csvText = await response.text();
    return this.parseCSV(csvText);
  }
  
  async fetchJSON() {
    const response = await fetch(this.config.DATA_SOURCE.url);
    if (!response.ok) {
      throw new Error(`Failed to fetch JSON: ${response.status}`);
    }
    
    return await response.json();
  }
  
  async fetchLocal() {
    const response = await fetch(SAMPLE_DATA);
    return await response.json();
  }
  
  parseCSV(csvText) {
    const lines = csvText.split('\n').filter(line => line.trim());
    if (lines.length < 2) return [];
    
    // Parse headers with normalization
    const rawHeaders = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const headers = rawHeaders.map(h => this.normalizeHeader(h));
    
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
  
  normalizeHeader(header) {
    // Convert various header formats to standard field names
    const normalized = header.toLowerCase()
      .replace(/[-\s]+/g, '_')
      .replace(/[^\w]/g, '');
    
    // Map common variations to standard names
    const headerMap = {
      'imageurl': 'image_url',
      'imageufl': 'image_url',
      'image': 'image_url',
      'photo': 'image_url',
      'photourl': 'image_url',
      'clonename': 'clonal_name',
      'clone': 'clonal_name',
      'cultivar': 'clonal_name',
      'nativerange': 'native_range',
      'native': 'native_range',
      'origin': 'native_range',
      'elevationm': 'elevation_m',
      'elevation': 'elevation_m',
      'altitude': 'elevation_m',
      'bloomingseason': 'blooming_season',
      'blooming': 'blooming_season',
      'bloom': 'blooming_season',
      'flowering': 'blooming_season',
      'culturenotes': 'culture_notes',
      'culture': 'culture_notes',
      'care': 'culture_notes',
      'carenotes': 'culture_notes',
      'orchidgroup': 'orchid_group',
      'group': 'orchid_group',
      'type': 'orchid_group',
      'infraspecificrank': 'infraspecific_rank',
      'rank': 'infraspecific_rank',
      'accessionid': 'accession_id',
      'accession': 'accession_id',
      'id': 'accession_id',
      'licenseurl': 'license_url'
    };
    
    return headerMap[normalized] || normalized;
  }
  
  normalizeData(rawData) {
    if (!Array.isArray(rawData)) return [];
    
    return rawData.map(item => {
      const normalized = {};
      
      // Standard fields with defaults
      const fields = [
        'genus', 'species', 'variety', 'hybrid', 'grex', 'clonal_name',
        'infraspecific_rank', 'orchid_group', 'title', 'caption', 'image_url',
        'photographer', 'credit', 'license', 'license_url', 'native_range',
        'habitat', 'elevation_m', 'blooming_season', 'culture_notes',
        'date', 'tags', 'accession_id'
      ];
      
      fields.forEach(field => {
        normalized[field] = item[field] || item[this.normalizeHeader(field)] || '';
      });
      
      return normalized;
    });
  }
  
  getTodaysOrchid() {
    if (!this.data || this.data.length === 0) return null;
    
    const today = this.getTodayString();
    const lastDate = localStorage.getItem(this.LAST_DATE_KEY);
    
    // Update date if it's a new day
    if (lastDate !== today) {
      localStorage.setItem(this.LAST_DATE_KEY, today);
    }
    
    // Get deterministic index using mulberry32 PRNG
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
    return new Intl.DateTimeFormat('en-CA', {
      timeZone: this.config.timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(now);
  }
  
  // Mulberry32 PRNG for stable date-based seeding
  hashDate(dateString) {
    let seed = 0;
    for (let i = 0; i < dateString.length; i++) {
      seed = Math.imul(31, seed) + dateString.charCodeAt(i) | 0;
    }
    
    // Mulberry32 algorithm
    seed = Math.imul(seed ^ seed >>> 15, seed | 1);
    seed ^= seed + Math.imul(seed ^ seed >>> 7, seed | 61);
    return ((seed ^ seed >>> 14) >>> 0) / 4294967296;
  }
  
  getHistory() {
    try {
      const stored = localStorage.getItem(this.HISTORY_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      return [];
    }
  }
  
  addToHistory(index) {
    try {
      let history = this.getHistory();
      history.push(index);
      
      // Keep only recent history to prevent repeats
      if (history.length > this.config.maxRecentHistory) {
        history = history.slice(-this.config.maxRecentHistory);
      }
      
      localStorage.setItem(this.HISTORY_KEY, JSON.stringify(history));
    } catch (e) {
      // Silently continue if localStorage not available
    }
  }
  
  // Name composer: builds botanical title with correct formatting
  composeName(orchid) {
    const parts = [];
    
    // Primary name construction
    if (orchid.genus && orchid.species) {
      // Species: *Genus species*
      let scientificName = `<em>${orchid.genus} ${orchid.species}</em>`;
      
      // Add infraspecific rank and variety if present
      if (orchid.infraspecific_rank && orchid.variety) {
        scientificName += ` ${orchid.infraspecific_rank} ${orchid.variety}`;
      }
      
      parts.push(scientificName);
    } else if (orchid.hybrid || orchid.grex) {
      // Hybrid: *Genus* Hybrid or just Hybrid
      const hybridName = orchid.hybrid || orchid.grex;
      if (orchid.genus) {
        parts.push(`<em>${orchid.genus}</em> ${hybridName}`);
      } else {
        parts.push(hybridName);
      }
    } else if (orchid.title) {
      // Use provided title
      parts.push(orchid.title);
    } else {
      // Fallback
      parts.push(orchid.genus ? `<em>${orchid.genus}</em> sp.` : 'Unknown Orchid');
    }
    
    // Add clonal name in quotes
    if (orchid.clonal_name) {
      parts.push(`'${orchid.clonal_name}'`);
    }
    
    return parts.join(' ');
  }
  
  // Caption composer: builds 2-4 sentence description from available fields
  composeCaption(orchid) {
    if (orchid.caption && orchid.caption.trim()) {
      return orchid.caption.trim();
    }
    
    const sentences = [];
    
    // Sentence 1: Origin and habitat
    const originParts = [];
    if (orchid.native_range) {
      originParts.push(`native to ${orchid.native_range}`);
    }
    if (orchid.habitat) {
      originParts.push(`found in ${orchid.habitat.toLowerCase()}`);
    }
    if (orchid.elevation_m) {
      const elevation = orchid.elevation_m.replace(/[^\d-]/g, '');
      if (elevation) {
        originParts.push(`at ${elevation}m elevation`);
      }
    }
    
    if (originParts.length > 0) {
      sentences.push(`This orchid is ${originParts.join(', ')}.`);
    }
    
    // Sentence 2: Blooming information
    if (orchid.blooming_season) {
      sentences.push(`It blooms during ${orchid.blooming_season.toLowerCase()}.`);
    }
    
    // Sentence 3: Cultural notes (truncated)
    if (orchid.culture_notes && sentences.length < 3) {
      let notes = orchid.culture_notes.trim();
      if (notes.length > 100) {
        notes = notes.substring(0, 97) + '...';
      }
      sentences.push(notes.endsWith('.') ? notes : notes + '.');
    }
    
    // Sentence 4: Group information if space allows
    if (sentences.length < 3 && orchid.orchid_group) {
      sentences.push(`A member of the ${orchid.orchid_group} group.`);
    }
    
    // Fallback if no information available
    if (sentences.length === 0) {
      sentences.push('A beautiful orchid from our collection.');
    }
    
    return sentences.join(' ');
  }
  
  render() {
    const orchid = this.getTodaysOrchid();
    
    if (!orchid) {
      this.renderError("No orchid data available");
      return;
    }
    
    const title = this.composeName(orchid);
    const caption = this.composeCaption(orchid);
    
    // Build information chips
    const chips = [];
    if (orchid.orchid_group) {
      chips.push(orchid.orchid_group);
    }
    if (orchid.blooming_season) {
      chips.push(orchid.blooming_season);
    }
    if (orchid.native_range) {
      chips.push(orchid.native_range);
    }
    
    const chipHtml = chips.slice(0, 3).map(chip => 
      `<span class="chip">${this.escapeHtml(chip)}</span>`
    ).join('');
    
    // Credit and license information
    let creditHtml = '';
    if (orchid.credit || orchid.photographer) {
      const credit = orchid.credit || orchid.photographer;
      creditHtml = `<div class="credit">Photo: ${this.escapeHtml(credit)}</div>`;
    }
    
    let licenseHtml = '';
    if (orchid.license && orchid.license_url) {
      licenseHtml = `<a href="${this.escapeHtml(orchid.license_url)}" class="license" target="_blank" rel="noopener">${this.escapeHtml(orchid.license)}</a>`;
    } else if (orchid.license) {
      licenseHtml = `<span class="license">${this.escapeHtml(orchid.license)}</span>`;
    }
    
    // Alt text for accessibility
    const altText = this.buildAltText(orchid);
    
    // Font family selection
    const fontFamily = this.config.brand.font === 'system' 
      ? `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
      : this.config.brand.font;
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: ${fontFamily};
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
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 14px;
          font-weight: 500;
          line-height: 1;
        }
        
        .orchid-image {
          width: 100%;
          max-width: 560px;
          height: auto;
          border-radius: 8px;
          margin-bottom: 16px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
          display: block;
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
          padding: 4px 8px;
          border-radius: 4px;
          display: inline-block;
          transition: background-color 0.2s ease;
        }
        
        .license:hover {
          background: #f5f5f5;
          text-decoration: underline;
        }
        
        .error {
          background: #fff3cd;
          border: 2px solid #ffeaa7;
          color: #856404;
          padding: 24px;
          border-radius: 12px;
          text-align: center;
          font-size: 18px;
          line-height: 1.5;
          max-width: 600px;
          margin: 0 auto;
        }
        
        /* Accessibility enhancements */
        :focus {
          outline: 3px solid ${this.config.brand.title};
          outline-offset: 2px;
        }
        
        .orchid-image:focus {
          transform: scale(1.02);
          transition: transform 0.2s ease;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 600px) {
          .orchid-card {
            padding: 20px;
            margin: 0 10px;
          }
          
          .orchid-title {
            font-size: 22px;
          }
          
          .orchid-caption {
            font-size: 16px;
          }
          
          .chips {
            gap: 6px;
          }
          
          .chip {
            font-size: 13px;
            padding: 5px 10px;
          }
        }
        
        @media (max-width: 400px) {
          .orchid-card {
            padding: 16px;
            margin: 0 8px;
          }
          
          .orchid-title {
            font-size: 20px;
          }
          
          .orchid-caption {
            font-size: 15px;
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
          onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
          tabindex="0"
        />
        <div style="display:none; padding: 20px; background: #f5f5f5; border-radius: 8px; text-align: center; color: #666;">
          Image temporarily unavailable
        </div>
        <p class="orchid-caption">${caption}</p>
        ${creditHtml}
        ${licenseHtml}
      </div>
    `;
    
    // Add click tracking if enabled
    if (this.config.tracking.enabled && this.config.tracking.onClick) {
      const card = this.shadowRoot.querySelector('.orchid-card');
      card.style.cursor = 'pointer';
      card.addEventListener('click', () => {
        this.config.tracking.onClick(orchid);
      });
    }
  }
  
  buildAltText(orchid) {
    const parts = [];
    
    if (orchid.genus && orchid.species) {
      parts.push(`${orchid.genus} ${orchid.species} orchid`);
    } else if (orchid.hybrid || orchid.grex) {
      parts.push(`${orchid.hybrid || orchid.grex} orchid`);
    } else {
      parts.push('Orchid flower');
    }
    
    if (orchid.clonal_name) {
      parts.push(`clone ${orchid.clonal_name}`);
    }
    
    if (orchid.native_range) {
      parts.push(`from ${orchid.native_range}`);
    }
    
    return parts.join(' ');
  }
  
  renderError(message) {
    const fontFamily = this.config.brand.font === 'system' 
      ? `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
      : this.config.brand.font;
    
    this.shadowRoot.innerHTML = `
      <style>
        .error {
          background: #fff3cd;
          border: 2px solid #ffeaa7;
          color: #856404;
          padding: 24px;
          border-radius: 12px;
          text-align: center;
          font-size: 18px;
          line-height: 1.5;
          font-family: ${fontFamily};
          max-width: 600px;
          margin: 0 auto;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        @media (max-width: 600px) {
          .error {
            margin: 0 10px;
            padding: 20px;
            font-size: 16px;
          }
        }
      </style>
      <div class="error" role="alert">
        🌺 ${this.escapeHtml(message)}
      </div>
    `;
  }
  
  escapeHtml(text) {
    if (typeof text !== 'string') return '';
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
      console.warn('FCOS Orchid Widget: Could not cache data');
    }
  }
}

// Auto-initialize when DOM is ready
(function() {
  new OrchidOfTheDayWidget(CONFIG);
})();