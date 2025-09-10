/**
 * Main FCOS Orchid Judge Application Controller
 * Coordinates all components and manages app state
 */

class FCOSJudgeApp {
    constructor() {
        this.currentStep = 'home';
        this.data = {
            consent: false,
            photos: {},
            taxonomy: {},
            analysis: {},
            scoring: {},
            certificate: {}
        };
        this.steps = ['home', 'capture', 'taxonomy', 'analysis', 'scoring', 'certificate'];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.checkInstallPrompt();
        this.registerServiceWorker();
        this.goToStep('home');
    }

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('start-new-entry')?.addEventListener('click', () => {
            this.startNewEntry();
        });

        document.getElementById('view-history')?.addEventListener('click', () => {
            this.viewHistory();
        });

        document.getElementById('about-btn')?.addEventListener('click', () => {
            this.goToStep('about');
        });

        // Step navigation
        this.setupStepNavigation();

        // Settings
        document.getElementById('dark-mode-toggle')?.addEventListener('change', (e) => {
            this.toggleDarkMode(e.target.checked);
        });

        document.getElementById('large-text-toggle')?.addEventListener('change', (e) => {
            this.toggleLargeText(e.target.checked);
        });

        // Consent modal
        document.getElementById('consent-checkbox')?.addEventListener('change', (e) => {
            document.getElementById('consent-accept').disabled = !e.target.checked;
        });

        document.getElementById('consent-accept')?.addEventListener('click', () => {
            this.acceptConsent();
        });

        document.getElementById('consent-decline')?.addEventListener('click', () => {
            this.declineConsent();
        });

        // Window events
        window.addEventListener('beforeinstallprompt', (e) => {
            this.handleInstallPrompt(e);
        });

        window.addEventListener('beforeunload', () => {
            this.saveCurrentState();
        });
    }

    setupStepNavigation() {
        // Back buttons
        document.getElementById('capture-back-btn')?.addEventListener('click', () => {
            this.goToStep('home');
        });

        document.getElementById('taxonomy-back-btn')?.addEventListener('click', () => {
            this.goToStep('capture');
        });

        document.getElementById('analysis-back-btn')?.addEventListener('click', () => {
            this.goToStep('taxonomy');
        });

        document.getElementById('scoring-back-btn')?.addEventListener('click', () => {
            this.goToStep('analysis');
        });

        document.getElementById('certificate-back-btn')?.addEventListener('click', () => {
            this.goToStep('scoring');
        });

        document.getElementById('about-back-btn')?.addEventListener('click', () => {
            this.goToStep('home');
        });

        // Next buttons
        document.getElementById('next-step-btn')?.addEventListener('click', () => {
            this.goToStep('taxonomy');
        });

        document.getElementById('taxonomy-next-btn')?.addEventListener('click', () => {
            this.goToStep('analysis');
        });

        document.getElementById('analysis-next-btn')?.addEventListener('click', () => {
            this.goToStep('scoring');
        });

        document.getElementById('scoring-next-btn')?.addEventListener('click', () => {
            this.goToStep('certificate');
        });

        document.getElementById('start-over-btn')?.addEventListener('click', () => {
            this.startNewEntry();
        });
    }

    startNewEntry() {
        if (this.hasUnsavedWork()) {
            if (!confirm('You have unsaved work. Start a new entry anyway?')) {
                return;
            }
        }

        this.resetData();
        this.showConsentModal();
    }

    showConsentModal() {
        const modal = document.getElementById('consent-modal');
        if (modal) {
            modal.style.display = 'flex';
            document.getElementById('consent-checkbox').checked = false;
            document.getElementById('consent-accept').disabled = true;
        }
    }

    acceptConsent() {
        this.data.consent = true;
        this.hideConsentModal();
        this.goToStep('capture');
    }

    declineConsent() {
        this.hideConsentModal();
        this.goToStep('home');
    }

    hideConsentModal() {
        const modal = document.getElementById('consent-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    goToStep(stepName) {
        if (!this.steps.includes(stepName) && stepName !== 'about') {
            console.error('Invalid step:', stepName);
            return;
        }

        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });

        // Show target screen
        const targetScreen = document.getElementById(`${stepName}-screen`);
        if (targetScreen) {
            targetScreen.classList.add('active');
            this.currentStep = stepName;

            // Initialize step-specific functionality
            this.initializeStep(stepName);

            // Update URL hash for navigation
            if (stepName !== 'home') {
                window.history.pushState({step: stepName}, '', `#${stepName}`);
            } else {
                window.history.pushState({step: stepName}, '', '#');
            }
        }
    }

    initializeStep(stepName) {
        switch (stepName) {
            case 'capture':
                this.initializeCaptureStep();
                break;
            case 'taxonomy':
                this.initializeTaxonomyStep();
                break;
            case 'analysis':
                this.initializeAnalysisStep();
                break;
            case 'scoring':
                this.initializeScoringStep();
                break;
            case 'certificate':
                this.initializeCertificateStep();
                break;
        }
    }

    initializeCaptureStep() {
        // Photo capture is automatically initialized
        // Check if we have existing photos
        if (window.photoCapture) {
            const existingPhotos = window.photoCapture.getPhotos();
            if (existingPhotos.plant || existingPhotos.tag) {
                this.data.photos = existingPhotos;
            }
        }
    }

    initializeTaxonomyStep() {
        // OCR analysis is automatically initialized
        // Load saved taxonomy data if available
        if (window.ocrAnalyzer) {
            const savedData = window.ocrAnalyzer.loadSavedTaxonomyData();
            if (savedData) {
                this.data.taxonomy = savedData;
            }
        }

        // Trigger OCR if we have a tag photo and no OCR results yet
        if (this.data.photos.tag && window.ocrAnalyzer && !window.ocrAnalyzer.ocrResults) {
            window.ocrAnalyzer.performOCR(this.data.photos.tag.blob);
        }
    }

    initializeAnalysisStep() {
        // Load saved analysis data if available
        if (window.aiAnalyzer) {
            const savedData = window.aiAnalyzer.loadSavedAnalysisData();
            if (savedData) {
                this.data.analysis = savedData;
                window.aiAnalyzer.displayResults(savedData);
            } else if (this.data.photos.plant) {
                // Trigger AI analysis if we have a plant photo
                window.aiAnalyzer.performAnalysis(this.data.photos.plant.blob);
            }
        }
    }

    initializeScoringStep() {
        if (window.judgingSystems) {
            // Load saved scoring data if available
            const savedData = window.judgingSystems.loadSavedScores();
            if (savedData) {
                this.data.scoring = savedData;
            }
            
            // Display the scoring interface
            window.judgingSystems.displayScoringInterface();
        }
    }

    initializeCertificateStep() {
        this.generateCertificate();
    }

    generateCertificate() {
        // Collect all data for certificate
        const certificateData = {
            submitter: this.getSubmitterInfo(),
            plant: this.data.taxonomy,
            photos: this.data.photos,
            analysis: this.data.analysis,
            scoring: this.data.scoring,
            timestamp: new Date().toISOString(),
            judgingSystem: this.data.scoring.system || 'AOS'
        };

        this.data.certificate = certificateData;
        this.displayCertificatePreview(certificateData);
    }

    getSubmitterInfo() {
        // This could be enhanced to collect submitter details
        return {
            name: 'FCOS Member',
            email: '',
            membershipNumber: ''
        };
    }

    displayCertificatePreview(data) {
        const container = document.getElementById('certificate-preview');
        if (!container) return;

        const plantName = this.formatPlantName(data.plant);
        const awardBand = data.scoring.awardBand;
        const totalScore = data.scoring.totalScore;

        container.innerHTML = `
            <div class="certificate-card">
                <div class="certificate-header">
                    <div class="fcos-logo">
                        <svg width="48" height="48" viewBox="0 0 100 100" fill="none">
                            <circle cx="50" cy="50" r="45" stroke="#5B2A6E" stroke-width="3" fill="#8E44AD"/>
                            <path d="M35 50 L45 60 L65 40" stroke="white" stroke-width="4" fill="none"/>
                        </svg>
                    </div>
                    <div class="certificate-title">
                        <h2>Educational Practice Certificate</h2>
                        <p>Five Cities Orchid Society</p>
                    </div>
                </div>

                <div class="certificate-body">
                    <div class="plant-info">
                        <h3>${plantName}</h3>
                        ${data.plant.isHybrid ? `
                            <p class="hybrid-parents">
                                ${data.plant.parentA} × ${data.plant.parentB}
                            </p>
                        ` : ''}
                        <div class="certificate-details">
                            <div>Submitter: ${data.submitter.name}</div>
                            <div>Date: ${new Date(data.timestamp).toLocaleDateString()}</div>
                            <div>System: ${data.judgingSystem}</div>
                        </div>
                    </div>

                    <div class="score-summary">
                        <div class="total-score">
                            <span class="score-value">${totalScore}</span>
                            <span class="score-max">/100</span>
                        </div>
                        ${awardBand ? `
                            <div class="award-achieved" style="background-color: ${awardBand.color};">
                                ${awardBand.label}
                            </div>
                        ` : ''}
                    </div>

                    <div class="certificate-photos">
                        <div class="photo-container">
                            <img src="${data.photos.plant.url}" alt="Plant photo" class="cert-photo">
                            <label>Plant</label>
                        </div>
                        <div class="photo-container">
                            <img src="${data.photos.tag.url}" alt="Tag photo" class="cert-photo">
                            <label>Tag</label>
                        </div>
                    </div>

                    ${data.scoring.judgesNotes ? `
                        <div class="judges-notes">
                            <h4>Notes</h4>
                            <p>${data.scoring.judgesNotes}</p>
                        </div>
                    ` : ''}
                </div>

                <div class="certificate-footer">
                    <div class="watermark">Educational — Not Official Judging</div>
                    <div class="generated-by">Generated by FCOS Orchid Judge Beta</div>
                </div>
            </div>
        `;

        // Setup certificate actions
        this.setupCertificateActions();
    }

    formatPlantName(taxonomy) {
        let name = '';
        if (taxonomy.genus) name += taxonomy.genus;
        if (taxonomy.species) name += ` ${taxonomy.species}`;
        if (taxonomy.clone) name += ` '${taxonomy.clone}'`;
        return name || 'Unknown Orchid';
    }

    setupCertificateActions() {
        // PDF generation
        document.getElementById('generate-pdf-btn')?.addEventListener('click', () => {
            this.generatePDF();
        });

        // Save to FCOS
        document.getElementById('save-to-fcos-btn')?.addEventListener('click', () => {
            this.saveToFCOS();
        });

        // Email copy
        document.getElementById('email-copy-btn')?.addEventListener('click', () => {
            this.emailCopy();
        });
    }

    async generatePDF() {
        try {
            const button = document.getElementById('generate-pdf-btn');
            const originalText = button.textContent;
            button.textContent = 'Generating...';
            button.disabled = true;

            const response = await fetch('/api/fcos-judge/generate-pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.data.certificate)
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `FCOS-Certificate-${Date.now()}.pdf`;
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                throw new Error('PDF generation failed');
            }
        } catch (error) {
            console.error('PDF generation error:', error);
            alert('Failed to generate PDF. Please try again.');
        } finally {
            const button = document.getElementById('generate-pdf-btn');
            button.textContent = 'Generate Certificate (PDF)';
            button.disabled = false;
        }
    }

    async saveToFCOS() {
        try {
            const button = document.getElementById('save-to-fcos-btn');
            const originalText = button.textContent;
            button.textContent = 'Saving...';
            button.disabled = true;

            const response = await fetch('/api/fcos-judge/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.data)
            });

            if (response.ok) {
                const result = await response.json();
                alert('Successfully saved to FCOS database!');
                this.data.submissionId = result.id;
            } else {
                throw new Error('Submission failed');
            }
        } catch (error) {
            console.error('Submission error:', error);
            
            // Store for offline sync
            this.storeForOfflineSync();
            alert('Saved locally. Will sync when online.');
        } finally {
            const button = document.getElementById('save-to-fcos-btn');
            button.textContent = 'Save to FCOS';
            button.disabled = false;
        }
    }

    async emailCopy() {
        const email = prompt('Enter your email address:');
        if (!email) return;

        try {
            const response = await fetch('/api/fcos-judge/email-certificate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    certificateData: this.data.certificate
                })
            });

            if (response.ok) {
                alert('Certificate emailed successfully!');
            } else {
                throw new Error('Email failed');
            }
        } catch (error) {
            console.error('Email error:', error);
            alert('Failed to send email. Please try again.');
        }
    }

    async storeForOfflineSync() {
        try {
            const db = await this.openIndexedDB();
            const transaction = db.transaction(['submissions'], 'readwrite');
            const store = transaction.objectStore('submissions');
            
            const submission = {
                id: Date.now(),
                data: this.data,
                timestamp: new Date().toISOString(),
                synced: false
            };
            
            await store.add(submission);
            
            // Register for background sync
            if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('judge-submission');
            }
        } catch (error) {
            console.error('Failed to store for offline sync:', error);
        }
    }

    openIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('FCOSJudgeDB', 1);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('submissions')) {
                    db.createObjectStore('submissions', { keyPath: 'id' });
                }
            };
        });
    }

    viewHistory() {
        // TODO: Implement history viewing
        alert('History feature coming soon!');
    }

    toggleDarkMode(enabled) {
        if (enabled) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        localStorage.setItem('fcos-dark-mode', enabled.toString());
    }

    toggleLargeText(enabled) {
        if (enabled) {
            document.body.classList.add('large-text');
        } else {
            document.body.classList.remove('large-text');
        }
        localStorage.setItem('fcos-large-text', enabled.toString());
    }

    loadSettings() {
        // Dark mode
        const darkMode = localStorage.getItem('fcos-dark-mode') === 'true';
        const darkToggle = document.getElementById('dark-mode-toggle');
        if (darkToggle) {
            darkToggle.checked = darkMode;
            this.toggleDarkMode(darkMode);
        }

        // Large text
        const largeText = localStorage.getItem('fcos-large-text') === 'true';
        const textToggle = document.getElementById('large-text-toggle');
        if (textToggle) {
            textToggle.checked = largeText;
            this.toggleLargeText(largeText);
        }
    }

    handleInstallPrompt(e) {
        e.preventDefault();
        this.deferredPrompt = e;
        
        // Show install button or banner
        this.showInstallOption();
    }

    showInstallOption() {
        // Add install prompt to home screen
        const homeScreen = document.getElementById('home-screen');
        if (homeScreen && !document.getElementById('install-prompt')) {
            const installPrompt = document.createElement('div');
            installPrompt.id = 'install-prompt';
            installPrompt.className = 'install-prompt';
            installPrompt.innerHTML = `
                <div class="card">
                    <h3>Install FCOS Judge</h3>
                    <p>Add to your home screen for quick access and offline use.</p>
                    <button id="install-app-btn" class="btn btn-primary">
                        Install App
                    </button>
                </div>
            `;
            homeScreen.appendChild(installPrompt);

            document.getElementById('install-app-btn').addEventListener('click', () => {
                this.installApp();
            });
        }
    }

    async installApp() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;
            
            if (outcome === 'accepted') {
                console.log('App installed');
                document.getElementById('install-prompt')?.remove();
            }
            
            this.deferredPrompt = null;
        }
    }

    checkInstallPrompt() {
        // Check if app is already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('App is installed');
            return;
        }

        // Check if install prompt was dismissed
        if (localStorage.getItem('fcos-install-dismissed')) {
            return;
        }
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/js/service-worker.js');
                console.log('Service Worker registered:', registration);
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    resetData() {
        this.data = {
            consent: false,
            photos: {},
            taxonomy: {},
            analysis: {},
            scoring: {},
            certificate: {}
        };
        
        // Clear session storage
        sessionStorage.removeItem('fcos-taxonomy-data');
        sessionStorage.removeItem('fcos-analysis-data');
        sessionStorage.removeItem('fcos-scoring-data');
    }

    hasUnsavedWork() {
        return Object.keys(this.data.photos).length > 0 || 
               Object.keys(this.data.taxonomy).length > 0 ||
               Object.keys(this.data.analysis).length > 0 ||
               Object.keys(this.data.scoring).length > 0;
    }

    saveCurrentState() {
        localStorage.setItem('fcos-current-step', this.currentStep);
        localStorage.setItem('fcos-app-data', JSON.stringify(this.data));
    }

    // Data setters for component integration
    setPhotos(photos) {
        this.data.photos = photos;
    }

    setTaxonomyData(taxonomy) {
        this.data.taxonomy = taxonomy;
    }

    setAnalysisData(analysis) {
        this.data.analysis = analysis;
    }

    setScoringData(scoring) {
        this.data.scoring = scoring;
    }

    // Getters
    getCurrentStep() {
        return this.currentStep;
    }

    getData() {
        return this.data;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.fcosJudge = new FCOSJudgeApp();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FCOSJudgeApp;
}