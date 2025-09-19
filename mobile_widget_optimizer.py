#!/usr/bin/env python3
"""
Mobile Widget Optimizer - Touch-optimized controls and mobile enhancements
"""

import json
import logging
from flask import request, jsonify
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MobileWidgetOptimizer:
    """
    Optimizes widget experience for mobile devices with touch controls
    """
    
    def __init__(self):
        self.mobile_breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1200
        }
        
    def detect_device_type(self) -> str:
        """Detect device type from user agent"""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipad', 'blackberry', 'windows phone']
        tablet_indicators = ['tablet', 'ipad']
        
        if any(indicator in user_agent for indicator in tablet_indicators):
            return 'tablet'
        elif any(indicator in user_agent for indicator in mobile_indicators):
            return 'mobile'
        else:
            return 'desktop'
    
    def get_mobile_optimized_config(self, widget_type: str, device_type: str = None) -> Dict:
        """Get mobile-optimized configuration for specific widget"""
        if not device_type:
            device_type = self.detect_device_type()
            
        base_config = {
            'device_type': device_type,
            'touch_optimized': device_type in ['mobile', 'tablet'],
            'responsive_breakpoints': self.mobile_breakpoints
        }
        
        # Widget-specific mobile optimizations
        if widget_type == 'map':
            return {
                **base_config,
                'map': {
                    'touch_controls': True,
                    'gesture_handling': 'cooperative' if device_type == 'mobile' else 'greedy',
                    'zoom_control_size': 'large' if device_type == 'mobile' else 'default',
                    'marker_size': 'large' if device_type == 'mobile' else 'default',
                    'info_window_mobile': True,
                    'cluster_size': 60 if device_type == 'mobile' else 40,
                    'animation_duration': 300 if device_type == 'mobile' else 200
                }
            }
            
        elif widget_type == 'weather':
            return {
                **base_config,
                'weather': {
                    'chart_height': '250px' if device_type == 'mobile' else '400px',
                    'stack_charts': device_type == 'mobile',
                    'touch_scroll': True,
                    'simplified_legend': device_type == 'mobile',
                    'font_size': 'large' if device_type == 'mobile' else 'default'
                }
            }
            
        elif widget_type == 'gallery':
            return {
                **base_config,
                'gallery': {
                    'grid_columns': 1 if device_type == 'mobile' else (2 if device_type == 'tablet' else 3),
                    'image_lazy_loading': True,
                    'swipe_navigation': device_type in ['mobile', 'tablet'],
                    'touch_zoom': True,
                    'infinite_scroll': True,
                    'thumbnail_size': 'large' if device_type == 'mobile' else 'medium'
                }
            }
            
        elif widget_type == 'search':
            return {
                **base_config,
                'search': {
                    'autocomplete_touch': True,
                    'voice_search': device_type in ['mobile', 'tablet'],
                    'camera_search': device_type in ['mobile', 'tablet'],
                    'suggestion_size': 'large' if device_type == 'mobile' else 'default',
                    'virtual_keyboard_aware': True
                }
            }
            
        elif widget_type == 'comparison':
            return {
                **base_config,
                'comparison': {
                    'vertical_layout': device_type == 'mobile',
                    'swipe_between': device_type in ['mobile', 'tablet'],
                    'accordion_details': device_type == 'mobile',
                    'full_screen_modal': device_type == 'mobile'
                }
            }
            
        return base_config
    
    def get_touch_controls_javascript(self, widget_type: str) -> str:
        """Generate JavaScript for touch-optimized controls"""
        js_code = """
        // Mobile Widget Touch Controls
        class MobileWidgetControls {
            constructor(widgetType, config) {
                this.widgetType = widgetType;
                this.config = config;
                this.isTouch = 'ontouchstart' in window;
                this.init();
            }
            
            init() {
                if (!this.config.touch_optimized) return;
                
                this.setupTouchEvents();
                this.optimizeForMobile();
                this.handleOrientationChange();
            }
            
            setupTouchEvents() {
                // Add touch event handlers based on widget type
                switch(this.widgetType) {
                    case 'map':
                        this.setupMapTouchControls();
                        break;
                    case 'gallery':
                        this.setupGalleryTouchControls();
                        break;
                    case 'weather':
                        this.setupWeatherTouchControls();
                        break;
                    case 'search':
                        this.setupSearchTouchControls();
                        break;
                }
            }
            
            setupMapTouchControls() {
                const mapContainer = document.querySelector('.map-widget-container');
                if (!mapContainer) return;
                
                // Enable touch gestures
                mapContainer.style.touchAction = 'pan-x pan-y';
                
                // Double-tap to zoom
                let lastTap = 0;
                mapContainer.addEventListener('touchend', (e) => {
                    const currentTime = new Date().getTime();
                    const tapLength = currentTime - lastTap;
                    
                    if (tapLength < 500 && tapLength > 0) {
                        // Double tap detected - zoom in
                        this.triggerMapZoom(e);
                    }
                    lastTap = currentTime;
                });
            }
            
            setupGalleryTouchControls() {
                const gallery = document.querySelector('.gallery-widget-container');
                if (!gallery) return;
                
                // Swipe navigation
                let startX = 0;
                let startY = 0;
                
                gallery.addEventListener('touchstart', (e) => {
                    startX = e.touches[0].clientX;
                    startY = e.touches[0].clientY;
                });
                
                gallery.addEventListener('touchend', (e) => {
                    const endX = e.changedTouches[0].clientX;
                    const endY = e.changedTouches[0].clientY;
                    
                    const deltaX = endX - startX;
                    const deltaY = endY - startY;
                    
                    // Horizontal swipe
                    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                        if (deltaX > 0) {
                            this.navigateGallery('prev');
                        } else {
                            this.navigateGallery('next');
                        }
                    }
                });
            }
            
            setupWeatherTouchControls() {
                const weatherWidget = document.querySelector('.weather-widget-container');
                if (!weatherWidget) return;
                
                // Touch-friendly chart interactions
                const charts = weatherWidget.querySelectorAll('.weather-chart');
                charts.forEach(chart => {
                    chart.style.touchAction = 'pan-x';
                    
                    // Add touch indicators
                    const touchIndicator = document.createElement('div');
                    touchIndicator.className = 'touch-indicator';
                    touchIndicator.textContent = '👆 Swipe to explore data';
                    chart.appendChild(touchIndicator);
                });
            }
            
            setupSearchTouchControls() {
                const searchInput = document.querySelector('.search-widget input');
                if (!searchInput) return;
                
                // Voice search button
                if (this.config.search && this.config.search.voice_search) {
                    this.addVoiceSearchButton(searchInput);
                }
                
                // Camera search button
                if (this.config.search && this.config.search.camera_search) {
                    this.addCameraSearchButton(searchInput);
                }
                
                // Virtual keyboard handling
                this.handleVirtualKeyboard(searchInput);
            }
            
            addVoiceSearchButton(searchInput) {
                const voiceBtn = document.createElement('button');
                voiceBtn.className = 'voice-search-btn mobile-optimized';
                voiceBtn.innerHTML = '🎤';
                voiceBtn.title = 'Voice Search';
                
                voiceBtn.addEventListener('click', () => {
                    if ('webkitSpeechRecognition' in window) {
                        this.startVoiceRecognition(searchInput);
                    } else {
                        alert('Voice search not supported on this device');
                    }
                });
                
                searchInput.parentNode.insertBefore(voiceBtn, searchInput.nextSibling);
            }
            
            addCameraSearchButton(searchInput) {
                const cameraBtn = document.createElement('button');
                cameraBtn.className = 'camera-search-btn mobile-optimized';
                cameraBtn.innerHTML = '📷';
                cameraBtn.title = 'Camera Search';
                
                cameraBtn.addEventListener('click', () => {
                    this.openCameraSearch();
                });
                
                searchInput.parentNode.insertBefore(cameraBtn, searchInput.nextSibling);
            }
            
            startVoiceRecognition(input) {
                const recognition = new webkitSpeechRecognition();
                recognition.continuous = false;
                recognition.lang = 'en-US';
                
                recognition.onresult = (event) => {
                    const result = event.results[0][0].transcript;
                    input.value = result;
                    input.dispatchEvent(new Event('input'));
                };
                
                recognition.start();
            }
            
            openCameraSearch() {
                // Create camera input
                const cameraInput = document.createElement('input');
                cameraInput.type = 'file';
                cameraInput.accept = 'image/*';
                cameraInput.capture = 'environment';
                
                cameraInput.addEventListener('change', (e) => {
                    const file = e.target.files[0];
                    if (file) {
                        this.processImageSearch(file);
                    }
                });
                
                cameraInput.click();
            }
            
            processImageSearch(file) {
                // Upload image for AI identification
                const formData = new FormData();
                formData.append('image', file);
                
                fetch('/api/identify-orchid', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(result => {
                    if (result.scientific_name) {
                        const searchInput = document.querySelector('.search-widget input');
                        searchInput.value = result.scientific_name;
                        searchInput.dispatchEvent(new Event('input'));
                    }
                })
                .catch(error => {
                    console.error('Image search failed:', error);
                });
            }
            
            handleVirtualKeyboard(input) {
                // Adjust layout when virtual keyboard appears
                let initialViewportHeight = window.innerHeight;
                
                window.addEventListener('resize', () => {
                    const currentHeight = window.innerHeight;
                    const heightDifference = initialViewportHeight - currentHeight;
                    
                    // Virtual keyboard likely appeared
                    if (heightDifference > 150) {
                        document.body.classList.add('virtual-keyboard-open');
                        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    } else {
                        document.body.classList.remove('virtual-keyboard-open');
                    }
                });
            }
            
            optimizeForMobile() {
                // Add mobile-specific CSS classes
                document.body.classList.add(`device-${this.config.device_type}`);
                
                if (this.config.touch_optimized) {
                    document.body.classList.add('touch-optimized');
                }
                
                // Optimize button sizes
                const buttons = document.querySelectorAll('button, .btn');
                buttons.forEach(btn => {
                    if (this.config.device_type === 'mobile') {
                        btn.style.minHeight = '44px';
                        btn.style.minWidth = '44px';
                        btn.style.fontSize = '16px';
                    }
                });
            }
            
            handleOrientationChange() {
                window.addEventListener('orientationchange', () => {
                    setTimeout(() => {
                        // Trigger widget resize/reflow
                        window.dispatchEvent(new Event('resize'));
                        
                        // Specific handling for different widgets
                        if (this.widgetType === 'weather') {
                            this.resizeWeatherCharts();
                        } else if (this.widgetType === 'map') {
                            this.resizeMap();
                        }
                    }, 100);
                });
            }
            
            resizeWeatherCharts() {
                const charts = document.querySelectorAll('.weather-chart canvas');
                charts.forEach(chart => {
                    // Trigger chart resize
                    if (chart.chart) {
                        chart.chart.resize();
                    }
                });
            }
            
            resizeMap() {
                // Trigger map resize
                const mapElement = document.querySelector('.map-widget');
                if (mapElement && mapElement.map) {
                    setTimeout(() => {
                        mapElement.map.getViewport().dispatchEvent(new Event('resize'));
                    }, 200);
                }
            }
            
            triggerMapZoom(e) {
                // Zoom map at touch point
                const mapElement = document.querySelector('.map-widget');
                if (mapElement && mapElement.map) {
                    const rect = mapElement.getBoundingClientRect();
                    const x = e.changedTouches[0].clientX - rect.left;
                    const y = e.changedTouches[0].clientY - rect.top;
                    
                    // Zoom in at touch coordinates
                    mapElement.map.getView().animate({
                        zoom: mapElement.map.getView().getZoom() + 1,
                        center: mapElement.map.getCoordinateFromPixel([x, y]),
                        duration: 300
                    });
                }
            }
            
            navigateGallery(direction) {
                const gallery = document.querySelector('.gallery-widget-container');
                const currentIndex = parseInt(gallery.dataset.currentIndex || 0);
                const totalItems = gallery.querySelectorAll('.gallery-item').length;
                
                let newIndex;
                if (direction === 'next') {
                    newIndex = (currentIndex + 1) % totalItems;
                } else {
                    newIndex = (currentIndex - 1 + totalItems) % totalItems;
                }
                
                gallery.dataset.currentIndex = newIndex;
                
                // Trigger gallery update
                const event = new CustomEvent('galleryNavigate', {
                    detail: { index: newIndex, direction: direction }
                });
                gallery.dispatchEvent(event);
            }
        }
        
        // Auto-initialize mobile controls when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize for each widget type found on page
            const widgetTypes = ['map', 'gallery', 'weather', 'search', 'comparison'];
            
            widgetTypes.forEach(type => {
                const widget = document.querySelector(`.${type}-widget-container`);
                if (widget) {
                    fetch(`/api/mobile-config/${type}`)
                        .then(response => response.json())
                        .then(config => {
                            new MobileWidgetControls(type, config);
                        })
                        .catch(error => {
                            console.error(`Failed to load mobile config for ${type}:`, error);
                        });
                }
            });
        });
        """
        
        return js_code
    
    def get_mobile_css(self) -> str:
        """Generate CSS for mobile widget optimization"""
        css = """
        /* Mobile Widget Optimization CSS */
        
        /* Base mobile styles */
        .device-mobile {
            font-size: 16px; /* Prevent zoom on input focus */
        }
        
        .touch-optimized button,
        .touch-optimized .btn {
            min-height: 44px;
            min-width: 44px;
            padding: 12px 16px;
        }
        
        .touch-optimized input,
        .touch-optimized select,
        .touch-optimized textarea {
            min-height: 44px;
            font-size: 16px;
            padding: 12px;
        }
        
        /* Gallery widget mobile styles */
        .device-mobile .gallery-widget-container {
            padding: 8px;
        }
        
        .device-mobile .gallery-grid {
            grid-template-columns: 1fr;
            gap: 16px;
        }
        
        .device-mobile .gallery-item {
            border-radius: 12px;
            overflow: hidden;
        }
        
        .device-mobile .gallery-item img {
            width: 100%;
            height: auto;
            max-height: 300px;
            object-fit: cover;
        }
        
        /* Map widget mobile styles */
        .device-mobile .map-widget-container {
            height: 300px;
            position: relative;
        }
        
        .device-mobile .map-controls {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }
        
        .device-mobile .map-controls button {
            background: rgba(255, 255, 255, 0.9);
            border: none;
            border-radius: 8px;
            width: 44px;
            height: 44px;
            margin-bottom: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        /* Weather widget mobile styles */
        .device-mobile .weather-widget-container {
            padding: 16px 8px;
        }
        
        .device-mobile .weather-chart {
            height: 250px;
            margin-bottom: 16px;
            position: relative;
        }
        
        .device-mobile .weather-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }
        
        .device-mobile .weather-controls button {
            flex: 1;
            min-width: 120px;
            font-size: 14px;
        }
        
        .device-mobile .touch-indicator {
            position: absolute;
            bottom: 8px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 10;
        }
        
        /* Search widget mobile styles */
        .device-mobile .search-widget-container {
            padding: 16px;
        }
        
        .device-mobile .search-input-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .device-mobile .search-input-group input {
            flex: 1;
            border-radius: 12px;
            border: 2px solid #ddd;
        }
        
        .device-mobile .voice-search-btn,
        .device-mobile .camera-search-btn {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: none;
            background: #007bff;
            color: white;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .device-mobile .search-suggestions {
            margin-top: 16px;
            border-radius: 12px;
            background: #f8f9fa;
            padding: 16px;
        }
        
        .device-mobile .search-suggestion {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            background: white;
            border: 1px solid #ddd;
            cursor: pointer;
        }
        
        /* Comparison widget mobile styles */
        .device-mobile .comparison-widget-container {
            padding: 16px;
        }
        
        .device-mobile .comparison-layout {
            flex-direction: column;
        }
        
        .device-mobile .comparison-item {
            margin-bottom: 24px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .device-mobile .comparison-details {
            padding: 16px;
        }
        
        .device-mobile .comparison-toggle {
            width: 100%;
            padding: 12px;
            background: #f8f9fa;
            border: none;
            text-align: left;
            font-weight: bold;
        }
        
        .device-mobile .comparison-content {
            padding: 16px;
            display: none;
        }
        
        .device-mobile .comparison-content.expanded {
            display: block;
        }
        
        /* Virtual keyboard handling */
        .virtual-keyboard-open {
            padding-bottom: 50vh;
        }
        
        .virtual-keyboard-open .fixed-bottom {
            bottom: 50vh;
        }
        
        /* Swipe indicators */
        .swipe-indicator {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.5);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 14px;
            z-index: 1000;
            pointer-events: none;
        }
        
        .swipe-indicator.left {
            left: 16px;
        }
        
        .swipe-indicator.right {
            right: 16px;
        }
        
        /* Loading states for mobile */
        .mobile-loading {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
            font-size: 18px;
        }
        
        .mobile-loading::before {
            content: '🌺';
            animation: spin 2s linear infinite;
            margin-right: 12px;
            font-size: 24px;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        /* Tablet specific adjustments */
        .device-tablet .gallery-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .device-tablet .weather-controls button {
            min-width: 150px;
        }
        
        .device-tablet .map-widget-container {
            height: 400px;
        }
        
        /* Landscape orientation */
        @media screen and (orientation: landscape) {
            .device-mobile .map-widget-container {
                height: 250px;
            }
            
            .device-mobile .weather-chart {
                height: 200px;
            }
        }
        """
        
        return css


# Global instance
mobile_optimizer = MobileWidgetOptimizer()