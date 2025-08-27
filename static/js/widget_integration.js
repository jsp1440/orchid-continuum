/**
 * Widget Integration System - Cross-widget communication and enhanced user experience
 * Five Cities Orchid Society Platform
 */

class WidgetIntegrationSystem {
    constructor() {
        this.widgets = new Map();
        this.currentSession = null;
        this.favorites = new Set();
        this.recommendations = [];
        this.isMobile = this.detectMobile();
        
        this.init();
    }
    
    init() {
        this.loadUserSession();
        this.setupEventListeners();
        this.initializeWidgets();
        this.loadFavorites();
        
        // Auto-save session periodically
        setInterval(() => this.saveSession(), 30000); // Every 30 seconds
    }
    
    detectMobile() {
        return window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    async loadUserSession() {
        try {
            const response = await fetch('/api/widget-session');
            this.currentSession = await response.json();
        } catch (error) {
            console.warn('Failed to load user session:', error);
            this.currentSession = this.createDefaultSession();
        }
    }
    
    createDefaultSession() {
        return {
            session_id: `user_${Date.now()}`,
            created_at: new Date().toISOString(),
            widget_history: [],
            current_context: {},
            preferences: {
                preferred_view: 'gallery',
                favorite_genus: null,
                last_search: null,
                map_region: 'global',
                weather_location: null
            }
        };
    }
    
    async loadFavorites() {
        try {
            const response = await fetch('/api/favorites');
            const data = await response.json();
            this.favorites = new Set(data.favorites.map(f => f.id));
            this.updateFavoriteButtons();
        } catch (error) {
            console.warn('Failed to load favorites:', error);
        }
    }
    
    updateFavoriteButtons() {
        document.querySelectorAll('[data-orchid-id]').forEach(btn => {
            const orchidId = parseInt(btn.dataset.orchidId);
            if (this.favorites.has(orchidId)) {
                btn.classList.add('favorited');
                btn.innerHTML = '<i data-feather="heart" class="text-danger"></i>';
            }
        });
        feather.replace();
    }
    
    setupEventListeners() {
        // Global favorite button handling
        document.addEventListener('click', (e) => {
            if (e.target.closest('.favorite-btn')) {
                this.handleFavoriteClick(e.target.closest('.favorite-btn'));
            }
            
            if (e.target.closest('.add-to-collection-btn')) {
                this.handleAddToCollection(e.target.closest('.add-to-collection-btn'));
            }
        });
        
        // Search enhancement
        document.addEventListener('input', (e) => {
            if (e.target.matches('.widget-search-input')) {
                this.handleEnhancedSearch(e.target);
            }
        });
        
        // Widget view tracking
        document.addEventListener('scroll', this.throttle(() => {
            this.trackVisibleWidgets();
        }, 1000));
        
        // Mobile-specific event handling
        if (this.isMobile) {
            this.setupMobileGestures();
        }
    }
    
    async handleFavoriteClick(btn) {
        const orchidId = parseInt(btn.dataset.orchidId);
        const orchidData = this.extractOrchidData(btn);
        
        try {
            if (this.favorites.has(orchidId)) {
                // Remove from favorites
                await fetch(`/api/favorites?orchid_id=${orchidId}`, { method: 'DELETE' });
                this.favorites.delete(orchidId);
                btn.classList.remove('favorited');
                btn.innerHTML = '<i data-feather="heart"></i>';
                this.showToast('Removed from favorites', 'info');
            } else {
                // Add to favorites
                await fetch('/api/favorites', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ orchid_id: orchidId, orchid_data: orchidData })
                });
                this.favorites.add(orchidId);
                btn.classList.add('favorited');
                btn.innerHTML = '<i data-feather="heart" class="text-danger"></i>';
                this.showToast('Added to favorites', 'success');
            }
            feather.replace();
        } catch (error) {
            this.showToast('Error updating favorites', 'error');
        }
    }
    
    async handleAddToCollection(btn) {
        const orchidId = parseInt(btn.dataset.orchidId);
        const collectionType = btn.dataset.collectionType || 'wishlist';
        
        try {
            const response = await fetch('/api/collection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'add_orchid',
                    orchid_id: orchidId,
                    collection_type: collectionType
                })
            });
            
            const result = await response.json();
            if (result.success) {
                btn.innerHTML = '<i data-feather="check"></i> Added';
                btn.disabled = true;
                this.showToast(`Added to ${collectionType}`, 'success');
                
                // Update recommendations
                this.loadRecommendations();
            } else {
                this.showToast(result.error || 'Error adding to collection', 'error');
            }
            feather.replace();
        } catch (error) {
            this.showToast('Network error occurred', 'error');
        }
    }
    
    async handleEnhancedSearch(input) {
        const query = input.value.trim();
        if (query.length < 2) return;
        
        try {
            // Track search interaction
            await this.trackInteraction('search', 'search', { query: query });
            
            // Perform cross-widget search
            const response = await fetch(`/api/cross-widget-search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            // Update search results
            this.updateSearchResults(data.results);
            
            // Update other widgets based on search
            this.propagateSearchToWidgets(query, data);
            
            // Show recommendations
            this.displaySearchRecommendations(data.recommendations);
            
        } catch (error) {
            console.error('Enhanced search error:', error);
        }
    }
    
    updateSearchResults(results) {
        const container = document.querySelector('.search-results-container');
        if (!container) return;
        
        container.innerHTML = results.map(orchid => `
            <div class="search-result-item" data-orchid-id="${orchid.id}">
                <img src="${orchid.image_url || '/static/images/placeholder.png'}" 
                     alt="${orchid.display_name}" class="result-image">
                <div class="result-info">
                    <h6>${orchid.display_name}</h6>
                    <p class="text-muted small">${orchid.scientific_name || ''}</p>
                    <span class="badge bg-secondary">${orchid.genus || 'Unknown'}</span>
                </div>
                <div class="result-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/orchid/${orchid.id}'">
                        View
                    </button>
                    <button class="favorite-btn btn btn-sm btn-outline-danger" data-orchid-id="${orchid.id}">
                        <i data-feather="heart"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        feather.replace();
        this.updateFavoriteButtons();
    }
    
    propagateSearchToWidgets(query, searchData) {
        // Update map widget if present
        const mapWidget = document.querySelector('.map-widget-container');
        if (mapWidget && searchData.map_update_url) {
            this.updateWidget('map', searchData.map_update_url);
        }
        
        // Update weather widget if present
        const weatherWidget = document.querySelector('.weather-widget-container');
        if (weatherWidget && searchData.weather_update_url) {
            this.updateWidget('weather', searchData.weather_update_url);
        }
        
        // Update gallery filter
        const galleryWidget = document.querySelector('.gallery-widget-container');
        if (galleryWidget) {
            this.filterGalleryByGenus(query.split(' ')[0]);
        }
    }
    
    async updateWidget(widgetType, updateUrl) {
        try {
            const response = await fetch(updateUrl);
            const data = await response.json();
            
            const widgetContainer = document.querySelector(`.${widgetType}-widget-container`);
            if (widgetContainer) {
                // Trigger widget update event
                const event = new CustomEvent('widgetUpdate', {
                    detail: { type: widgetType, data: data }
                });
                widgetContainer.dispatchEvent(event);
            }
        } catch (error) {
            console.error(`Failed to update ${widgetType} widget:`, error);
        }
    }
    
    displaySearchRecommendations(recommendations) {
        const container = document.querySelector('.widget-recommendations');
        if (!container || !recommendations.next_widgets) return;
        
        container.innerHTML = `
            <div class="recommendations-header">
                <h6><i data-feather="arrow-right"></i> Explore Next</h6>
            </div>
            ${recommendations.next_widgets.map(widget => `
                <div class="recommendation-item">
                    <strong>${widget.widget}</strong>: ${widget.reason}
                    <a href="${widget.action_url}" class="btn btn-sm btn-primary ms-2">Go</a>
                </div>
            `).join('')}
        `;
        feather.replace();
    }
    
    async trackInteraction(widgetName, action, context = {}) {
        try {
            await fetch('/api/widget-interaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    widget_name: widgetName,
                    action: action,
                    context: context
                })
            });
        } catch (error) {
            console.warn('Failed to track interaction:', error);
        }
    }
    
    async loadRecommendations(widgetType = 'dashboard') {
        try {
            const response = await fetch(`/api/widget-recommendations/${widgetType}`);
            this.recommendations = await response.json();
            this.displayRecommendations();
        } catch (error) {
            console.warn('Failed to load recommendations:', error);
        }
    }
    
    displayRecommendations() {
        const container = document.querySelector('.global-recommendations');
        if (!container || !this.recommendations.next_widgets) return;
        
        container.innerHTML = this.recommendations.next_widgets.map(rec => `
            <div class="recommendation-card">
                <div class="rec-icon">🎯</div>
                <div class="rec-content">
                    <strong>${rec.widget.charAt(0).toUpperCase() + rec.widget.slice(1)}</strong>
                    <p>${rec.reason}</p>
                    <a href="${rec.action_url}" class="btn btn-sm btn-outline-primary">Explore</a>
                </div>
            </div>
        `).join('');
    }
    
    setupMobileGestures() {
        let touchStartX = 0;
        let touchStartY = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            
            // Horizontal swipe gestures
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                const target = e.target.closest('.swipe-container');
                if (target) {
                    if (deltaX > 0) {
                        this.handleSwipe(target, 'right');
                    } else {
                        this.handleSwipe(target, 'left');
                    }
                }
            }
        });
    }
    
    handleSwipe(container, direction) {
        const event = new CustomEvent('swipeGesture', {
            detail: { direction: direction, container: container }
        });
        container.dispatchEvent(event);
    }
    
    trackVisibleWidgets() {
        const widgets = document.querySelectorAll('[data-widget-type]');
        const visibleWidgets = [];
        
        widgets.forEach(widget => {
            const rect = widget.getBoundingClientRect();
            const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
            
            if (isVisible) {
                const widgetType = widget.dataset.widgetType;
                visibleWidgets.push(widgetType);
                
                // Track widget view if not already tracked
                if (!widget.dataset.viewTracked) {
                    this.trackInteraction(widgetType, 'view');
                    widget.dataset.viewTracked = 'true';
                }
            }
        });
        
        // Update user preferences based on visible widgets
        if (visibleWidgets.length > 0) {
            this.currentSession.preferences.preferred_view = visibleWidgets[0];
        }
    }
    
    extractOrchidData(element) {
        const card = element.closest('[data-orchid-id]');
        if (!card) return {};
        
        return {
            display_name: card.querySelector('.orchid-name, .display-name')?.textContent || '',
            scientific_name: card.querySelector('.scientific-name')?.textContent || '',
            genus: card.querySelector('.genus')?.textContent || '',
            image_url: card.querySelector('img')?.src || ''
        };
    }
    
    filterGalleryByGenus(genus) {
        const galleryItems = document.querySelectorAll('.gallery-item');
        
        galleryItems.forEach(item => {
            const itemGenus = item.dataset.genus || item.querySelector('.genus')?.textContent || '';
            
            if (!genus || itemGenus.toLowerCase().includes(genus.toLowerCase())) {
                item.style.display = 'block';
                item.classList.remove('filtered-out');
            } else {
                item.style.display = 'none';
                item.classList.add('filtered-out');
            }
        });
        
        // Update gallery counter
        const visibleCount = document.querySelectorAll('.gallery-item:not(.filtered-out)').length;
        const counter = document.querySelector('.gallery-counter');
        if (counter) {
            counter.textContent = `Showing ${visibleCount} orchids`;
        }
    }
    
    initializeWidgets() {
        // Initialize each widget type found on the page
        const widgetTypes = ['gallery', 'search', 'map', 'weather', 'comparison'];
        
        widgetTypes.forEach(type => {
            const widgets = document.querySelectorAll(`.${type}-widget-container`);
            widgets.forEach(widget => {
                this.registerWidget(type, widget);
                this.loadMobileConfig(type, widget);
            });
        });
    }
    
    registerWidget(type, element) {
        const widgetId = element.id || `${type}-${Date.now()}`;
        
        this.widgets.set(widgetId, {
            type: type,
            element: element,
            config: {},
            lastInteraction: Date.now()
        });
        
        // Set data attribute for tracking
        element.dataset.widgetType = type;
        element.dataset.widgetId = widgetId;
    }
    
    async loadMobileConfig(type, element) {
        if (!this.isMobile) return;
        
        try {
            const response = await fetch(`/api/mobile-config/${type}`);
            const config = await response.json();
            
            // Apply mobile configuration
            if (config.touch_optimized) {
                element.classList.add('touch-optimized');
                element.classList.add(`device-${config.device_type}`);
            }
            
            // Store config for widget
            const widgetId = element.dataset.widgetId;
            if (this.widgets.has(widgetId)) {
                this.widgets.get(widgetId).config = config;
            }
            
        } catch (error) {
            console.warn(`Failed to load mobile config for ${type}:`, error);
        }
    }
    
    showToast(message, type = 'info') {
        // Create toast if toast container doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : (type === 'success' ? 'success' : 'primary')} border-0`;
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
    
    saveSession() {
        // Save session to localStorage as backup
        try {
            localStorage.setItem('orchid_widget_session', JSON.stringify(this.currentSession));
        } catch (error) {
            console.warn('Failed to save session to localStorage:', error);
        }
    }
    
    // Public API methods for other scripts to use
    
    addFavorite(orchidId, orchidData = {}) {
        const btn = document.querySelector(`[data-orchid-id="${orchidId}"].favorite-btn`);
        if (btn) {
            this.handleFavoriteClick(btn);
        }
    }
    
    searchOrchids(query) {
        const searchInput = document.querySelector('.widget-search-input');
        if (searchInput) {
            searchInput.value = query;
            this.handleEnhancedSearch(searchInput);
        }
    }
    
    navigateToWidget(widgetType, params = {}) {
        const widget = document.querySelector(`.${widgetType}-widget-container`);
        if (widget) {
            widget.scrollIntoView({ behavior: 'smooth' });
            this.trackInteraction(widgetType, 'navigation', params);
        }
    }
    
    getWidgetRecommendations(widgetType) {
        return fetch(`/api/widget-recommendations/${widgetType}`)
            .then(response => response.json());
    }
}

// Initialize the widget integration system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.OrchidWidgets = new WidgetIntegrationSystem();
    
    // Make it globally accessible for other scripts
    window.addToFavorites = (orchidId, data) => window.OrchidWidgets.addFavorite(orchidId, data);
    window.searchOrchids = (query) => window.OrchidWidgets.searchOrchids(query);
    window.navigateToWidget = (type, params) => window.OrchidWidgets.navigateToWidget(type, params);
    
    console.log('🌺 Widget Integration System initialized');
});

// Expose key functions globally for backward compatibility
window.trackWidgetInteraction = function(widgetName, action, context = {}) {
    if (window.OrchidWidgets) {
        window.OrchidWidgets.trackInteraction(widgetName, action, context);
    }
};

window.showOrchidToast = function(message, type = 'info') {
    if (window.OrchidWidgets) {
        window.OrchidWidgets.showToast(message, type);
    }
};