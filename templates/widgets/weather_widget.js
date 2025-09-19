// Orchid Weather Comparison Widget JavaScript
(function() {
    'use strict';
    
    // Weather Widget Class
    class OrchidWeatherWidget {
        constructor(containerId, options = {}) {
            this.containerId = containerId;
            this.options = {
                autoLocation: true,
                refreshInterval: 300000, // 5 minutes
                ...options
            };
            this.weatherData = null;
            this.userLocation = null;
            
            this.init();
        }
        
        init() {
            this.loadWidget();
            if (this.options.autoLocation) {
                this.detectLocation();
            }
            this.startAutoRefresh();
        }
        
        loadWidget() {
            const container = document.getElementById(this.containerId);
            if (!container) {
                console.error('Orchid Weather Widget: Container not found');
                return;
            }
            
            // Load widget HTML
            fetch(`/widgets/embed/weather?container=${this.containerId}`)
                .then(response => response.text())
                .then(html => {
                    container.innerHTML = html;
                    this.bindEvents();
                })
                .catch(error => {
                    console.error('Error loading widget:', error);
                    container.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Unable to load weather widget</div>';
                });
        }
        
        bindEvents() {
            const locationSelect = document.querySelector(`#location-select-${this.containerId.replace('orchid-weather-widget-', '')}`);
            if (locationSelect) {
                locationSelect.addEventListener('change', (e) => {
                    if (e.target.value === 'zip') {
                        this.showZipInput();
                    } else if (e.target.value === 'auto') {
                        this.detectLocation();
                    }
                });
            }
        }
        
        detectLocation() {
            if (!navigator.geolocation) {
                this.showLocationError('Geolocation not supported');
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        method: 'geolocation'
                    };
                    this.updateWeather();
                },
                (error) => {
                    console.log('Geolocation error:', error);
                    this.showZipInput();
                },
                { timeout: 10000, enableHighAccuracy: false }
            );
        }
        
        showZipInput() {
            const zipInput = document.querySelector(`#zip-input-${this.containerId.replace('orchid-weather-widget-', '')}`);
            if (zipInput) {
                zipInput.style.display = 'block';
            }
        }
        
        updateWeatherFromZip(zipCode) {
            fetch(`/api/weather/zip/${zipCode}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        this.showLocationError('Invalid ZIP code');
                        return;
                    }
                    
                    this.userLocation = {
                        lat: data.latitude,
                        lon: data.longitude,
                        name: data.name,
                        method: 'zip'
                    };
                    this.updateWeather();
                })
                .catch(error => {
                    console.error('ZIP lookup error:', error);
                    this.showLocationError('Unable to find location');
                });
        }
        
        updateWeather() {
            if (!this.userLocation) return;
            
            const { lat, lon } = this.userLocation;
            
            // Fetch current weather and forecast
            Promise.all([
                fetch(`/api/weather/current?lat=${lat}&lon=${lon}`),
                fetch(`/api/weather/forecast?lat=${lat}&lon=${lon}&days=5`)
            ])
            .then(responses => Promise.all(responses.map(r => r.json())))
            .then(([current, forecast]) => {
                this.weatherData = { current, forecast };
                this.updateWeatherDisplay();
                this.updateClimateComparisons();
                this.loadBakerAdvice(current, forecast);
            })
            .catch(error => {
                console.error('Weather update error:', error);
                this.showWeatherError();
            });
        }
        
        updateWeatherDisplay() {
            if (!this.weatherData || !this.weatherData.current) return;
            
            const current = this.weatherData.current;
            const currentWeatherEl = document.querySelector(`#current-weather-${this.containerId.replace('orchid-weather-widget-', '')}`);
            
            if (currentWeatherEl) {
                currentWeatherEl.innerHTML = `
                    <div class="temperature-display">
                        <span class="temp-large">${Math.round(current.temperature)}°</span>
                        <div class="weather-condition">${current.description || 'Clear'}</div>
                        <div class="temp-range">H: ${Math.round(current.temperature_max || current.temperature + 5)}° L: ${Math.round(current.temperature_min || current.temperature - 5)}°</div>
                    </div>
                `;
            }
            
            this.updateForecast();
        }
        
        updateForecast() {
            if (!this.weatherData || !this.weatherData.forecast) return;
            
            const forecast = this.weatherData.forecast.slice(0, 4);
            const forecastDays = document.querySelector('.forecast-days');
            
            if (forecastDays) {
                forecastDays.innerHTML = forecast.map(day => {
                    const date = new Date(day.date);
                    const dayName = date.toLocaleDateString('en', { weekday: 'short' });
                    
                    return `
                        <div class="day-forecast">
                            <div class="day-name">${dayName}</div>
                            <div class="day-icon">${this.getWeatherIcon(day.weather_code)}</div>
                            <div class="day-temp">${Math.round(day.temperature_max)}°</div>
                        </div>
                    `;
                }).join('');
            }
        }
        
        updateClimateComparisons() {
            if (!this.weatherData) return;
            
            const current = this.weatherData.current;
            const indicators = document.querySelectorAll('.climate-indicator');
            
            indicators.forEach((indicator, index) => {
                const climateCard = indicator.closest('.orchid-comparison-card');
                const orchidSelector = climateCard.querySelector('.orchid-selector');
                
                if (orchidSelector) {
                    const selectedOption = orchidSelector.selectedOptions[0];
                    const climateType = selectedOption.dataset.climate;
                    
                    // Compare current weather to orchid's preferred climate
                    const comparison = this.compareWeatherToClimate(current, climateType);
                    
                    // Update indicator
                    indicator.textContent = comparison.icon;
                    indicator.className = `climate-indicator ${comparison.status}`;
                    
                    // Update care advice
                    const adviceText = climateCard.querySelector('.advice-text');
                    if (adviceText) {
                        adviceText.textContent = comparison.advice;
                    }
                }
            });
        }
        
        compareWeatherToClimate(currentWeather, climateType) {
            const temp = currentWeather.temperature;
            const humidity = currentWeather.humidity;
            
            let comparison = { icon: '🌱', status: 'ideal', advice: 'Perfect growing conditions!' };
            
            // Climate-specific comparisons
            if (climateType === 'cool') {
                if (temp > 25) {
                    comparison = { icon: '🔴', status: 'stress', advice: 'Too hot! Increase ventilation and humidity.' };
                } else if (temp > 20) {
                    comparison = { icon: '🌼', status: 'warning', advice: 'Getting warm. Monitor for stress signs.' };
                }
            } else if (climateType === 'warm') {
                if (temp < 15) {
                    comparison = { icon: '🔴', status: 'stress', advice: 'Too cold! Move to warmer location.' };
                } else if (temp < 18) {
                    comparison = { icon: '🌼', status: 'warning', advice: 'Cool conditions. Reduce watering.' };
                }
            } else { // intermediate
                if (temp < 15 || temp > 30) {
                    comparison = { icon: '🔴', status: 'stress', advice: 'Temperature stress! Adjust conditions.' };
                } else if (temp < 18 || temp > 28) {
                    comparison = { icon: '🌼', status: 'warning', advice: 'Monitor temperature closely.' };
                }
            }
            
            // Humidity considerations
            if (humidity < 40) {
                comparison.advice += ' Increase humidity with misting.';
            } else if (humidity > 85) {
                comparison.advice += ' Ensure good air circulation.';
            }
            
            return comparison;
        }
        
        getWeatherIcon(weatherCode) {
            const iconMap = {
                0: '☀️',    // Clear sky
                1: '🌤️',    // Mainly clear
                2: '⛅',    // Partly cloudy
                3: '☁️',    // Overcast
                45: '🌫️',   // Fog
                48: '🌫️',   // Depositing rime fog
                51: '🌦️',   // Light drizzle
                53: '🌦️',   // Moderate drizzle
                55: '🌦️',   // Dense drizzle
                61: '🌧️',   // Light rain
                63: '🌧️',   // Moderate rain
                65: '🌧️',   // Heavy rain
                71: '🌨️',   // Light snow
                73: '🌨️',   // Moderate snow
                75: '🌨️',   // Heavy snow
                95: '⛈️',   // Thunderstorm
            };
            
            return iconMap[weatherCode] || '⛅';
        }
        
        showLocationError(message) {
            console.error('Location error:', message);
            // Could show error state in widget
        }
        
        showWeatherError() {
            console.error('Weather error');
            // Could show error state in widget
        }
        
        startAutoRefresh() {
            setInterval(() => {
                if (this.userLocation) {
                    this.updateWeather();
                }
            }, this.options.refreshInterval);
        }
    }
    
    // Global function to initialize widget
    window.OrchidWeatherWidget = OrchidWeatherWidget;
    
    // Auto-initialize if data-orchid-weather attribute is found
    document.addEventListener('DOMContentLoaded', function() {
        const widgets = document.querySelectorAll('[data-orchid-weather]');
        widgets.forEach(widget => {
            new OrchidWeatherWidget(widget.id, {
                autoLocation: widget.dataset.autoLocation !== 'false'
            });
        });
    });
    
})();