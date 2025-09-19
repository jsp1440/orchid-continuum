/**
 * Simplified Orchid Mahjong - Control Panel Only
 * Starting with a working control panel to debug the main file
 */

(function() {
    'use strict';

    // Namespace for the widget
    window.OrchidMahjong = window.OrchidMahjong || {};

    /**
     * Simple Orchid Mahjong Game Class
     */
    class OrchidMahjongGame {
        constructor(container, options = {}) {
            this.container = typeof container === 'string' ? document.querySelector(container) : container;
            this.options = {
                theme: 'fcos',
                layout: 'turtle',
                difficulty: 'normal',
                sound: false,
                music: false,
                ...options
            };

            // Initialize control panel immediately
            this.createControlPanel();
        }

        /**
         * Create control panel for game setup
         */
        createControlPanel() {
            this.container.innerHTML = `
                <div class="orchid-mahjong-control-panel">
                    <div class="control-header">
                        <h2>🌺 Orchid Mahjong Solitaire</h2>
                        <p>Configure your game settings and start playing with real orchid photos!</p>
                    </div>
                    
                    <div class="control-sections">
                        <div class="control-section">
                            <h3>🎨 Visual Settings</h3>
                            <div class="setting-group">
                                <label for="theme-select">Theme:</label>
                                <select id="theme-select">
                                    <option value="fcos">Five Cities Orchid Society</option>
                                    <option value="neutral">Classic Neutral</option>
                                    <option value="highContrast">High Contrast</option>
                                </select>
                            </div>
                            <div class="setting-group">
                                <label for="layout-select">Layout:</label>
                                <select id="layout-select">
                                    <option value="turtle">Turtle (Normal)</option>
                                    <option value="orchid">Orchid Bloom (Normal)</option>
                                    <option value="pyramid">Pyramid (Easy)</option>
                                    <option value="dragon">Dragon (Hard)</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="control-section">
                            <h3>🎮 Game Settings</h3>
                            <div class="setting-group">
                                <label for="difficulty-select">Difficulty:</label>
                                <select id="difficulty-select">
                                    <option value="easy">Easy (Extra hints)</option>
                                    <option value="normal" selected>Normal</option>
                                    <option value="hard">Hard (Limited hints)</option>
                                    <option value="expert">Expert (No hints)</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="control-section">
                            <h3>🔊 Audio Settings</h3>
                            <div class="setting-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="sound-effects"> Sound Effects
                                </label>
                            </div>
                            <div class="setting-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="background-music"> Background Music
                                </label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="control-actions">
                        <button class="start-game-btn" id="start-game">🎮 Start Game</button>
                        <button class="preview-btn" id="preview-tiles">👁️ Preview Orchids</button>
                        <button class="reset-btn" id="reset-settings">🔄 Reset to Defaults</button>
                    </div>
                </div>
            `;
            
            this.bindControlPanelEvents();
        }
        
        /**
         * Bind control panel events
         */
        bindControlPanelEvents() {
            const startBtn = this.container.querySelector('#start-game');
            const previewBtn = this.container.querySelector('#preview-tiles');
            const resetBtn = this.container.querySelector('#reset-settings');
            
            if (startBtn) {
                startBtn.addEventListener('click', () => this.startGame());
            }
            
            if (previewBtn) {
                previewBtn.addEventListener('click', () => this.previewOrchids());
            }
            
            if (resetBtn) {
                resetBtn.addEventListener('click', () => this.resetSettings());
            }
        }
        
        /**
         * Start the game
         */
        startGame() {
            // Collect settings
            this.options.theme = this.container.querySelector('#theme-select').value;
            this.options.layout = this.container.querySelector('#layout-select').value;
            this.options.difficulty = this.container.querySelector('#difficulty-select').value;
            this.options.sound = this.container.querySelector('#sound-effects').checked;
            this.options.music = this.container.querySelector('#background-music').checked;
            
            // Show game board placeholder
            this.container.innerHTML = `
                <div class="orchid-mahjong-widget" data-theme="${this.options.theme}">
                    <div class="game-header">
                        <h2>🌺 Orchid Mahjong - ${this.options.layout} Layout</h2>
                        <p>Theme: ${this.options.theme} | Difficulty: ${this.options.difficulty}</p>
                        <button onclick="location.reload()">🔄 Back to Settings</button>
                    </div>
                    <div class="game-board" style="text-align: center; padding: 50px;">
                        <h3>🎮 Game Board Will Load Here</h3>
                        <p>Settings applied successfully!</p>
                        <p>Theme: ${this.options.theme}</p>
                        <p>Layout: ${this.options.layout}</p>
                        <p>Difficulty: ${this.options.difficulty}</p>
                        <p>Sound: ${this.options.sound ? 'On' : 'Off'}</p>
                        <p>Music: ${this.options.music ? 'On' : 'Off'}</p>
                    </div>
                </div>
            `;
        }
        
        /**
         * Preview orchid tiles
         */
        async previewOrchids() {
            alert('🌺 Orchid preview would show real photos from Google Drive here!');
        }
        
        /**
         * Reset settings to defaults
         */
        resetSettings() {
            this.container.querySelector('#theme-select').value = 'fcos';
            this.container.querySelector('#layout-select').value = 'turtle';
            this.container.querySelector('#difficulty-select').value = 'normal';
            this.container.querySelector('#sound-effects').checked = false;
            this.container.querySelector('#background-music').checked = false;
        }
    }

    /**
     * Public API
     */
    window.OrchidMahjong.init = function(selector, options) {
        const container = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (!container) {
            console.error('OrchidMahjong: Container not found');
            return null;
        }
        
        return new OrchidMahjongGame(container, options);
    };

    window.OrchidMahjong.Game = OrchidMahjongGame;

    // Auto-initialize if data attributes are present
    document.addEventListener('DOMContentLoaded', () => {
        const elements = document.querySelectorAll('[data-orchid-mahjong]');
        elements.forEach(element => {
            const options = {};
            if (element.dataset.theme) options.theme = element.dataset.theme;
            if (element.dataset.layout) options.layout = element.dataset.layout;
            
            window.OrchidMahjong.init(element, options);
        });
    });

})();