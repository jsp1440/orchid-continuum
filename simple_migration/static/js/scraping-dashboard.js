// Live Scraping Dashboard JavaScript
console.log('🖥️ Scraping Dashboard loaded');

let dashboardUpdateInterval;
let isScrapingActive = false;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing scraping dashboard...');
    
    // Start automatic updates every 2 seconds
    startDashboardUpdates();
    
    // Load initial data
    refreshDashboard();
});

function startDashboardUpdates() {
    if (dashboardUpdateInterval) {
        clearInterval(dashboardUpdateInterval);
    }
    
    dashboardUpdateInterval = setInterval(refreshDashboard, 2000); // Update every 2 seconds
    console.log('⏱️ Dashboard auto-refresh started (2s intervals)');
}

function stopDashboardUpdates() {
    if (dashboardUpdateInterval) {
        clearInterval(dashboardUpdateInterval);
        dashboardUpdateInterval = null;
    }
}

async function refreshDashboard() {
    try {
        const response = await fetch('/admin/scraping/dashboard-stats');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const stats = await response.json();
        updateDashboardDisplay(stats);
        
    } catch (error) {
        console.error('Dashboard refresh failed:', error);
        
        // Show connection error in UI
        document.getElementById('currentScraper').textContent = 'Connection Error';
        document.getElementById('currentScraper').className = 'h5 text-danger';
    }
}

function updateDashboardDisplay(stats) {
    // Update main stats
    document.getElementById('totalScraped').textContent = stats.total_scraped || 0;
    document.getElementById('successRate').textContent = `${stats.success_rate || 0}%`;
    document.getElementById('currentCycle').textContent = stats.current_cycle || 0;
    document.getElementById('uptime').textContent = stats.uptime_formatted || '00:00:00';
    
    // Update current scraper status
    const currentScraperElement = document.getElementById('currentScraper');
    if (stats.is_running && stats.current_scraper) {
        currentScraperElement.textContent = stats.current_scraper.replace('_', ' ');
        currentScraperElement.className = 'h5 text-success';
        isScrapingActive = true;
    } else {
        currentScraperElement.textContent = 'Idle';
        currentScraperElement.className = 'h5 text-muted';
        isScrapingActive = false;
    }
    
    // Update individual scraper stats
    const scraperStats = stats.scraper_stats || {};
    Object.keys(scraperStats).forEach(scraperName => {
        const scraperData = scraperStats[scraperName];
        
        // Update status badge
        const statusElement = document.getElementById(`${scraperName}_status`);
        if (statusElement) {
            statusElement.textContent = scraperData.status || 'idle';
            statusElement.className = `badge ${getBadgeClass(scraperData.status)}`;
        }
        
        // Update plants count
        const plantsElement = document.getElementById(`${scraperName}_plants`);
        if (plantsElement) {
            plantsElement.textContent = scraperData.plants_found || 0;
        }
        
        // Update images count
        const imagesElement = document.getElementById(`${scraperName}_images`);
        if (imagesElement) {
            imagesElement.textContent = scraperData.images_collected || 0;
        }
    });
    
    // Update button states
    updateButtonStates(stats.is_running);
}

function getBadgeClass(status) {
    switch (status) {
        case 'active':
            return 'bg-success';
        case 'running':
            return 'bg-primary';
        case 'error':
            return 'bg-danger';
        case 'idle':
        default:
            return 'bg-secondary';
    }
}

function updateButtonStates(isRunning) {
    const startBtn = document.getElementById('startScrapingBtn');
    const stopBtn = document.getElementById('stopScrapingBtn');
    
    if (startBtn && stopBtn) {
        if (isRunning) {
            startBtn.disabled = true;
            startBtn.textContent = 'Running...';
            stopBtn.disabled = false;
        } else {
            startBtn.disabled = false;
            startBtn.textContent = 'Start';
            stopBtn.disabled = true;
        }
    }
}

async function startMethodicalScraping() {
    try {
        const response = await fetch('/admin/scraping/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ Methodical scraping started');
            showNotification('Methodical scraping started successfully!', 'success');
            
            // Immediate dashboard refresh
            setTimeout(refreshDashboard, 500);
        } else {
            console.error('❌ Failed to start scraping:', result.error);
            showNotification(result.error || 'Failed to start scraping', 'error');
        }
        
    } catch (error) {
        console.error('Error starting scraping:', error);
        showNotification('Connection error starting scraping', 'error');
    }
}

async function stopScraping() {
    try {
        const response = await fetch('/admin/scraping/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('⏹️ Scraping stopped');
            showNotification('Scraping stopped successfully!', 'info');
            
            // Immediate dashboard refresh
            setTimeout(refreshDashboard, 500);
        } else {
            console.error('❌ Failed to stop scraping:', result.error);
            showNotification(result.error || 'Failed to stop scraping', 'error');
        }
        
    } catch (error) {
        console.error('Error stopping scraping:', error);
        showNotification('Connection error stopping scraping', 'error');
    }
}

async function manualTrigger(scraperName) {
    try {
        console.log(`🎯 Manually triggering ${scraperName}...`);
        
        const response = await fetch('/admin/scraping/manual-trigger', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scraper: scraperName
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`✅ ${scraperName} triggered successfully`);
            showNotification(`${scraperName.replace('_', ' ')} triggered: ${result.images || 0} images found`, 'success');
            
            // Immediate dashboard refresh
            setTimeout(refreshDashboard, 500);
        } else {
            console.error(`❌ ${scraperName} failed:`, result.error);
            showNotification(`${scraperName.replace('_', ' ')} failed: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error(`Error triggering ${scraperName}:`, error);
        showNotification(`Connection error triggering ${scraperName.replace('_', ' ')}`, 'error');
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Cleanup when page unloads
window.addEventListener('beforeunload', function() {
    stopDashboardUpdates();
});