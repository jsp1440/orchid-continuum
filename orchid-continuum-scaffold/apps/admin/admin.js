/**
 * Orchid Continuum Admin Dashboard
 * Curator interface with keyboard shortcuts and real-time updates
 */

class AdminDashboard {
    constructor() {
        this.apiBase = 'https://api.orchidcontinuum.org';
        this.currentView = 'dashboard';
        this.selectedRow = 0;
        this.reviewItems = [];
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupKeyboardShortcuts();
        this.loadView('dashboard');
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = link.dataset.view;
                this.loadView(view);
                
                // Update active state
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return; // Don't interfere with form inputs
            }

            switch (e.key.toLowerCase()) {
                case 'j':
                    e.preventDefault();
                    this.selectNext();
                    break;
                case 'k':
                    e.preventDefault();
                    this.selectPrevious();
                    break;
                case 'a':
                    e.preventDefault();
                    this.performAction('approve');
                    break;
                case 'f':
                    e.preventDefault();
                    this.performAction('flag');
                    break;
                case 'm':
                    e.preventDefault();
                    this.performAction('merge');
                    break;
                case 'r':
                    e.preventDefault();
                    this.reloadCurrentView();
                    break;
            }
        });
    }

    async loadView(viewName) {
        this.currentView = viewName;
        const titleElement = document.getElementById('page-title');
        const contentElement = document.getElementById('app-content');

        // Update page title
        const titles = {
            dashboard: 'Curator Dashboard',
            'review-queue': 'Review Queue',
            records: 'Records Management',
            analytics: 'Analytics',
            settings: 'Settings'
        };
        titleElement.textContent = titles[viewName] || 'Dashboard';

        // Show loading
        contentElement.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';

        try {
            switch (viewName) {
                case 'dashboard':
                    await this.loadDashboard();
                    break;
                case 'review-queue':
                    await this.loadReviewQueue();
                    break;
                case 'records':
                    await this.loadRecords();
                    break;
                case 'analytics':
                    await this.loadAnalytics();
                    break;
                case 'settings':
                    await this.loadSettings();
                    break;
                default:
                    contentElement.innerHTML = '<div class="loading">View not found</div>';
            }
        } catch (error) {
            console.error('Failed to load view:', error);
            contentElement.innerHTML = '<div class="loading">Failed to load content. Please try again.</div>';
        }
    }

    async loadDashboard() {
        const content = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">1,247</div>
                    <div class="stat-label">Total Records</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">89</div>
                    <div class="stat-label">Pending Review</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">23</div>
                    <div class="stat-label">Flagged Items</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">94%</div>
                    <div class="stat-label">AI Accuracy</div>
                </div>
            </div>
            
            <div class="content-card">
                <div class="card-header">
                    <h2 class="card-title">Recent Activity</h2>
                </div>
                <div class="table-container">
                    <table class="review-table">
                        <thead>
                            <tr>
                                <th>Record</th>
                                <th>Action</th>
                                <th>Curator</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Phalaenopsis amabilis #1234</td>
                                <td>Approved</td>
                                <td>John Curator</td>
                                <td>2 minutes ago</td>
                            </tr>
                            <tr>
                                <td>Cattleya labiata #1235</td>
                                <td>Flagged for review</td>
                                <td>Jane Curator</td>
                                <td>5 minutes ago</td>
                            </tr>
                            <tr>
                                <td>Dendrobium nobile #1236</td>
                                <td>Merged with #1180</td>
                                <td>Bob Curator</td>
                                <td>10 minutes ago</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('app-content').innerHTML = content;
    }

    async loadReviewQueue() {
        try {
            // Fetch review queue data
            const response = await fetch(`${this.apiBase}/curation/queue`);
            if (!response.ok) throw new Error('Failed to fetch review queue');
            
            this.reviewItems = await response.json();
            this.renderReviewQueue();
            
        } catch (error) {
            console.error('Failed to load review queue:', error);
            // Show demo data
            this.reviewItems = [
                {
                    id: '1234',
                    title: 'Phalaenopsis amabilis',
                    confidence: 0.65,
                    suggested_tags: ['epiphyte', 'white_flowers'],
                    needs_review_reason: 'Low AI confidence'
                },
                {
                    id: '1235',
                    title: 'Cattleya unknown hybrid',
                    confidence: 0.45,
                    suggested_tags: ['hybrid', 'purple_flowers'],
                    needs_review_reason: 'Uncertain identification'
                },
                {
                    id: '1236',
                    title: 'Dendrobium sp.',
                    confidence: 0.72,
                    suggested_tags: ['cane_orchid', 'deciduous'],
                    needs_review_reason: 'Species unclear'
                }
            ];
            this.renderReviewQueue();
        }
    }

    renderReviewQueue() {
        const content = `
            <div class="content-card">
                <div class="card-header">
                    <h2 class="card-title">Items Needing Review (${this.reviewItems.length})</h2>
                    <button class="btn btn-approve" onclick="adminDashboard.reloadCurrentView()">
                        🔄 Reload
                    </button>
                </div>
                <div class="table-container">
                    <table class="review-table">
                        <thead>
                            <tr>
                                <th>Record</th>
                                <th>Confidence</th>
                                <th>Suggested Tags</th>
                                <th>Reason</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.reviewItems.map((item, index) => `
                                <tr class="review-row ${index === this.selectedRow ? 'selected' : ''}" 
                                    data-index="${index}" data-id="${item.id}">
                                    <td>
                                        <strong>${item.title}</strong><br>
                                        <small>ID: ${item.id}</small>
                                    </td>
                                    <td>
                                        <span class="confidence-badge ${this.getConfidenceClass(item.confidence)}">
                                            ${Math.round(item.confidence * 100)}%
                                        </span>
                                    </td>
                                    <td>
                                        ${item.suggested_tags.map(tag => 
                                            `<span class="tag">${tag}</span>`
                                        ).join(' ')}
                                    </td>
                                    <td>${item.needs_review_reason}</td>
                                    <td>
                                        <div class="action-buttons">
                                            <button class="btn btn-approve" 
                                                    onclick="adminDashboard.performActionOnItem('${item.id}', 'approve')">
                                                ✓ Approve
                                            </button>
                                            <button class="btn btn-flag"
                                                    onclick="adminDashboard.performActionOnItem('${item.id}', 'flag')">
                                                🚩 Flag
                                            </button>
                                            <button class="btn btn-merge"
                                                    onclick="adminDashboard.performActionOnItem('${item.id}', 'merge')">
                                                🔗 Merge
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('app-content').innerHTML = content;
        this.updateSelectedRow();
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.6) return 'confidence-medium';
        return 'confidence-low';
    }

    selectNext() {
        if (this.currentView === 'review-queue' && this.reviewItems.length > 0) {
            this.selectedRow = Math.min(this.selectedRow + 1, this.reviewItems.length - 1);
            this.updateSelectedRow();
        }
    }

    selectPrevious() {
        if (this.currentView === 'review-queue' && this.reviewItems.length > 0) {
            this.selectedRow = Math.max(this.selectedRow - 1, 0);
            this.updateSelectedRow();
        }
    }

    updateSelectedRow() {
        const rows = document.querySelectorAll('.review-row');
        rows.forEach((row, index) => {
            row.classList.toggle('selected', index === this.selectedRow);
        });
        
        // Scroll to selected row
        const selectedRow = rows[this.selectedRow];
        if (selectedRow) {
            selectedRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    performAction(action) {
        if (this.currentView === 'review-queue' && this.reviewItems[this.selectedRow]) {
            const item = this.reviewItems[this.selectedRow];
            this.performActionOnItem(item.id, action);
        }
    }

    async performActionOnItem(itemId, action) {
        try {
            // Optimistic update
            this.showToast(`${action.charAt(0).toUpperCase() + action.slice(1)} action initiated...`);
            
            const response = await fetch(`${this.apiBase}/curation/queue/${itemId}/action`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    action: action,
                    notes: `Performed via admin dashboard`
                })
            });

            if (!response.ok) throw new Error(`Action failed: ${response.status}`);

            const result = await response.json();
            this.showToast(`✅ ${action.charAt(0).toUpperCase() + action.slice(1)} completed successfully`);
            
            // Remove item from review queue
            this.reviewItems = this.reviewItems.filter(item => item.id !== itemId);
            this.selectedRow = Math.min(this.selectedRow, this.reviewItems.length - 1);
            this.renderReviewQueue();
            
        } catch (error) {
            console.error('Action failed:', error);
            this.showToast(`❌ ${action} failed. Please try again.`, 'error');
        }
    }

    async loadRecords() {
        const content = `
            <div class="content-card">
                <div class="card-header">
                    <h2 class="card-title">Records Management</h2>
                </div>
                <div style="padding: 24px;">
                    <p>Records management interface would go here. This would include:</p>
                    <ul style="margin: 16px 0; padding-left: 24px;">
                        <li>Search and filter records</li>
                        <li>Bulk operations</li>
                        <li>Export functionality</li>
                        <li>Quality metrics</li>
                    </ul>
                </div>
            </div>
        `;
        
        document.getElementById('app-content').innerHTML = content;
    }

    async loadAnalytics() {
        const content = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">15,431</div>
                    <div class="stat-label">Total Photos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">547</div>
                    <div class="stat-label">Unique Genera</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">2,853</div>
                    <div class="stat-label">Species</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">89%</div>
                    <div class="stat-label">Data Quality</div>
                </div>
            </div>
            
            <div class="content-card">
                <div class="card-header">
                    <h2 class="card-title">Analytics Dashboard</h2>
                </div>
                <div style="padding: 24px;">
                    <p>Detailed analytics and reporting would be displayed here, including:</p>
                    <ul style="margin: 16px 0; padding-left: 24px;">
                        <li>Collection growth over time</li>
                        <li>AI accuracy metrics</li>
                        <li>Geographic distribution</li>
                        <li>User engagement statistics</li>
                        <li>Data source performance</li>
                    </ul>
                </div>
            </div>
        `;
        
        document.getElementById('app-content').innerHTML = content;
    }

    async loadSettings() {
        const content = `
            <div class="content-card">
                <div class="card-header">
                    <h2 class="card-title">System Settings</h2>
                </div>
                <div style="padding: 24px;">
                    <div class="secrecy-notice">
                        <h4>🔒 Secrecy & Disclosure Policy</h4>
                        <p><strong>Confidential Information (Never Disclosed):</strong></p>
                        <ul style="margin: 8px 0; padding-left: 20px;">
                            <li>Database schema and structural blueprints</li>
                            <li>Integration workflows and ingestion pipelines</li>
                            <li>AI processing logic and validation systems</li>
                            <li>Proprietary expansion technologies</li>
                            <li>Source code or algorithms</li>
                        </ul>
                        <p><strong>Public-Safe Information:</strong></p>
                        <ul style="margin: 8px 0; padding-left: 20px;">
                            <li>Executive summary, general features, statistics</li>
                            <li>Research, education, and conservation applications</li>
                            <li>Future opportunities and broad expansion areas</li>
                        </ul>
                    </div>
                    
                    <h3>Configuration Options</h3>
                    <p>System configuration settings would be available here for authorized administrators.</p>
                </div>
            </div>
        `;
        
        document.getElementById('app-content').innerHTML = content;
    }

    async reloadCurrentView() {
        await this.loadView(this.currentView);
    }

    showToast(message, type = 'success') {
        // Remove existing toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }

        // Create new toast
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        
        if (type === 'error') {
            toast.style.background = '#e53e3e';
        }

        document.body.appendChild(toast);

        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Hide toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getAuthToken() {
        // In production, this would get the actual auth token
        return 'demo-auth-token';
    }
}

// Initialize dashboard
const adminDashboard = new AdminDashboard();

// Add CSS for selected row
const style = document.createElement('style');
style.textContent = `
    .review-row.selected {
        background: #e6fffa !important;
        border-left: 4px solid #38b2ac;
    }
    
    .tag {
        display: inline-block;
        background: #edf2f7;
        color: #4a5568;
        padding: 2px 6px;
        border-radius: 12px;
        font-size: 11px;
        margin-right: 4px;
    }
`;
document.head.appendChild(style);