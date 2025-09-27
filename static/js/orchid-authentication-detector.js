/*!
 * Orchid Authentication & Mislabeling Detector Widget
 * AI-powered orchid authentication system to detect fraud and mislabeling
 * Part of The Orchid Continuum platform
 */

class OrchidAuthenticationDetector {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            maxFileSize: 10 * 1024 * 1024, // 10MB
            allowedTypes: ['image/jpeg', 'image/png', 'image/webp'],
            showAdvancedOptions: true,
            enableDragDrop: true,
            ...options
        };
        
        this.currentAnalysis = null;
        this.capabilities = null;
        this.uploadedImage = null;
        this.claimedIdentity = {};
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error(`Orchid authentication detector container not found: ${this.containerId}`);
            return;
        }
        
        this.render();
        this.attachEventListeners();
        this.loadCapabilities();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="orchid-authentication-detector">
                <div class="authentication-header">
                    <div class="header-content">
                        <div class="header-icon">
                            <i data-feather="shield-check" class="shield-icon"></i>
                        </div>
                        <div class="header-text">
                            <h3>Orchid Authentication & Fraud Detector</h3>
                            <p>AI-powered analysis to detect mislabeling and verify orchid authenticity</p>
                        </div>
                    </div>
                </div>
                
                <div class="authentication-upload-section" id="uploadSection">
                    <div class="upload-area" id="uploadArea">
                        <div class="upload-content">
                            <div class="upload-icon">
                                <i data-feather="upload-cloud" class="upload-cloud-icon"></i>
                            </div>
                            <h4>Upload Orchid Photo for Authentication</h4>
                            <p>Drop an image here or click to select</p>
                            <input type="file" id="imageUpload" accept="image/*" style="display: none;">
                            <button type="button" class="btn btn-primary" id="selectImageBtn">
                                <i data-feather="image" class="me-2"></i>Select Image
                            </button>
                            <div class="upload-requirements">
                                <small class="text-muted">
                                    Supports JPEG, PNG, WebP • Max 10MB • Min 800x600 recommended
                                </small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="image-preview" id="imagePreview" style="display: none;">
                        <div class="preview-container">
                            <img id="previewImage" alt="Uploaded orchid" class="preview-img">
                            <div class="preview-actions">
                                <button type="button" class="btn btn-sm btn-outline-secondary" id="changeImageBtn">
                                    <i data-feather="refresh-cw" class="me-1"></i>Change Image
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="claimed-identity-section">
                        <h5><i data-feather="tag" class="me-2"></i>Claimed Identity (Optional)</h5>
                        <p class="text-muted">Provide the claimed identification to verify authenticity</p>
                        
                        <div class="row">
                            <div class="col-md-4">
                                <label class="form-label">Genus</label>
                                <input type="text" class="form-control" id="genusInput" 
                                       placeholder="e.g., Phalaenopsis">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Species</label>
                                <input type="text" class="form-control" id="speciesInput" 
                                       placeholder="e.g., amabilis">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Hybrid Name</label>
                                <input type="text" class="form-control" id="hybridInput" 
                                       placeholder="e.g., White Beauty">
                            </div>
                        </div>
                    </div>
                    
                    <div class="additional-info-section">
                        <h5><i data-feather="info" class="me-2"></i>Additional Information (Optional)</h5>
                        <p class="text-muted">Provide context to help with authentication analysis</p>
                        
                        <div class="row">
                            <div class="col-md-4">
                                <label class="form-label">Source</label>
                                <select class="form-select" id="sourceSelect">
                                    <option value="">Select source...</option>
                                    <option value="reputable_nursery">Reputable Nursery</option>
                                    <option value="online_seller">Online Seller</option>
                                    <option value="auction">Auction Site</option>
                                    <option value="private_collector">Private Collector</option>
                                    <option value="gift">Gift/Unknown</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Seller Information</label>
                                <input type="text" class="form-control" id="sellerInput" 
                                       placeholder="Seller name or details">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Price Paid</label>
                                <input type="text" class="form-control" id="priceInput" 
                                       placeholder="e.g., $25.00">
                            </div>
                        </div>
                    </div>
                    
                    <div class="authentication-controls">
                        <button type="button" class="btn btn-danger btn-lg" id="authenticateBtn" disabled>
                            <i data-feather="shield-check" class="me-2"></i>Authenticate Orchid
                        </button>
                    </div>
                </div>
                
                <div class="authentication-progress" id="progressSection" style="display: none;">
                    <div class="progress-content">
                        <div class="progress-icon">
                            <div class="spinner-border text-danger" role="status"></div>
                        </div>
                        <h4>Analyzing Orchid Authenticity</h4>
                        <p id="progressText">Performing AI vision analysis...</p>
                        <div class="progress mt-3">
                            <div class="progress-bar bg-danger progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
                
                <div class="authentication-results" id="resultsSection" style="display: none;">
                    <!-- Results will be populated here -->
                </div>
                
                <div class="authentication-error" id="errorSection" style="display: none;">
                    <div class="alert alert-danger">
                        <i data-feather="alert-triangle" class="me-2"></i>
                        <span id="errorMessage">An error occurred during authentication.</span>
                        <button type="button" class="btn btn-sm btn-outline-danger ms-2" id="retryBtn">
                            Try Again
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Initialize Feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    attachEventListeners() {
        // File upload
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('imageUpload');
        const selectBtn = document.getElementById('selectImageBtn');
        
        selectBtn?.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput?.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleImageUpload(file);
            }
        });
        
        // Drag and drop
        if (this.options.enableDragDrop) {
            uploadArea?.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('drag-over');
            });
            
            uploadArea?.addEventListener('dragleave', () => {
                uploadArea.classList.remove('drag-over');
            });
            
            uploadArea?.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleImageUpload(files[0]);
                }
            });
        }
        
        // Change image
        document.getElementById('changeImageBtn')?.addEventListener('click', () => {
            this.clearImage();
        });
        
        // Form inputs
        ['genusInput', 'speciesInput', 'hybridInput', 'sourceSelect', 'sellerInput', 'priceInput'].forEach(id => {
            document.getElementById(id)?.addEventListener('input', () => {
                this.updateClaimedIdentity();
            });
        });
        
        document.getElementById('sourceSelect')?.addEventListener('change', () => {
            this.updateClaimedIdentity();
        });
        
        // Authentication button
        document.getElementById('authenticateBtn')?.addEventListener('click', () => {
            this.performAuthentication();
        });
        
        // Retry button
        document.getElementById('retryBtn')?.addEventListener('click', () => {
            this.resetAuthentication();
        });
    }
    
    async loadCapabilities() {
        try {
            const response = await fetch('/api/orchid-authentication-capabilities');
            const data = await response.json();
            
            if (data.success) {
                this.capabilities = data.capabilities;
                console.log('Authentication capabilities loaded:', this.capabilities);
            }
        } catch (error) {
            console.error('Error loading authentication capabilities:', error);
        }
    }
    
    handleImageUpload(file) {
        // Validate file type
        if (!this.options.allowedTypes.includes(file.type)) {
            this.showError('Please upload a valid image file (JPEG, PNG, or WebP)');
            return;
        }
        
        // Validate file size
        if (file.size > this.options.maxFileSize) {
            this.showError(`File too large. Maximum size is ${this.options.maxFileSize / (1024*1024)}MB`);
            return;
        }
        
        // Store file and show preview
        this.uploadedImage = file;
        this.showImagePreview(file);
        
        // Enable authentication button
        document.getElementById('authenticateBtn').disabled = false;
    }
    
    showImagePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewImage = document.getElementById('previewImage');
            const uploadArea = document.getElementById('uploadArea');
            const imagePreview = document.getElementById('imagePreview');
            
            previewImage.src = e.target.result;
            uploadArea.style.display = 'none';
            imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
    
    clearImage() {
        this.uploadedImage = null;
        
        const uploadArea = document.getElementById('uploadArea');
        const imagePreview = document.getElementById('imagePreview');
        const authenticateBtn = document.getElementById('authenticateBtn');
        
        uploadArea.style.display = 'block';
        imagePreview.style.display = 'none';
        authenticateBtn.disabled = true;
        
        // Clear file input
        document.getElementById('imageUpload').value = '';
    }
    
    updateClaimedIdentity() {
        this.claimedIdentity = {
            genus: document.getElementById('genusInput')?.value.trim() || '',
            species: document.getElementById('speciesInput')?.value.trim() || '',
            hybrid_name: document.getElementById('hybridInput')?.value.trim() || ''
        };
        
        // Remove empty values
        Object.keys(this.claimedIdentity).forEach(key => {
            if (!this.claimedIdentity[key]) {
                delete this.claimedIdentity[key];
            }
        });
    }
    
    async performAuthentication() {
        try {
            if (!this.uploadedImage) {
                this.showError('Please upload an image first');
                return;
            }
            
            // Show progress
            this.showProgress('Performing AI vision analysis...');
            
            // Update claimed identity
            this.updateClaimedIdentity();
            
            // Prepare form data
            const formData = new FormData();
            formData.append('image', this.uploadedImage);
            
            // Add claimed identity
            if (this.claimedIdentity.genus) {
                formData.append('genus', this.claimedIdentity.genus);
            }
            if (this.claimedIdentity.species) {
                formData.append('species', this.claimedIdentity.species);
            }
            if (this.claimedIdentity.hybrid_name) {
                formData.append('hybrid_name', this.claimedIdentity.hybrid_name);
            }
            
            // Add additional info
            const source = document.getElementById('sourceSelect')?.value;
            const seller = document.getElementById('sellerInput')?.value.trim();
            const price = document.getElementById('priceInput')?.value.trim();
            
            if (source) formData.append('source', source);
            if (seller) formData.append('seller_info', seller);
            if (price) formData.append('price_paid', price);
            
            this.updateProgress(30, 'Cross-referencing with database...');
            
            const response = await fetch('/api/orchid-authentication', {
                method: 'POST',
                body: formData
            });
            
            this.updateProgress(70, 'Analyzing morphological features...');
            
            const result = await response.json();
            
            this.updateProgress(100, 'Finalizing authentication report...');
            
            if (result.success) {
                this.currentAnalysis = result.authentication_result;
                setTimeout(() => {
                    this.showResults(result.authentication_result);
                }, 1000);
            } else {
                this.showError(result.error || 'Authentication analysis failed');
            }
            
        } catch (error) {
            console.error('Authentication error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }
    
    showProgress(message) {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        document.getElementById('progressText').textContent = message;
        document.getElementById('progressSection').style.display = 'block';
        
        // Reset progress bar
        const progressBar = document.querySelector('.progress-bar');
        progressBar.style.width = '0%';
    }
    
    updateProgress(percentage, message) {
        document.getElementById('progressText').textContent = message;
        const progressBar = document.querySelector('.progress-bar');
        progressBar.style.width = `${percentage}%`;
    }
    
    showResults(analysisResult) {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.innerHTML = this.renderAnalysisResults(analysisResult);
        resultsSection.style.display = 'block';
        
        // Initialize Feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    renderAnalysisResults(result) {
        const authenticityClass = this.getAuthenticityClass(result.authenticity_level);
        const authenticityIcon = this.getAuthenticityIcon(result.authenticity_level);
        const authenticityTitle = this.getAuthenticityTitle(result.authenticity_level);
        
        return `
            <div class="analysis-results-content">
                <div class="results-header">
                    <div class="authenticity-badge ${authenticityClass}">
                        <i data-feather="${authenticityIcon}" class="me-2"></i>
                        <span>${authenticityTitle}</span>
                    </div>
                    <div class="confidence-score">
                        <div class="confidence-circle">
                            <span class="confidence-number">${Math.round(result.overall_confidence)}%</span>
                            <small>Confidence</small>
                        </div>
                    </div>
                </div>
                
                ${result.identified_species ? `
                    <div class="identification-section">
                        <h5><i data-feather="search" class="me-2"></i>AI Identification</h5>
                        <div class="identification-card">
                            <div class="identification-info">
                                <h6>${result.identified_species.genus || 'Unknown'} ${result.identified_species.species || ''}</h6>
                                <p class="text-muted">AI Confidence: ${result.identified_species.confidence || 0}%</p>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                ${result.claimed_identity ? `
                    <div class="claimed-vs-identified">
                        <h5><i data-feather="compare" class="me-2"></i>Claimed vs Identified</h5>
                        <div class="comparison-cards">
                            <div class="comparison-card claimed">
                                <h6>Claimed Identity</h6>
                                <p><strong>${result.claimed_identity.genus || 'Not provided'} ${result.claimed_identity.species || ''}</strong></p>
                                ${result.claimed_identity.hybrid_name ? `<p><em>${result.claimed_identity.hybrid_name}</em></p>` : ''}
                            </div>
                            <div class="comparison-card identified">
                                <h6>AI Identified</h6>
                                <p><strong>${result.identified_species?.genus || 'Unknown'} ${result.identified_species?.species || ''}</strong></p>
                                <p class="confidence-text">${result.identified_species?.confidence || 0}% confidence</p>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                ${result.database_matches.length > 0 ? `
                    <div class="database-matches-section">
                        <h5><i data-feather="database" class="me-2"></i>Database Matches (Top ${Math.min(result.database_matches.length, 3)})</h5>
                        <div class="matches-list">
                            ${result.database_matches.slice(0, 3).map(match => this.renderDatabaseMatch(match)).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${result.issues_detected.length > 0 ? `
                    <div class="issues-section">
                        <h5><i data-feather="alert-triangle" class="me-2"></i>Issues Detected</h5>
                        <div class="issues-list">
                            ${result.issues_detected.map(issue => this.renderIssue(issue)).join('')}
                        </div>
                    </div>
                ` : `
                    <div class="no-issues-section">
                        <div class="alert alert-success">
                            <i data-feather="check-circle" class="me-2"></i>
                            <strong>No major authenticity concerns detected</strong>
                        </div>
                    </div>
                `}
                
                <div class="morphological-section">
                    <h5><i data-feather="eye" class="me-2"></i>Morphological Analysis</h5>
                    <div class="morphological-grid">
                        ${result.morphological_analysis.flower_characteristics.size ? `
                            <div class="morph-item">
                                <span class="morph-label">Flower Size:</span>
                                <span class="morph-value">${result.morphological_analysis.flower_characteristics.size}</span>
                            </div>
                        ` : ''}
                        ${result.morphological_analysis.flower_characteristics.colors?.length > 0 ? `
                            <div class="morph-item">
                                <span class="morph-label">Colors:</span>
                                <span class="morph-value">${result.morphological_analysis.flower_characteristics.colors.join(', ')}</span>
                            </div>
                        ` : ''}
                        ${result.morphological_analysis.plant_structure.growth_habit ? `
                            <div class="morph-item">
                                <span class="morph-label">Growth Habit:</span>
                                <span class="morph-value">${result.morphological_analysis.plant_structure.growth_habit}</span>
                            </div>
                        ` : ''}
                        ${result.morphological_analysis.flower_characteristics.petal_shape ? `
                            <div class="morph-item">
                                <span class="morph-label">Petal Shape:</span>
                                <span class="morph-value">${result.morphological_analysis.flower_characteristics.petal_shape}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="recommendations-section">
                    <h5><i data-feather="lightbulb" class="me-2"></i>Recommendations</h5>
                    <div class="recommendations-list">
                        ${result.recommendations.map(rec => `
                            <div class="recommendation-item">
                                <span>${rec}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="authentication-report">
                    <h5><i data-feather="file-text" class="me-2"></i>Authentication Report</h5>
                    <div class="report-summary">
                        <div class="report-grid">
                            <div class="report-item">
                                <span class="report-label">Analysis Methods:</span>
                                <span class="report-value">${result.analysis_methods.join(', ').replace(/_/g, ' ')}</span>
                            </div>
                            <div class="report-item">
                                <span class="report-label">Database Size:</span>
                                <span class="report-value">${result.authentication_report.verification_details.database_size}</span>
                            </div>
                            <div class="report-item">
                                <span class="report-label">AI Model:</span>
                                <span class="report-value">${result.authentication_report.verification_details.ai_model}</span>
                            </div>
                            <div class="report-item">
                                <span class="report-label">Analysis Time:</span>
                                <span class="report-value">${new Date(result.timestamp).toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <div class="row">
                        <div class="col-md-4">
                            <button class="btn btn-outline-primary w-100" onclick="${this.containerId}Instance.exportReport()">
                                <i data-feather="download" class="me-2"></i>Export Report
                            </button>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-outline-info w-100" onclick="${this.containerId}Instance.shareResults()">
                                <i data-feather="share-2" class="me-2"></i>Share Results
                            </button>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-secondary w-100" onclick="${this.containerId}Instance.resetAuthentication()">
                                <i data-feather="refresh-cw" class="me-2"></i>New Analysis
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderDatabaseMatch(match) {
        return `
            <div class="match-card">
                <div class="match-header">
                    <span class="match-confidence">${Math.round(match.confidence_score)}%</span>
                    <div class="match-indicators">
                        ${match.genus_match ? '<span class="match-indicator success">Genus ✓</span>' : ''}
                        ${match.species_match ? '<span class="match-indicator success">Species ✓</span>' : ''}
                    </div>
                </div>
                <div class="match-content">
                    <p><strong>Orchid ID:</strong> ${match.orchid_id}</p>
                    ${match.matching_features.length > 0 ? `
                        <p><strong>Matching:</strong> ${match.matching_features.slice(0, 2).join(', ')}</p>
                    ` : ''}
                    ${match.conflicting_features.length > 0 ? `
                        <p class="text-warning"><strong>Conflicts:</strong> ${match.conflicting_features.slice(0, 2).join(', ')}</p>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    renderIssue(issue) {
        const severityClass = {
            'low': 'success',
            'medium': 'warning', 
            'high': 'warning',
            'critical': 'danger'
        }[issue.severity] || 'secondary';
        
        return `
            <div class="issue-card alert alert-${severityClass}">
                <div class="issue-header">
                    <strong>${issue.type.replace(/_/g, ' ').toUpperCase()}</strong>
                    <span class="badge bg-${severityClass}">${issue.severity}</span>
                </div>
                <p>${issue.description}</p>
                <small><strong>Recommendation:</strong> ${issue.recommendation}</small>
            </div>
        `;
    }
    
    getAuthenticityClass(level) {
        const classes = {
            'authentic': 'success',
            'likely_authentic': 'success',
            'uncertain': 'warning',
            'likely_mislabeled': 'warning',
            'mislabeled': 'danger',
            'fraudulent': 'danger'
        };
        return classes[level] || 'secondary';
    }
    
    getAuthenticityIcon(level) {
        const icons = {
            'authentic': 'check-circle',
            'likely_authentic': 'check',
            'uncertain': 'help-circle',
            'likely_mislabeled': 'alert-triangle',
            'mislabeled': 'x-circle',
            'fraudulent': 'shield-off'
        };
        return icons[level] || 'help-circle';
    }
    
    getAuthenticityTitle(level) {
        const titles = {
            'authentic': 'AUTHENTIC',
            'likely_authentic': 'LIKELY AUTHENTIC',
            'uncertain': 'UNCERTAIN',
            'likely_mislabeled': 'LIKELY MISLABELED', 
            'mislabeled': 'MISLABELED',
            'fraudulent': 'FRAUD DETECTED'
        };
        return titles[level] || 'UNKNOWN';
    }
    
    exportReport() {
        if (!this.currentAnalysis) return;
        
        const reportData = {
            analysis_date: new Date().toISOString(),
            authenticity_level: this.currentAnalysis.authenticity_level,
            confidence: this.currentAnalysis.overall_confidence,
            claimed_identity: this.currentAnalysis.claimed_identity,
            identified_species: this.currentAnalysis.identified_species,
            issues_detected: this.currentAnalysis.issues_detected,
            recommendations: this.currentAnalysis.recommendations,
            analysis_report: this.currentAnalysis.authentication_report
        };
        
        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `orchid-authentication-report-${Date.now()}.json`;
        link.click();
    }
    
    shareResults() {
        if (!this.currentAnalysis) return;
        
        const summary = `Orchid Authentication Results:
${this.getAuthenticityTitle(this.currentAnalysis.authenticity_level)} (${Math.round(this.currentAnalysis.overall_confidence)}% confidence)

Identified as: ${this.currentAnalysis.identified_species?.genus || 'Unknown'} ${this.currentAnalysis.identified_species?.species || ''}
Issues detected: ${this.currentAnalysis.issues_detected.length}

Authenticated by The Orchid Continuum platform`;
        
        if (navigator.share) {
            navigator.share({
                title: 'Orchid Authentication Results',
                text: summary
            });
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(summary).then(() => {
                alert('Results copied to clipboard!');
            });
        }
    }
    
    showError(message) {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').style.display = 'block';
    }
    
    resetAuthentication() {
        this.currentAnalysis = null;
        this.clearImage();
        
        // Reset form fields
        ['genusInput', 'speciesInput', 'hybridInput', 'sellerInput', 'priceInput'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.value = '';
        });
        
        const sourceSelect = document.getElementById('sourceSelect');
        if (sourceSelect) sourceSelect.value = '';
        
        // Show upload section
        document.getElementById('uploadSection').style.display = 'block';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('orchid-authentication-detector-widget');
    if (container) {
        window.orchidAuthenticationInstance = new OrchidAuthenticationDetector('orchid-authentication-detector-widget');
    }
});

// Global access for integration
window.OrchidAuthenticationDetector = OrchidAuthenticationDetector;