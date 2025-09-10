/**
 * OCR Analysis System for FCOS Orchid Judge
 * Handles tag text extraction and taxonomy parsing
 */

class OCRAnalyzer {
    constructor() {
        this.ocrResults = null;
        this.parsedTaxonomy = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadTaxonomyPatterns();
    }

    setupEventListeners() {
        // Auto-save on field changes
        document.addEventListener('change', (e) => {
            if (e.target.matches('.taxonomy-field')) {
                this.saveTaxonomyData();
            }
        });

        // Hybrid toggle
        document.getElementById('hybrid-toggle')?.addEventListener('change', (e) => {
            this.toggleHybridFields(e.target.checked);
        });

        // Manual OCR retry
        document.getElementById('retry-ocr-btn')?.addEventListener('click', () => {
            this.retryOCR();
        });
    }

    loadTaxonomyPatterns() {
        // Common orchid naming patterns for better parsing
        this.patterns = {
            genus: /^[A-Z][a-z]+/,
            species: /[a-z]+(?=\s|$)/,
            grex: /'([^']+)'/,
            clone: /'([^']+)'\s*(?:'([^']+)')?/,
            hybrid: /×|\sx\s/i,
            cultivar: /'([^']+)'$/,
            breeder: /\(([^)]+)\)/,
            potSize: /(\d+(?:\.\d+)?)\s*(?:inch|in|"|cm)?/i,
            date: /\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4}|\d{4}[-\/]\d{1,2}[-\/]\d{1,2}/
        };
    }

    async performOCR(imageBlob) {
        try {
            // Show loading state
            this.showOCRLoading(true);

            const formData = new FormData();
            formData.append('image', imageBlob, 'tag.jpg');

            const response = await fetch('/api/fcos-judge/ocr', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`OCR failed: ${response.statusText}`);
            }

            const result = await response.json();
            this.ocrResults = result;
            this.parseExtractedText(result.text);
            this.displayResults(result);

        } catch (error) {
            console.error('OCR error:', error);
            this.showOCRError(error.message);
        } finally {
            this.showOCRLoading(false);
        }
    }

    parseExtractedText(text) {
        if (!text) return;

        // Clean and normalize text
        const cleanText = text.replace(/[^\w\s'()×\-\/]/g, ' ').trim();
        const lines = cleanText.split('\n').map(line => line.trim()).filter(line => line);

        this.parsedTaxonomy = {
            genus: '',
            species: '',
            grex: '',
            clone: '',
            cultivar: '',
            isHybrid: false,
            parentA: '',
            parentB: '',
            breeder: '',
            source: '',
            potSize: '',
            date: '',
            confidence: 0
        };

        // Parse each line for different components
        for (const line of lines) {
            this.parseLineForTaxonomy(line);
        }

        // Determine if this is a hybrid
        this.parsedTaxonomy.isHybrid = this.patterns.hybrid.test(cleanText);

        // Calculate confidence based on how many fields we found
        const fieldsFound = Object.values(this.parsedTaxonomy).filter(v => 
            typeof v === 'string' && v.length > 0
        ).length;
        this.parsedTaxonomy.confidence = Math.min(fieldsFound / 6, 1.0);
    }

    parseLineForTaxonomy(line) {
        // Try to extract genus (first capitalized word)
        if (!this.parsedTaxonomy.genus) {
            const genusMatch = line.match(this.patterns.genus);
            if (genusMatch) {
                this.parsedTaxonomy.genus = genusMatch[0];
            }
        }

        // Try to extract species/grex (lowercase word after genus)
        if (!this.parsedTaxonomy.species && this.parsedTaxonomy.genus) {
            const speciesRegex = new RegExp(`${this.parsedTaxonomy.genus}\\s+([a-z]+)`, 'i');
            const speciesMatch = line.match(speciesRegex);
            if (speciesMatch) {
                this.parsedTaxonomy.species = speciesMatch[1];
            }
        }

        // Try to extract clone/cultivar (text in quotes)
        if (!this.parsedTaxonomy.clone) {
            const cloneMatch = line.match(/'([^']+)'/);
            if (cloneMatch) {
                this.parsedTaxonomy.clone = cloneMatch[1];
            }
        }

        // Try to extract breeder (text in parentheses)
        if (!this.parsedTaxonomy.breeder) {
            const breederMatch = line.match(/\(([^)]+)\)/);
            if (breederMatch) {
                this.parsedTaxonomy.breeder = breederMatch[1];
            }
        }

        // Try to extract pot size
        if (!this.parsedTaxonomy.potSize) {
            const potMatch = line.match(this.patterns.potSize);
            if (potMatch) {
                this.parsedTaxonomy.potSize = potMatch[1];
            }
        }

        // Try to extract date
        if (!this.parsedTaxonomy.date) {
            const dateMatch = line.match(this.patterns.date);
            if (dateMatch) {
                this.parsedTaxonomy.date = dateMatch[0];
            }
        }
    }

    displayResults(ocrResult) {
        const container = document.getElementById('ocr-results');
        if (!container) return;

        const confidence = this.parsedTaxonomy.confidence;
        const confidenceClass = confidence > 0.7 ? 'confidence-high' : 
                               confidence > 0.4 ? 'confidence-medium' : 'confidence-low';

        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>Tag Information</h3>
                    <div class="confidence-chip ${confidenceClass}">
                        Confidence: ${Math.round(confidence * 100)}%
                    </div>
                </div>
                
                <div class="ocr-section">
                    <h4>Extracted Text</h4>
                    <div class="extracted-text">${ocrResult.text || 'No text detected'}</div>
                    <button id="retry-ocr-btn" class="btn btn-outline btn-small">
                        Retry OCR
                    </button>
                </div>

                <div class="taxonomy-section">
                    <h4>Parsed Information</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Genus *</label>
                            <input type="text" class="form-input taxonomy-field" 
                                   id="genus-field" value="${this.parsedTaxonomy.genus}"
                                   placeholder="e.g., Cattleya">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Species/Grex *</label>
                            <input type="text" class="form-input taxonomy-field" 
                                   id="species-field" value="${this.parsedTaxonomy.species}"
                                   placeholder="e.g., mossiae or Blue Boy">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Clone/Cultivar</label>
                            <input type="text" class="form-input taxonomy-field" 
                                   id="clone-field" value="${this.parsedTaxonomy.clone}"
                                   placeholder="e.g., 'Coerulea'">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Breeder</label>
                            <input type="text" class="form-input taxonomy-field" 
                                   id="breeder-field" value="${this.parsedTaxonomy.breeder}"
                                   placeholder="e.g., (Smith 2020)">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Source/Vendor</label>
                            <input type="text" class="form-input taxonomy-field" 
                                   id="source-field" value="${this.parsedTaxonomy.source}"
                                   placeholder="e.g., Orchid Inn">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Pot Size (inches)</label>
                            <input type="text" class="form-input taxonomy-field" 
                                   id="pot-size-field" value="${this.parsedTaxonomy.potSize}"
                                   placeholder="e.g., 4.0">
                        </div>
                    </div>
                    
                    <div class="hybrid-section">
                        <label class="checkbox-label">
                            <input type="checkbox" id="hybrid-toggle" 
                                   ${this.parsedTaxonomy.isHybrid ? 'checked' : ''}>
                            This is a hybrid
                        </label>
                        
                        <div id="hybrid-fields" class="hybrid-fields" 
                             style="display: ${this.parsedTaxonomy.isHybrid ? 'block' : 'none'}">
                            <div class="form-grid">
                                <div class="form-group">
                                    <label class="form-label">Parent A</label>
                                    <input type="text" class="form-input taxonomy-field" 
                                           id="parent-a-field" value="${this.parsedTaxonomy.parentA}"
                                           placeholder="First parent species">
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label">Parent B</label>
                                    <input type="text" class="form-input taxonomy-field" 
                                           id="parent-b-field" value="${this.parsedTaxonomy.parentB}"
                                           placeholder="Second parent species">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="taxonomy-actions">
                    <button id="lookup-taxonomy-btn" class="btn btn-secondary">
                        Lookup in Database
                    </button>
                    <button id="save-taxonomy-btn" class="btn btn-primary">
                        Save & Continue
                    </button>
                </div>
            </div>
        `;

        // Bind new event listeners
        this.bindTaxonomyEvents();
    }

    bindTaxonomyEvents() {
        // Hybrid toggle
        document.getElementById('hybrid-toggle')?.addEventListener('change', (e) => {
            this.toggleHybridFields(e.target.checked);
        });

        // Taxonomy lookup
        document.getElementById('lookup-taxonomy-btn')?.addEventListener('click', () => {
            this.lookupTaxonomy();
        });

        // Save and continue
        document.getElementById('save-taxonomy-btn')?.addEventListener('click', () => {
            this.saveTaxonomyData();
            this.proceedToNextStep();
        });

        // Retry OCR
        document.getElementById('retry-ocr-btn')?.addEventListener('click', () => {
            this.retryOCR();
        });
    }

    toggleHybridFields(show) {
        const hybridFields = document.getElementById('hybrid-fields');
        if (hybridFields) {
            hybridFields.style.display = show ? 'block' : 'none';
        }
    }

    async lookupTaxonomy() {
        const genus = document.getElementById('genus-field')?.value.trim();
        const species = document.getElementById('species-field')?.value.trim();

        if (!genus) {
            alert('Please enter a genus to lookup');
            return;
        }

        try {
            const response = await fetch(`/api/fcos-judge/lookup-taxonomy?genus=${encodeURIComponent(genus)}&species=${encodeURIComponent(species)}`);
            
            if (response.ok) {
                const data = await response.json();
                this.displayTaxonomyLookupResults(data);
            }
        } catch (error) {
            console.error('Taxonomy lookup failed:', error);
        }
    }

    displayTaxonomyLookupResults(data) {
        // Display suggested matches in a modal or dropdown
        console.log('Taxonomy lookup results:', data);
        // TODO: Implement UI for showing suggested matches
    }

    saveTaxonomyData() {
        const taxonomyData = {
            genus: document.getElementById('genus-field')?.value.trim() || '',
            species: document.getElementById('species-field')?.value.trim() || '',
            clone: document.getElementById('clone-field')?.value.trim() || '',
            breeder: document.getElementById('breeder-field')?.value.trim() || '',
            source: document.getElementById('source-field')?.value.trim() || '',
            potSize: document.getElementById('pot-size-field')?.value.trim() || '',
            isHybrid: document.getElementById('hybrid-toggle')?.checked || false,
            parentA: document.getElementById('parent-a-field')?.value.trim() || '',
            parentB: document.getElementById('parent-b-field')?.value.trim() || '',
            confidence: this.parsedTaxonomy.confidence || 0
        };

        // Store in session storage for form persistence
        sessionStorage.setItem('fcos-taxonomy-data', JSON.stringify(taxonomyData));
        
        // Also store in the global app state
        if (window.fcosJudge) {
            window.fcosJudge.setTaxonomyData(taxonomyData);
        }

        return taxonomyData;
    }

    loadSavedTaxonomyData() {
        try {
            const saved = sessionStorage.getItem('fcos-taxonomy-data');
            if (saved) {
                const data = JSON.parse(saved);
                this.populateFields(data);
                return data;
            }
        } catch (error) {
            console.error('Failed to load saved taxonomy data:', error);
        }
        return null;
    }

    populateFields(data) {
        document.getElementById('genus-field').value = data.genus || '';
        document.getElementById('species-field').value = data.species || '';
        document.getElementById('clone-field').value = data.clone || '';
        document.getElementById('breeder-field').value = data.breeder || '';
        document.getElementById('source-field').value = data.source || '';
        document.getElementById('pot-size-field').value = data.potSize || '';
        document.getElementById('hybrid-toggle').checked = data.isHybrid || false;
        document.getElementById('parent-a-field').value = data.parentA || '';
        document.getElementById('parent-b-field').value = data.parentB || '';
        
        this.toggleHybridFields(data.isHybrid);
    }

    retryOCR() {
        if (window.photoCapture && window.photoCapture.photos.tag) {
            this.performOCR(window.photoCapture.photos.tag.blob);
        }
    }

    proceedToNextStep() {
        // Trigger navigation to AI analysis step
        if (window.fcosJudge) {
            window.fcosJudge.goToStep('analysis');
        }
    }

    showOCRLoading(show) {
        const container = document.getElementById('ocr-results');
        if (show && container) {
            container.innerHTML = `
                <div class="card">
                    <div class="loading-state">
                        <div class="loading"></div>
                        <p>Analyzing tag text...</p>
                    </div>
                </div>
            `;
        }
    }

    showOCRError(message) {
        const container = document.getElementById('ocr-results');
        if (container) {
            container.innerHTML = `
                <div class="card">
                    <div class="error-state">
                        <p>OCR failed: ${message}</p>
                        <p>Please enter the plant information manually.</p>
                        <button id="manual-entry-btn" class="btn btn-primary">
                            Enter Manually
                        </button>
                    </div>
                </div>
            `;
            
            document.getElementById('manual-entry-btn')?.addEventListener('click', () => {
                this.displayResults({ text: '', confidence: 0 });
            });
        }
    }

    getTaxonomyData() {
        return this.saveTaxonomyData();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.ocrAnalyzer = new OCRAnalyzer();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OCRAnalyzer;
}