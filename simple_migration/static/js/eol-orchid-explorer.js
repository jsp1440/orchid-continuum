/**
 * EOL Orchid Explorer Widget
 * Integrates Encyclopedia of Life data with the Orchid Continuum database
 * Displays orchid images, taxonomic information, and conservation data
 */

class EOLOrchidExplorer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`EOL Orchid Explorer: Container '${containerId}' not found`);
            return;
        }
        
        this.options = {
            mode: 'explore', // 'explore', 'species', 'conservation'
            orchidId: null,
            showImages: true,
            showTaxonomy: true,
            showConservation: true,
            autoRefresh: 300000, // 5 minutes
            maxImages: 6,
            ...options
        };
        
        this.currentData = null;
        this.currentIndex = 0;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.container.className = 'eol-orchid-explorer';
        this.render();
        this.loadData();
        
        // Auto-refresh if enabled
        if (this.options.autoRefresh > 0) {
            setInterval(() => this.loadData(), this.options.autoRefresh);
        }
    }
    
    render() {
        this.container.innerHTML = `
            <div class="eol-widget-header">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="text-light mb-0">
                        <i class="feather-icon" data-feather="globe"></i>
                        EOL Orchid Explorer
                    </h5>
                    <div class="eol-controls">
                        <button class="btn btn-sm btn-outline-light eol-refresh-btn" title="Refresh Data">
                            <i class="feather-icon" data-feather="refresh-cw"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-light eol-mode-btn" title="Switch Mode">
                            <i class="feather-icon" data-feather="shuffle"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="eol-content">
                <div class="eol-loading text-center py-4" style="display: none;">
                    <div class="spinner-border text-success" role="status">
                        <span class="visually-hidden">Loading EOL data...</span>
                    </div>
                    <p class="text-muted mt-2">Fetching Encyclopedia of Life data...</p>
                </div>
                
                <div class="eol-error text-center py-4" style="display: none;">
                    <i class="feather-icon text-warning" data-feather="alert-triangle"></i>
                    <p class="text-muted mt-2">Failed to load EOL data</p>
                    <button class="btn btn-sm btn-outline-warning eol-retry-btn">Try Again</button>
                </div>
                
                <div class="eol-data" style="display: none;">
                    <!-- Dynamic content will be inserted here -->
                </div>
            </div>
            
            <div class="eol-footer">
                <small class="text-muted">
                    <i class="feather-icon" data-feather="external-link"></i>
                    Powered by <a href="https://eol.org" target="_blank" class="text-success">Encyclopedia of Life</a>
                </small>
            </div>
        `;
        
        this.setupEventHandlers();
        
        // Initialize Feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    setupEventHandlers() {
        const refreshBtn = this.container.querySelector('.eol-refresh-btn');
        const modeBtn = this.container.querySelector('.eol-mode-btn');
        const retryBtn = this.container.querySelector('.eol-retry-btn');
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadData(true));
        }
        
        if (modeBtn) {
            modeBtn.addEventListener('click', () => this.switchMode());
        }
        
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.loadData(true));
        }
    }
    
    async loadData(force = false) {
        if (this.isLoading && !force) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            let url = '/api/eol-orchid-explorer';
            if (this.options.orchidId) {
                url += `/${this.options.orchidId}`;
            }
            
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.status === 'success') {
                this.currentData = result.data;
                this.renderData();
                this.hideLoading();
            } else {
                throw new Error(result.error || 'Failed to load EOL data');
            }
        } catch (error) {
            console.error('EOL Orchid Explorer Error:', error);
            this.showError();
        } finally {
            this.isLoading = false;
        }
    }
    
    renderData() {
        if (!this.currentData) return;
        
        const dataContainer = this.container.querySelector('.eol-data');
        
        if (this.options.orchidId && this.currentData.orchid) {
            // Single orchid mode
            dataContainer.innerHTML = this.renderSingleOrchid(this.currentData);
        } else if (this.currentData.featured_orchids) {
            // Exploration mode
            dataContainer.innerHTML = this.renderExploreMode(this.currentData);
        }
        
        // Re-initialize Feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        // Setup image galleries
        this.setupImageGallery();
    }
    
    renderSingleOrchid(data) {
        const { orchid, eol_data, related_species } = data;
        
        let html = `
            <div class="eol-orchid-details">
                <div class="row">
                    <div class="col-md-6">
                        <div class="eol-orchid-image">
                            ${orchid.image_filename ? 
                                `<img src="/static/orchid_photos/${orchid.image_filename}" 
                                     class="img-fluid rounded eol-main-image" 
                                     alt="${orchid.display_name}">` :
                                `<div class="eol-no-image text-center p-4">
                                     <i class="feather-icon text-muted" data-feather="image"></i>
                                     <p class="text-muted mt-2">No image available</p>
                                 </div>`
                            }
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-light">${orchid.display_name}</h6>
                        <p class="text-muted"><em>${orchid.scientific_name}</em></p>
                        
                        ${orchid.ai_description ? 
                            `<div class="eol-description">
                                 <small class="text-light">${orchid.ai_description.substring(0, 200)}...</small>
                             </div>` : ''
                        }
        `;
        
        // Add EOL data if available
        if (eol_data) {
            html += this.renderEOLData(eol_data);
        }
        
        html += `
                    </div>
                </div>
            </div>
        `;
        
        // Add related species
        if (related_species && related_species.length > 0) {
            html += `
                <div class="eol-related-species mt-4">
                    <h6 class="text-light mb-3">Related Species</h6>
                    <div class="row">
                        ${related_species.map(species => `
                            <div class="col-md-4 mb-3">
                                <div class="card bg-dark border-secondary eol-species-card" 
                                     data-orchid-id="${species.id}">
                                    ${species.image_filename ?
                                        `<img src="/static/orchid_photos/${species.image_filename}" 
                                             class="card-img-top eol-related-image" 
                                             alt="${species.display_name}">` :
                                        `<div class="card-img-top eol-no-image-small">
                                             <i class="feather-icon text-muted" data-feather="image"></i>
                                         </div>`
                                    }
                                    <div class="card-body p-2">
                                        <small class="text-light">${species.display_name}</small>
                                        <br>
                                        <small class="text-muted"><em>${species.scientific_name}</em></small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        return html;
    }
    
    renderExploreMode(data) {
        const { featured_orchids, total_database_size } = data;
        
        if (!featured_orchids || featured_orchids.length === 0) {
            return '<p class="text-muted text-center py-4">No orchids available for exploration</p>';
        }
        
        return `
            <div class="eol-explore-header mb-3">
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                        Exploring ${featured_orchids.length} of ${total_database_size} orchids
                    </small>
                    <div class="eol-status-indicators">
                        ${featured_orchids.filter(o => o.eol_summary.has_eol_data).length > 0 ?
                            `<span class="badge bg-success">
                                 <i class="feather-icon" data-feather="globe"></i>
                                 ${featured_orchids.filter(o => o.eol_summary.has_eol_data).length} EOL Enhanced
                             </span>` : ''
                        }
                    </div>
                </div>
            </div>
            
            <div class="eol-orchid-grid">
                <div class="row">
                    ${featured_orchids.map(orchid => `
                        <div class="col-md-4 col-lg-3 mb-3">
                            <div class="card bg-dark border-secondary eol-orchid-card h-100" 
                                 data-orchid-id="${orchid.id}">
                                <div class="position-relative">
                                    ${orchid.image_filename ?
                                        `<img src="/static/orchid_photos/${orchid.image_filename}" 
                                             class="card-img-top eol-grid-image" 
                                             alt="${orchid.display_name}">` :
                                        `<div class="card-img-top eol-no-image-grid">
                                             <i class="feather-icon text-muted" data-feather="image"></i>
                                         </div>`
                                    }
                                    
                                    ${orchid.eol_summary.has_eol_data ?
                                        `<div class="eol-badge">
                                             <i class="feather-icon" data-feather="globe"></i>
                                         </div>` : ''
                                    }
                                    
                                    ${orchid.eol_summary.conservation_status ?
                                        `<div class="eol-conservation-badge ${this.getConservationClass(orchid.eol_summary.conservation_status)}">
                                             <i class="feather-icon" data-feather="shield"></i>
                                         </div>` : ''
                                    }
                                </div>
                                
                                <div class="card-body p-2">
                                    <h6 class="card-title text-light small mb-1">${orchid.display_name}</h6>
                                    <p class="card-text">
                                        <small class="text-muted"><em>${orchid.scientific_name}</em></small>
                                        <br>
                                        ${orchid.eol_summary.eol_images_count > 0 ?
                                            `<small class="text-success">
                                                 <i class="feather-icon" data-feather="images"></i>
                                                 ${orchid.eol_summary.eol_images_count} EOL images
                                             </small>` :
                                            `<small class="text-muted">Local collection</small>`
                                        }
                                    </p>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    renderEOLData(eol_data) {
        if (!eol_data) return '';
        
        let html = '<div class="eol-external-data mt-3">';
        html += '<h6 class="text-success"><i class="feather-icon" data-feather="globe"></i> Encyclopedia of Life</h6>';
        
        // Add EOL images if available
        if (eol_data.images && eol_data.images.length > 0) {
            html += `
                <div class="eol-image-gallery mb-3">
                    <div class="row">
                        ${eol_data.images.slice(0, this.options.maxImages).map(img => `
                            <div class="col-4 col-md-3 mb-2">
                                <img src="${img.medium_url || img.original_url}" 
                                     class="img-fluid rounded eol-gallery-image" 
                                     data-bs-toggle="modal" 
                                     data-bs-target="#eolImageModal"
                                     data-image-url="${img.original_url}"
                                     data-image-license="${img.license}"
                                     data-image-owner="${img.owner}"
                                     alt="EOL Image">
                            </div>
                        `).join('')}
                    </div>
                    <small class="text-muted">Images from Encyclopedia of Life</small>
                </div>
            `;
        }
        
        // Add conservation status
        if (eol_data.conservation_status) {
            html += `
                <div class="eol-conservation mb-2">
                    <span class="badge ${this.getConservationClass(eol_data.conservation_status)}">
                        <i class="feather-icon" data-feather="shield"></i>
                        ${eol_data.conservation_status}
                    </span>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    getConservationClass(status) {
        if (!status) return 'bg-secondary';
        
        const statusLower = status.toLowerCase();
        if (statusLower.includes('endangered') || statusLower.includes('critically')) return 'bg-danger';
        if (statusLower.includes('vulnerable') || statusLower.includes('threatened')) return 'bg-warning';
        if (statusLower.includes('concern')) return 'bg-info';
        return 'bg-success';
    }
    
    setupImageGallery() {
        // Setup click handlers for EOL orchid cards
        const orchidCards = this.container.querySelectorAll('.eol-orchid-card, .eol-species-card');
        orchidCards.forEach(card => {
            card.addEventListener('click', (e) => {
                const orchidId = card.dataset.orchidId;
                if (orchidId) {
                    this.viewOrchid(orchidId);
                }
            });
        });
        
        // Setup image modal if bootstrap is available
        if (typeof bootstrap !== 'undefined') {
            this.setupImageModal();
        }
    }
    
    setupImageModal() {
        // Create modal if it doesn't exist
        if (!document.getElementById('eolImageModal')) {
            const modal = document.createElement('div');
            modal.innerHTML = `
                <div class="modal fade" id="eolImageModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content bg-dark">
                            <div class="modal-header">
                                <h5 class="modal-title text-light">EOL Image</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body text-center">
                                <img id="eolModalImage" class="img-fluid" alt="EOL Image">
                                <div id="eolModalAttribution" class="mt-3"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        // Setup image click handlers
        const galleryImages = this.container.querySelectorAll('.eol-gallery-image');
        galleryImages.forEach(img => {
            img.addEventListener('click', (e) => {
                const imageUrl = img.dataset.imageUrl;
                const license = img.dataset.imageLicense;
                const owner = img.dataset.imageOwner;
                
                const modalImage = document.getElementById('eolModalImage');
                const modalAttribution = document.getElementById('eolModalAttribution');
                
                modalImage.src = imageUrl;
                modalAttribution.innerHTML = `
                    <small class="text-muted">
                        License: ${license || 'Unknown'}<br>
                        © ${owner || 'Encyclopedia of Life'}
                    </small>
                `;
            });
        });
    }
    
    viewOrchid(orchidId) {
        // Create new widget instance for specific orchid
        const detailContainer = document.createElement('div');
        detailContainer.id = 'eol-detail-' + orchidId;
        
        // Insert into page or modal
        this.container.appendChild(detailContainer);
        
        new EOLOrchidExplorer(detailContainer.id, {
            orchidId: parseInt(orchidId),
            mode: 'species'
        });
    }
    
    switchMode() {
        const modes = ['explore', 'conservation'];
        const currentIndex = modes.indexOf(this.options.mode);
        this.options.mode = modes[(currentIndex + 1) % modes.length];
        
        this.loadData(true);
    }
    
    showLoading() {
        this.container.querySelector('.eol-loading').style.display = 'block';
        this.container.querySelector('.eol-data').style.display = 'none';
        this.container.querySelector('.eol-error').style.display = 'none';
    }
    
    hideLoading() {
        this.container.querySelector('.eol-loading').style.display = 'none';
        this.container.querySelector('.eol-data').style.display = 'block';
        this.container.querySelector('.eol-error').style.display = 'none';
    }
    
    showError() {
        this.container.querySelector('.eol-loading').style.display = 'none';
        this.container.querySelector('.eol-data').style.display = 'none';
        this.container.querySelector('.eol-error').style.display = 'block';
    }
}

// Make available globally
window.EOLOrchidExplorer = EOLOrchidExplorer;

// Auto-initialize if data attributes present
document.addEventListener('DOMContentLoaded', function() {
    const eolWidgets = document.querySelectorAll('[data-eol-orchid-explorer]');
    eolWidgets.forEach(widget => {
        const options = {};
        
        // Parse data attributes
        if (widget.dataset.orchidId) options.orchidId = parseInt(widget.dataset.orchidId);
        if (widget.dataset.mode) options.mode = widget.dataset.mode;
        if (widget.dataset.showImages !== undefined) options.showImages = widget.dataset.showImages === 'true';
        if (widget.dataset.autoRefresh) options.autoRefresh = parseInt(widget.dataset.autoRefresh);
        
        new EOLOrchidExplorer(widget.id, options);
    });
});