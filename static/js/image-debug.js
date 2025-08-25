// Image Loading Debug System
console.log('🖼️ Image Debug System Active');

// Track all image load attempts
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Scanning for images...');
    
    const images = document.querySelectorAll('img');
    console.log(`📊 Found ${images.length} images on page`);
    
    images.forEach((img, index) => {
        const src = img.getAttribute('src');
        console.log(`📷 Image ${index + 1}: ${src}`);
        
        // Add comprehensive error tracking
        img.addEventListener('error', function(e) {
            console.error(`❌ Image ${index + 1} FAILED to load:`, {
                src: src,
                originalSrc: img.getAttribute('data-original-src') || src,
                alt: img.alt,
                element: img
            });
            
            // Force fallback to FCOS placeholder
            if (!src.includes('fcos_placeholder_rect.png')) {
                console.log(`🔄 Switching to fallback for image ${index + 1}`);
                img.src = '/static/images/fcos_placeholder_rect.png';
            }
        });
        
        img.addEventListener('load', function(e) {
            console.log(`✅ Image ${index + 1} loaded successfully:`, src);
        });
        
        // Store original src for debugging
        img.setAttribute('data-original-src', src);
    });
    
    // Test Google Drive API endpoint
    setTimeout(() => {
        testGoogleDriveAPI();
    }, 2000);
});

function testGoogleDriveAPI() {
    console.log('🧪 Testing Google Drive API...');
    
    // Test a known Google Drive ID
    const testId = '185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I';
    const testUrl = `/api/drive-photo/${testId}`;
    
    fetch(testUrl)
        .then(response => {
            console.log(`📡 Google Drive API test (${testId}):`, {
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries(response.headers.entries())
            });
            return response.blob();
        })
        .then(blob => {
            console.log(`📦 Image blob received:`, {
                size: blob.size,
                type: blob.type
            });
        })
        .catch(error => {
            console.error('❌ Google Drive API test failed:', error);
        });
}

// Global function for manual testing
window.debugImages = function() {
    const images = document.querySelectorAll('img');
    console.table(Array.from(images).map((img, index) => ({
        index: index + 1,
        src: img.src,
        originalSrc: img.getAttribute('data-original-src'),
        naturalWidth: img.naturalWidth,
        naturalHeight: img.naturalHeight,
        complete: img.complete,
        alt: img.alt
    })));
};

console.log('🛠️ Use debugImages() to see all image status');