/**
 * REALISTIC CELESTIAL MECHANICS ENGINE
 * ===================================
 * Real-time astronomical calculations for accurate Earth rotation,
 * sun position, moon phase, and planetary alignment
 */

class AstronomicalEngine {
    constructor() {
        this.startTime = Date.now();
        this.realTimeMode = false; // Toggle between real-time and accelerated
        this.timeMultiplier = 1000; // Default: 1000x speed for demo purposes
        
        // Astronomical constants
        this.EARTH_ROTATION_MS = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        this.LUNAR_ORBIT_MS = 27.3 * 24 * 60 * 60 * 1000; // 27.3 days
        this.EARTH_ORBITAL_YEAR_MS = 365.25 * 24 * 60 * 60 * 1000; // 1 year
        
        // Current astronomical state
        this.currentTime = new Date();
        this.earthRotation = 0;
        this.sunPosition = { x: 0, y: 0, z: 0 };
        this.moonPosition = { x: 0, y: 0, z: 0 };
        this.moonPhase = 0;
    }
    
    /**
     * Get current astronomical time (real-time or accelerated)
     */
    getCurrentAstronomicalTime() {
        const elapsed = Date.now() - this.startTime;
        if (this.realTimeMode) {
            return new Date();
        } else {
            // Accelerated time for demo purposes
            return new Date(this.currentTime.getTime() + (elapsed * this.timeMultiplier));
        }
    }
    
    /**
     * Calculate realistic Earth rotation based on current time
     * Earth rotates 360° in 24 hours (15° per hour, 0.25° per minute)
     */
    calculateEarthRotation() {
        const now = this.getCurrentAstronomicalTime();
        
        if (this.realTimeMode) {
            // Real-time: Earth rotates once every 24 hours
            const hoursInDay = now.getUTCHours() + (now.getUTCMinutes() / 60) + (now.getUTCSeconds() / 3600);
            this.earthRotation = (hoursInDay / 24) * Math.PI * 2;
        } else {
            // Accelerated: Visible rotation for demonstration
            const elapsed = Date.now() - this.startTime;
            this.earthRotation = (elapsed * this.timeMultiplier / this.EARTH_ROTATION_MS) * Math.PI * 2;
        }
        
        return this.earthRotation;
    }
    
    /**
     * Calculate sun position based on Earth's orbital position
     * Uses simplified solar position algorithm
     */
    calculateSunPosition() {
        const now = this.getCurrentAstronomicalTime();
        
        // Days since J2000 epoch (January 1, 2000, 12:00 UTC)
        const j2000 = new Date('2000-01-01T12:00:00Z');
        const daysSinceJ2000 = (now - j2000) / (1000 * 60 * 60 * 24);
        
        // Mean longitude of sun (simplified)
        const meanLongitude = (280.460 + 0.9856474 * daysSinceJ2000) * (Math.PI / 180);
        
        // Mean anomaly
        const meanAnomaly = (357.528 + 0.9856003 * daysSinceJ2000) * (Math.PI / 180);
        
        // Ecliptic longitude
        const eclipticLongitude = meanLongitude + (1.915 * Math.sin(meanAnomaly) + 0.020 * Math.sin(2 * meanAnomaly)) * (Math.PI / 180);
        
        // Sun distance from Earth (in AU, simplified to 1 for visualization)
        const sunDistance = 15; // Visual distance for 3D scene
        
        // Convert to 3D coordinates
        this.sunPosition = {
            x: sunDistance * Math.cos(eclipticLongitude),
            y: sunDistance * Math.sin(eclipticLongitude) * Math.sin(23.44 * Math.PI / 180), // Earth's axial tilt
            z: sunDistance * Math.sin(eclipticLongitude) * Math.cos(23.44 * Math.PI / 180)
        };
        
        return this.sunPosition;
    }
    
    /**
     * Calculate moon position and phase
     */
    calculateMoonPosition() {
        const now = this.getCurrentAstronomicalTime();
        
        // Days since J2000 epoch
        const j2000 = new Date('2000-01-01T12:00:00Z');
        const daysSinceJ2000 = (now - j2000) / (1000 * 60 * 60 * 24);
        
        // Lunar mean longitude
        const lunarMeanLongitude = (218.316 + 13.176396 * daysSinceJ2000) * (Math.PI / 180);
        
        // Lunar mean anomaly
        const lunarMeanAnomaly = (134.963 + 13.064993 * daysSinceJ2000) * (Math.PI / 180);
        
        // Moon's longitude
        const moonLongitude = lunarMeanLongitude + (6.289 * Math.sin(lunarMeanAnomaly)) * (Math.PI / 180);
        
        // Moon distance from Earth (visual)
        const moonDistance = 4; // Visual distance for 3D scene
        
        // Convert to 3D coordinates (simplified orbital mechanics)
        this.moonPosition = {
            x: moonDistance * Math.cos(moonLongitude),
            y: moonDistance * Math.sin(moonLongitude) * 0.1, // Slight inclination
            z: moonDistance * Math.sin(moonLongitude)
        };
        
        // Calculate moon phase
        const sunMoonAngle = moonLongitude - (this.sunPosition.x + this.sunPosition.z);
        this.moonPhase = (1 + Math.cos(sunMoonAngle)) / 2; // 0 = new moon, 1 = full moon
        
        return { position: this.moonPosition, phase: this.moonPhase };
    }
    
    /**
     * Calculate planetary positions (simplified)
     */
    calculatePlanetaryPositions() {
        const now = this.getCurrentAstronomicalTime();
        const j2000 = new Date('2000-01-01T12:00:00Z');
        const daysSinceJ2000 = (now - j2000) / (1000 * 60 * 60 * 24);
        
        // Simplified planetary positions (mean longitudes)
        const planets = {
            mercury: {
                period: 87.97, // days
                distance: 8,
                longitude: (252.251 + 4.092317 * daysSinceJ2000) * (Math.PI / 180)
            },
            venus: {
                period: 224.7, // days
                distance: 10,
                longitude: (181.979 + 1.602136 * daysSinceJ2000) * (Math.PI / 180)
            },
            mars: {
                period: 686.98, // days
                distance: 20,
                longitude: (355.453 + 0.524039 * daysSinceJ2000) * (Math.PI / 180)
            },
            jupiter: {
                period: 4332.6, // days
                distance: 35,
                longitude: (34.351 + 0.083056 * daysSinceJ2000) * (Math.PI / 180)
            }
        };
        
        const positions = {};
        for (const [name, planet] of Object.entries(planets)) {
            positions[name] = {
                x: planet.distance * Math.cos(planet.longitude),
                y: planet.distance * Math.sin(planet.longitude) * 0.1,
                z: planet.distance * Math.sin(planet.longitude)
            };
        }
        
        return positions;
    }
    
    /**
     * Get comprehensive astronomical state
     */
    getAstronomicalState() {
        const currentTime = this.getCurrentAstronomicalTime();
        
        return {
            currentTime: currentTime,
            realTimeMode: this.realTimeMode,
            timeMultiplier: this.timeMultiplier,
            earthRotation: this.calculateEarthRotation(),
            sunPosition: this.calculateSunPosition(),
            moonData: this.calculateMoonPosition(),
            planetaryPositions: this.calculatePlanetaryPositions(),
            
            // Additional data for UI
            timeString: currentTime.toISOString(),
            earthRotationDegrees: (this.earthRotation * 180 / Math.PI) % 360,
            moonPhasePercent: Math.round(this.moonPhase * 100)
        };
    }
    
    /**
     * Toggle between real-time and accelerated time
     */
    toggleRealTime() {
        this.realTimeMode = !this.realTimeMode;
        this.startTime = Date.now(); // Reset timing
        if (!this.realTimeMode) {
            this.currentTime = new Date(); // Reset to current time for acceleration
        }
        return this.realTimeMode;
    }
    
    /**
     * Set time multiplier for accelerated mode
     */
    setTimeMultiplier(multiplier) {
        this.timeMultiplier = Math.max(1, multiplier);
        this.startTime = Date.now(); // Reset timing
        return this.timeMultiplier;
    }
    
    /**
     * Get human-readable status
     */
    getStatusText() {
        const state = this.getAstronomicalState();
        
        const mode = state.realTimeMode ? 'Real-Time' : `${state.timeMultiplier}x Speed`;
        const rotation = `Earth: ${state.earthRotationDegrees.toFixed(1)}°`;
        const moonPhase = `Moon: ${state.moonPhasePercent}% illuminated`;
        const time = state.currentTime.toLocaleString();
        
        return {
            mode,
            rotation,
            moonPhase,
            time,
            full: `${mode} | ${rotation} | ${moonPhase} | ${time}`
        };
    }
}

// Export for use in main application
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AstronomicalEngine;
} else if (typeof window !== 'undefined') {
    window.AstronomicalEngine = AstronomicalEngine;
}