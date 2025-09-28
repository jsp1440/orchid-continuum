/*!
 * Adaptive Care Calendar Widget
 * Dynamic orchid care scheduling that adapts to weather patterns and species needs
 * Part of The Orchid Continuum platform
 */

class AdaptiveCareCalendar {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            defaultDuration: 90,
            showWeatherIntegration: true,
            enableExports: true,
            maxTasksPerDay: 5,
            ...options
        };
        
        this.currentCalendar = null;
        this.templates = null;
        this.orchidDatabase = null;
        this.selectedOrchid = null;
        this.userPreferences = {
            skill_level: 'intermediate',
            max_daily_minutes: 30,
            available_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
            weather_integration: true
        };
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error(`Adaptive care calendar container not found: ${this.containerId}`);
            return;
        }
        
        this.render();
        this.attachEventListeners();
        this.loadInitialData();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="adaptive-care-calendar">
                <div class="calendar-header">
                    <div class="header-content">
                        <div class="header-icon">
                            <i data-feather="calendar" class="calendar-icon"></i>
                        </div>
                        <div class="header-text">
                            <h3>Adaptive Care Calendar</h3>
                            <p>Personalized orchid care schedules that adapt to weather and seasonal changes</p>
                        </div>
                    </div>
                </div>
                
                <div class="calendar-setup-section" id="setupSection">
                    <div class="setup-steps">
                        <!-- Step 1: Orchid Selection -->
                        <div class="setup-step active" data-step="1">
                            <div class="step-header">
                                <span class="step-number">1</span>
                                <h4>Select Your Orchid</h4>
                            </div>
                            <div class="step-content">
                                <div class="orchid-search-box">
                                    <input type="text" id="orchidSearch" class="form-control" 
                                           placeholder="Search for your orchid...">
                                    <div class="search-results" id="orchidResults"></div>
                                </div>
                                <div class="selected-orchid" id="selectedOrchid" style="display: none;">
                                    <div class="orchid-info-card">
                                        <div class="orchid-image">
                                            <img src="" alt="" class="orchid-photo">
                                            <div class="no-image"><i data-feather="flower"></i></div>
                                        </div>
                                        <div class="orchid-details">
                                            <h5 class="orchid-name"></h5>
                                            <p class="orchid-scientific"></p>
                                            <button type="button" class="btn btn-sm btn-outline-secondary clear-selection">
                                                <i data-feather="x" class="me-1"></i>Change
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 2: Calendar Settings -->
                        <div class="setup-step" data-step="2">
                            <div class="step-header">
                                <span class="step-number">2</span>
                                <h4>Calendar Settings</h4>
                            </div>
                            <div class="step-content">
                                <div class="row">
                                    <div class="col-md-6">
                                        <label class="form-label">Calendar Duration</label>
                                        <select class="form-select" id="durationSelect">
                                            <option value="30">1 Month (30 days)</option>
                                            <option value="60">2 Months (60 days)</option>
                                            <option value="90" selected>3 Months (90 days)</option>
                                            <option value="120">4 Months (120 days)</option>
                                            <option value="180">6 Months (180 days)</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label">Care Template</label>
                                        <select class="form-select" id="templateSelect">
                                            <option value="standard_care">Standard Care</option>
                                            <option value="beginner_friendly">Beginner Friendly</option>
                                            <option value="intensive_care">Intensive Care</option>
                                            <option value="seasonal_focus">Seasonal Focus</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="row mt-3">
                                    <div class="col-md-6">
                                        <label class="form-label">Your Experience Level</label>
                                        <select class="form-select" id="skillSelect">
                                            <option value="beginner">Beginner</option>
                                            <option value="intermediate" selected>Intermediate</option>
                                            <option value="advanced">Advanced</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label">Daily Time Available (minutes)</label>
                                        <select class="form-select" id="timeSelect">
                                            <option value="15">15 minutes</option>
                                            <option value="30" selected>30 minutes</option>
                                            <option value="45">45 minutes</option>
                                            <option value="60">1 hour</option>
                                            <option value="90">1.5 hours</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 3: Location & Weather -->
                        <div class="setup-step" data-step="3">
                            <div class="step-header">
                                <span class="step-number">3</span>
                                <h4>Location & Weather</h4>
                            </div>
                            <div class="step-content">
                                <div class="weather-integration">
                                    <div class="form-check form-switch mb-3">
                                        <input class="form-check-input" type="checkbox" id="weatherIntegration" checked>
                                        <label class="form-check-label" for="weatherIntegration">
                                            Enable weather-adaptive scheduling
                                        </label>
                                    </div>
                                    
                                    <div class="location-input">
                                        <label class="form-label">Your Location (for weather data)</label>
                                        <input type="text" class="form-control" id="locationInput" 
                                               placeholder="Enter city, state or zip code">
                                        <small class="form-text text-muted">
                                            Optional: Helps adapt watering and care based on local weather
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 4: Availability -->
                        <div class="setup-step" data-step="4">
                            <div class="step-header">
                                <span class="step-number">4</span>
                                <h4>Your Availability</h4>
                            </div>
                            <div class="step-content">
                                <div class="availability-selector">
                                    <label class="form-label">Days available for care tasks:</label>
                                    <div class="days-grid">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="monday" value="monday" checked>
                                            <label class="form-check-label" for="monday">Monday</label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="tuesday" value="tuesday" checked>
                                            <label class="form-check-label" for="tuesday">Tuesday</label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="wednesday" value="wednesday" checked>
                                            <label class="form-check-label" for="wednesday">Wednesday</label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="thursday" value="thursday" checked>
                                            <label class="form-check-label" for="thursday">Thursday</label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="friday" value="friday" checked>
                                            <label class="form-check-label" for="friday">Friday</label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="saturday" value="saturday" checked>
                                            <label class="form-check-label" for="saturday">Saturday</label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="sunday" value="sunday" checked>
                                            <label class="form-check-label" for="sunday">Sunday</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="setup-controls">
                        <div class="row">
                            <div class="col-md-4">
                                <button type="button" class="btn btn-outline-secondary w-100" id="prevStepBtn" disabled>
                                    <i data-feather="chevron-left" class="me-2"></i>Previous
                                </button>
                            </div>
                            <div class="col-md-4">
                                <button type="button" class="btn btn-outline-info w-100" id="nextStepBtn" disabled>
                                    Next<i data-feather="chevron-right" class="ms-2"></i>
                                </button>
                            </div>
                            <div class="col-md-4">
                                <button type="button" class="btn btn-primary w-100" id="generateCalendarBtn" disabled>
                                    <i data-feather="calendar-plus" class="me-2"></i>Generate Calendar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="calendar-progress" id="progressSection" style="display: none;">
                    <div class="progress-content">
                        <div class="progress-icon">
                            <div class="spinner-border text-primary" role="status"></div>
                        </div>
                        <h4>Generating Your Adaptive Care Calendar</h4>
                        <p id="progressText">Analyzing orchid needs and weather patterns...</p>
                        <div class="progress mt-3">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
                
                <div class="calendar-results" id="resultsSection" style="display: none;">
                    <!-- Results will be populated here -->
                </div>
                
                <div class="calendar-error" id="errorSection" style="display: none;">
                    <div class="alert alert-danger">
                        <i data-feather="alert-circle" class="me-2"></i>
                        <span id="errorMessage">An error occurred generating the calendar.</span>
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
        // Orchid search
        document.getElementById('orchidSearch')?.addEventListener('input', (e) => {
            this.searchOrchids(e.target.value);
        });
        
        // Step navigation
        document.getElementById('prevStepBtn')?.addEventListener('click', () => {
            this.previousStep();
        });
        
        document.getElementById('nextStepBtn')?.addEventListener('click', () => {
            this.nextStep();
        });
        
        // Generate calendar
        document.getElementById('generateCalendarBtn')?.addEventListener('click', () => {
            this.generateCalendar();
        });
        
        // Clear orchid selection
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('clear-selection') || 
                e.target.parentElement?.classList.contains('clear-selection')) {
                this.clearOrchidSelection();
            }
        });
        
        // Form changes
        ['durationSelect', 'templateSelect', 'skillSelect', 'timeSelect'].forEach(id => {
            document.getElementById(id)?.addEventListener('change', () => {
                this.updateUserPreferences();
            });
        });
        
        // Availability checkboxes
        document.querySelectorAll('.days-grid input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateUserPreferences();
            });
        });
        
        document.getElementById('retryBtn')?.addEventListener('click', () => {
            this.resetCalendar();
        });
    }
    
    async loadInitialData() {
        try {
            // Load orchid database
            await this.loadOrchidDatabase();
            
            // Load templates
            await this.loadTemplates();
            
            // Enable first step
            this.updateStepState();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }
    
    async loadOrchidDatabase() {
        try {
            const response = await fetch('/api/recent-orchids?limit=500');
            const data = await response.json();
            
            if (data && Array.isArray(data)) {
                this.orchidDatabase = data.map(orchid => ({
                    id: orchid.id,
                    display_name: orchid.display_name || `${orchid.genus} ${orchid.species}`,
                    genus: orchid.genus,
                    species: orchid.species,
                    scientific_name: orchid.scientific_name,
                    google_drive_id: orchid.google_drive_id
                }));
                console.log(`Loaded ${this.orchidDatabase.length} orchids for care calendar`);
            }
        } catch (error) {
            console.error('Error loading orchid database:', error);
        }
    }
    
    async loadTemplates() {
        try {
            const response = await fetch('/api/care-calendar-templates');
            const data = await response.json();
            
            if (data.success) {
                this.templates = data;
                this.populateTemplateSelector();
            }
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }
    
    populateTemplateSelector() {
        const select = document.getElementById('templateSelect');
        if (!select || !this.templates) return;
        
        select.innerHTML = '';
        
        Object.entries(this.templates.templates).forEach(([key, template]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = template.name;
            option.title = template.description;
            select.appendChild(option);
        });
    }
    
    searchOrchids(query) {
        if (!query || query.length < 2 || !this.orchidDatabase) {
            document.getElementById('orchidResults').innerHTML = '';
            return;
        }
        
        const results = this.orchidDatabase.filter(orchid => 
            orchid.display_name.toLowerCase().includes(query.toLowerCase()) ||
            orchid.genus.toLowerCase().includes(query.toLowerCase()) ||
            (orchid.species && orchid.species.toLowerCase().includes(query.toLowerCase()))
        ).slice(0, 10);
        
        const resultsContainer = document.getElementById('orchidResults');
        resultsContainer.innerHTML = results.map(orchid => `
            <div class="search-result" data-orchid-id="${orchid.id}">
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
                this.selectOrchid(orchidId);
            }
        });
        
        // Re-initialize Feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    selectOrchid(orchidId) {
        const orchid = this.orchidDatabase.find(o => o.id === orchidId);
        if (!orchid) return;
        
        this.selectedOrchid = orchid;
        
        // Update UI
        const searchBox = document.getElementById('orchidSearch');
        const resultsContainer = document.getElementById('orchidResults');
        const selectedContainer = document.getElementById('selectedOrchid');
        
        // Hide search, show selected
        searchBox.style.display = 'none';
        resultsContainer.innerHTML = '';
        selectedContainer.style.display = 'block';
        
        // Populate selected orchid info
        const nameElement = selectedContainer.querySelector('.orchid-name');
        const scientificElement = selectedContainer.querySelector('.orchid-scientific');
        const imageElement = selectedContainer.querySelector('.orchid-photo');
        const noImageElement = selectedContainer.querySelector('.no-image');
        
        nameElement.textContent = orchid.display_name;
        scientificElement.textContent = `${orchid.genus} ${orchid.species || 'hybrid'}`;
        
        if (orchid.google_drive_id) {
            imageElement.src = `/api/drive-photo/${orchid.google_drive_id}`;
            imageElement.alt = orchid.display_name;
            imageElement.style.display = 'block';
            noImageElement.style.display = 'none';
        } else {
            imageElement.style.display = 'none';
            noImageElement.style.display = 'block';
        }
        
        this.updateStepState();
    }
    
    clearOrchidSelection() {
        this.selectedOrchid = null;
        
        // Reset UI
        const searchBox = document.getElementById('orchidSearch');
        const resultsContainer = document.getElementById('orchidResults');
        const selectedContainer = document.getElementById('selectedOrchid');
        
        searchBox.style.display = 'block';
        searchBox.value = '';
        resultsContainer.innerHTML = '';
        selectedContainer.style.display = 'none';
        
        this.updateStepState();
    }
    
    updateStepState() {
        const prevBtn = document.getElementById('prevStepBtn');
        const nextBtn = document.getElementById('nextStepBtn');
        const generateBtn = document.getElementById('generateCalendarBtn');
        
        // Update button states based on current step and selections
        const currentStep = document.querySelector('.setup-step.active');
        const stepNumber = currentStep ? parseInt(currentStep.getAttribute('data-step')) : 1;
        
        prevBtn.disabled = stepNumber === 1;
        
        if (stepNumber === 1) {
            nextBtn.disabled = !this.selectedOrchid;
            generateBtn.disabled = true;
        } else if (stepNumber === 4) {
            nextBtn.disabled = true;
            generateBtn.disabled = !this.selectedOrchid;
        } else {
            nextBtn.disabled = !this.selectedOrchid;
            generateBtn.disabled = true;
        }
    }
    
    previousStep() {
        const currentStep = document.querySelector('.setup-step.active');
        if (!currentStep) return;
        
        const stepNumber = parseInt(currentStep.getAttribute('data-step'));
        if (stepNumber > 1) {
            currentStep.classList.remove('active');
            const prevStep = document.querySelector(`[data-step="${stepNumber - 1}"]`);
            if (prevStep) {
                prevStep.classList.add('active');
            }
        }
        
        this.updateStepState();
    }
    
    nextStep() {
        const currentStep = document.querySelector('.setup-step.active');
        if (!currentStep) return;
        
        const stepNumber = parseInt(currentStep.getAttribute('data-step'));
        if (stepNumber < 4) {
            currentStep.classList.remove('active');
            const nextStep = document.querySelector(`[data-step="${stepNumber + 1}"]`);
            if (nextStep) {
                nextStep.classList.add('active');
            }
        }
        
        this.updateStepState();
    }
    
    updateUserPreferences() {
        // Collect current form values
        const availableDays = [];
        document.querySelectorAll('.days-grid input[type="checkbox"]:checked').forEach(cb => {
            availableDays.push(cb.value);
        });
        
        this.userPreferences = {
            skill_level: document.getElementById('skillSelect')?.value || 'intermediate',
            max_daily_minutes: parseInt(document.getElementById('timeSelect')?.value) || 30,
            available_days: availableDays,
            weather_integration: document.getElementById('weatherIntegration')?.checked || false
        };
    }
    
    async generateCalendar() {
        try {
            if (!this.selectedOrchid) {
                this.showError('Please select an orchid first');
                return;
            }
            
            // Show progress
            this.showProgress('Generating your adaptive care calendar...');
            
            // Update preferences
            this.updateUserPreferences();
            
            const requestData = {
                orchid_id: this.selectedOrchid.id,
                duration_days: parseInt(document.getElementById('durationSelect')?.value) || 90,
                location: document.getElementById('locationInput')?.value || null,
                user_preferences: this.userPreferences
            };
            
            this.updateProgress(30, 'Analyzing orchid requirements...');
            
            const response = await fetch('/api/care-calendar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            this.updateProgress(70, 'Applying weather adaptations...');
            
            const result = await response.json();
            
            this.updateProgress(100, 'Finalizing your calendar...');
            
            if (result.success) {
                this.currentCalendar = result.calendar;
                setTimeout(() => {
                    this.showResults(result.calendar);
                }, 1000);
            } else {
                this.showError(result.error || 'Calendar generation failed');
            }
            
        } catch (error) {
            console.error('Calendar generation error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }
    
    showProgress(message) {
        document.getElementById('setupSection').style.display = 'none';
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
    
    showResults(calendar) {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.innerHTML = this.renderCalendarResults(calendar);
        resultsSection.style.display = 'block';
        
        // Initialize Feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    renderCalendarResults(calendar) {
        const summary = calendar.summary;
        const upcomingTasks = calendar.upcoming_tasks.slice(0, 14); // Next 2 weeks
        
        return `
            <div class="calendar-results-content">
                <div class="results-header">
                    <h4><i data-feather="calendar-check" class="me-2"></i>Your Adaptive Care Calendar</h4>
                    <p class="text-muted">
                        ${calendar.orchid_info.name} • ${calendar.schedule_period.duration_days} days
                    </p>
                </div>
                
                <div class="calendar-overview">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="stat-card">
                                <div class="stat-value">${summary.schedule_overview.total_tasks}</div>
                                <div class="stat-label">Total Tasks</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card">
                                <div class="stat-value">${summary.schedule_overview.tasks_per_week}</div>
                                <div class="stat-label">Tasks/Week</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card">
                                <div class="stat-value">${Math.round(summary.estimated_weekly_time / 7)}</div>
                                <div class="stat-label">Min/Day</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card">
                                <div class="stat-value ${this.getIntensityClass(summary.care_intensity)}">${summary.care_intensity}</div>
                                <div class="stat-label">Intensity</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="upcoming-tasks-section">
                    <h5><i data-feather="clock" class="me-2"></i>Upcoming Tasks (Next 2 Weeks)</h5>
                    <div class="tasks-list">
                        ${upcomingTasks.map(task => this.renderTaskCard(task)).join('')}
                    </div>
                </div>
                
                <div class="task-breakdown">
                    <h5><i data-feather="pie-chart" class="me-2"></i>Task Breakdown</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="breakdown-section">
                                <h6>By Priority</h6>
                                <div class="breakdown-items">
                                    ${Object.entries(summary.task_breakdown.by_priority).map(([priority, count]) => `
                                        <div class="breakdown-item">
                                            <span class="priority-badge ${priority}">${priority}</span>
                                            <span class="count">${count} tasks</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="breakdown-section">
                                <h6>By Activity</h6>
                                <div class="breakdown-items">
                                    ${Object.entries(summary.task_breakdown.by_action).slice(0, 5).map(([action, count]) => `
                                        <div class="breakdown-item">
                                            <span class="activity-badge">${action.replace('_', ' ')}</span>
                                            <span class="count">${count} tasks</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${calendar.weather_integration ? `
                    <div class="weather-info">
                        <div class="alert alert-info">
                            <i data-feather="cloud" class="me-2"></i>
                            <strong>Weather Integration Active:</strong> Your calendar will automatically adjust based on local weather conditions.
                            Tasks marked as weather-dependent will be modified based on rainfall, humidity, and temperature.
                        </div>
                    </div>
                ` : ''}
                
                <div class="calendar-actions">
                    <div class="row">
                        <div class="col-md-3">
                            <button class="btn btn-outline-primary w-100" onclick="${this.containerId}Instance.viewFullCalendar()">
                                <i data-feather="eye" class="me-2"></i>View Full Calendar
                            </button>
                        </div>
                        <div class="col-md-3">
                            <button class="btn btn-outline-success w-100" onclick="${this.containerId}Instance.exportCalendar('ical')">
                                <i data-feather="download" class="me-2"></i>Export iCal
                            </button>
                        </div>
                        <div class="col-md-3">
                            <button class="btn btn-outline-info w-100" onclick="${this.containerId}Instance.exportCalendar('csv')">
                                <i data-feather="file-text" class="me-2"></i>Export CSV
                            </button>
                        </div>
                        <div class="col-md-3">
                            <button class="btn btn-secondary w-100" onclick="${this.containerId}Instance.resetCalendar()">
                                <i data-feather="refresh-cw" class="me-2"></i>New Calendar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderTaskCard(task) {
        const dateObj = new Date(task.date);
        const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
        const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        
        return `
            <div class="task-card ${task.priority}">
                <div class="task-date">
                    <div class="day-name">${dayName}</div>
                    <div class="date-str">${dateStr}</div>
                    <div class="days-away">
                        ${task.days_from_now === 0 ? 'Today' : 
                          task.days_from_now === 1 ? 'Tomorrow' : 
                          `in ${task.days_from_now} days`}
                    </div>
                </div>
                <div class="task-content">
                    <div class="task-header">
                        <span class="task-action">${task.action.replace('_', ' ').toUpperCase()}</span>
                        <span class="task-duration">${task.duration_minutes}min</span>
                    </div>
                    <div class="task-description">${task.description}</div>
                </div>
                <div class="task-priority">
                    <span class="priority-indicator ${task.priority}"></span>
                </div>
            </div>
        `;
    }
    
    getIntensityClass(intensity) {
        const classes = {
            'low': 'text-success',
            'medium': 'text-warning',
            'high': 'text-danger'
        };
        return classes[intensity] || 'text-secondary';
    }
    
    viewFullCalendar() {
        if (!this.currentCalendar) return;
        
        // Create modal for full calendar view
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Complete Care Calendar</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="full-calendar-view">
                            ${this.renderFullCalendarView()}
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
    
    renderFullCalendarView() {
        const tasks = this.currentCalendar.tasks;
        
        // Group tasks by week
        const weeklyTasks = {};
        tasks.forEach(task => {
            const date = new Date(task.date);
            const weekStart = new Date(date);
            weekStart.setDate(date.getDate() - date.getDay());
            const weekKey = weekStart.toISOString().split('T')[0];
            
            if (!weeklyTasks[weekKey]) {
                weeklyTasks[weekKey] = [];
            }
            weeklyTasks[weekKey].push(task);
        });
        
        return `
            <div class="weekly-calendar">
                ${Object.entries(weeklyTasks).map(([weekStart, weekTasks]) => {
                    const startDate = new Date(weekStart);
                    const endDate = new Date(startDate);
                    endDate.setDate(startDate.getDate() + 6);
                    
                    return `
                        <div class="calendar-week">
                            <div class="week-header">
                                <h6>${startDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })} - 
                                    ${endDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}</h6>
                                <span class="task-count">${weekTasks.length} tasks</span>
                            </div>
                            <div class="week-tasks">
                                ${weekTasks.map(task => this.renderTaskCard(task)).join('')}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
    
    exportCalendar(format) {
        if (!this.currentCalendar || !this.currentCalendar.export_formats) return;
        
        const exportData = this.currentCalendar.export_formats[format];
        if (!exportData) {
            alert('Export format not available');
            return;
        }
        
        const filename = `orchid-care-calendar-${this.selectedOrchid.genus}-${format === 'ical' ? 'ics' : format}`;
        const mimeType = format === 'ical' ? 'text/calendar' : format === 'csv' ? 'text/csv' : 'application/json';
        
        const blob = new Blob([exportData], { type: mimeType });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    }
    
    showError(message) {
        document.getElementById('setupSection').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').style.display = 'block';
    }
    
    resetCalendar() {
        this.currentCalendar = null;
        this.clearOrchidSelection();
        
        // Reset all form fields
        document.getElementById('durationSelect').value = '90';
        document.getElementById('templateSelect').value = 'standard_care';
        document.getElementById('skillSelect').value = 'intermediate';
        document.getElementById('timeSelect').value = '30';
        document.getElementById('locationInput').value = '';
        document.getElementById('weatherIntegration').checked = true;
        
        // Reset all checkboxes
        document.querySelectorAll('.days-grid input[type="checkbox"]').forEach(cb => {
            cb.checked = true;
        });
        
        // Reset to first step
        document.querySelectorAll('.setup-step').forEach(step => {
            step.classList.remove('active');
        });
        document.querySelector('[data-step="1"]').classList.add('active');
        
        // Show setup section
        document.getElementById('setupSection').style.display = 'block';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        this.updateStepState();
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('adaptive-care-calendar-widget');
    if (container) {
        window.adaptiveCareCalendarInstance = new AdaptiveCareCalendar('adaptive-care-calendar-widget');
    }
});

// Global access for integration
window.AdaptiveCareCalendar = AdaptiveCareCalendar;