// Enhanced search functionality for Orchid Continuum
// Extracted from search.html template for optimization

// Enhanced search functionality
function clearAllFilters() {
    const form = document.getElementById('searchForm');
    const inputs = form.querySelectorAll('input[type="text"], select');
    inputs.forEach(input => {
        if (input.name !== 'sort_by' && input.name !== 'results_per_page') {
            input.value = '';
        }
    });
    
    // Reset sort and results to defaults
    document.getElementById('sort_by').value = 'relevance';
    document.getElementById('results_per_page').value = '50';
}

function exportResults() {
    // Get current search parameters
    const form = document.getElementById('searchForm');
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    // Add export parameter and redirect
    params.append('export', 'csv');
    window.open('/search?' + params.toString(), '_blank');
}

// Enhanced Mapping Integration Functions
let searchMap = null;
let currentMapMarkers = [];

// Toggle between regional and coordinate map views
function toggleMapView(viewType) {
    const regionalView = document.getElementById('regional-view');
    const coordinatesView = document.getElementById('coordinates-view');
    const regionalBtn = document.getElementById('regional-btn');
    const coordinatesBtn = document.getElementById('coordinates-btn');
    
    // Reset button states
    regionalBtn.classList.remove('active');
    coordinatesBtn.classList.remove('active');
    
    if (viewType === 'regional') {
        regionalView.style.display = 'block';
        coordinatesView.style.display = 'none';
        regionalBtn.classList.add('active');
    } else if (viewType === 'coordinates') {
        regionalView.style.display = 'none';
        coordinatesView.style.display = 'block';
        coordinatesBtn.classList.add('active');
        
        // Initialize coordinate map if not already done
        initializeCoordinateMap();
    }
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// Initialize interactive coordinate map
function initializeCoordinateMap() {
    if (searchMap || !window.L) {
        return; // Map already exists or Leaflet not loaded
    }
    
    const mapContainer = document.getElementById('search-map');
    if (!mapContainer) return;
    
    // Initialize map
    searchMap = L.map('search-map').setView([20, 0], 2);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(searchMap);
    
    // Load orchid coordinates via API if needed
    loadOrchidCoordinates();
}

// Load orchid coordinates dynamically
function loadOrchidCoordinates() {
    fetch('/api/orchid-coordinates-all')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Failed to load coordinates');
        })
        .then(coordinates => {
            coordinates.forEach(coord => {
                const marker = L.marker([coord.lat, coord.lng])
                    .addTo(searchMap)
                    .bindPopup(`
                        <div class="p-2">
                            <h6 class="mb-1">${coord.name}</h6>
                            <div class="small text-muted">
                                <div><strong>Genus:</strong> ${coord.genus}</div>
                                <div><strong>Location:</strong> ${coord.location}</div>
                                <div><strong>Region:</strong> ${coord.region}</div>
                            </div>
                            <a href="/orchid/${coord.id}" class="btn btn-sm btn-primary mt-2">View Details</a>
                        </div>
                    `);
                
                currentMapMarkers.push(marker);
            });
            
            // Fit map to show all markers
            if (currentMapMarkers.length > 0) {
                const group = new L.featureGroup(currentMapMarkers);
                searchMap.fitBounds(group.getBounds().pad(0.1));
            }
        })
        .catch(error => {
            console.warn('Could not load orchid coordinates:', error);
        });
}

// Focus map on specific orchid coordinates
function focusOnOrchid(lat, lng) {
    if (searchMap) {
        searchMap.setView([lat, lng], 8);
        
        // Find and open popup for this coordinate
        currentMapMarkers.forEach(marker => {
            const pos = marker.getLatLng();
            if (Math.abs(pos.lat - lat) < 0.001 && Math.abs(pos.lng - lng) < 0.001) {
                marker.openPopup();
            }
        });
    }
}

// Show all coordinates in expanded view
function showAllCoordinates() {
    toggleMapView('coordinates');
    if (searchMap && currentMapMarkers.length > 0) {
        const group = new L.featureGroup(currentMapMarkers);
        searchMap.fitBounds(group.getBounds().pad(0.1));
    }
}

// Filter search results by region
function filterByRegion(region) {
    const form = document.getElementById('searchForm');
    const regionInput = form.querySelector('input[name="region"]');
    
    if (regionInput) {
        regionInput.value = region;
    } else {
        // Create hidden input for region filter
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'region';
        hiddenInput.value = region;
        form.appendChild(hiddenInput);
    }
    
    form.submit();
}

// Open 3D Globe view with current search filters
function openGlobeView() {
    const form = document.getElementById('searchForm');
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    // Build URL with search parameters for 3D globe
    let globeUrl = '/space-earth-globe';
    
    // Add genus filter if specified
    const genus = params.get('genus');
    if (genus && genus !== '') {
        globeUrl += '?genus=' + encodeURIComponent(genus);
    }
    
    // Open 3D globe in new window/tab
    window.open(globeUrl, '_blank', 'width=1200,height=800');
}

// Enhanced image gallery viewing
function openImageGallery(orchidId, imageSrc, orchidName) {
    // Create modal for full-size image viewing
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'imageGalleryModal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${orchidName}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${imageSrc}" class="img-fluid" alt="${orchidName}" style="max-height: 70vh;">
                </div>
                <div class="modal-footer">
                    <a href="/orchid/${orchidId}" class="btn btn-primary">View Full Details</a>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    if (typeof bootstrap !== 'undefined') {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Clean up modal after hiding
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });
    }
}

// Quick filter functions
function quickFilter(field, value) {
    const form = document.getElementById('searchForm');
    const input = form.querySelector(`input[name="${field}"]`) || form.querySelector(`select[name="${field}"]`);
    
    if (input) {
        input.value = value;
        form.submit();
    }
}

// Export search results
function exportSearchResults() {
    exportResults();
}

// Toggle nursery directory
function toggleNurseryDirectory() {
    window.open('/nursery-directory', '_blank');
}

// Toggle society directory  
function toggleSocietyDirectory() {
    window.open('/society-directory', '_blank');
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Search enhancement system initialized');
    
    // Initialize feather icons if available
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});