// Orchid Continuum Main JavaScript
// Enhanced interactivity and user experience features

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeFeatherIcons();
    initializeTooltips();
    initializeImageLazyLoading();
    initializeSearchEnhancements();
    initializeUploadFeatures();
    initializeGalleryFeatures();
    initializeNotifications();
    
    console.log('Orchid Continuum initialized successfully');
});

// Initialize Feather icons
function initializeFeatherIcons() {
    if (typeof feather !== 'undefined') {
        feather.replace();
        
        // Re-initialize icons for dynamically added content
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length > 0) {
                    feather.replace();
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Lazy loading for images
function initializeImageLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        img.classList.add('orchid-bloom-animation');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(function(img) {
            imageObserver.observe(img);
        });
    }
}

// Enhanced search functionality
function initializeSearchEnhancements() {
    const searchForm = document.querySelector('form[action*="search"]');
    const searchInput = document.querySelector('input[name="q"]');
    
    if (searchInput) {
        // Add search suggestions
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                // Here you could implement live search suggestions
                // For now, we'll just add some visual feedback
                if (searchInput.value.length > 2) {
                    searchInput.classList.add('is-valid');
                } else {
                    searchInput.classList.remove('is-valid');
                }
            }, 300);
        });
        
        // Add search history
        if (localStorage) {
            const searchHistory = JSON.parse(localStorage.getItem('orchidSearchHistory') || '[]');
            
            searchInput.addEventListener('focus', function() {
                if (searchHistory.length > 0) {
                    showSearchSuggestions(searchHistory.slice(0, 5));
                }
            });
            
            if (searchForm) {
                searchForm.addEventListener('submit', function() {
                    const query = searchInput.value.trim();
                    if (query && !searchHistory.includes(query)) {
                        searchHistory.unshift(query);
                        if (searchHistory.length > 10) {
                            searchHistory.pop();
                        }
                        localStorage.setItem('orchidSearchHistory', JSON.stringify(searchHistory));
                    }
                });
            }
        }
    }
}

// Show search suggestions
function showSearchSuggestions(suggestions) {
    // Implementation for search suggestions dropdown
    // This could be expanded to show a dropdown with recent searches
    console.log('Recent searches:', suggestions);
}

// Enhanced upload functionality
function initializeUploadFeatures() {
    const fileInput = document.querySelector('#file');
    const uploadForm = document.querySelector('#uploadForm');
    
    if (fileInput && uploadForm) {
        // Drag and drop functionality
        const uploadZone = document.createElement('div');
        uploadZone.className = 'upload-zone p-4 text-center mb-3';
        uploadZone.innerHTML = `
            <i data-feather="upload-cloud" style="width: 48px; height: 48px;" class="text-muted mb-3"></i>
            <p class="mb-2">Drag and drop your orchid photos here</p>
            <p class="text-muted small">or click to select files</p>
        `;
        
        // Insert upload zone before the file input
        fileInput.parentNode.insertBefore(uploadZone, fileInput);
        
        // Make upload zone clickable
        uploadZone.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Drag and drop events
        uploadZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });
        
        uploadZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
        });
        
        uploadZone.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                fileInput.dispatchEvent(new Event('change'));
            }
        });
        
        // Enhanced file validation
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // Validate file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp'];
                if (!allowedTypes.includes(file.type)) {
                    showNotification('Please select a valid image file (JPG, PNG, GIF, or BMP)', 'error');
                    this.value = '';
                    return;
                }
                
                // Validate file size (16MB)
                if (file.size > 16 * 1024 * 1024) {
                    showNotification('File size must be less than 16MB', 'error');
                    this.value = '';
                    return;
                }
                
                // Show file info
                uploadZone.innerHTML = `
                    <i data-feather="image" style="width: 48px; height: 48px;" class="text-success mb-3"></i>
                    <p class="mb-1"><strong>${file.name}</strong></p>
                    <p class="text-muted small">${(file.size / 1024 / 1024).toFixed(1)} MB</p>
                    <p class="text-success small">Ready to upload!</p>
                `;
                
                showNotification('Image selected successfully!', 'success');
            }
        });
    }
}

// Gallery enhancements
function initializeGalleryFeatures() {
    // Masonry-style layout for gallery (if needed)
    const galleryContainer = document.querySelector('.gallery-container');
    if (galleryContainer) {
        // Add any gallery-specific enhancements here
        console.log('Gallery features initialized');
    }
    
    // Image lightbox functionality
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('gallery-image')) {
            const src = e.target.src;
            const title = e.target.alt;
            showImageLightbox(src, title);
        }
    });
    
    // Infinite scroll for gallery (optional)
    if (document.querySelector('.gallery-pagination')) {
        initializeInfiniteScroll();
    }
}

// Image lightbox
function showImageLightbox(src, title) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-xl modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${src}" alt="${title}" class="img-fluid">
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

// Notification system
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.querySelector('#notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1080';
        document.body.appendChild(container);
    }
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.querySelector('#notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i data-feather="${getNotificationIcon(type)}" class="me-2"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notification);
    feather.replace();
    
    // Auto-dismiss after duration
    setTimeout(function() {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(function() {
                if (notification.parentNode) {
                    container.removeChild(notification);
                }
            }, 150);
        }
    }, duration);
}

// Get notification icon based on type
function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'alert-circle',
        warning: 'alert-triangle',
        info: 'info'
    };
    return icons[type] || 'info';
}

// Infinite scroll implementation
function initializeInfiniteScroll() {
    let loading = false;
    let page = 2; // Start from page 2 since page 1 is already loaded
    
    const loadMoreContent = function() {
        if (loading) return;
        loading = true;
        
        // Add loading indicator
        showNotification('Loading more orchids...', 'info', 2000);
        
        // This would make an AJAX request to load more content
        // For now, we'll just show a message
        setTimeout(function() {
            loading = false;
            console.log('Infinite scroll would load page', page);
            page++;
        }, 1000);
    };
    
    window.addEventListener('scroll', function() {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 1000) {
            loadMoreContent();
        }
    });
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
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

// API helper functions
function makeAPIRequest(url, options = {}) {
    return fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .catch(error => {
        console.error('API request failed:', error);
        showNotification('Request failed. Please try again.', 'error');
        throw error;
    });
}

// Local storage helpers
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (e) {
        console.warn('Could not save to localStorage:', e);
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.warn('Could not load from localStorage:', e);
        return defaultValue;
    }
}

// Export functions for use in other scripts
window.OrchidContinuum = {
    showNotification,
    showImageLightbox,
    makeAPIRequest,
    saveToLocalStorage,
    loadFromLocalStorage
};
