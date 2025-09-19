/**
 * AI Analysis System for FCOS Orchid Judge
 * Handles flower count, spike count, symmetry, and measurement analysis
 */

class AIAnalysisSystem {
    constructor() {
        this.analysisResults = null;
        this.referenceCardDetected = false;
        this.pixelToMmRatio = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Manual edit buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.edit-value-btn')) {
                const field = e.target.dataset.field;
                this.editValue(field);
            }
        });

        // Rerun analysis
        document.getElementById('rerun-analysis-btn')?.addEventListener('click', () => {
            this.rerunAnalysis();
        });
    }

    async performAnalysis(imageBlob) {
        try {
            this.showAnalysisLoading(true);

            const formData = new FormData();
            formData.append('image', imageBlob, 'plant.jpg');
            
            // Include reference card preference
            formData.append('detectReferenceCard', 'true');

            const response = await fetch('/api/fcos-judge/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Analysis failed: ${response.statusText}`);
            }

            const result = await response.json();
            this.analysisResults = result;
            this.processAnalysisResults(result);
            this.displayResults(result);

        } catch (error) {
            console.error('AI analysis error:', error);
            this.showAnalysisError(error.message);
        } finally {
            this.showAnalysisLoading(false);
        }
    }

    processAnalysisResults(results) {
        // Detect reference card and calculate pixel-to-mm ratio
        if (results.referenceCard) {
            this.referenceCardDetected = true;
            this.pixelToMmRatio = this.calculatePixelToMmRatio(results.referenceCard);
        }

        // Convert pixel measurements to mm if reference card detected
        if (this.pixelToMmRatio && results.measurements) {
            results.measurements.naturalSpread = this.convertToMm(results.measurements.naturalSpreadPixels);
            results.measurements.dorsalLength = this.convertToMm(results.measurements.dorsalLengthPixels);
            results.measurements.petalWidth = this.convertToMm(results.measurements.petalWidthPixels);
            results.measurements.lipWidth = this.convertToMm(results.measurements.lipWidthPixels);
            results.measurements.unit = 'mm';
        } else {
            results.measurements.unit = 'approx';
        }
    }

    calculatePixelToMmRatio(referenceCard) {
        // Standard credit card: 85.6mm × 54mm
        const cardWidthMm = 85.6;
        const cardHeightMm = 54.0;
        
        // Use the detected card dimensions in pixels
        const cardWidthPixels = referenceCard.width;
        const cardHeightPixels = referenceCard.height;
        
        // Calculate ratio (using width as primary reference)
        return cardWidthMm / cardWidthPixels;
    }

    convertToMm(pixels) {
        if (!this.pixelToMmRatio || !pixels) return null;
        return Math.round(pixels * this.pixelToMmRatio * 10) / 10; // Round to 1 decimal
    }

    displayResults(results) {
        const container = document.getElementById('analysis-results');
        if (!container) return;

        const confidenceClass = this.getConfidenceClass(results.overallConfidence);
        const scaleInfo = this.referenceCardDetected ? 'Scaled measurements' : 'Approximate measurements';

        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>AI Analysis Results</h3>
                    <div class="confidence-chip ${confidenceClass}">
                        Confidence: ${Math.round(results.overallConfidence * 100)}%
                    </div>
                </div>

                <!-- Reference Card Detection -->
                <div class="analysis-section">
                    <h4>Scale Reference</h4>
                    <div class="reference-status">
                        ${this.referenceCardDetected ? 
                            `<div class="status-good">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                                Reference card detected - ${scaleInfo}
                            </div>` :
                            `<div class="status-warning">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.083 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                                </svg>
                                No reference card - ${scaleInfo}
                            </div>`
                        }
                    </div>
                </div>

                <!-- Flower Counts -->
                <div class="analysis-section">
                    <h4>Flower Analysis</h4>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <label>Flower Count</label>
                            <div class="analysis-value">
                                <span class="value" id="flower-count-value">${results.flowerCount.total}</span>
                                <span class="confidence-chip ${this.getConfidenceClass(results.flowerCount.confidence)}">
                                    ±${results.flowerCount.uncertainty}
                                </span>
                                <button class="edit-value-btn" data-field="flowerCount">Edit</button>
                            </div>
                        </div>

                        <div class="analysis-item">
                            <label>Spike Count</label>
                            <div class="analysis-value">
                                <span class="value" id="spike-count-value">${results.spikeCount.total}</span>
                                <span class="confidence-chip ${this.getConfidenceClass(results.spikeCount.confidence)}">
                                    ±${results.spikeCount.uncertainty}
                                </span>
                                <button class="edit-value-btn" data-field="spikeCount">Edit</button>
                            </div>
                        </div>

                        <div class="analysis-item">
                            <label>Flowers per Spike</label>
                            <div class="analysis-value">
                                <span class="value">${results.flowersPerSpike.average.toFixed(1)}</span>
                                <span class="range">(${results.flowersPerSpike.min}-${results.flowersPerSpike.max})</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Symmetry Analysis -->
                <div class="analysis-section">
                    <h4>Symmetry & Form</h4>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <label>Overall Symmetry</label>
                            <div class="analysis-value">
                                <span class="value">${results.symmetry.overall.toFixed(1)}/10</span>
                                <div class="symmetry-bar">
                                    <div class="symmetry-fill" style="width: ${results.symmetry.overall * 10}%"></div>
                                </div>
                            </div>
                        </div>

                        <div class="analysis-item">
                            <label>Petal Symmetry</label>
                            <div class="analysis-value">
                                <span class="value">${results.symmetry.petals.toFixed(1)}/10</span>
                                <span class="detail">Angle variance: ${results.symmetry.petalAngleVariance.toFixed(1)}°</span>
                            </div>
                        </div>

                        <div class="analysis-item">
                            <label>Lip Orientation</label>
                            <div class="analysis-value">
                                <span class="value">${results.symmetry.lip.consistency.toFixed(1)}/10</span>
                                <span class="detail">${results.symmetry.lip.notes}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Measurements -->
                <div class="analysis-section">
                    <h4>Measurements ${results.measurements.unit === 'mm' ? '(mm)' : '(approximate)'}</h4>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <label>Natural Spread</label>
                            <div class="analysis-value">
                                <span class="value" id="natural-spread-value">
                                    ${results.measurements.naturalSpread ? results.measurements.naturalSpread + ' mm' : 'Not measured'}
                                </span>
                                <button class="edit-value-btn" data-field="naturalSpread">Edit</button>
                            </div>
                        </div>

                        <div class="analysis-item">
                            <label>Dorsal Sepal Length</label>
                            <div class="analysis-value">
                                <span class="value" id="dorsal-length-value">
                                    ${results.measurements.dorsalLength ? results.measurements.dorsalLength + ' mm' : 'Not measured'}
                                </span>
                                <button class="edit-value-btn" data-field="dorsalLength">Edit</button>
                            </div>
                        </div>

                        <div class="analysis-item">
                            <label>Petal Width</label>
                            <div class="analysis-value">
                                <span class="value" id="petal-width-value">
                                    ${results.measurements.petalWidth ? results.measurements.petalWidth + ' mm' : 'Not measured'}
                                </span>
                                <button class="edit-value-btn" data-field="petalWidth">Edit</button>
                            </div>
                        </div>

                        <div class="analysis-item">
                            <label>Lip Width</label>
                            <div class="analysis-value">
                                <span class="value" id="lip-width-value">
                                    ${results.measurements.lipWidth ? results.measurements.lipWidth + ' mm' : 'Not measured'}
                                </span>
                                <button class="edit-value-btn" data-field="lipWidth">Edit</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Condition Analysis -->
                <div class="analysis-section">
                    <h4>Condition Assessment</h4>
                    <div class="condition-grid">
                        <div class="condition-item">
                            <label>Overall Condition</label>
                            <div class="condition-score ${this.getConditionClass(results.condition.overall)}">
                                ${results.condition.overall.toFixed(1)}/10
                            </div>
                        </div>
                        
                        <div class="condition-flags">
                            <h5>Detected Issues</h5>
                            <div class="flags-list">
                                ${results.condition.flags.length > 0 ? 
                                    results.condition.flags.map(flag => 
                                        `<span class="condition-flag">${flag}</span>`
                                    ).join('') :
                                    '<span class="no-issues">No significant issues detected</span>'
                                }
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Color Analysis -->
                <div class="analysis-section">
                    <h4>Color Analysis</h4>
                    <div class="color-analysis">
                        <div class="dominant-colors">
                            ${results.colorAnalysis.dominantColors.map(color => 
                                `<div class="color-swatch" style="background-color: ${color.hex};" 
                                     title="${color.name} (${color.percentage}%)"></div>`
                            ).join('')}
                        </div>
                        <div class="color-stats">
                            <div>Color uniformity: ${results.colorAnalysis.uniformity.toFixed(1)}/10</div>
                            <div>Saturation: ${results.colorAnalysis.saturation.toFixed(1)}/10</div>
                        </div>
                    </div>
                </div>

                <div class="analysis-actions">
                    <button id="rerun-analysis-btn" class="btn btn-outline">
                        Rerun Analysis
                    </button>
                    <button id="manual-adjustments-btn" class="btn btn-secondary">
                        Manual Adjustments
                    </button>
                </div>
            </div>
        `;

        // Bind event listeners for the new elements
        this.bindAnalysisEvents();
    }

    bindAnalysisEvents() {
        // Edit value buttons
        document.querySelectorAll('.edit-value-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const field = e.target.dataset.field;
                this.editValue(field);
            });
        });

        // Rerun analysis
        document.getElementById('rerun-analysis-btn')?.addEventListener('click', () => {
            this.rerunAnalysis();
        });

        // Manual adjustments
        document.getElementById('manual-adjustments-btn')?.addEventListener('click', () => {
            this.showManualAdjustments();
        });
    }

    editValue(field) {
        const valueElement = document.getElementById(`${field.replace(/([A-Z])/g, '-$1').toLowerCase()}-value`);
        if (!valueElement) return;

        const currentValue = valueElement.textContent.replace(/[^\d.]/g, '');
        const newValue = prompt(`Enter new value for ${field}:`, currentValue);
        
        if (newValue !== null && !isNaN(parseFloat(newValue))) {
            const numValue = parseFloat(newValue);
            
            // Update the display
            if (field.includes('Count')) {
                valueElement.textContent = Math.round(numValue);
                this.analysisResults[field].total = Math.round(numValue);
            } else if (field.includes('Spread') || field.includes('Length') || field.includes('Width')) {
                valueElement.textContent = numValue + ' mm';
                this.analysisResults.measurements[field] = numValue;
            }

            // Mark as manually edited
            valueElement.classList.add('manually-edited');
            
            // Save the changes
            this.saveAnalysisData();
        }
    }

    showManualAdjustments() {
        // Create a modal for comprehensive manual adjustments
        const modal = this.createManualAdjustmentModal();
        document.body.appendChild(modal);
    }

    createManualAdjustmentModal() {
        const modal = document.createElement('div');
        modal.className = 'modal manual-adjustment-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Manual Adjustments</h3>
                    <button class="close-btn" type="button">×</button>
                </div>
                <div class="modal-body">
                    <div class="adjustment-section">
                        <h4>Flower Counts</h4>
                        <div class="form-grid">
                            <div class="form-group">
                                <label>Total Flowers</label>
                                <input type="number" id="adj-flower-count" 
                                       value="${this.analysisResults.flowerCount.total}">
                            </div>
                            <div class="form-group">
                                <label>Spike Count</label>
                                <input type="number" id="adj-spike-count" 
                                       value="${this.analysisResults.spikeCount.total}">
                            </div>
                        </div>
                    </div>
                    
                    <div class="adjustment-section">
                        <h4>Measurements (mm)</h4>
                        <div class="form-grid">
                            <div class="form-group">
                                <label>Natural Spread</label>
                                <input type="number" step="0.1" id="adj-natural-spread" 
                                       value="${this.analysisResults.measurements.naturalSpread || ''}">
                            </div>
                            <div class="form-group">
                                <label>Dorsal Length</label>
                                <input type="number" step="0.1" id="adj-dorsal-length" 
                                       value="${this.analysisResults.measurements.dorsalLength || ''}">
                            </div>
                            <div class="form-group">
                                <label>Petal Width</label>
                                <input type="number" step="0.1" id="adj-petal-width" 
                                       value="${this.analysisResults.measurements.petalWidth || ''}">
                            </div>
                            <div class="form-group">
                                <label>Lip Width</label>
                                <input type="number" step="0.1" id="adj-lip-width" 
                                       value="${this.analysisResults.measurements.lipWidth || ''}">
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-outline" onclick="this.closest('.modal').remove()">
                        Cancel
                    </button>
                    <button class="btn btn-primary" id="apply-adjustments-btn">
                        Apply Changes
                    </button>
                </div>
            </div>
        `;

        // Bind apply button
        modal.querySelector('#apply-adjustments-btn').addEventListener('click', () => {
            this.applyManualAdjustments(modal);
            modal.remove();
        });

        // Bind close button
        modal.querySelector('.close-btn').addEventListener('click', () => {
            modal.remove();
        });

        return modal;
    }

    applyManualAdjustments(modal) {
        // Get values from the modal
        const adjustments = {
            flowerCount: parseInt(modal.querySelector('#adj-flower-count').value) || 0,
            spikeCount: parseInt(modal.querySelector('#adj-spike-count').value) || 0,
            naturalSpread: parseFloat(modal.querySelector('#adj-natural-spread').value) || null,
            dorsalLength: parseFloat(modal.querySelector('#adj-dorsal-length').value) || null,
            petalWidth: parseFloat(modal.querySelector('#adj-petal-width').value) || null,
            lipWidth: parseFloat(modal.querySelector('#adj-lip-width').value) || null
        };

        // Update the analysis results
        this.analysisResults.flowerCount.total = adjustments.flowerCount;
        this.analysisResults.spikeCount.total = adjustments.spikeCount;
        this.analysisResults.measurements.naturalSpread = adjustments.naturalSpread;
        this.analysisResults.measurements.dorsalLength = adjustments.dorsalLength;
        this.analysisResults.measurements.petalWidth = adjustments.petalWidth;
        this.analysisResults.measurements.lipWidth = adjustments.lipWidth;

        // Mark as manually adjusted
        this.analysisResults.manuallyAdjusted = true;

        // Refresh the display
        this.displayResults(this.analysisResults);
        
        // Save the changes
        this.saveAnalysisData();
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.6) return 'confidence-medium';
        return 'confidence-low';
    }

    getConditionClass(score) {
        if (score >= 8) return 'condition-excellent';
        if (score >= 6) return 'condition-good';
        if (score >= 4) return 'condition-fair';
        return 'condition-poor';
    }

    rerunAnalysis() {
        if (window.photoCapture && window.photoCapture.photos.plant) {
            this.performAnalysis(window.photoCapture.photos.plant.blob);
        }
    }

    saveAnalysisData() {
        // Store in session storage for form persistence
        sessionStorage.setItem('fcos-analysis-data', JSON.stringify(this.analysisResults));
        
        // Also store in the global app state
        if (window.fcosJudge) {
            window.fcosJudge.setAnalysisData(this.analysisResults);
        }
    }

    loadSavedAnalysisData() {
        try {
            const saved = sessionStorage.getItem('fcos-analysis-data');
            if (saved) {
                this.analysisResults = JSON.parse(saved);
                return this.analysisResults;
            }
        } catch (error) {
            console.error('Failed to load saved analysis data:', error);
        }
        return null;
    }

    showAnalysisLoading(show) {
        const container = document.getElementById('analysis-results');
        if (show && container) {
            container.innerHTML = `
                <div class="card">
                    <div class="loading-state">
                        <div class="loading"></div>
                        <p>Analyzing plant photo...</p>
                        <p class="loading-detail">This may take 10-30 seconds</p>
                    </div>
                </div>
            `;
        }
    }

    showAnalysisError(message) {
        const container = document.getElementById('analysis-results');
        if (container) {
            container.innerHTML = `
                <div class="card">
                    <div class="error-state">
                        <h3>Analysis Failed</h3>
                        <p>AI analysis failed: ${message}</p>
                        <p>You can proceed with manual measurements and scoring.</p>
                        <button id="manual-entry-btn" class="btn btn-primary">
                            Enter Manual Measurements
                        </button>
                    </div>
                </div>
            `;
            
            document.getElementById('manual-entry-btn')?.addEventListener('click', () => {
                this.showManualEntryForm();
            });
        }
    }

    showManualEntryForm() {
        // Create a basic analysis result structure for manual entry
        const manualResults = {
            flowerCount: { total: 0, confidence: 0, uncertainty: 0 },
            spikeCount: { total: 0, confidence: 0, uncertainty: 0 },
            flowersPerSpike: { average: 0, min: 0, max: 0 },
            symmetry: { overall: 5.0, petals: 5.0, petalAngleVariance: 0, lip: { consistency: 5.0, notes: 'Manual entry' } },
            measurements: { naturalSpread: null, dorsalLength: null, petalWidth: null, lipWidth: null, unit: 'approx' },
            condition: { overall: 8.0, flags: [] },
            colorAnalysis: { dominantColors: [], uniformity: 5.0, saturation: 5.0 },
            overallConfidence: 0,
            manualEntry: true
        };

        this.analysisResults = manualResults;
        this.displayResults(manualResults);
    }

    getAnalysisData() {
        return this.analysisResults;
    }

    hasAnalysisData() {
        return this.analysisResults !== null;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.aiAnalyzer = new AIAnalysisSystem();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIAnalysisSystem;
}