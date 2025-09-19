// Gallery Widget JavaScript
class OrchidGallery {
    constructor() {
        this.galleryData = null;
        this.container = document.getElementById('gallery-content');
        this.init();
    }

    async init() {
        try {
            await this.loadGalleryData();
            this.renderGallery();
        } catch (error) {
            this.showError('Failed to load gallery data: ' + error.message);
        }
    }

    async loadGalleryData() {
        // Use absolute path for fetch to work from any directory
        const response = await fetch('/assets/data/gallery.json');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        this.galleryData = await response.json();
    }

    renderGallery() {
        if (!this.galleryData || !this.galleryData.images) {
            this.showError('No gallery data available');
            return;
        }

        const galleryHTML = `
            <div class="gallery-grid">
                ${this.galleryData.images.map(image => this.renderGalleryItem(image)).join('')}
            </div>
        `;

        this.container.innerHTML = galleryHTML;
    }

    renderGalleryItem(image) {
        return `
            <div class="gallery-item">
                <img 
                    src="${image.src}" 
                    alt="${image.title}"
                    class="gallery-image"
                    onerror="this.src='/images/orchid_placeholder.svg'"
                >
                <div class="gallery-content">
                    <div class="gallery-title">${image.title}</div>
                    <div class="gallery-description">${image.description}</div>
                    <span class="gallery-category">${image.category}</span>
                </div>
            </div>
        `;
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="error">
                <h3>Error Loading Gallery</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize gallery when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new OrchidGallery();
});