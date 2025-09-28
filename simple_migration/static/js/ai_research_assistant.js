/**
 * AI Research Assistant JavaScript
 * Handles real-time communication with AI research endpoints and UI interactions
 */

class AIResearchAssistant {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.queryCount = 0;
        this.sessionStartTime = new Date();
        this.researchTrail = [];
        this.savedCitations = [];
        this.currentUploadedImage = null;
        this.isProcessing = false;
        
        this.initializeEventListeners();
        this.initializeSession();
        this.loadSessionData();
        
        console.log('AI Research Assistant initialized with session:', this.sessionId);
    }
    
    generateSessionId() {
        return 'ai_research_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    initializeEventListeners() {
        // Chat form submission
        const chatForm = document.getElementById('chatForm');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        }
        
        // Research category buttons
        document.querySelectorAll('.research-category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleCategorySelect(e));
        });
        
        // Quick template buttons
        document.querySelectorAll('.quick-template').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickTemplate(e));
        });
        
        // Image upload functionality
        this.initializeImageUpload();
        
        // Voice input (if supported)
        const voiceBtn = document.getElementById('voiceInputBtn');
        if (voiceBtn && 'webkitSpeechRecognition' in window) {
            voiceBtn.addEventListener('click', () => this.handleVoiceInput());
        } else if (voiceBtn) {
            voiceBtn.style.display = 'none';
        }
        
        // Session management buttons
        const exportBtn = document.getElementById('exportSessionBtn');
        const clearBtn = document.getElementById('clearSessionBtn');
        
        if (exportBtn) exportBtn.addEventListener('click', () => this.exportSession());
        if (clearBtn) clearBtn.addEventListener('click', () => this.clearSession());
        
        // Research modal save button
        const saveResearchBtn = document.getElementById('saveResearchBtn');
        if (saveResearchBtn) {
            saveResearchBtn.addEventListener('click', () => this.saveCurrentResearch());
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }
    
    initializeImageUpload() {
        const uploadZone = document.getElementById('imageUploadZone');
        const fileInput = document.getElementById('imageUpload');
        
        if (!uploadZone || !fileInput) return;
        
        // Click to upload
        uploadZone.addEventListener('click', () => fileInput.click());
        
        // File input change
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('drag-over');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.processImageFile(files[0]);
            }
        });
    }
    
    initializeSession() {
        // Update UI with session info
        document.getElementById('sessionId').textContent = this.sessionId.slice(-8);
        document.getElementById('queryCount').textContent = this.queryCount;
        document.getElementById('sessionStartTime').textContent = this.sessionStartTime.toLocaleTimeString();
    }
    
    loadSessionData() {
        // Load any existing session data from localStorage
        const savedSession = localStorage.getItem(`ai_research_session_${this.sessionId}`);
        if (savedSession) {
            try {
                const sessionData = JSON.parse(savedSession);
                this.queryCount = sessionData.queryCount || 0;
                this.researchTrail = sessionData.researchTrail || [];
                this.savedCitations = sessionData.savedCitations || [];
                this.updateUI();
            } catch (error) {
                console.warn('Error loading session data:', error);
            }
        }
    }
    
    saveSessionData() {
        const sessionData = {
            sessionId: this.sessionId,
            queryCount: this.queryCount,
            researchTrail: this.researchTrail,
            savedCitations: this.savedCitations,
            lastActivity: new Date().toISOString()
        };
        
        localStorage.setItem(`ai_research_session_${this.sessionId}`, JSON.stringify(sessionData));
    }
    
    async handleChatSubmit(e) {
        e.preventDefault();
        
        if (this.isProcessing) return;
        
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Clear input immediately
        messageInput.value = '';
        
        // Add user message to chat
        this.addUserMessage(message);
        
        // Determine query type and process
        await this.processUserQuery(message);
    }
    
    async processUserQuery(message) {
        this.isProcessing = true;
        this.showTypingIndicator();
        
        try {
            // Determine the best endpoint based on message content
            const endpoint = this.determineEndpoint(message);
            
            // Prepare request data
            const requestData = {
                query: message,
                session_id: this.sessionId,
                context: this.getSessionContext(),
                image_data: this.currentUploadedImage
            };
            
            // Make API request
            const response = await this.makeAPIRequest(endpoint, requestData);
            
            if (response.success) {
                this.addAIMessage(response.data);
                this.updateResearchTrail(message, response.data, endpoint);
                this.queryCount++;
                this.updateUI();
            } else {
                this.addErrorMessage(response.error || 'An error occurred while processing your request.');
            }
            
        } catch (error) {
            console.error('Error processing query:', error);
            this.addErrorMessage('Failed to connect to AI research service. Please try again.');
        } finally {
            this.hideTypingIndicator();
            this.isProcessing = false;
            this.saveSessionData();
        }
    }
    
    determineEndpoint(message) {
        const lowerMessage = message.toLowerCase();
        
        // Image identification
        if (this.currentUploadedImage || lowerMessage.includes('identify') || lowerMessage.includes('what orchid')) {
            return '/api/ai-research/identify';
        }
        
        // Cultivation advice
        if (lowerMessage.includes('care') || lowerMessage.includes('cultivation') || lowerMessage.includes('grow')) {
            return '/api/ai-research/cultivation-advice';
        }
        
        // Citations
        if (lowerMessage.includes('citation') || lowerMessage.includes('reference') || lowerMessage.includes('paper')) {
            return '/api/ai-research/citations';
        }
        
        // Research insights
        if (lowerMessage.includes('research') || lowerMessage.includes('study') || lowerMessage.includes('scientific')) {
            return '/api/ai-research/research-insights';
        }
        
        // Default to general query
        return '/api/ai-research/query';
    }
    
    async makeAPIRequest(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('API request failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    getSessionContext() {
        return {
            recent_queries: this.researchTrail.slice(-5),
            query_count: this.queryCount,
            session_start: this.sessionStartTime.toISOString()
        };
    }
    
    handleCategorySelect(e) {
        const category = e.target.closest('.research-category-btn').dataset.category;
        const messageInput = document.getElementById('messageInput');
        
        // Set category-specific prompt
        const prompts = {
            'identification': 'Please help me identify this orchid. ',
            'cultivation': 'I need cultivation advice for ',
            'research': 'Show me research insights about ',
            'citations': 'Find academic citations for '
        };
        
        messageInput.value = prompts[category] || '';
        messageInput.focus();
        
        // Add visual feedback
        document.querySelectorAll('.research-category-btn').forEach(btn => btn.classList.remove('active'));
        e.target.closest('.research-category-btn').classList.add('active');
    }
    
    handleQuickTemplate(e) {
        const template = e.target.closest('.quick-template').dataset.template;
        const messageInput = document.getElementById('messageInput');
        messageInput.value = template;
        messageInput.focus();
    }
    
    async handleFileUpload(e) {
        const file = e.target.files[0];
        if (file) {
            await this.processImageFile(file);
        }
    }
    
    async processImageFile(file) {
        if (!file.type.startsWith('image/')) {
            this.showToast('Please upload a valid image file.', 'error');
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            this.showToast('Image file too large. Please upload an image under 10MB.', 'error');
            return;
        }
        
        try {
            // Convert to base64
            const base64 = await this.fileToBase64(file);
            this.currentUploadedImage = {
                data: base64,
                filename: file.name,
                size: file.size,
                type: file.type
            };
            
            // Update UI to show uploaded image
            this.displayUploadedImage(file);
            
            // Suggest identification
            const messageInput = document.getElementById('messageInput');
            if (!messageInput.value.trim()) {
                messageInput.value = 'Please identify this orchid from the uploaded image.';
            }
            
            this.showToast('Image uploaded successfully. Ready for identification!', 'success');
            
        } catch (error) {
            console.error('Error processing image:', error);
            this.showToast('Error processing image. Please try again.', 'error');
        }
    }
    
    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
    
    displayUploadedImage(file) {
        const uploadZone = document.getElementById('imageUploadZone');
        
        // Create image preview
        const preview = document.createElement('div');
        preview.className = 'uploaded-image-preview mt-2';
        preview.innerHTML = `
            <div class="d-flex align-items-center">
                <img src="${URL.createObjectURL(file)}" alt="Uploaded orchid" 
                     style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px;">
                <div class="ms-3 flex-grow-1">
                    <div class="fw-bold">${file.name}</div>
                    <small class="text-muted">${this.formatFileSize(file.size)}</small>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="researchAssistant.clearUploadedImage()">
                    <i data-feather="x" style="width: 14px; height: 14px;"></i>
                </button>
            </div>
        `;
        
        // Remove any existing preview
        const existingPreview = uploadZone.querySelector('.uploaded-image-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        uploadZone.appendChild(preview);
        
        // Re-initialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    clearUploadedImage() {
        this.currentUploadedImage = null;
        const uploadZone = document.getElementById('imageUploadZone');
        const preview = uploadZone.querySelector('.uploaded-image-preview');
        if (preview) {
            preview.remove();
        }
        this.showToast('Image cleared.', 'info');
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    addUserMessage(message) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message mb-4';
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start justify-content-end">
                <div class="flex-grow-1 me-3">
                    <div class="message-bubble bg-primary text-white p-3 rounded-3 text-end">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <small class="text-white-50">${new Date().toLocaleTimeString()}</small>
                            <strong>You</strong>
                        </div>
                        <p class="mb-0">${this.escapeHtml(message)}</p>
                    </div>
                </div>
                <div class="flex-shrink-0">
                    <div class="avatar bg-success rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                        <i data-feather="user" style="width: 20px; height: 20px; color: white;"></i>
                    </div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        if (typeof feather !== 'undefined') feather.replace();
        this.scrollToBottom();
    }
    
    addAIMessage(data) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message mb-4';
        
        // Format response based on type
        const content = this.formatAIResponse(data);
        
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="flex-shrink-0 me-3">
                    <div class="avatar bg-primary rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                        <i data-feather="cpu" style="width: 20px; height: 20px; color: white;"></i>
                    </div>
                </div>
                <div class="flex-grow-1">
                    <div class="message-bubble bg-light p-3 rounded-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-primary">AI Research Assistant</strong>
                            <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                        </div>
                        ${content}
                    </div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        if (typeof feather !== 'undefined') feather.replace();
        this.scrollToBottom();
    }
    
    formatAIResponse(data) {
        if (typeof data === 'string') {
            return `<p class="mb-0">${this.escapeHtml(data)}</p>`;
        }
        
        let html = '';
        
        // Main response
        if (data.response) {
            html += `<p class="mb-3">${this.escapeHtml(data.response)}</p>`;
        }
        
        // Confidence score
        if (data.confidence !== undefined) {
            const confidenceClass = this.getConfidenceClass(data.confidence);
            html += `<div class="mb-2">
                <span class="confidence-score ${confidenceClass}">
                    Confidence: ${Math.round(data.confidence * 100)}%
                </span>
            </div>`;
        }
        
        // Scientific name and details
        if (data.scientific_name) {
            html += `<div class="research-detail mb-2">
                <strong>Scientific Name:</strong> <em>${this.escapeHtml(data.scientific_name)}</em>
            </div>`;
        }
        
        // Citations
        if (data.citations && data.citations.length > 0) {
            html += `<div class="citations-section mt-3">
                <h6><i data-feather="bookmark" style="width: 16px; height: 16px;"></i> Citations:</h6>
                <ul class="small">`;
            data.citations.forEach(citation => {
                html += `<li class="mb-1">${this.escapeHtml(citation)}</li>`;
            });
            html += `</ul></div>`;
        }
        
        // Sources
        if (data.sources && data.sources.length > 0) {
            html += `<div class="research-source mt-2">
                <strong>Sources:</strong> ${data.sources.map(s => this.escapeHtml(s)).join(', ')}
            </div>`;
        }
        
        return html || `<p class="mb-0">No response data available.</p>`;
    }
    
    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.6) return 'confidence-medium';
        return 'confidence-low';
    }
    
    addErrorMessage(error) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message mb-4';
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="flex-shrink-0 me-3">
                    <div class="avatar bg-danger rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                        <i data-feather="alert-circle" style="width: 20px; height: 20px; color: white;"></i>
                    </div>
                </div>
                <div class="flex-grow-1">
                    <div class="message-bubble bg-light p-3 rounded-3 border-start border-danger border-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-danger">Error</strong>
                            <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                        </div>
                        <p class="mb-0 text-danger">${this.escapeHtml(error)}</p>
                    </div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        if (typeof feather !== 'undefined') feather.replace();
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.classList.remove('d-none');
            this.scrollToBottom();
        }
    }
    
    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.classList.add('d-none');
        }
    }
    
    scrollToBottom() {
        const chatContainer = document.getElementById('chatContainer');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    updateResearchTrail(query, response, endpoint) {
        const trailItem = {
            timestamp: new Date().toISOString(),
            query: query,
            response: response,
            endpoint: endpoint,
            session_id: this.sessionId
        };
        
        this.researchTrail.push(trailItem);
        
        // Keep only last 20 items
        if (this.researchTrail.length > 20) {
            this.researchTrail = this.researchTrail.slice(-20);
        }
        
        this.updateResearchTrailUI();
    }
    
    updateResearchTrailUI() {
        const trailContainer = document.getElementById('researchTrail');
        if (!trailContainer) return;
        
        if (this.researchTrail.length === 0) {
            trailContainer.innerHTML = '<div class="text-muted">No research queries yet. Start by asking a question or uploading an image!</div>';
            return;
        }
        
        const html = this.researchTrail.slice(-5).map(item => `
            <div class="trail-item p-2 mb-2 bg-dark rounded">
                <div class="small text-primary fw-bold">${new Date(item.timestamp).toLocaleTimeString()}</div>
                <div class="small">${this.escapeHtml(item.query.substring(0, 100))}${item.query.length > 100 ? '...' : ''}</div>
            </div>
        `).join('');
        
        trailContainer.innerHTML = html;
    }
    
    updateUI() {
        document.getElementById('queryCount').textContent = this.queryCount;
        this.updateResearchTrailUI();
    }
    
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const toastId = 'toast_' + Date.now();
        const bgClass = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';
        
        const toastHtml = `
            <div id="${toastId}" class="toast ${bgClass} text-white" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${this.escapeHtml(message)}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove from DOM after hiding
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    exportSession() {
        const sessionData = {
            sessionId: this.sessionId,
            startTime: this.sessionStartTime.toISOString(),
            queryCount: this.queryCount,
            researchTrail: this.researchTrail,
            savedCitations: this.savedCitations,
            exportTime: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(sessionData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ai_research_session_${this.sessionId}_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast('Session exported successfully!', 'success');
    }
    
    clearSession() {
        if (confirm('Are you sure you want to clear the current research session? This will remove all conversation history.')) {
            // Clear UI
            const chatMessages = document.getElementById('chatMessages');
            const welcomeMessage = chatMessages.querySelector('.ai-message');
            chatMessages.innerHTML = '';
            if (welcomeMessage) {
                chatMessages.appendChild(welcomeMessage);
            }
            
            // Reset data
            this.queryCount = 0;
            this.researchTrail = [];
            this.savedCitations = [];
            this.currentUploadedImage = null;
            
            // Clear uploaded image display
            this.clearUploadedImage();
            
            // Generate new session
            this.sessionId = this.generateSessionId();
            this.sessionStartTime = new Date();
            
            // Update UI
            this.initializeSession();
            this.updateUI();
            
            // Clear local storage
            localStorage.removeItem(`ai_research_session_${this.sessionId}`);
            
            this.showToast('Session cleared successfully!', 'success');
        }
    }
    
    handleVoiceInput() {
        if (!('webkitSpeechRecognition' in window)) {
            this.showToast('Voice input not supported in this browser.', 'error');
            return;
        }
        
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        const voiceBtn = document.getElementById('voiceInputBtn');
        const messageInput = document.getElementById('messageInput');
        
        recognition.onstart = () => {
            voiceBtn.classList.add('btn-danger');
            voiceBtn.querySelector('i').setAttribute('data-feather', 'mic-off');
            if (typeof feather !== 'undefined') feather.replace();
        };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            messageInput.value = transcript;
            messageInput.focus();
        };
        
        recognition.onend = () => {
            voiceBtn.classList.remove('btn-danger');
            voiceBtn.querySelector('i').setAttribute('data-feather', 'mic');
            if (typeof feather !== 'undefined') feather.replace();
        };
        
        recognition.onerror = (event) => {
            this.showToast('Voice recognition error: ' + event.error, 'error');
            recognition.onend();
        };
        
        recognition.start();
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter to send message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const chatForm = document.getElementById('chatForm');
            if (chatForm) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
        
        // Escape to clear input
        if (e.key === 'Escape') {
            const messageInput = document.getElementById('messageInput');
            if (messageInput && messageInput === document.activeElement) {
                messageInput.value = '';
            }
        }
    }
    
    saveCurrentResearch() {
        // This would be implemented to save current research to user's account
        this.showToast('Research save functionality will be implemented with user authentication.', 'info');
    }
}