/*!
 * Breeding Compatibility Predictor Widget
 * AI-powered orchid breeding compatibility analysis and success rate prediction
 * Part of The Orchid Continuum platform
 */

class BreedingCompatibilityPredictor {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            enableAIAnalysis: true,
            showDetailedGenetics: true,
            maxPartnerSuggestions: 8,
            ...options
        };
        
        this.currentPrediction = null;
        this.orchidDatabase = null;
        this.selectedParents = {
            parent1: null,
            parent2: null
        };
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error(`Breeding predictor container not found: ${this.containerId}`);
            return;
        }
        
        this.render();
        this.attachEventListeners();
        this.loadOrchidDatabase();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="breeding-compatibility-predictor">
                <div class="predictor-header">
                    <div class="header-content">
                        <div class="header-icon">
                            <i data-feather="git-merge" class="predictor-icon"></i>
                        </div>
                        <div class="header-text">
                            <h3>AI Breeding Compatibility Predictor</h3>
                            <p>Predict breeding success rates and offspring characteristics using advanced genetic analysis</p>
                        </div>
                    </div>
                </div>
                
                <div class="predictor-setup-section" id="setupSection">
                    <div class="parent-selection">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="parent-selector" data-parent="1">
                                    <h5><i data-feather="flower" class="me-2"></i>Parent 1 (Seed Parent)</h5>
                                    <div class="orchid-search-box">
                                        <input type="text" id="parent1Search" class="form-control orchid-search" 
                                               placeholder="Search for first parent orchid...">
                                        <div class="search-results" id="parent1Results"></div>
                                    </div>
                                    <div class="selected-orchid" id="parent1Selected" style="display: none;">
                                        <div class="orchid-card">
                                            <div class="orchid-image">
                                                <img src="" alt="" class="parent-image">
                                            </div>
                                            <div class="orchid-info">
                                                <h6 class="orchid-name"></h6>
                                                <p class="orchid-scientific"></p>
                                                <button type="button" class="btn btn-sm btn-outline-secondary clear-parent">
                                                    <i data-feather="x" class="me-1"></i>Change
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div class="parent-selector" data-parent="2">
                                    <h5><i data-feather="flower" class="me-2"></i>Parent 2 (Pollen Parent)</h5>
                                    <div class="orchid-search-box">
                                        <input type="text" id="parent2Search" class="form-control orchid-search" 
                                               placeholder="Search for second parent orchid...">
                                        <div class="search-results" id="parent2Results"></div>
                                    </div>
                                    <div class="selected-orchid" id="parent2Selected" style="display: none;">
                                        <div class="orchid-card">
                                            <div class="orchid-image">
                                                <img src="" alt="" class="parent-image">
                                            </div>
                                            <div class="orchid-info">
                                                <h6 class="orchid-name"></h6>
                                                <p class="orchid-scientific"></p>
                                                <button type="button" class="btn btn-sm btn-outline-secondary clear-parent">
                                                    <i data-feather="x" class="me-1"></i>Change
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="breeding-options mt-4">
                        <h6><i data-feather="settings" class="me-2"></i>Analysis Options</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="aiAnalysisCheck" checked>
                                    <label class="form-check-label" for="aiAnalysisCheck">
                                        Include AI-powered genetic analysis
                                    </label>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="detailedGeneticsCheck" checked>
                                    <label class="form-check-label" for="detailedGeneticsCheck">
                                        Show detailed genetic predictions
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="analysis-controls mt-4">
                        <div class="row">
                            <div class="col-md-6">
                                <button type="button" class="btn btn-primary w-100" id="predictCompatibilityBtn" disabled>
                                    <i data-feather="zap" class="me-2"></i>Predict Breeding Compatibility
                                </button>
                            </div>
                            <div class="col-md-6">
                                <button type="button" class="btn btn-outline-info w-100" id="findPartnersBtn" disabled>
                                    <i data-feather="search" class="me-2"></i>Find Breeding Partners
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="predictor-progress" id="progressSection" style="display: none;">
                    <div class="progress-content">
                        <div class="progress-icon">
                            <div class="spinner-border text-primary" role="status"></div>
                        </div>
                        <h4>Analyzing Breeding Compatibility</h4>
                        <p id="progressText">Performing genetic compatibility analysis...</p>
                        <div class="progress mt-3">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
                
                <div class="predictor-results" id="resultsSection" style="display: none;">
                    <!-- Results will be populated here -->
                </div>
                
                <div class="partner-suggestions" id="partnerSection" style="display: none;">
                    <!-- Partner suggestions will be populated here -->
                </div>
                
                <div class="predictor-error" id="errorSection" style="display: none;">
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
        // Search functionality
        document.getElementById('parent1Search')?.addEventListener('input', (e) => {
            this.searchOrchids(e.target.value, 1);
        });
        
        document.getElementById('parent2Search')?.addEventListener('input', (e) => {
            this.searchOrchids(e.target.value, 2);
        });
        
        // Analysis buttons
        document.getElementById('predictCompatibilityBtn')?.addEventListener('click', () => {
            this.predictCompatibility();
        });
        
        document.getElementById('findPartnersBtn')?.addEventListener('click', () => {
            this.findBreedingPartners();
        });
        
        // Clear parent selections
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('clear-parent') || e.target.parentElement?.classList.contains('clear-parent')) {
                const parentNum = e.target.closest('.parent-selector').getAttribute('data-parent');
                this.clearParent(parseInt(parentNum));
            }
        });
        
        document.getElementById('retryBtn')?.addEventListener('click', () => {
            this.resetPredictor();
        });
    }
    
    async loadOrchidDatabase() {
        try {
            // Load basic orchid data for search functionality
            const response = await fetch('/api/recent-orchids?limit=1000');
            const data = await response.json();
            
            if (data && Array.isArray(data)) {
                this.orchidDatabase = data.map(orchid => ({
                    id: orchid.id,
                    display_name: orchid.display_name || `${orchid.genus} ${orchid.species}`,
                    genus: orchid.genus,
                    species: orchid.species,
                    google_drive_id: orchid.google_drive_id,
                    scientific_name: orchid.scientific_name
                }));
                console.log(`Loaded ${this.orchidDatabase.length} orchids for breeding analysis`);
            }
        } catch (error) {
            console.error('Error loading orchid database:', error);
        }
    }
    
    searchOrchids(query, parentNumber) {
        if (!query || query.length < 2 || !this.orchidDatabase) {
            document.getElementById(`parent${parentNumber}Results`).innerHTML = '';
            return;
        }
        
        const results = this.orchidDatabase.filter(orchid => 
            orchid.display_name.toLowerCase().includes(query.toLowerCase()) ||
            orchid.genus.toLowerCase().includes(query.toLowerCase()) ||
            (orchid.species && orchid.species.toLowerCase().includes(query.toLowerCase()))
        ).slice(0, 10);
        
        const resultsContainer = document.getElementById(`parent${parentNumber}Results`);
        resultsContainer.innerHTML = results.map(orchid => `
            <div class="search-result" data-orchid-id="${orchid.id}" data-parent="${parentNumber}">
                <div class="result-content">
                    <div class="result-image">
                        ${orchid.google_drive_id ? `
                            <img src="/api/drive-photo/${orchid.google_drive_id}" 
                                 alt="${orchid.display_name}" 
                                 onerror="this.style.display='none'">
                        ` : '<div class="no-image"><i data-feather="flower"></i></div>'}
                    </div>
                    <div class="result-info">
                        <h6>${orchid.display_name}</h6>
                        <p><em>${orchid.genus} ${orchid.species || 'hybrid'}</em></p>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Add click handlers for results
        resultsContainer.addEventListener('click', (e) => {
            const resultElement = e.target.closest('.search-result');
            if (resultElement) {
                const orchidId = parseInt(resultElement.getAttribute('data-orchid-id'));
                const parentNum = parseInt(resultElement.getAttribute('data-parent'));
                this.selectParent(orchidId, parentNum);
            }
        });
        
        // Re-initialize Feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    selectParent(orchidId, parentNumber) {
        const orchid = this.orchidDatabase.find(o => o.id === orchidId);
        if (!orchid) return;
        
        this.selectedParents[`parent${parentNumber}`] = orchid;
        
        // Update UI
        const searchBox = document.getElementById(`parent${parentNumber}Search`);
        const resultsContainer = document.getElementById(`parent${parentNumber}Results`);
        const selectedContainer = document.getElementById(`parent${parentNumber}Selected`);
        
        // Hide search, show selected
        searchBox.style.display = 'none';
        resultsContainer.innerHTML = '';
        selectedContainer.style.display = 'block';
        
        // Populate selected orchid info
        const nameElement = selectedContainer.querySelector('.orchid-name');
        const scientificElement = selectedContainer.querySelector('.orchid-scientific');
        const imageElement = selectedContainer.querySelector('.parent-image');
        
        nameElement.textContent = orchid.display_name;
        scientificElement.textContent = `${orchid.genus} ${orchid.species || 'hybrid'}`;
        
        if (orchid.google_drive_id) {
            imageElement.src = `/api/drive-photo/${orchid.google_drive_id}`;
            imageElement.alt = orchid.display_name;
            imageElement.style.display = 'block';
        } else {
            imageElement.style.display = 'none';
        }
        
        this.updateControlStates();
    }
    
    clearParent(parentNumber) {
        this.selectedParents[`parent${parentNumber}`] = null;
        
        // Reset UI
        const searchBox = document.getElementById(`parent${parentNumber}Search`);
        const resultsContainer = document.getElementById(`parent${parentNumber}Results`);
        const selectedContainer = document.getElementById(`parent${parentNumber}Selected`);
        
        searchBox.style.display = 'block';
        searchBox.value = '';
        resultsContainer.innerHTML = '';
        selectedContainer.style.display = 'none';
        
        this.updateControlStates();
    }
    
    updateControlStates() {
        const predictBtn = document.getElementById('predictCompatibilityBtn');
        const findPartnersBtn = document.getElementById('findPartnersBtn');
        
        const bothSelected = this.selectedParents.parent1 && this.selectedParents.parent2;
        const oneSelected = this.selectedParents.parent1 || this.selectedParents.parent2;
        
        predictBtn.disabled = !bothSelected;
        findPartnersBtn.disabled = !oneSelected;
    }
    
    async predictCompatibility() {
        try {
            if (!this.selectedParents.parent1 || !this.selectedParents.parent2) {
                this.showError('Please select both parent orchids');
                return;
            }
            
            // Show progress
            this.showProgress('Analyzing genetic compatibility...');
            
            const requestData = {
                parent1_id: this.selectedParents.parent1.id,
                parent2_id: this.selectedParents.parent2.id,
                include_ai_analysis: document.getElementById('aiAnalysisCheck').checked
            };
            
            const response = await fetch('/api/breeding-compatibility', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentPrediction = result.prediction;
                this.showResults(result.prediction);
            } else {
                this.showError(result.error || 'Breeding compatibility analysis failed');
            }
            
        } catch (error) {
            console.error('Compatibility prediction error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }
    
    async findBreedingPartners() {
        try {
            const targetParent = this.selectedParents.parent1 || this.selectedParents.parent2;
            if (!targetParent) {
                this.showError('Please select at least one parent orchid');
                return;
            }
            
            // Show progress
            this.showProgress('Finding optimal breeding partners...');
            
            const response = await fetch(`/api/breeding-partners/${targetParent.id}?max_suggestions=${this.options.maxPartnerSuggestions}`);
            const result = await response.json();
            
            if (result.success) {
                this.showPartnerSuggestions(result, targetParent);
            } else {
                this.showError(result.error || 'Breeding partner search failed');
            }
            
        } catch (error) {
            console.error('Partner search error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }
    
    showProgress(message) {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('partnerSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        document.getElementById('progressText').textContent = message;
        document.getElementById('progressSection').style.display = 'block';
        
        this.simulateProgress();
    }
    
    simulateProgress() {
        const progressBar = document.querySelector('.progress-bar');
        let width = 0;
        const interval = setInterval(() => {
            if (width < 90) {
                width += Math.random() * 20;
                progressBar.style.width = `${Math.min(width, 90)}%`;
            } else {
                clearInterval(interval);
            }
        }, 500);
    }
    
    showResults(prediction) {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('partnerSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.innerHTML = this.renderPredictionResults(prediction);
        resultsSection.style.display = 'block';
        
        // Initialize Feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    renderPredictionResults(prediction) {
        const analysis = prediction.compatibility_analysis;
        const predictions = prediction.predictions;
        const guidance = prediction.guidance;
        
        return `
            <div class="prediction-results">
                <div class="results-header">
                    <h4><i data-feather="check-circle" class="me-2"></i>Breeding Compatibility Analysis</h4>
                    <p class="text-muted">
                        ${prediction.parent1.name} × ${prediction.parent2.name}
                    </p>
                </div>
                
                <div class="compatibility-summary">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="metric-card compatibility-score">
                                <div class="metric-value ${this.getScoreColorClass(analysis.compatibility_score)}">
                                    ${analysis.compatibility_score}%
                                </div>
                                <div class="metric-label">Compatibility Score</div>
                                <div class="metric-status">${analysis.compatibility_level}</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-card success-rate">
                                <div class="metric-value ${this.getScoreColorClass(analysis.success_probability)}">
                                    ${analysis.success_probability}%
                                </div>
                                <div class="metric-label">Success Probability</div>
                                <div class="metric-status">Expected success rate</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-card difficulty">
                                <div class="metric-value ${this.getDifficultyColorClass(analysis.breeding_difficulty)}">
                                    ${analysis.breeding_difficulty.replace('_', ' ').toUpperCase()}
                                </div>
                                <div class="metric-label">Breeding Difficulty</div>
                                <div class="metric-status">${analysis.hybrid_vigor} vigor expected</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="prediction-details">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="detail-section">
                                <h5><i data-feather="calendar" class="me-2"></i>Timeline Predictions</h5>
                                <ul class="timeline-list">
                                    <li>Seed development: ${predictions.estimated_timeline.seed_development_months} months</li>
                                    <li>Germination: ${predictions.estimated_timeline.germination_days} days</li>
                                    <li>First flowering: ${predictions.estimated_timeline.first_flowering_years} years</li>
                                </ul>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="detail-section">
                                <h5><i data-feather="dna" class="me-2"></i>Predicted Traits</h5>
                                <ul class="traits-list">
                                    <li><strong>Growth habit:</strong> ${predictions.predicted_traits.growth_habit}</li>
                                    <li><strong>Temperature:</strong> ${predictions.predicted_traits.temperature_preference}</li>
                                    <li><strong>Fertility:</strong> ${predictions.predicted_traits.fertility_expectation}</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="guidance-sections">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="guidance-card advantages">
                                <h6><i data-feather="thumbs-up" class="me-2"></i>Breeding Advantages</h6>
                                <ul>
                                    ${guidance.breeding_advantages.map(adv => `<li>${adv}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="guidance-card challenges">
                                <h6><i data-feather="alert-triangle" class="me-2"></i>Potential Challenges</h6>
                                <ul>
                                    ${guidance.potential_challenges.map(chall => `<li>${chall}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${prediction.ai_analysis ? `
                    <div class="ai-analysis-section">
                        <h5><i data-feather="brain" class="me-2"></i>AI Expert Analysis</h5>
                        <div class="ai-analysis-content">
                            ${prediction.ai_analysis.split('\n').map(p => `<p>${p}</p>`).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="actions-section">
                    <div class="row">
                        <div class="col-md-4">
                            <button class="btn btn-outline-primary w-100" onclick="${this.containerId}Instance.resetPredictor()">
                                <i data-feather="refresh-cw" class="me-2"></i>New Analysis
                            </button>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-outline-info w-100" onclick="${this.containerId}Instance.showCareGuide()">
                                <i data-feather="book" class="me-2"></i>Breeding Guide
                            </button>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-success w-100" onclick="${this.containerId}Instance.exportPrediction()">
                                <i data-feather="download" class="me-2"></i>Save Results
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    showPartnerSuggestions(result, targetParent) {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        const partnerSection = document.getElementById('partnerSection');
        partnerSection.innerHTML = this.renderPartnerSuggestions(result, targetParent);
        partnerSection.style.display = 'block';
        
        // Initialize Feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    renderPartnerSuggestions(result, targetParent) {
        const partners = result.partner_suggestions || [];
        
        return `
            <div class="partner-suggestions-results">
                <div class="suggestions-header">
                    <h4><i data-feather="users" class="me-2"></i>Breeding Partners for ${targetParent.display_name}</h4>
                    <p class="text-muted">Found ${partners.length} compatible breeding partners</p>
                </div>
                
                <div class="partners-grid">
                    ${partners.map(partner => this.renderPartnerCard(partner)).join('')}
                </div>
                
                <div class="actions-section mt-4">
                    <button class="btn btn-outline-primary" onclick="${this.containerId}Instance.resetPredictor()">
                        <i data-feather="refresh-cw" class="me-2"></i>New Search
                    </button>
                </div>
            </div>
        `;
    }
    
    renderPartnerCard(partner) {
        return `
            <div class="partner-card">
                <div class="card">
                    ${partner.partner.image_id ? `
                        <img src="/api/drive-photo/${partner.partner.image_id}" 
                             class="card-img-top" alt="${partner.partner.name}"
                             onerror="this.style.display='none'">
                    ` : ''}
                    <div class="card-body">
                        <h5 class="card-title">${partner.partner.name}</h5>
                        <p class="text-muted">${partner.partner.genus} ${partner.partner.species}</p>
                        
                        <div class="compatibility-score mb-2">
                            <div class="score-header">
                                <span>Compatibility</span>
                                <span class="badge ${this.getScoreColorClass(partner.compatibility_score)}">${partner.compatibility_score}%</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar ${this.getScoreColorClass(partner.compatibility_score)}" 
                                     style="width: ${partner.compatibility_score}%"></div>
                            </div>
                        </div>
                        
                        <div class="partner-details">
                            <small class="d-block"><strong>Success rate:</strong> ${partner.success_probability}%</small>
                            <small class="d-block"><strong>Difficulty:</strong> ${partner.breeding_difficulty.replace('_', ' ')}</small>
                            <small class="d-block"><strong>Timeline:</strong> ${partner.timeline}</small>
                        </div>
                        
                        <div class="advantages mt-2">
                            <small class="text-muted">Key advantages:</small>
                            <ul class="small mb-2">
                                ${partner.advantages.map(adv => `<li>${adv}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <button class="btn btn-outline-primary btn-sm" 
                                onclick="${this.containerId}Instance.analyzePartnerPair(${partner.partner.id})">
                            <i data-feather="zap" class="me-1"></i>Analyze Cross
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    async analyzePartnerPair(partnerId) {
        const targetParent = this.selectedParents.parent1 || this.selectedParents.parent2;
        if (!targetParent) return;
        
        // Find partner orchid in database
        const partnerOrchid = this.orchidDatabase.find(o => o.id === partnerId);
        if (!partnerOrchid) return;
        
        // Set both parents and analyze
        this.selectedParents.parent1 = targetParent;
        this.selectedParents.parent2 = partnerOrchid;
        
        await this.predictCompatibility();
    }
    
    getScoreColorClass(score) {
        if (score >= 80) return 'text-success';
        if (score >= 60) return 'text-info';
        if (score >= 40) return 'text-warning';
        return 'text-danger';
    }
    
    getDifficultyColorClass(difficulty) {
        const classes = {
            'beginner': 'text-success',
            'intermediate': 'text-info',
            'advanced': 'text-warning',
            'expert_only': 'text-orange',
            'research_grade': 'text-danger'
        };
        return classes[difficulty] || 'text-secondary';
    }
    
    showCareGuide() {
        if (!this.currentPrediction) return;
        
        const guidance = this.currentPrediction.guidance;
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Breeding Care Guide</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="care-requirements">
                            <h6>Care Requirements:</h6>
                            <ul>
                                ${Object.entries(guidance.care_requirements).map(([key, value]) => `
                                    <li><strong>${key.replace('_', ' ')}:</strong> ${value}</li>
                                `).join('')}
                            </ul>
                        </div>
                        
                        <div class="breeding-tips mt-4">
                            <h6>Success Tips:</h6>
                            <ul>
                                <li>Ensure both parent plants are healthy and mature</li>
                                <li>Time pollination for optimal flower condition</li>
                                <li>Maintain sterile conditions throughout the process</li>
                                <li>Be patient - orchid breeding requires time and persistence</li>
                                <li>Keep detailed records of all breeding attempts</li>
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
    
    exportPrediction() {
        if (!this.currentPrediction) return;
        
        const dataStr = JSON.stringify(this.currentPrediction, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `breeding-prediction-${this.currentPrediction.parent1.name}-x-${this.currentPrediction.parent2.name}-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }
    
    showError(message) {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('partnerSection').style.display = 'none';
        
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').style.display = 'block';
    }
    
    resetPredictor() {
        this.currentPrediction = null;
        this.clearParent(1);
        this.clearParent(2);
        
        // Show setup section
        document.getElementById('setupSection').style.display = 'block';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('partnerSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('breeding-compatibility-predictor-widget');
    if (container) {
        window.breedingCompatibilityPredictorInstance = new BreedingCompatibilityPredictor('breeding-compatibility-predictor-widget');
    }
});

// Global access for integration
window.BreedingCompatibilityPredictor = BreedingCompatibilityPredictor;