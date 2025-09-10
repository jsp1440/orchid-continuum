/**
 * Judging Systems for FCOS Orchid Judge
 * Handles AOS, AOC, NZ, and RHS educational scoring rubrics
 */

class JudgingSystems {
    constructor() {
        this.currentSystem = 'AOS';
        this.rubrics = this.initializeRubrics();
        this.scores = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSavedScores();
    }

    setupEventListeners() {
        // Judging system picker
        document.getElementById('judging-system-picker')?.addEventListener('change', (e) => {
            this.switchJudgingSystem(e.target.value);
        });

        // Score inputs
        document.addEventListener('input', (e) => {
            if (e.target.matches('.score-input')) {
                this.updateScore(e.target);
            }
        });

        // AI suggest button
        document.getElementById('ai-suggest-scores-btn')?.addEventListener('click', () => {
            this.suggestScoresFromAI();
        });

        // Reset scores button
        document.getElementById('reset-scores-btn')?.addEventListener('click', () => {
            this.resetScores();
        });
    }

    initializeRubrics() {
        return {
            "AOS": {
                "name": "American Orchid Society (Educational)",
                "sections": [
                    {"key":"form","label":"Form / Symmetry / Balance","weight":0.30,"maxScore":30},
                    {"key":"color","label":"Color & Saturation","weight":0.15,"maxScore":15},
                    {"key":"size","label":"Size / Substance","weight":0.15,"maxScore":15},
                    {"key":"floriferous","label":"Floriferousness & Arrangement","weight":0.20,"maxScore":20},
                    {"key":"condition","label":"Condition & Grooming","weight":0.10,"maxScore":10},
                    {"key":"distinct","label":"Distinctiveness / Impression","weight":0.10,"maxScore":10}
                ],
                "awardBands":[
                    {"label":"HCC (educational)","min":75,"max":79,"color":"#ffd700"},
                    {"label":"AM (educational)","min":80,"max":89,"color":"#c0c0c0"},
                    {"label":"FCC (educational)","min":90,"max":100,"color":"#cd7f32"}
                ],
                "totalScore": 100
            },
            "AOC": {
                "name": "Australian Orchid Council (Educational)",
                "sections": [
                    {"key":"form","label":"Form / Symmetry","weight":0.30,"maxScore":30},
                    {"key":"color","label":"Color","weight":0.20,"maxScore":20},
                    {"key":"size","label":"Size / Substance","weight":0.15,"maxScore":15},
                    {"key":"floriferous","label":"Floriferousness","weight":0.20,"maxScore":20},
                    {"key":"condition","label":"Condition","weight":0.10,"maxScore":10},
                    {"key":"distinct","label":"Distinctiveness","weight":0.05,"maxScore":5}
                ],
                "awardBands":[
                    {"label":"Award range A (edu)","min":75,"max":79,"color":"#ffd700"},
                    {"label":"Award range B (edu)","min":80,"max":89,"color":"#c0c0c0"},
                    {"label":"Award range C (edu)","min":90,"max":100,"color":"#cd7f32"}
                ],
                "totalScore": 100
            },
            "NZ": {
                "name": "New Zealand Orchid Society (Educational)",
                "sections": [
                    {"key":"form","label":"Form / Symmetry","weight":0.35,"maxScore":35},
                    {"key":"color","label":"Color & Pattern","weight":0.20,"maxScore":20},
                    {"key":"size","label":"Size & Substance","weight":0.15,"maxScore":15},
                    {"key":"floriferous","label":"Floral Arrangement","weight":0.15,"maxScore":15},
                    {"key":"condition","label":"Condition","weight":0.10,"maxScore":10},
                    {"key":"distinct","label":"Distinction","weight":0.05,"maxScore":5}
                ],
                "awardBands":[
                    {"label":"Bronze (edu)","min":70,"max":79,"color":"#cd7f32"},
                    {"label":"Silver (edu)","min":80,"max":89,"color":"#c0c0c0"},
                    {"label":"Gold (edu)","min":90,"max":100,"color":"#ffd700"}
                ],
                "totalScore": 100
            },
            "RHS": {
                "name": "Royal Horticultural Society (Educational)",
                "sections": [
                    {"key":"form","label":"Form & Substance","weight":0.25,"maxScore":25},
                    {"key":"color","label":"Colour & Markings","weight":0.20,"maxScore":20},
                    {"key":"size","label":"Size","weight":0.15,"maxScore":15},
                    {"key":"floriferous","label":"Floriferousness","weight":0.20,"maxScore":20},
                    {"key":"condition","label":"Condition & Staging","weight":0.15,"maxScore":15},
                    {"key":"distinct","label":"Distinction & Character","weight":0.05,"maxScore":5}
                ],
                "awardBands":[
                    {"label":"Bronze Medal (edu)","min":70,"max":79,"color":"#cd7f32"},
                    {"label":"Silver Medal (edu)","min":80,"max":89,"color":"#c0c0c0"},
                    {"label":"Gold Medal (edu)","min":90,"max":100,"color":"#ffd700"}
                ],
                "totalScore": 100
            }
        };
    }

    displayScoringInterface() {
        const container = document.getElementById('scoring-interface');
        if (!container) return;

        const currentRubric = this.rubrics[this.currentSystem];

        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>Educational Scoring System</h3>
                    <div class="system-picker">
                        <label for="judging-system-picker">Judging System:</label>
                        <select id="judging-system-picker" class="form-input">
                            ${Object.keys(this.rubrics).map(key => 
                                `<option value="${key}" ${key === this.currentSystem ? 'selected' : ''}>
                                    ${this.rubrics[key].name}
                                </option>`
                            ).join('')}
                        </select>
                    </div>
                </div>

                <div class="educational-disclaimer">
                    <strong>Educational Practice Only:</strong> These scores are for learning purposes and do not represent official judging.
                </div>

                <div class="scoring-sections">
                    ${currentRubric.sections.map(section => this.renderScoringSection(section)).join('')}
                </div>

                <div class="scoring-summary">
                    <div class="total-score">
                        <label>Total Score</label>
                        <div class="total-display">
                            <span id="total-score-value">0</span>
                            <span class="total-max">/ ${currentRubric.totalScore}</span>
                        </div>
                    </div>

                    <div class="award-bands">
                        <h4>Award Bands (Educational)</h4>
                        <div class="bands-list">
                            ${currentRubric.awardBands.map(band => 
                                `<div class="award-band" data-min="${band.min}" data-max="${band.max}" 
                                      style="border-color: ${band.color}">
                                    <div class="band-label">${band.label}</div>
                                    <div class="band-range">${band.min}-${band.max} points</div>
                                </div>`
                            ).join('')}
                        </div>
                    </div>
                </div>

                <div class="scoring-notes">
                    <h4>Judge's Notes</h4>
                    <textarea id="judges-notes" class="form-input" rows="4" 
                              placeholder="Enter your educational observations and comments about the plant..."></textarea>
                </div>

                <div class="scoring-actions">
                    <button id="ai-suggest-scores-btn" class="btn btn-secondary">
                        AI Suggest Scores
                    </button>
                    <button id="reset-scores-btn" class="btn btn-outline">
                        Reset All Scores
                    </button>
                    <button id="save-scores-btn" class="btn btn-primary">
                        Save & Continue
                    </button>
                </div>
            </div>
        `;

        // Bind new event listeners
        this.bindScoringEvents();
        
        // Load any existing scores
        this.loadScoresIntoInterface();
        
        // Update total score
        this.updateTotalScore();
    }

    renderScoringSection(section) {
        const currentScore = this.scores[section.key] || 0;
        const aiSuggestion = this.getAISuggestionForSection(section.key);
        
        return `
            <div class="scoring-section" data-section="${section.key}">
                <div class="section-header">
                    <h4>${section.label}</h4>
                    <div class="section-weight">Weight: ${Math.round(section.weight * 100)}%</div>
                </div>
                
                <div class="section-scoring">
                    <div class="score-input-group">
                        <input type="number" 
                               class="score-input" 
                               id="score-${section.key}"
                               data-section="${section.key}"
                               min="0" 
                               max="${section.maxScore}" 
                               step="0.5"
                               value="${currentScore}"
                               placeholder="0">
                        <span class="score-max">/ ${section.maxScore}</span>
                    </div>
                    
                    ${aiSuggestion ? `
                        <div class="ai-suggestion">
                            <span class="ai-label">AI suggests:</span>
                            <button class="ai-score-btn" data-section="${section.key}" data-score="${aiSuggestion}">
                                ${aiSuggestion}
                            </button>
                        </div>
                    ` : ''}
                    
                    <div class="score-slider">
                        <input type="range" 
                               class="score-range"
                               data-section="${section.key}"
                               min="0" 
                               max="${section.maxScore}" 
                               step="0.5"
                               value="${currentScore}">
                    </div>
                </div>
                
                <div class="section-guidelines">
                    ${this.getSectionGuidelines(section.key)}
                </div>
            </div>
        `;
    }

    getSectionGuidelines(sectionKey) {
        const guidelines = {
            form: "Assess shape, symmetry, proportion, and balance. Look for even spacing, proper flower positioning, and overall aesthetic appeal.",
            color: "Evaluate color intensity, clarity, patterns, and contrast. Consider if colors are vibrant and true to type.",
            size: "Consider flower size relative to the plant and species norm. Assess petal/sepal substance and thickness.",
            floriferous: "Count total flowers and evaluate their arrangement. More flowers generally score higher, but consider natural species characteristics.",
            condition: "Look for damage, disease, cleanliness, and overall plant health. Deduct for brown tips, spots, or poor grooming.",
            distinct: "Assess uniqueness, rarity, and overall impression. Consider if this plant stands out positively from typical examples."
        };
        
        return guidelines[sectionKey] || "Evaluate this aspect according to judging standards.";
    }

    getAISuggestionForSection(sectionKey) {
        if (!window.aiAnalyzer || !window.aiAnalyzer.analysisResults) return null;
        
        const analysis = window.aiAnalyzer.analysisResults;
        const currentRubric = this.rubrics[this.currentSystem];
        const section = currentRubric.sections.find(s => s.key === sectionKey);
        
        if (!section) return null;
        
        let suggestion = 0;
        
        switch (sectionKey) {
            case 'form':
                suggestion = (analysis.symmetry.overall / 10) * section.maxScore;
                break;
            case 'color':
                suggestion = ((analysis.colorAnalysis.uniformity + analysis.colorAnalysis.saturation) / 20) * section.maxScore;
                break;
            case 'size':
                // Base size scoring on measurements if available
                suggestion = analysis.measurements.naturalSpread ? 
                    Math.min(section.maxScore * 0.8, section.maxScore) : 
                    section.maxScore * 0.6;
                break;
            case 'floriferous':
                // Score based on flower count
                const flowerCount = analysis.flowerCount.total;
                if (flowerCount >= 20) suggestion = section.maxScore * 0.9;
                else if (flowerCount >= 10) suggestion = section.maxScore * 0.7;
                else if (flowerCount >= 5) suggestion = section.maxScore * 0.5;
                else suggestion = section.maxScore * 0.3;
                break;
            case 'condition':
                suggestion = (analysis.condition.overall / 10) * section.maxScore;
                break;
            case 'distinct':
                // Default to middle-high score for distinction
                suggestion = section.maxScore * 0.7;
                break;
        }
        
        return Math.round(suggestion * 2) / 2; // Round to nearest 0.5
    }

    bindScoringEvents() {
        // System picker
        document.getElementById('judging-system-picker')?.addEventListener('change', (e) => {
            this.switchJudgingSystem(e.target.value);
        });

        // Score inputs and sliders
        document.querySelectorAll('.score-input, .score-range').forEach(input => {
            input.addEventListener('input', (e) => {
                this.updateScore(e.target);
            });
        });

        // AI suggestion buttons
        document.querySelectorAll('.ai-score-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const section = e.target.dataset.section;
                const score = parseFloat(e.target.dataset.score);
                this.setScore(section, score);
            });
        });

        // Action buttons
        document.getElementById('ai-suggest-scores-btn')?.addEventListener('click', () => {
            this.suggestScoresFromAI();
        });

        document.getElementById('reset-scores-btn')?.addEventListener('click', () => {
            this.resetScores();
        });

        document.getElementById('save-scores-btn')?.addEventListener('click', () => {
            this.saveScores();
        });
    }

    switchJudgingSystem(system) {
        this.currentSystem = system;
        this.displayScoringInterface();
    }

    updateScore(input) {
        const section = input.dataset.section;
        const score = parseFloat(input.value) || 0;
        
        this.scores[section] = score;
        
        // Sync between input and slider
        const siblingInput = input.classList.contains('score-input') ? 
            document.querySelector(`.score-range[data-section="${section}"]`) :
            document.querySelector(`.score-input[data-section="${section}"]`);
        
        if (siblingInput) {
            siblingInput.value = score;
        }
        
        this.updateTotalScore();
        this.highlightAwardBand();
    }

    setScore(section, score) {
        this.scores[section] = score;
        
        // Update UI
        const input = document.getElementById(`score-${section}`);
        const slider = document.querySelector(`.score-range[data-section="${section}"]`);
        
        if (input) input.value = score;
        if (slider) slider.value = score;
        
        this.updateTotalScore();
        this.highlightAwardBand();
    }

    updateTotalScore() {
        const total = Object.values(this.scores).reduce((sum, score) => sum + (score || 0), 0);
        const totalElement = document.getElementById('total-score-value');
        
        if (totalElement) {
            totalElement.textContent = total.toFixed(1);
        }
        
        return total;
    }

    highlightAwardBand() {
        const total = this.updateTotalScore();
        const currentRubric = this.rubrics[this.currentSystem];
        
        document.querySelectorAll('.award-band').forEach(band => {
            const min = parseInt(band.dataset.min);
            const max = parseInt(band.dataset.max);
            
            if (total >= min && total <= max) {
                band.classList.add('active-band');
            } else {
                band.classList.remove('active-band');
            }
        });
    }

    suggestScoresFromAI() {
        if (!window.aiAnalyzer || !window.aiAnalyzer.analysisResults) {
            alert('No AI analysis available. Please complete the analysis step first.');
            return;
        }

        const currentRubric = this.rubrics[this.currentSystem];
        
        currentRubric.sections.forEach(section => {
            const suggestion = this.getAISuggestionForSection(section.key);
            if (suggestion !== null) {
                this.setScore(section.key, suggestion);
            }
        });
    }

    resetScores() {
        if (confirm('Are you sure you want to reset all scores?')) {
            this.scores = {};
            
            // Clear UI
            document.querySelectorAll('.score-input, .score-range').forEach(input => {
                input.value = 0;
            });
            
            this.updateTotalScore();
            this.highlightAwardBand();
        }
    }

    saveScores() {
        const judgesNotes = document.getElementById('judges-notes')?.value || '';
        const totalScore = this.updateTotalScore();
        
        const scoringData = {
            system: this.currentSystem,
            scores: this.scores,
            totalScore: totalScore,
            judgesNotes: judgesNotes,
            awardBand: this.getCurrentAwardBand(),
            timestamp: new Date().toISOString()
        };

        // Store in session storage
        sessionStorage.setItem('fcos-scoring-data', JSON.stringify(scoringData));
        
        // Store in global app state
        if (window.fcosJudge) {
            window.fcosJudge.setScoringData(scoringData);
        }

        // Proceed to certificate
        this.proceedToCertificate();
    }

    getCurrentAwardBand() {
        const total = this.updateTotalScore();
        const currentRubric = this.rubrics[this.currentSystem];
        
        for (const band of currentRubric.awardBands) {
            if (total >= band.min && total <= band.max) {
                return band;
            }
        }
        
        return null;
    }

    loadScoresIntoInterface() {
        Object.keys(this.scores).forEach(section => {
            this.setScore(section, this.scores[section]);
        });
    }

    loadSavedScores() {
        try {
            const saved = sessionStorage.getItem('fcos-scoring-data');
            if (saved) {
                const data = JSON.parse(saved);
                this.currentSystem = data.system || 'AOS';
                this.scores = data.scores || {};
                
                // Load judges notes if available
                setTimeout(() => {
                    const notesField = document.getElementById('judges-notes');
                    if (notesField && data.judgesNotes) {
                        notesField.value = data.judgesNotes;
                    }
                }, 100);
                
                return data;
            }
        } catch (error) {
            console.error('Failed to load saved scoring data:', error);
        }
        return null;
    }

    proceedToCertificate() {
        if (window.fcosJudge) {
            window.fcosJudge.goToStep('certificate');
        }
    }

    getScoringData() {
        return {
            system: this.currentSystem,
            scores: this.scores,
            totalScore: this.updateTotalScore(),
            judgesNotes: document.getElementById('judges-notes')?.value || '',
            awardBand: this.getCurrentAwardBand()
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.judgingSystems = new JudgingSystems();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JudgingSystems;
}