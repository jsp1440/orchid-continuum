/**
 * Photo Capture System for FCOS Orchid Judge
 * Handles dual photo capture (plant + tag) with reference card overlay
 */

class PhotoCaptureSystem {
    constructor() {
        this.photos = {
            plant: null,
            tag: null
        };
        this.referenceCardActive = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkCameraSupport();
    }

    setupEventListeners() {
        // Photo slot click handlers
        document.getElementById('plant-photo-slot')?.addEventListener('click', () => {
            this.capturePhoto('plant');
        });

        document.getElementById('tag-photo-slot')?.addEventListener('click', () => {
            this.capturePhoto('tag');
        });

        // Reference card toggle
        document.getElementById('reference-toggle')?.addEventListener('change', (e) => {
            this.toggleReferenceCard(e.target.checked);
        });

        // File input handlers
        document.getElementById('plant-file-input')?.addEventListener('change', (e) => {
            this.handleFileSelect(e, 'plant');
        });

        document.getElementById('tag-file-input')?.addEventListener('change', (e) => {
            this.handleFileSelect(e, 'tag');
        });
    }

    async checkCameraSupport() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => track.stop());
            this.cameraSupported = true;
        } catch (error) {
            this.cameraSupported = false;
            console.log('Camera not available, falling back to file input');
        }
    }

    async capturePhoto(type) {
        if (this.cameraSupported) {
            await this.openCamera(type);
        } else {
            this.openFileInput(type);
        }
    }

    async openCamera(type) {
        try {
            const modal = this.createCameraModal(type);
            document.body.appendChild(modal);

            const video = modal.querySelector('video');
            const canvas = modal.querySelector('canvas');
            const captureBtn = modal.querySelector('.capture-btn');
            const closeBtn = modal.querySelector('.close-btn');

            const stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            });

            video.srcObject = stream;
            video.play();

            captureBtn.addEventListener('click', () => {
                this.captureFromVideo(video, canvas, type);
                this.closeCameraModal(modal, stream);
            });

            closeBtn.addEventListener('click', () => {
                this.closeCameraModal(modal, stream);
            });

        } catch (error) {
            console.error('Camera access denied:', error);
            this.openFileInput(type);
        }
    }

    createCameraModal(type) {
        const modal = document.createElement('div');
        modal.className = 'camera-modal';
        modal.innerHTML = `
            <div class="camera-container">
                <div class="camera-header">
                    <h3>Capture ${type === 'plant' ? 'Plant' : 'Tag'} Photo</h3>
                    <button class="close-btn" type="button">×</button>
                </div>
                <div class="camera-viewport">
                    <video autoplay playsinline></video>
                    ${type === 'plant' && this.referenceCardActive ? this.getReferenceCardOverlay() : ''}
                    <div class="camera-guidelines">
                        ${type === 'plant' 
                            ? '<p>Center the main flower(s) in frame</p>' 
                            : '<p>Keep tag text sharp and readable</p>'
                        }
                    </div>
                </div>
                <div class="camera-controls">
                    <button class="btn btn-primary capture-btn">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <circle cx="12" cy="12" r="10"/>
                        </svg>
                        Capture
                    </button>
                </div>
                <canvas style="display: none;"></canvas>
            </div>
        `;

        // Add modal styles
        const style = document.createElement('style');
        style.textContent = `
            .camera-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.9);
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .camera-container {
                background: white;
                border-radius: 16px;
                max-width: 90vw;
                max-height: 90vh;
                overflow: hidden;
            }
            .camera-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem;
                border-bottom: 1px solid #eee;
            }
            .close-btn {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                padding: 4px;
            }
            .camera-viewport {
                position: relative;
                overflow: hidden;
            }
            .camera-viewport video {
                width: 100%;
                height: auto;
                display: block;
            }
            .camera-guidelines {
                position: absolute;
                bottom: 16px;
                left: 16px;
                right: 16px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 8px;
                text-align: center;
                font-size: 14px;
            }
            .camera-controls {
                padding: 1rem;
                text-align: center;
            }
            .capture-btn {
                min-width: 120px;
            }
        `;
        document.head.appendChild(style);

        return modal;
    }

    getReferenceCardOverlay() {
        return `
            <div class="reference-overlay active">
                <div class="reference-label">Credit Card (85.6×54mm)</div>
            </div>
        `;
    }

    captureFromVideo(video, canvas, type) {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        context.drawImage(video, 0, 0);
        
        canvas.toBlob((blob) => {
            this.processPhoto(blob, type);
        }, 'image/jpeg', 0.9);
    }

    closeCameraModal(modal, stream) {
        stream.getTracks().forEach(track => track.stop());
        modal.remove();
    }

    openFileInput(type) {
        const input = document.getElementById(`${type}-file-input`);
        if (input) {
            input.click();
        }
    }

    handleFileSelect(event, type) {
        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            this.processPhoto(file, type);
        }
    }

    processPhoto(blob, type) {
        const url = URL.createObjectURL(blob);
        this.photos[type] = {
            blob: blob,
            url: url,
            timestamp: new Date().toISOString(),
            type: type
        };

        this.displayPhoto(url, type);
        this.enableNextStep();

        // Store for offline use
        this.storePhotoOffline(blob, type);

        // Trigger analysis if this is a tag photo
        if (type === 'tag') {
            this.triggerOCR(blob);
        } else if (type === 'plant') {
            this.triggerAIAnalysis(blob);
        }
    }

    displayPhoto(url, type) {
        const slot = document.getElementById(`${type}-photo-slot`);
        if (slot) {
            slot.innerHTML = `
                <img src="${url}" alt="${type} photo" class="photo-preview">
                <div class="photo-label">${type === 'plant' ? 'Plant Photo' : 'Tag Photo'}</div>
                <button class="retake-btn" onclick="photoCapture.retakePhoto('${type}')">
                    Retake
                </button>
            `;
            slot.classList.add('filled');
        }
    }

    retakePhoto(type) {
        if (this.photos[type]) {
            URL.revokeObjectURL(this.photos[type].url);
            this.photos[type] = null;
        }

        const slot = document.getElementById(`${type}-photo-slot`);
        if (slot) {
            slot.innerHTML = `
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                </svg>
                <p>Tap to capture ${type === 'plant' ? 'plant' : 'tag'} photo</p>
            `;
            slot.classList.remove('filled');
        }

        this.updateNextStepButton();
    }

    toggleReferenceCard(active) {
        this.referenceCardActive = active;
        // Update any active overlays
        document.querySelectorAll('.reference-overlay').forEach(overlay => {
            overlay.classList.toggle('active', active);
        });
    }

    enableNextStep() {
        if (this.photos.plant && this.photos.tag) {
            const nextBtn = document.getElementById('next-step-btn');
            if (nextBtn) {
                nextBtn.disabled = false;
                nextBtn.textContent = 'Continue to Analysis';
            }
        }
    }

    updateNextStepButton() {
        const nextBtn = document.getElementById('next-step-btn');
        if (nextBtn) {
            const bothPhotos = this.photos.plant && this.photos.tag;
            nextBtn.disabled = !bothPhotos;
            nextBtn.textContent = bothPhotos ? 'Continue to Analysis' : 'Take Both Photos First';
        }
    }

    async storePhotoOffline(blob, type) {
        try {
            const db = await this.openIndexedDB();
            const transaction = db.transaction(['photos'], 'readwrite');
            const store = transaction.objectStore('photos');
            
            const photoData = {
                id: `${type}_${Date.now()}`,
                type: type,
                blob: blob,
                timestamp: new Date().toISOString()
            };
            
            await store.put(photoData);
        } catch (error) {
            console.error('Failed to store photo offline:', error);
        }
    }

    openIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('FCOSJudgePhotos', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('photos')) {
                    db.createObjectStore('photos', { keyPath: 'id' });
                }
            };
        });
    }

    async triggerOCR(blob) {
        try {
            const formData = new FormData();
            formData.append('image', blob, 'tag.jpg');
            
            const response = await fetch('/api/fcos-judge/ocr', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayOCRResults(result);
            }
        } catch (error) {
            console.error('OCR failed:', error);
        }
    }

    async triggerAIAnalysis(blob) {
        try {
            const formData = new FormData();
            formData.append('image', blob, 'plant.jpg');
            
            const response = await fetch('/api/fcos-judge/analyze', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayAnalysisResults(result);
            }
        } catch (error) {
            console.error('AI analysis failed:', error);
        }
    }

    displayOCRResults(result) {
        // This will be handled by the OCR component
        if (window.ocrAnalyzer) {
            window.ocrAnalyzer.displayResults(result);
        }
    }

    displayAnalysisResults(result) {
        // This will be handled by the AI analysis component
        if (window.aiAnalyzer) {
            window.aiAnalyzer.displayResults(result);
        }
    }

    getPhotos() {
        return this.photos;
    }

    hasPhotos() {
        return this.photos.plant && this.photos.tag;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.photoCapture = new PhotoCaptureSystem();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhotoCaptureSystem;
}