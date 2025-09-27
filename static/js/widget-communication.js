/**
 * Widget Communication System
 * Enables seamless data sharing between all specialized orchid grower tools
 */

class WidgetCommunicationBus {
    constructor() {
        this.eventBus = new EventTarget();
        this.sharedState = {
            activeOrchid: null,
            analyses: {},
            insights: {},
            recommendations: [],
            sessionId: this.generateSessionId()
        };
        
        this.subscribers = new Map();
        this.messageHistory = [];
        this.maxHistorySize = 100;
        
        // Initialize communication system
        this.initializeBus();
        this.loadPersistedState();
        
        console.log('🔄 Widget Communication Bus initialized');
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    initializeBus() {
        // Global event listener for widget messages
        this.eventBus.addEventListener('widget-message', (event) => {
            this.handleMessage(event.detail);
        });
        
        // Set up periodic state sync
        setInterval(() => {
            this.syncState();
        }, 5000); // Sync every 5 seconds
        
        // Clean up old messages
        setInterval(() => {
            this.cleanupHistory();
        }, 60000); // Cleanup every minute
    }
    
    // Core messaging methods
    publish(event, data, source = 'unknown') {
        const message = {
            id: this.generateMessageId(),
            event: event,
            data: data,
            source: source,
            timestamp: new Date().toISOString(),
            sessionId: this.sharedState.sessionId
        };
        
        // Add to history
        this.messageHistory.push(message);
        this.cleanupHistory();
        
        // Dispatch event
        const customEvent = new CustomEvent('widget-message', {
            detail: message
        });
        
        this.eventBus.dispatchEvent(customEvent);
        
        // Log for debugging
        console.log(`📤 Widget message: ${event}`, message);
        
        return message.id;
    }
    
    subscribe(event, callback, widgetId) {
        if (!this.subscribers.has(event)) {
            this.subscribers.set(event, new Map());
        }
        
        this.subscribers.get(event).set(widgetId, callback);
        
        console.log(`📥 Widget ${widgetId} subscribed to: ${event}`);
        
        // Return unsubscribe function
        return () => {
            if (this.subscribers.has(event)) {
                this.subscribers.get(event).delete(widgetId);
                console.log(`📤 Widget ${widgetId} unsubscribed from: ${event}`);
            }
        };
    }
    
    handleMessage(message) {
        const { event, data, source } = message;
        
        // Update shared state based on message type
        this.updateSharedState(event, data, source);
        
        // Notify subscribers
        if (this.subscribers.has(event)) {
            this.subscribers.get(event).forEach((callback, widgetId) => {
                if (widgetId !== source) { // Don't notify the sender
                    try {
                        callback(data, message);
                    } catch (error) {
                        console.error(`❌ Error in subscriber ${widgetId}:`, error);
                    }
                }
            });
        }
        
        // Handle system-wide events
        this.handleSystemEvents(event, data, source);
    }
    
    updateSharedState(event, data, source) {
        switch (event) {
            case 'orchid-selected':
                this.sharedState.activeOrchid = data;
                break;
                
            case 'analysis-completed':
                this.sharedState.analyses[source] = data;
                this.generateCrossToolInsights();
                break;
                
            case 'health-diagnosed':
                this.sharedState.analyses.health = data;
                this.generateHealthRecommendations(data);
                break;
                
            case 'conditions-matched':
                this.sharedState.analyses.conditions = data;
                this.generateConditionRecommendations(data);
                break;
                
            case 'breeding-analyzed':
                this.sharedState.analyses.breeding = data;
                this.generateBreedingRecommendations(data);
                break;
                
            case 'care-scheduled':
                this.sharedState.analyses.care = data;
                this.generateCareRecommendations(data);
                break;
                
            case 'authenticity-verified':
                this.sharedState.analyses.authentication = data;
                this.generateAuthenticationRecommendations(data);
                break;
                
            case 'state-cleared':
                this.clearState();
                break;
        }
        
        // Persist state
        this.persistState();
    }
    
    generateCrossToolInsights() {
        const analyses = this.sharedState.analyses;
        const insights = {};
        
        // Health + Conditions insight
        if (analyses.health && analyses.conditions) {
            insights.healthConditions = {
                title: 'Health-Environment Analysis',
                message: this.correlateHealthAndConditions(analyses.health, analyses.conditions),
                priority: 'high'
            };
        }
        
        // Breeding + Care insight  
        if (analyses.breeding && analyses.care) {
            insights.breedingCare = {
                title: 'Breeding-Care Optimization',
                message: this.correlateBreedingAndCare(analyses.breeding, analyses.care),
                priority: 'medium'
            };
        }
        
        // Authentication + Health insight
        if (analyses.authentication && analyses.health) {
            insights.authenticationHealth = {
                title: 'Authenticity-Health Verification',
                message: this.correlateAuthenticationAndHealth(analyses.authentication, analyses.health),
                priority: 'high'
            };
        }
        
        this.sharedState.insights = insights;
        
        // Broadcast insights update
        this.publish('insights-generated', insights, 'communication-bus');
    }
    
    correlateHealthAndConditions(health, conditions) {
        if (health.health_score < 70 && conditions.compatibility_score > 80) {
            return "Despite good environmental conditions, health issues detected. Consider pest inspection or nutritional deficiency.";
        } else if (health.health_score > 80 && conditions.compatibility_score < 60) {
            return "Orchid appears healthy but environmental conditions may not be optimal for long-term growth.";
        } else if (health.health_score > 80 && conditions.compatibility_score > 80) {
            return "Excellent health in perfect conditions! This orchid is thriving in your environment.";
        }
        return "Health and environmental analysis completed. Review both reports for detailed insights.";
    }
    
    correlateBreedingAndCare(breeding, care) {
        if (breeding.compatibility_score > 80 && care.care_intensity === 'high') {
            return "High breeding potential requires intensive care schedule. Your care plan supports successful breeding.";
        } else if (breeding.compatibility_score > 80 && care.care_intensity === 'low') {
            return "High breeding potential detected but care schedule may be too minimal. Consider increasing care frequency.";
        }
        return "Breeding analysis and care schedule have been coordinated for optimal results.";
    }
    
    correlateAuthenticationAndHealth(auth, health) {
        if (auth.authenticity_level === 'likely_mislabeled' && health.health_score < 60) {
            return "ALERT: Potential mislabeling detected with poor health. Verify species identity before treating health issues.";
        } else if (auth.authenticity_level === 'authentic' && health.health_score > 80) {
            return "Verified authentic orchid in excellent health. Your identification and care are on track.";
        }
        return "Authentication and health analysis completed. Cross-reference results for accurate care decisions.";
    }
    
    generateHealthRecommendations(healthData) {
        const recommendations = [];
        
        if (healthData.health_score < 70) {
            recommendations.push({
                tool: 'conditions',
                action: 'Check environmental conditions',
                reason: 'Poor health may be due to suboptimal growing conditions'
            });
            
            recommendations.push({
                tool: 'care',
                action: 'Generate intensive care schedule',
                reason: 'Unhealthy orchids need more frequent care and monitoring'
            });
        }
        
        if (healthData.diseases && healthData.diseases.length > 0) {
            recommendations.push({
                tool: 'authentication',
                action: 'Verify orchid identity',
                reason: 'Ensure correct species identification for proper disease treatment'
            });
        }
        
        this.addRecommendations(recommendations);
    }
    
    generateConditionRecommendations(conditionsData) {
        const recommendations = [];
        
        if (conditionsData.compatibility_score < 60) {
            recommendations.push({
                tool: 'health',
                action: 'Perform health diagnostic',
                reason: 'Poor conditions may already be affecting orchid health'
            });
            
            recommendations.push({
                tool: 'care',
                action: 'Adjust care schedule',
                reason: 'Suboptimal conditions require modified care routines'
            });
        }
        
        this.addRecommendations(recommendations);
    }
    
    generateBreedingRecommendations(breedingData) {
        const recommendations = [];
        
        if (breedingData.compatibility_score > 80) {
            recommendations.push({
                tool: 'care',
                action: 'Create breeding care calendar',
                reason: 'High breeding potential requires specialized care schedule'
            });
            
            recommendations.push({
                tool: 'health',
                action: 'Monitor parent plant health',
                reason: 'Healthy parent plants are crucial for successful breeding'
            });
        }
        
        this.addRecommendations(recommendations);
    }
    
    generateCareRecommendations(careData) {
        const recommendations = [];
        
        if (careData.care_intensity === 'high') {
            recommendations.push({
                tool: 'health',
                action: 'Regular health monitoring',
                reason: 'Intensive care schedules require frequent health checks'
            });
        }
        
        this.addRecommendations(recommendations);
    }
    
    generateAuthenticationRecommendations(authData) {
        const recommendations = [];
        
        if (authData.authenticity_level === 'likely_mislabeled') {
            recommendations.push({
                tool: 'conditions',
                action: 'Verify growing requirements',
                reason: 'Mislabeled orchids may have different care needs'
            });
            
            recommendations.push({
                tool: 'care',
                action: 'Research correct care schedule',
                reason: 'Proper species identification is crucial for appropriate care'
            });
        }
        
        this.addRecommendations(recommendations);
    }
    
    addRecommendations(newRecommendations) {
        this.sharedState.recommendations = [
            ...this.sharedState.recommendations,
            ...newRecommendations
        ].slice(-10); // Keep only latest 10 recommendations
        
        this.publish('recommendations-updated', this.sharedState.recommendations, 'communication-bus');
    }
    
    // State management
    clearState() {
        this.sharedState = {
            activeOrchid: null,
            analyses: {},
            insights: {},
            recommendations: [],
            sessionId: this.generateSessionId()
        };
        
        console.log('🧹 Shared state cleared');
    }
    
    getState() {
        return { ...this.sharedState };
    }
    
    persistState() {
        try {
            localStorage.setItem('orchid-widget-state', JSON.stringify(this.sharedState));
        } catch (error) {
            console.warn('⚠️ Could not persist widget state:', error);
        }
    }
    
    loadPersistedState() {
        try {
            const saved = localStorage.getItem('orchid-widget-state');
            if (saved) {
                const parsed = JSON.parse(saved);
                // Only restore data, generate new session
                this.sharedState = {
                    ...parsed,
                    sessionId: this.generateSessionId()
                };
                console.log('📂 Restored widget state from storage');
            }
        } catch (error) {
            console.warn('⚠️ Could not load persisted state:', error);
        }
    }
    
    syncState() {
        // Sync with dashboard if available
        if (typeof window.dashboardAPI !== 'undefined') {
            try {
                const dashboardState = window.dashboardAPI.getSharedData();
                
                // Merge states if different
                if (JSON.stringify(dashboardState) !== JSON.stringify(this.sharedState)) {
                    this.sharedState = { ...this.sharedState, ...dashboardState };
                    this.persistState();
                }
            } catch (error) {
                console.warn('⚠️ Could not sync with dashboard:', error);
            }
        }
    }
    
    // Utility methods
    generateMessageId() {
        return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
    }
    
    cleanupHistory() {
        if (this.messageHistory.length > this.maxHistorySize) {
            this.messageHistory = this.messageHistory.slice(-this.maxHistorySize);
        }
    }
    
    // Debug methods
    getMessageHistory() {
        return [...this.messageHistory];
    }
    
    getSubscribers() {
        const result = {};
        this.subscribers.forEach((widgets, event) => {
            result[event] = Array.from(widgets.keys());
        });
        return result;
    }
    
    // Widget helper methods for easy integration
    static createWidgetAdapter(widgetId) {
        return {
            // Publish methods
            setActiveOrchid: (orchidData) => {
                communicationBus.publish('orchid-selected', orchidData, widgetId);
            },
            
            reportAnalysis: (analysisData) => {
                communicationBus.publish('analysis-completed', analysisData, widgetId);
            },
            
            reportHealth: (healthData) => {
                communicationBus.publish('health-diagnosed', healthData, widgetId);
            },
            
            reportConditions: (conditionsData) => {
                communicationBus.publish('conditions-matched', conditionsData, widgetId);
            },
            
            reportBreeding: (breedingData) => {
                communicationBus.publish('breeding-analyzed', breedingData, widgetId);
            },
            
            reportCare: (careData) => {
                communicationBus.publish('care-scheduled', careData, widgetId);
            },
            
            reportAuthentication: (authData) => {
                communicationBus.publish('authenticity-verified', authData, widgetId);
            },
            
            clearState: () => {
                communicationBus.publish('state-cleared', {}, widgetId);
            },
            
            // Subscribe methods
            onOrchidSelected: (callback) => {
                return communicationBus.subscribe('orchid-selected', callback, widgetId);
            },
            
            onAnalysisCompleted: (callback) => {
                return communicationBus.subscribe('analysis-completed', callback, widgetId);
            },
            
            onInsightsGenerated: (callback) => {
                return communicationBus.subscribe('insights-generated', callback, widgetId);
            },
            
            onRecommendationsUpdated: (callback) => {
                return communicationBus.subscribe('recommendations-updated', callback, widgetId);
            },
            
            // State access
            getSharedState: () => {
                return communicationBus.getState();
            },
            
            getActiveOrchid: () => {
                return communicationBus.getState().activeOrchid;
            },
            
            getAnalyses: () => {
                return communicationBus.getState().analyses;
            },
            
            getInsights: () => {
                return communicationBus.getState().insights;
            },
            
            getRecommendations: () => {
                return communicationBus.getState().recommendations;
            }
        };
    }
}

// Initialize global communication bus
const communicationBus = new WidgetCommunicationBus();

// Expose global API
window.WidgetCommunication = {
    bus: communicationBus,
    createAdapter: WidgetCommunicationBus.createWidgetAdapter
};

// Integration with existing dashboard API
if (typeof window.dashboardAPI !== 'undefined') {
    // Enhance dashboard API with communication features
    window.dashboardAPI.communication = {
        bus: communicationBus,
        createAdapter: WidgetCommunicationBus.createWidgetAdapter,
        
        // Dashboard-specific methods
        broadcastOrchidSelection: (orchidData) => {
            communicationBus.publish('orchid-selected', orchidData, 'dashboard');
            // Also update dashboard state for backward compatibility
            if (window.dashboardAPI.setSharedOrchid) {
                window.dashboardAPI.setSharedOrchid(orchidData);
            }
        },
        
        broadcastAnalysisResult: (toolId, result) => {
            communicationBus.publish('analysis-completed', result, toolId);
            // Also update dashboard state for backward compatibility
            if (window.dashboardAPI.addAnalysisResult) {
                window.dashboardAPI.addAnalysisResult(toolId, result);
            }
        }
    };
    
    console.log('🔗 Widget Communication integrated with Dashboard API');
}

console.log('✅ Widget Communication System loaded and ready');