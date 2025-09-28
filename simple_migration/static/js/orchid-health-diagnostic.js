/*!
 * Orchid Health Diagnostic Widget
 * AI-powered orchid health diagnosis and treatment recommendations
 * Part of The Orchid Continuum platform
 */

class OrchidHealthDiagnostic {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            showProgress: true,
            enableTreatmentTracking: true,
            showConfidenceScores: true,
            maxImageSize: 10 * 1024 * 1024, // 10MB
            ...options
        };
        
        this.currentDiagnosis = null;
        this.treatmentTracking = null;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error(`Health diagnostic container not found: ${this.containerId}`);
            return;
        }
        
        this.render();
        this.attachEventListeners();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="orchid-health-diagnostic">
                <div class="diagnostic-header">
                    <div class="header-content">
                        <div class="header-icon">
                            <i data-feather="activity" class="diagnostic-icon"></i>
                        </div>
                        <div class="header-text">
                            <h3>AI Orchid Health Diagnostic</h3>
                            <p>Upload a photo of your orchid for instant AI health analysis and treatment recommendations</p>
                        </div>
                    </div>
                </div>
                
                <div class="diagnostic-upload-section" id="uploadSection">
                    <div class="upload-zone" id="uploadZone">
                        <div class="upload-content">
                            <i data-feather="camera" class="upload-icon"></i>
                            <h4>Upload Orchid Photo</h4>
                            <p>Drag & drop or click to select a photo showing health concerns</p>
                            <button type="button" class="btn btn-primary" id="selectImageBtn">
                                <i data-feather="image" class="me-2"></i>Select Image
                            </button>
                        </div>
                        <input type="file" id="imageInput" accept="image/*" style="display: none;">
                    </div>
                    
                    <div class="additional-info mt-3">
                        <label for="userNotes" class="form-label">Describe the problem (optional):</label>
                        <textarea id="userNotes" class="form-control" rows="3" 
                                  placeholder="Describe symptoms you've noticed (yellowing leaves, spots, wilting, etc.)"></textarea>
                    </div>
                </div>
                
                <div class="diagnostic-progress" id="progressSection" style="display: none;">
                    <div class="progress-content">
                        <div class="progress-icon">
                            <div class="spinner-border text-primary" role="status"></div>
                        </div>
                        <h4>Analyzing Your Orchid's Health</h4>
                        <p>Our AI is examining the image for health problems...</p>
                        <div class="progress mt-3">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 0%"></div>
                        </div>
                        <div class="progress-steps mt-2">
                            <small class="text-muted" id="progressText">Initializing analysis...</small>
                        </div>
                    </div>
                </div>
                
                <div class="diagnostic-results" id="resultsSection" style="display: none;">
                    <!-- Results will be populated here -->
                </div>
                
                <div class="diagnostic-error" id="errorSection" style="display: none;">
                    <div class="alert alert-danger">
                        <i data-feather="alert-circle" class="me-2"></i>
                        <span id="errorMessage">An error occurred during diagnosis.</span>
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
        const uploadZone = document.getElementById('uploadZone');
        const selectImageBtn = document.getElementById('selectImageBtn');
        const imageInput = document.getElementById('imageInput');
        const retryBtn = document.getElementById('retryBtn');
        
        // File upload events
        selectImageBtn?.addEventListener('click', () => imageInput.click());
        imageInput?.addEventListener('change', this.handleImageSelection.bind(this));
        
        // Drag and drop events
        uploadZone?.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadZone?.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadZone?.addEventListener('drop', this.handleDrop.bind(this));
        
        // Retry button
        retryBtn?.addEventListener('click', this.resetWidget.bind(this));
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadZone')?.classList.add('drag-over');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadZone')?.classList.remove('drag-over');
    }
    
    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadZone')?.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processImage(files[0]);
        }
    }
    
    handleImageSelection(e) {
        const file = e.target.files[0];
        if (file) {
            this.processImage(file);
        }
    }
    
    processImage(file) {
        // Validate file
        if (!this.validateImage(file)) {
            return;
        }
        
        // Show progress
        this.showProgress();
        
        // Create form data
        const formData = new FormData();
        formData.append('image', file);
        const userNotes = document.getElementById('userNotes')?.value || '';
        formData.append('notes', userNotes);
        
        // Start diagnosis
        this.performDiagnosis(formData);
    }
    
    validateImage(file) {
        // Check file type
        if (!file.type.startsWith('image/')) {
            this.showError('Please select a valid image file.');
            return false;
        }
        
        // Check file size
        if (file.size > this.options.maxImageSize) {
            this.showError('Image is too large. Please select an image smaller than 10MB.');
            return false;
        }
        
        return true;
    }
    
    async performDiagnosis(formData) {
        try {
            this.simulateProgress();
            
            const response = await fetch('/api/orchid-health-diagnostic', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentDiagnosis = result.diagnosis;
                this.showResults(result.diagnosis);
            } else {
                this.showError(result.error || 'Diagnosis failed');
            }
        } catch (error) {
            console.error('Diagnosis error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }
    
    simulateProgress() {
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.getElementById('progressText');
        
        if (!progressBar || !progressText) return;
        
        const steps = [
            { progress: 20, text: 'Processing image...' },
            { progress: 40, text: 'Analyzing plant structure...' },
            { progress: 60, text: 'Identifying health issues...' },
            { progress: 80, text: 'Generating treatment recommendations...' },
            { progress: 95, text: 'Finalizing diagnosis...' }
        ];
        
        let currentStep = 0;
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progressBar.style.width = `${step.progress}%`;
                progressText.textContent = step.text;
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 800);
    }
    
    showProgress() {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
    }
    
    showResults(diagnosis) {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.innerHTML = this.renderResults(diagnosis);
        resultsSection.style.display = 'block';
        
        // Initialize Feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    renderResults(diagnosis) {
        const healthAssessment = diagnosis.health_diagnosis?.health_assessment || {};
        const problemClassification = diagnosis.health_diagnosis?.problem_classification || {};
        const treatmentPlan = diagnosis.health_diagnosis?.treatment_plan || {};
        const recoveryPrognosis = diagnosis.health_diagnosis?.recovery_prognosis || {};
        
        const urgencyClass = this.getUrgencyClass(healthAssessment.urgency_level);
        const statusClass = this.getStatusClass(healthAssessment.overall_status);
        
        return `
            <div class="results-content">
                <div class="results-header">
                    <h4><i data-feather="check-circle" class="me-2"></i>Health Diagnosis Complete</h4>
                    <p class="text-muted">Analysis completed on ${new Date(diagnosis.analysis_timestamp).toLocaleDateString()}</p>
                </div>
                
                <div class="health-assessment-card">
                    <div class="assessment-header ${statusClass}">
                        <div class="status-indicator">
                            <i data-feather="${this.getStatusIcon(healthAssessment.overall_status)}" class="status-icon"></i>
                        </div>
                        <div class="status-details">
                            <h5>Overall Health Status</h5>
                            <p class="status-text">${this.formatStatus(healthAssessment.overall_status)}</p>
                            <div class="urgency-badge ${urgencyClass}">
                                ${this.formatUrgency(healthAssessment.urgency_level)}
                            </div>
                        </div>
                    </div>
                    
                    <div class="assessment-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6><i data-feather="target" class="me-2"></i>Primary Problem</h6>
                                <p>${healthAssessment.primary_problem || 'No specific problem identified'}</p>
                                ${this.options.showConfidenceScores ? `
                                    <div class="confidence-score">
                                        <small class="text-muted">Confidence: ${healthAssessment.confidence || 0}%</small>
                                        <div class="progress progress-sm mt-1">
                                            <div class="progress-bar bg-info" style="width: ${healthAssessment.confidence || 0}%"></div>
                                        </div>
                                    </div>
                                ` : ''}
                            </div>
                            <div class="col-md-6">
                                <h6><i data-feather="list" class="me-2"></i>Problem Classification</h6>
                                <p><strong>Type:</strong> ${this.formatProblemType(problemClassification.problem_type)}</p>
                                <p><strong>Severity:</strong> ${problemClassification.severity_score || 'Unknown'}/10</p>
                                ${problemClassification.affected_parts ? `
                                    <p><strong>Affected parts:</strong> ${problemClassification.affected_parts.join(', ')}</p>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
                
                ${treatmentPlan.immediate_actions ? this.renderTreatmentPlan(treatmentPlan) : ''}
                ${recoveryPrognosis.timeline_days ? this.renderRecoveryPrognosis(recoveryPrognosis) : ''}
                ${diagnosis.treatment_tracking ? this.renderTreatmentTracking(diagnosis.treatment_tracking) : ''}
                
                <div class="actions-section mt-4">
                    <div class="row">
                        <div class="col-md-6">
                            <button class="btn btn-primary w-100" onclick="window.print()">
                                <i data-feather="printer" class="me-2"></i>Print Diagnosis
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-outline-primary w-100" onclick="${this.containerId}Instance.resetWidget()">
                                <i data-feather="camera" class="me-2"></i>Diagnose Another Orchid
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderTreatmentPlan(treatmentPlan) {
        return `
            <div class="treatment-plan-card mt-4">
                <h5><i data-feather="shield" class="me-2"></i>Treatment Recommendations</h5>
                
                ${treatmentPlan.immediate_actions ? `
                    <div class="immediate-actions">
                        <h6 class="text-danger"><i data-feather="clock" class="me-2"></i>Immediate Actions (Next 24-48 hours)</h6>
                        <ul class="action-list">
                            ${treatmentPlan.immediate_actions.map(action => `<li>${action}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${treatmentPlan.specific_treatments ? `
                    <div class="specific-treatments mt-3">
                        <h6><i data-feather="zap" class="me-2"></i>Specific Treatments</h6>
                        <ul class="treatment-list">
                            ${treatmentPlan.specific_treatments.map(treatment => `<li>${treatment}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${treatmentPlan.product_recommendations ? `
                    <div class="product-recommendations mt-3">
                        <h6><i data-feather="shopping-cart" class="me-2"></i>Recommended Products</h6>
                        <ul class="product-list">
                            ${treatmentPlan.product_recommendations.map(product => `<li>${product}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${treatmentPlan.isolation_needed ? `
                    <div class="isolation-warning mt-3 p-3 bg-warning-subtle rounded">
                        <h6 class="text-warning"><i data-feather="alert-triangle" class="me-2"></i>Isolation Required</h6>
                        <p class="mb-0">This orchid should be isolated from other plants to prevent spread of the condition.</p>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    renderRecoveryPrognosis(recoveryPrognosis) {
        return `
            <div class="recovery-prognosis-card mt-4">
                <h5><i data-feather="trending-up" class="me-2"></i>Recovery Prognosis</h5>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="prognosis-stat">
                            <div class="stat-value">${recoveryPrognosis.timeline_days} days</div>
                            <div class="stat-label">Expected Recovery Time</div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="prognosis-stat">
                            <div class="stat-value">${recoveryPrognosis.success_probability}%</div>
                            <div class="stat-label">Success Probability</div>
                        </div>
                    </div>
                </div>
                
                ${recoveryPrognosis.improvement_signs ? `
                    <div class="improvement-signs mt-3">
                        <h6><i data-feather="eye" class="me-2"></i>Signs of Improvement to Watch For</h6>
                        <ul class="signs-list">
                            ${recoveryPrognosis.improvement_signs.map(sign => `<li>${sign}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    renderTreatmentTracking(tracking) {
        if (!this.options.enableTreatmentTracking) return '';
        
        return `
            <div class="treatment-tracking-card mt-4">
                <h5><i data-feather="calendar" class="me-2"></i>Treatment Schedule</h5>
                <p class="text-muted">Follow-up check-ins based on urgency level: <strong>${tracking.urgency_level}</strong></p>
                
                <div class="check-in-schedule">
                    <div class="timeline">
                        ${tracking.check_in_dates.map((date, index) => `
                            <div class="timeline-item">
                                <div class="timeline-marker"></div>
                                <div class="timeline-content">
                                    <div class="timeline-date">${new Date(date).toLocaleDateString()}</div>
                                    <div class="timeline-label">Check-in ${index + 1}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="tracking-info mt-3 p-3 bg-info-subtle rounded">
                    <small class="text-muted">
                        <i data-feather="info" class="me-2"></i>
                        Take photos on each check-in date to track progress. Upload them for comparison analysis.
                    </small>
                </div>
            </div>
        `;
    }
    
    getStatusClass(status) {
        const classes = {
            'healthy': 'status-healthy',
            'mild_issues': 'status-mild',
            'serious_problems': 'status-serious',
            'critical_condition': 'status-critical'
        };
        return classes[status] || 'status-unknown';
    }
    
    getStatusIcon(status) {
        const icons = {
            'healthy': 'check-circle',
            'mild_issues': 'alert-circle',
            'serious_problems': 'alert-triangle',
            'critical_condition': 'x-circle'
        };
        return icons[status] || 'help-circle';
    }
    
    getUrgencyClass(urgency) {
        const classes = {
            'low': 'badge bg-success',
            'medium': 'badge bg-warning',
            'high': 'badge bg-danger',
            'emergency': 'badge bg-danger blink'
        };
        return classes[urgency] || 'badge bg-secondary';
    }
    
    formatStatus(status) {
        const formats = {
            'healthy': 'Healthy Plant',
            'mild_issues': 'Mild Health Issues',
            'serious_problems': 'Serious Problems Detected',
            'critical_condition': 'Critical Condition'
        };
        return formats[status] || 'Status Unknown';
    }
    
    formatUrgency(urgency) {
        const formats = {
            'low': 'Low Priority',
            'medium': 'Medium Priority', 
            'high': 'High Priority',
            'emergency': 'EMERGENCY'
        };
        return formats[urgency] || 'Unknown';
    }
    
    formatProblemType(type) {
        const formats = {
            'disease': 'Disease/Pathogen',
            'pest': 'Pest Infestation',
            'environmental': 'Environmental Stress',
            'cultural': 'Cultural/Care Issue',
            'nutritional': 'Nutritional Deficiency'
        };
        return formats[type] || type || 'Unknown';
    }
    
    showError(message) {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').style.display = 'block';
    }
    
    resetWidget() {
        this.currentDiagnosis = null;
        this.treatmentTracking = null;
        
        document.getElementById('uploadSection').style.display = 'block';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        // Reset form
        document.getElementById('imageInput').value = '';
        document.getElementById('userNotes').value = '';
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('orchid-health-diagnostic-widget');
    if (container) {
        window.orchidHealthDiagnosticInstance = new OrchidHealthDiagnostic('orchid-health-diagnostic-widget');
    }
});

// Global access for integration
window.OrchidHealthDiagnostic = OrchidHealthDiagnostic;