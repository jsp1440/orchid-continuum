/*!
 * Personalized Growing Condition Matcher Widget
 * Matches users with optimal orchids based on location and growing conditions
 * Part of The Orchid Continuum platform
 */

class GrowingConditionMatcher {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            maxRecommendations: 8,
            showDetailedScoring: true,
            enableLocationDetection: true,
            ...options
        };
        
        this.currentRecommendations = null;
        this.userLocation = null;
        this.growingSetup = null;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error(`Growing condition matcher container not found: ${this.containerId}`);
            return;
        }
        
        this.render();
        this.attachEventListeners();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="growing-condition-matcher">
                <div class="matcher-header">
                    <div class="header-content">
                        <div class="header-icon">
                            <i data-feather="map-pin" class="matcher-icon"></i>
                        </div>
                        <div class="header-text">
                            <h3>Personalized Orchid Matcher</h3>
                            <p>Find the perfect orchids for your location and growing conditions</p>
                        </div>
                    </div>
                </div>
                
                <div class="matcher-setup-section" id="setupSection">
                    <div class="setup-wizard">
                        <div class="wizard-step active" data-step="1">
                            <h4><i data-feather="map-pin" class="me-2"></i>Your Location</h4>
                            <p>Enter your location for climate analysis</p>
                            
                            <div class="location-input-group">
                                <div class="row">
                                    <div class="col-md-8">
                                        <input type="text" id="locationInput" class="form-control" 
                                               placeholder="City, State, ZIP code, or coordinates">
                                    </div>
                                    <div class="col-md-4">
                                        <button type="button" class="btn btn-outline-primary w-100" id="detectLocationBtn">
                                            <i data-feather="navigation" class="me-2"></i>Detect Location
                                        </button>
                                    </div>
                                </div>
                                <small class="text-muted mt-2">Examples: "New York, NY", "90210", or "40.7128, -74.0060"</small>
                            </div>
                        </div>
                        
                        <div class="wizard-step" data-step="2">
                            <h4><i data-feather="home" class="me-2"></i>Growing Environment</h4>
                            <p>Describe your growing setup</p>
                            
                            <div class="environment-options">
                                <div class="row">
                                    <div class="col-md-6">
                                        <label class="form-label">Growing Environment:</label>
                                        <select id="environmentSelect" class="form-select">
                                            <option value="windowsill">Windowsill</option>
                                            <option value="indoor_lights">Indoor with grow lights</option>
                                            <option value="greenhouse">Greenhouse</option>
                                            <option value="outdoor">Outdoor growing</option>
                                            <option value="conservatory">Conservatory</option>
                                            <option value="terrarium">Terrarium/Vivarium</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label">Space Available:</label>
                                        <select id="spaceSizeSelect" class="form-select">
                                            <option value="small">Small (windowsill, few plants)</option>
                                            <option value="medium">Medium (dedicated area)</option>
                                            <option value="large">Large (room/greenhouse)</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="row mt-3">
                                    <div class="col-md-6">
                                        <label class="form-label">Experience Level:</label>
                                        <select id="experienceSelect" class="form-select">
                                            <option value="beginner">Beginner (new to orchids)</option>
                                            <option value="intermediate">Intermediate (some experience)</option>
                                            <option value="advanced">Advanced (multiple years)</option>
                                            <option value="expert">Expert (extensive knowledge)</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label">Light Hours (if using grow lights):</label>
                                        <input type="number" id="lightHoursInput" class="form-control" 
                                               placeholder="12-16 hours" min="0" max="24">
                                    </div>
                                </div>
                                
                                <div class="supplemental-systems mt-4">
                                    <h6>Available Equipment:</h6>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="heatingCheck">
                                                <label class="form-check-label" for="heatingCheck">
                                                    Supplemental heating
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="humidityCheck">
                                                <label class="form-check-label" for="humidityCheck">
                                                    Humidity control
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="circulationCheck">
                                                <label class="form-check-label" for="circulationCheck">
                                                    Air circulation fans
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="wizard-step" data-step="3">
                            <h4><i data-feather="settings" class="me-2"></i>Preferences</h4>
                            <p>Optional preferences to refine recommendations</p>
                            
                            <div class="preferences-options">
                                <div class="row">
                                    <div class="col-md-6">
                                        <label class="form-label">Budget Range:</label>
                                        <select id="budgetSelect" class="form-select">
                                            <option value="">No preference</option>
                                            <option value="low">Budget-conscious</option>
                                            <option value="medium">Moderate investment</option>
                                            <option value="high">Premium options</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label">Max Recommendations:</label>
                                        <select id="maxRecommendationsSelect" class="form-select">
                                            <option value="5">5 orchids</option>
                                            <option value="8" selected>8 orchids</option>
                                            <option value="12">12 orchids</option>
                                            <option value="15">15 orchids</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="mt-3">
                                    <label class="form-label">Bloom Timing Preference:</label>
                                    <select id="bloomTimingSelect" class="form-select">
                                        <option value="">No preference</option>
                                        <option value="spring">Spring blooming</option>
                                        <option value="summer">Summer blooming</option>
                                        <option value="fall">Fall blooming</option>
                                        <option value="winter">Winter blooming</option>
                                        <option value="multiple">Multiple seasons</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="wizard-navigation">
                        <button type="button" class="btn btn-secondary" id="prevStepBtn" style="display: none;">
                            <i data-feather="chevron-left" class="me-2"></i>Previous
                        </button>
                        <button type="button" class="btn btn-primary" id="nextStepBtn">
                            Next<i data-feather="chevron-right" class="ms-2"></i>
                        </button>
                        <button type="button" class="btn btn-success" id="findOrchidsBtn" style="display: none;">
                            <i data-feather="search" class="me-2"></i>Find My Perfect Orchids
                        </button>
                    </div>
                </div>
                
                <div class="matcher-progress" id="progressSection" style="display: none;">
                    <div class="progress-content">
                        <div class="progress-icon">
                            <div class="spinner-border text-primary" role="status"></div>
                        </div>
                        <h4>Finding Your Perfect Orchids</h4>
                        <p id="progressText">Analyzing your location and growing conditions...</p>
                        <div class="progress mt-3">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
                
                <div class="matcher-results" id="resultsSection" style="display: none;">
                    <!-- Results will be populated here -->
                </div>
                
                <div class="matcher-error" id="errorSection" style="display: none;">
                    <div class="alert alert-danger">
                        <i data-feather="alert-circle" class="me-2"></i>
                        <span id="errorMessage">An error occurred during analysis.</span>
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
        const nextStepBtn = document.getElementById('nextStepBtn');
        const prevStepBtn = document.getElementById('prevStepBtn');
        const findOrchidsBtn = document.getElementById('findOrchidsBtn');
        const detectLocationBtn = document.getElementById('detectLocationBtn');
        const retryBtn = document.getElementById('retryBtn');
        
        nextStepBtn?.addEventListener('click', this.nextStep.bind(this));
        prevStepBtn?.addEventListener('click', this.previousStep.bind(this));
        findOrchidsBtn?.addEventListener('click', this.findOrchids.bind(this));
        detectLocationBtn?.addEventListener('click', this.detectLocation.bind(this));
        retryBtn?.addEventListener('click', this.resetMatcher.bind(this));
        
        // Auto-detect location on load if enabled
        if (this.options.enableLocationDetection) {
            this.detectLocation(false); // Silent detection
        }
    }
    
    nextStep() {
        const currentStep = document.querySelector('.wizard-step.active');
        const stepNumber = parseInt(currentStep.getAttribute('data-step'));
        
        // Validate current step
        if (!this.validateStep(stepNumber)) {
            return;
        }
        
        if (stepNumber < 3) {
            // Move to next step
            currentStep.classList.remove('active');
            document.querySelector(`[data-step="${stepNumber + 1}"]`).classList.add('active');
            
            // Update navigation buttons
            document.getElementById('prevStepBtn').style.display = 'inline-block';
            
            if (stepNumber + 1 === 3) {
                document.getElementById('nextStepBtn').style.display = 'none';
                document.getElementById('findOrchidsBtn').style.display = 'inline-block';
            }
        }
    }
    
    previousStep() {
        const currentStep = document.querySelector('.wizard-step.active');
        const stepNumber = parseInt(currentStep.getAttribute('data-step'));
        
        if (stepNumber > 1) {
            // Move to previous step
            currentStep.classList.remove('active');
            document.querySelector(`[data-step="${stepNumber - 1}"]`).classList.add('active');
            
            // Update navigation buttons
            if (stepNumber - 1 === 1) {
                document.getElementById('prevStepBtn').style.display = 'none';
            }
            
            document.getElementById('nextStepBtn').style.display = 'inline-block';
            document.getElementById('findOrchidsBtn').style.display = 'none';
        }
    }
    
    validateStep(stepNumber) {
        switch (stepNumber) {
            case 1:
                const locationInput = document.getElementById('locationInput').value.trim();
                if (!locationInput) {
                    this.showError('Please enter your location');
                    return false;
                }
                break;
            case 2:
                // All fields are pre-selected with defaults, so validation passes
                break;
            case 3:
                // Preferences are optional
                break;
        }
        return true;
    }
    
    async detectLocation(showErrors = true) {
        try {
            if (!navigator.geolocation) {
                if (showErrors) {
                    this.showError('Geolocation is not supported by this browser');
                }
                return;
            }
            
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000
                });
            });
            
            const lat = position.coords.latitude.toFixed(4);
            const lon = position.coords.longitude.toFixed(4);
            document.getElementById('locationInput').value = `${lat}, ${lon}`;
            
            if (showErrors) {
                this.showSuccess('Location detected successfully!');
            }
            
        } catch (error) {
            if (showErrors) {
                this.showError('Unable to detect location. Please enter manually.');
            }
        }
    }
    
    async findOrchids() {
        try {
            // Collect all form data
            const formData = this.collectFormData();
            
            if (!this.validateFormData(formData)) {
                return;
            }
            
            // Show progress
            this.showProgress();
            
            // Make API request
            const response = await fetch('/api/growing-condition-matcher', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentRecommendations = result;
                this.showResults(result);
            } else {
                this.showError(result.error || 'Analysis failed');
            }
            
        } catch (error) {
            console.error('Orchid matching error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }
    
    collectFormData() {
        return {
            location: document.getElementById('locationInput').value.trim(),
            growing_setup: {
                environment: document.getElementById('environmentSelect').value,
                space_size: document.getElementById('spaceSizeSelect').value,
                experience_level: document.getElementById('experienceSelect').value,
                light_hours: parseInt(document.getElementById('lightHoursInput').value) || null,
                supplemental_heating: document.getElementById('heatingCheck').checked,
                humidity_control: document.getElementById('humidityCheck').checked,
                air_circulation: document.getElementById('circulationCheck').checked,
                budget_range: document.getElementById('budgetSelect').value || null,
                bloom_timing_preference: document.getElementById('bloomTimingSelect').value || null
            },
            max_recommendations: parseInt(document.getElementById('maxRecommendationsSelect').value) || 8
        };
    }
    
    validateFormData(formData) {
        if (!formData.location) {
            this.showError('Location is required');
            return false;
        }
        return true;
    }
    
    showProgress() {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'block';
        
        this.simulateProgress();
    }
    
    simulateProgress() {
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.getElementById('progressText');
        
        const steps = [
            { progress: 20, text: 'Analyzing your location...' },
            { progress: 40, text: 'Retrieving climate data...' },
            { progress: 60, text: 'Matching orchids to conditions...' },
            { progress: 80, text: 'Scoring compatibility...' },
            { progress: 95, text: 'Preparing recommendations...' }
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
    
    showResults(result) {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.innerHTML = this.renderResults(result);
        resultsSection.style.display = 'block';
        
        // Initialize Feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    renderResults(result) {
        const recommendations = result.recommendations || [];
        const location = result.location || {};
        const insights = result.care_insights || {};
        
        return `
            <div class="results-content">
                <div class="results-header">
                    <h4><i data-feather="check-circle" class="me-2"></i>Perfect Orchids Found!</h4>
                    <p class="text-muted">Personalized recommendations for ${location.name}</p>
                    <div class="climate-summary">
                        <small class="badge bg-info">${location.climate_summary?.climate_zone || 'Climate analyzed'}</small>
                        <small class="badge bg-success">${recommendations.length} matches found</small>
                    </div>
                </div>
                
                <div class="recommendations-grid">
                    ${recommendations.map(rec => this.renderRecommendationCard(rec)).join('')}
                </div>
                
                ${insights ? this.renderInsights(insights) : ''}
                ${result.seasonal_calendar ? this.renderSeasonalCalendar(result.seasonal_calendar) : ''}
                
                <div class="actions-section mt-4">
                    <div class="row">
                        <div class="col-md-6">
                            <button class="btn btn-outline-primary w-100" onclick="${this.containerId}Instance.resetMatcher()">
                                <i data-feather="refresh-cw" class="me-2"></i>Find Different Orchids
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-success w-100" onclick="${this.containerId}Instance.exportResults()">
                                <i data-feather="download" class="me-2"></i>Save Recommendations
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderRecommendationCard(rec) {
        const orchid = rec.orchid;
        const analysis = rec.match_analysis;
        
        return `
            <div class="recommendation-card">
                <div class="card">
                    ${orchid.google_drive_id ? `
                        <img src="/api/drive-photo/${orchid.google_drive_id}" 
                             class="card-img-top" alt="${orchid.display_name}"
                             onerror="this.style.display='none'">
                    ` : ''}
                    <div class="card-body">
                        <h5 class="card-title">${orchid.display_name || orchid.scientific_name}</h5>
                        <p class="text-muted">${orchid.genus} ${orchid.species}</p>
                        
                        <div class="match-score mb-3">
                            <div class="score-header">
                                <span class="score-label">Match Score</span>
                                <span class="score-value">${analysis.overall_score}%</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar ${this.getScoreColorClass(analysis.overall_score)}" 
                                     style="width: ${analysis.overall_score}%"></div>
                            </div>
                        </div>
                        
                        <div class="compatibility-breakdown mb-3">
                            <small class="text-muted d-block">Compatibility Breakdown:</small>
                            <div class="breakdown-item">
                                <i data-feather="thermometer" class="breakdown-icon"></i>
                                Climate: ${analysis.climate_compatibility}%
                            </div>
                            <div class="breakdown-item">
                                <i data-feather="home" class="breakdown-icon"></i>
                                Environment: ${analysis.environment_suitability}%
                            </div>
                            <div class="breakdown-item">
                                <i data-feather="user" class="breakdown-icon"></i>
                                Experience: ${analysis.experience_match}%
                            </div>
                        </div>
                        
                        <div class="care-difficulty mb-3">
                            <span class="badge ${this.getDifficultyColorClass(analysis.care_difficulty)}"}>
                                ${analysis.care_difficulty_name}
                            </span>
                        </div>
                        
                        <div class="recommendation-reasons">
                            <h6><i data-feather="star" class="me-2"></i>Why This Orchid:</h6>
                            <ul class="reasons-list">
                                ${rec.recommendations.reasons.map(reason => `<li>${reason}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <button class="btn btn-outline-primary btn-sm" onclick="${this.containerId}Instance.showDetailedInfo('${orchid.id}')">
                            <i data-feather="info" class="me-2"></i>Care Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderInsights(insights) {
        return `
            <div class="care-insights-section mt-4">
                <h5><i data-feather="lightbulb" class="me-2"></i>Growing Insights</h5>
                
                <div class="insights-grid">
                    <div class="insight-card">
                        <h6>Climate Overview</h6>
                        <p>${insights.climate_overview || 'Climate analysis completed'}</p>
                    </div>
                    
                    ${insights.setup_optimization ? `
                        <div class="insight-card">
                            <h6>Setup Optimization</h6>
                            <ul>
                                ${insights.setup_optimization.map(tip => `<li>${tip}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${insights.success_tips ? `
                        <div class="insight-card">
                            <h6>Success Tips</h6>
                            <ul>
                                ${insights.success_tips.map(tip => `<li>${tip}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    renderSeasonalCalendar(calendar) {
        const seasons = ['spring', 'summer', 'fall', 'winter'];
        
        return `
            <div class="seasonal-calendar-section mt-4">
                <h5><i data-feather="calendar" class="me-2"></i>Seasonal Care Calendar</h5>
                
                <div class="row">
                    ${seasons.map(season => `
                        <div class="col-md-3">
                            <div class="season-card">
                                <h6 class="season-title">${season.charAt(0).toUpperCase() + season.slice(1)}</h6>
                                <div class="season-priorities">
                                    <strong>Priorities:</strong>
                                    <ul class="small">
                                        ${calendar[season]?.priorities?.map(p => `<li>${p}</li>`).join('') || '<li>Standard care</li>'}
                                    </ul>
                                </div>
                                <div class="season-watch">
                                    <strong>Watch for:</strong>
                                    <ul class="small">
                                        ${calendar[season]?.watch_for?.map(w => `<li>${w}</li>`).join('') || '<li>Normal growth</li>'}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    getScoreColorClass(score) {
        if (score >= 80) return 'bg-success';
        if (score >= 60) return 'bg-info';
        if (score >= 40) return 'bg-warning';
        return 'bg-danger';
    }
    
    getDifficultyColorClass(difficulty) {
        const classes = {
            1: 'bg-success',
            2: 'bg-info',
            3: 'bg-warning',
            4: 'bg-orange',
            5: 'bg-danger'
        };
        return classes[difficulty] || 'bg-secondary';
    }
    
    showDetailedInfo(orchidId) {
        // Find the orchid in current recommendations
        const orchid = this.currentRecommendations?.recommendations?.find(r => r.orchid.id == orchidId);
        if (!orchid) return;
        
        // Create modal or expand card with detailed care info
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${orchid.orchid.display_name} - Care Details</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="care-tips-section">
                            <h6>Personalized Care Tips:</h6>
                            <ul>
                                ${orchid.recommendations.care_tips.map(tip => `<li>${tip}</li>`).join('')}
                            </ul>
                        </div>
                        
                        ${orchid.recommendations.potential_challenges.length > 0 ? `
                            <div class="challenges-section mt-3">
                                <h6>Potential Challenges:</h6>
                                <ul>
                                    ${orchid.recommendations.potential_challenges.map(challenge => `<li>${challenge}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        
                        <div class="success-indicators-section mt-3">
                            <h6>Signs of Success:</h6>
                            <ul>
                                ${orchid.recommendations.success_indicators.map(sign => `<li>${sign}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        new bootstrap.Modal(modal).show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }
    
    exportResults() {
        if (!this.currentRecommendations) return;
        
        const dataStr = JSON.stringify(this.currentRecommendations, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `orchid-recommendations-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }
    
    showError(message) {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').style.display = 'block';
    }
    
    showSuccess(message) {
        // Show temporary success message (could implement toast notification)
        console.log('Success:', message);
    }
    
    resetMatcher() {
        this.currentRecommendations = null;
        
        // Reset to first step
        document.querySelectorAll('.wizard-step').forEach(step => step.classList.remove('active'));
        document.querySelector('[data-step="1"]').classList.add('active');
        
        // Reset navigation
        document.getElementById('prevStepBtn').style.display = 'none';
        document.getElementById('nextStepBtn').style.display = 'inline-block';
        document.getElementById('findOrchidsBtn').style.display = 'none';
        
        // Show setup section
        document.getElementById('setupSection').style.display = 'block';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('growing-condition-matcher-widget');
    if (container) {
        window.growingConditionMatcherInstance = new GrowingConditionMatcher('growing-condition-matcher-widget');
    }
});

// Global access for integration
window.GrowingConditionMatcher = GrowingConditionMatcher;