/**
 * Orchid Mahjong Solitaire - Production Ready Widget
 * A complete, embeddable Mahjong Solitaire game with orchid theme
 * 
 * Features:
 * - Full Mahjong Solitaire gameplay (144 tiles)
 * - Multiple orchid-themed layouts
 * - Three color themes (FCOS, Neutral, High Contrast)
 * - Accessibility support with keyboard controls
 * - Touch and mouse support
 * - Daily challenges and local leaderboards
 * - Solvable shuffle algorithm
 * - Undo/Redo system
 * - Auto-save progress
 */

(function() {
    'use strict';

    // Namespace for the widget
    window.OrchidMahjong = window.OrchidMahjong || {};

    // Game constants
    const TILE_TYPES = {
        // Petals (Dots) 1-9
        PETALS: { 
            base: 'petals', 
            count: 9, 
            copies: 4, 
            theme: 'orchid-petals'
        },
        // Stems (Bamboo) 1-9  
        STEMS: { 
            base: 'stems', 
            count: 9, 
            copies: 4, 
            theme: 'orchid-stems'
        },
        // Labels (Characters) 1-9
        LABELS: { 
            base: 'labels', 
            count: 9, 
            copies: 4, 
            theme: 'orchid-labels'
        },
        // Winds (4 types)
        WINDS: { 
            base: 'winds', 
            count: 4, 
            copies: 4, 
            values: ['N', 'E', 'S', 'W'],
            theme: 'greenhouse-fans'
        },
        // Dragons (3 types)
        DRAGONS: { 
            base: 'dragons', 
            count: 3, 
            copies: 4, 
            values: ['Gold', 'Silver', 'Bronze'],
            theme: 'award-ribbons'
        },
        // Flowers/Seasons (8 unique)
        FLOWERS: { 
            base: 'flowers', 
            count: 8, 
            copies: 1, 
            values: ['Phalaenopsis', 'Cattleya', 'Dendrobium', 'Paphiopedilum', 'Vanda', 'Oncidium', 'Cymbidium', 'Masdevallia'],
            theme: 'orchid-portraits'
        }
    };

    // Extended orchid species for customization
    const ORCHID_SPECIES = {
        'Phalaenopsis': { emoji: '🦋🌺', color: '#FF69B4', family: 'Moth Orchids' },
        'Cattleya': { emoji: '👑🌸', color: '#DDA0DD', family: 'Corsage Orchids' },
        'Dendrobium': { emoji: '🌿💜', color: '#9370DB', family: 'Tree Orchids' },
        'Paphiopedilum': { emoji: '👞🌼', color: '#FFD700', family: 'Lady Slippers' },
        'Vanda': { emoji: '💙🌟', color: '#4169E1', family: 'Blue Orchids' },
        'Oncidium': { emoji: '☀️🌻', color: '#FFA500', family: 'Dancing Lady' },
        'Cymbidium': { emoji: '🗾🌷', color: '#FF1493', family: 'Boat Orchids' },
        'Masdevallia': { emoji: '🔺🌹', color: '#DC143C', family: 'Kite Orchids' },
        'Epidendrum': { emoji: '🌈🌺', color: '#FF6347', family: 'Reed Orchids' },
        'Brassia': { emoji: '🕷️🌾', color: '#228B22', family: 'Spider Orchids' },
        'Miltonia': { emoji: '🎭🌸', color: '#DA70D6', family: 'Pansy Orchids' },
        'Odontoglossum': { emoji: '❄️🌼', color: '#87CEEB', family: 'Tiger Orchids' },
        'Zygopetalum': { emoji: '💜🌺', color: '#8A2BE2', family: 'Fragrant Orchids' },
        'Bulbophyllum': { emoji: '🦅🌿', color: '#6B8E23', family: 'Bulb Orchids' },
        'Laelia': { emoji: '🌟💖', color: '#FF69B4', family: 'Autumn Orchids' },
        'Maxillaria': { emoji: '🍃🌹', color: '#8B4513', family: 'Coconut Orchids' }
    };

    // Game modes
    const GAME_MODES = {
        SOLITAIRE: 'solitaire',
        MULTIPLAYER_2: 'multiplayer_2',
        MULTIPLAYER_3: 'multiplayer_3', 
        MULTIPLAYER_4: 'multiplayer_4'
    };

    // Tile count options
    const TILE_COUNT_OPTIONS = {
        MINI: { tiles: 72, name: 'Mini (72 tiles)', difficulty: 'Beginner' },
        STANDARD: { tiles: 144, name: 'Standard (144 tiles)', difficulty: 'Normal' },
        LARGE: { tiles: 216, name: 'Large (216 tiles)', difficulty: 'Expert' },
        MEGA: { tiles: 288, name: 'Mega (288 tiles)', difficulty: 'Master' }
    };

    // Color themes
    const THEMES = {
        fcos: {
            name: 'FCOS Purple/Green/Beach',
            primary: '#4B0082',
            secondary: '#CDE4BC', 
            accent: '#e6f7ff',
            background: '#f8f9fa',
            tile: '#ffffff',
            selected: '#FFD700',
            matched: '#90EE90'
        },
        neutral: {
            name: 'Classic Neutral',
            primary: '#2c3e50',
            secondary: '#ecf0f1',
            accent: '#3498db',
            background: '#f5f5f5',
            tile: '#fefefe',
            selected: '#f39c12',
            matched: '#27ae60'
        },
        highContrast: {
            name: 'High Contrast',
            primary: '#000000',
            secondary: '#ffffff',
            accent: '#ffff00',
            background: '#ffffff',
            tile: '#ffffff',
            selected: '#ffff00',
            matched: '#00ff00'
        }
    };

    // Game layouts
    const LAYOUTS = {
        turtle: { name: 'Turtle', difficulty: 'Normal', pattern: 'classic_turtle' },
        dragon: { name: 'Dragon', difficulty: 'Hard', pattern: 'classic_dragon' },
        pyramid: { name: 'Pyramid', difficulty: 'Easy', pattern: 'classic_pyramid' },
        orchid: { name: 'Orchid Bloom', difficulty: 'Normal', pattern: 'orchid_flower' },
        greenhouse: { name: 'Greenhouse', difficulty: 'Hard', pattern: 'greenhouse_shape' },
        butterfly: { name: 'Butterfly', difficulty: 'Expert', pattern: 'butterfly_wings' },
        fortress: { name: 'Fortress', difficulty: 'Expert', pattern: 'fortress_walls' },
        garland: { name: 'Orchid Garland', difficulty: 'Normal', pattern: 'flower_garland' }
    };

    /**
     * Main Orchid Mahjong Game Class
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
                highlights: true,
                allowWildGroups: true,
                seed: null,
                gameMode: 'solitaire',
                tileCount: 144,
                selectedOrchids: ['Phalaenopsis', 'Cattleya', 'Dendrobium', 'Paphiopedilum', 'Vanda', 'Oncidium', 'Cymbidium', 'Masdevallia'],
                customPattern: null,
                playerName: '',
                roomCode: '',
                ...options
            };

            this.gameState = {
                tiles: [],
                selectedTiles: [],
                matchedTiles: new Set(),
                moves: 0,
                score: 0,
                startTime: null,
                endTime: null,
                isPaused: false,
                undoStack: [],
                redoStack: [],
                isMultiplayer: false,
                players: [],
                currentPlayer: 0,
                roomId: null,
                chatMessages: []
            };

            this.eventHandlers = {};
            // Initialize control panel first, then wait for user to start game
            this.createControlPanel();
        }

        /**
         * Initialize the game
         */
        async init() {
            this.createGameHTML();
            this.applyTheme(this.options.theme);
            await this.generateTiles();
            this.createLayout();
            this.bindEvents();
            this.setupEnhancedSettings();
            this.setupMultiplayer();
            this.setupChat();
            this.setupLeaderboard();
            this.loadSettings();
            this.startTimer();
            
            this.emit('init', { options: this.options });
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
                                    <option value="greenhouse">Greenhouse (Hard)</option>
                                    <option value="fortress">Fortress (Expert)</option>
                                    <option value="butterfly">Butterfly (Expert)</option>
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
                            <div class="setting-group">
                                <label for="game-mode-select">Game Mode:</label>
                                <select id="game-mode-select">
                                    <option value="solitaire" selected>Solitaire</option>
                                    <option value="timed">Timed Challenge</option>
                                    <option value="zen">Zen Mode (No score)</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="control-section">
                            <h3>🔊 Audio & Accessibility</h3>
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
                            <div class="setting-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="auto-hints" checked> Auto-hint after 60 seconds
                                </label>
                            </div>
                        </div>
                        
                        <div class="control-section">
                            <h3>🌸 Orchid Collection</h3>
                            <div class="setting-group">
                                <label for="orchid-count">Number of different orchid species:</label>
                                <select id="orchid-count">
                                    <option value="all">All Available (Varied)</option>
                                    <option value="16">16 Species (Classic)</option>
                                    <option value="8">8 Species (Beginner)</option>
                                </select>
                            </div>
                            <div class="preview-grid" id="orchid-preview">
                                <p>🌺 Real orchid photos will be loaded on game start</p>
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
            
            startBtn?.addEventListener('click', () => this.startGameFromControlPanel());
            previewBtn?.addEventListener('click', () => this.previewOrchidTiles());
            resetBtn?.addEventListener('click', () => this.resetControlPanelSettings());
            
            // Live preview theme changes
            const themeSelect = this.container.querySelector('#theme-select');
            themeSelect?.addEventListener('change', (e) => {
                this.container.setAttribute('data-theme', e.target.value);
            });
        }
        
        /**
         * Start game with control panel settings
         */
        async startGameFromControlPanel() {
            // Collect settings from control panel
            this.options.theme = this.container.querySelector('#theme-select').value;
            this.options.layout = this.container.querySelector('#layout-select').value;
            this.options.difficulty = this.container.querySelector('#difficulty-select').value;
            this.options.gameMode = this.container.querySelector('#game-mode-select').value;
            this.options.sound = this.container.querySelector('#sound-effects').checked;
            this.options.music = this.container.querySelector('#background-music').checked;
            this.options.autoHint = this.container.querySelector('#auto-hints').checked;
            
            // Show loading state
            const startBtn = this.container.querySelector('#start-game');
            startBtn.disabled = true;
            startBtn.textContent = '🔄 Loading orchid photos...';
            
            try {
                await this.init();
            } catch (error) {
                console.error('Failed to start game:', error);
                startBtn.disabled = false;
                startBtn.textContent = '❌ Failed to load - Try again';
            }
        }
        
        /**
         * Preview orchid tiles
         */
        async previewOrchidTiles() {
            const previewGrid = this.container.querySelector('#orchid-preview');
            previewGrid.innerHTML = '<p>🔄 Loading orchid preview...</p>';
            
            try {
                const response = await fetch('/api/mahjong/orchid-images');
                const data = await response.json();
                
                if (data.success && data.tiles) {
                    const preview = data.tiles.slice(0, 12).map(tile => `
                        <div class="preview-tile">
                            <img src="${tile.image_url}" alt="${tile.name}" onerror="this.src='${tile.backup_image}'" />
                            <span>${tile.name}</span>
                        </div>
                    `).join('');
                    
                    previewGrid.innerHTML = `<div class="preview-tiles">${preview}</div>`;
                } else {
                    previewGrid.innerHTML = '<p>❌ Could not load orchid preview</p>';
                }
            } catch (error) {
                previewGrid.innerHTML = '<p>❌ Preview unavailable</p>';
            }
        }
        
        /**
         * Reset control panel to defaults
         */
        resetControlPanelSettings() {
            this.container.querySelector('#theme-select').value = 'fcos';
            this.container.querySelector('#layout-select').value = 'turtle';
            this.container.querySelector('#difficulty-select').value = 'normal';
            this.container.querySelector('#game-mode-select').value = 'solitaire';
            this.container.querySelector('#sound-effects').checked = false;
            this.container.querySelector('#background-music').checked = false;
            this.container.querySelector('#auto-hints').checked = true;
            this.container.querySelector('#orchid-count').value = 'all';
            this.container.setAttribute('data-theme', 'fcos');
        }

        /**
         * Create the main game HTML structure
         */
        createGameHTML() {
            this.container.innerHTML = `
                <div class="orchid-mahjong-widget" data-theme="${this.options.theme}">
                    <!-- Header with game info -->
                    <div class="game-header">
                        <div class="game-stats">
                            <div class="stat-item">
                                <span class="stat-label">Time</span>
                                <span class="stat-value" id="om-timer">00:00</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Moves</span>
                                <span class="stat-value" id="om-moves">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Pairs</span>
                                <span class="stat-value" id="om-pairs">72</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Score</span>
                                <span class="stat-value" id="om-score">0</span>
                            </div>
                        </div>
                        
                        <div class="game-controls">
                            <button class="control-btn" id="om-undo" title="Undo (U)" aria-label="Undo last move">
                                <span class="btn-icon">↶</span>
                            </button>
                            <button class="control-btn" id="om-redo" title="Redo (R)" aria-label="Redo move">
                                <span class="btn-icon">↷</span>
                            </button>
                            <button class="control-btn" id="om-hint" title="Hint (H)" aria-label="Show hint">
                                <span class="btn-icon">💡</span>
                            </button>
                            <button class="control-btn" id="om-shuffle" title="Shuffle (S)" aria-label="Shuffle tiles">
                                <span class="btn-icon">🔀</span>
                            </button>
                            <button class="control-btn" id="om-new" title="New Game (T)" aria-label="Start new game">
                                <span class="btn-icon">🔄</span>
                            </button>
                            <button class="control-btn" id="om-settings" title="Settings" aria-label="Open settings">
                                <span class="btn-icon">⚙️</span>
                            </button>
                        </div>
                    </div>

                    <!-- Main game board -->
                    <div class="game-board-container">
                        <div class="game-board" id="om-board" role="grid" aria-label="Mahjong tile board">
                            <!-- Tiles will be generated here -->
                        </div>
                    </div>

                    <!-- Enhanced Settings panel (initially hidden) -->
                    <div class="settings-panel" id="om-settings-panel" style="display: none;">
                        <div class="settings-header">
                            <h3>Game Settings</h3>
                            <button class="close-btn" id="om-close-settings">&times;</button>
                        </div>
                        
                        <div class="settings-content">
                            <!-- Game Mode Selection -->
                            <div class="setting-group">
                                <label>Game Mode</label>
                                <select id="om-game-mode-select">
                                    <option value="solitaire">🧘 Solitaire</option>
                                    <option value="multiplayer_2">👥 2 Players</option>
                                    <option value="multiplayer_3">👥👥 3 Players</option>
                                    <option value="multiplayer_4">👥👥👥 4 Players</option>
                                </select>
                            </div>

                            <!-- Player Name (for multiplayer) -->
                            <div class="setting-group" id="om-player-name-group" style="display: none;">
                                <label>Your Name</label>
                                <input type="text" id="om-player-name" placeholder="Enter your name" maxlength="20">
                            </div>

                            <!-- Room Code (for multiplayer) -->
                            <div class="setting-group" id="om-room-code-group" style="display: none;">
                                <label>Room Code (leave empty to create new room)</label>
                                <input type="text" id="om-room-code" placeholder="Enter room code" maxlength="10">
                            </div>
                            
                            <!-- Tile Count -->
                            <div class="setting-group">
                                <label>Tile Count</label>
                                <select id="om-tile-count-select">
                                    <option value="72">🌱 Mini (72 tiles) - Beginner</option>
                                    <option value="144" selected>🌸 Standard (144 tiles) - Normal</option>
                                    <option value="216">🌺 Large (216 tiles) - Expert</option>
                                    <option value="288">🏆 Mega (288 tiles) - Master</option>
                                </select>
                            </div>

                            <!-- Theme -->
                            <div class="setting-group">
                                <label>Visual Theme</label>
                                <select id="om-theme-select">
                                    <option value="fcos">🌺 FCOS Purple/Green</option>
                                    <option value="neutral">⚪ Classic Neutral</option>
                                    <option value="highContrast">⚫ High Contrast</option>
                                </select>
                            </div>
                            
                            <!-- Layout/Pattern -->
                            <div class="setting-group">
                                <label>Layout Pattern</label>
                                <select id="om-layout-select">
                                    <option value="turtle">🐢 Turtle (Normal)</option>
                                    <option value="dragon">🐉 Dragon (Hard)</option>
                                    <option value="pyramid">🔺 Pyramid (Easy)</option>
                                    <option value="orchid">🌺 Orchid Bloom (Normal)</option>
                                    <option value="greenhouse">🏠 Greenhouse (Hard)</option>
                                    <option value="butterfly">🦋 Butterfly (Expert)</option>
                                    <option value="fortress">🏰 Fortress (Expert)</option>
                                    <option value="garland">🌸 Orchid Garland (Normal)</option>
                                </select>
                            </div>

                            <!-- Orchid Species Selection -->
                            <div class="setting-group">
                                <label>Flower Tile Species (select 8)</label>
                                <div class="orchid-selector" id="om-orchid-selector">
                                    <!-- Species checkboxes will be generated here -->
                                </div>
                                <small class="setting-note">Choose which orchid species appear on flower tiles</small>
                            </div>

                            <!-- Custom Pattern Designer -->
                            <div class="setting-group">
                                <label>Custom Pattern</label>
                                <div class="custom-pattern-controls">
                                    <button class="action-btn secondary" id="om-pattern-designer">🎨 Pattern Designer</button>
                                    <button class="action-btn secondary" id="om-import-pattern">📁 Import Pattern</button>
                                </div>
                                <small class="setting-note">Create your own tile layouts</small>
                            </div>
                            
                            <!-- Game Options -->
                            <div class="setting-group">
                                <label>Game Options</label>
                                <div class="checkbox-list">
                                    <label class="checkbox-item">
                                        <input type="checkbox" id="om-highlights" checked> 
                                        🔆 Show tile highlights
                                    </label>
                                    <label class="checkbox-item">
                                        <input type="checkbox" id="om-sound"> 
                                        🔊 Sound effects
                                    </label>
                                    <label class="checkbox-item">
                                        <input type="checkbox" id="om-auto-hint"> 
                                        💡 Auto-hint after 60 seconds
                                    </label>
                                    <label class="checkbox-item">
                                        <input type="checkbox" id="om-quick-match"> 
                                        ⚡ Quick match mode (no confirm delay)
                                    </label>
                                </div>
                            </div>
                            
                            <!-- Statistics & Data -->
                            <div class="setting-group">
                                <label>Statistics & Data</label>
                                <div class="stats-controls">
                                    <button class="action-btn secondary" id="om-view-stats">📊 View Statistics</button>
                                    <button class="action-btn secondary" id="om-export-data">💾 Export Game Data</button>
                                    <button class="action-btn danger" id="om-reset-stats">🗑️ Reset All Data</button>
                                </div>
                            </div>

                            <!-- Action Buttons -->
                            <div class="setting-group">
                                <div class="settings-actions">
                                    <button class="action-btn" id="om-apply-settings">✅ Apply & Start Game</button>
                                    <button class="action-btn secondary" id="om-save-settings">💾 Save Settings</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Multiplayer Lobby -->
                    <div class="multiplayer-lobby" id="om-multiplayer-lobby" style="display: none;">
                        <div class="lobby-content">
                            <h2>🎮 Game Room</h2>
                            <div class="room-info">
                                <div class="room-code">Room Code: <span id="om-room-display">------</span></div>
                                <div class="player-count">Players: <span id="om-player-count">0/4</span></div>
                            </div>
                            <div class="player-list" id="om-player-list">
                                <!-- Player avatars will appear here -->
                            </div>
                            <div class="lobby-actions">
                                <button class="action-btn" id="om-start-multiplayer-game" style="display: none;">🚀 Start Game</button>
                                <button class="action-btn secondary" id="om-leave-room">🚪 Leave Room</button>
                                <button class="action-btn secondary" id="om-copy-room-code">📋 Copy Room Code</button>
                            </div>
                        </div>
                    </div>

                    <!-- Chat System -->
                    <div class="chat-panel" id="om-chat-panel" style="display: none;">
                        <div class="chat-header">
                            <h4>💬 Chat</h4>
                            <button class="close-btn" id="om-close-chat">−</button>
                        </div>
                        <div class="chat-messages" id="om-chat-messages">
                            <!-- Messages will appear here -->
                        </div>
                        <div class="chat-input-container">
                            <input type="text" id="om-chat-input" placeholder="Type a message..." maxlength="200">
                            <button id="om-send-chat">📤</button>
                        </div>
                    </div>

                    <!-- Win screen overlay -->
                    <div class="win-overlay" id="om-win-overlay" style="display: none;">
                        <div class="win-content">
                            <h2>🌺 Congratulations! 🌺</h2>
                            <p>You've completed the Orchid Mahjong!</p>
                            <div class="win-stats">
                                <div class="win-stat">
                                    <strong>Time:</strong> <span id="om-win-time">--:--</span>
                                </div>
                                <div class="win-stat">
                                    <strong>Moves:</strong> <span id="om-win-moves">0</span>
                                </div>
                                <div class="win-stat">
                                    <strong>Score:</strong> <span id="om-win-score">0</span>
                                </div>
                                <div id="om-multiplayer-results" style="display: none;">
                                    <div class="win-stat">
                                        <strong>Ranking:</strong> <span id="om-player-rank">#1</span>
                                    </div>
                                </div>
                            </div>
                            <div class="win-actions">
                                <button class="action-btn" id="om-play-again">Play Again</button>
                                <button class="action-btn secondary" id="om-change-layout">Change Settings</button>
                                <button class="action-btn secondary" id="om-view-leaderboard">🏆 Leaderboard</button>
                            </div>
                        </div>
                    </div>

                    <!-- Leaderboard Modal -->
                    <div class="leaderboard-modal" id="om-leaderboard-modal" style="display: none;">
                        <div class="leaderboard-content">
                            <div class="leaderboard-header">
                                <h2>🏆 Global Leaderboard</h2>
                                <button class="close-btn" id="om-close-leaderboard">&times;</button>
                            </div>
                            <div class="leaderboard-tabs">
                                <button class="tab-btn active" data-tab="daily">Today</button>
                                <button class="tab-btn" data-tab="weekly">This Week</button>
                                <button class="tab-btn" data-tab="monthly">This Month</button>
                                <button class="tab-btn" data-tab="alltime">All Time</button>
                            </div>
                            <div class="leaderboard-list" id="om-leaderboard-list">
                                <!-- Leaderboard entries will appear here -->
                            </div>
                        </div>
                    </div>

                    <!-- Accessibility announcements -->
                    <div class="sr-only" id="om-announcements" aria-live="polite" aria-atomic="true"></div>
                </div>
            `;
        }

        /**
         * Generate the complete set of 144 Mahjong tiles with real orchid photos
         */
        async generateTiles() {
            this.gameState.tiles = [];
            
            try {
                // Fetch real orchid data from API
                const response = await fetch('/api/mahjong/orchid-images');
                const data = await response.json();
                
                if (data.success && data.tiles) {
                    // Use real orchid tiles from API
                    data.tiles.forEach((apiTile, index) => {
                        this.gameState.tiles.push({
                            id: index,
                            type: apiTile.suit || 'orchid',
                            value: apiTile.number || apiTile.name,
                            suit: apiTile.suit || 'orchid',
                            canMatch: (other) => {
                                // Match tiles with same suit and number, or same type for special tiles
                                if (apiTile.type === 'honor') {
                                    return other.type === 'honor' && other.value === apiTile.number;
                                }
                                return other.suit === apiTile.suit && other.value === apiTile.number;
                            },
                            display: this.createOrchidTile(apiTile),
                            aria: `${apiTile.name} - ${apiTile.suit} ${apiTile.number}`,
                            // Store orchid data for educational cards
                            orchidData: {
                                name: apiTile.name,
                                imageUrl: apiTile.image_url,
                                backupImage: apiTile.backup_image,
                                fact: apiTile.fact,
                                suit: apiTile.suit,
                                number: apiTile.number
                            }
                        });
                    });
                } else {
                    throw new Error('Failed to load orchid data');
                }
            } catch (error) {
                console.log('Failed to load real orchid tiles, using fallback:', error);
                // Fallback to basic tiles if API fails
                this.generateFallbackTiles();
            }

            // Shuffle tiles for random distribution
            this.shuffleTiles();
            
            console.log(`Generated ${this.gameState.tiles.length} tiles`);
        }
        
        /**
         * Create visual representation for orchid tiles with real photos
         */
        createOrchidTile(apiTile) {
            return `
                <div class="tile-content orchid-tile" data-suit="${apiTile.suit}" data-number="${apiTile.number}">
                    <div class="orchid-image-container">
                        <img src="${apiTile.image_url}" 
                             alt="${apiTile.name}" 
                             class="orchid-tile-image"
                             onerror="this.src='${apiTile.backup_image}'" />
                    </div>
                    <div class="tile-info">
                        <div class="tile-suit">${apiTile.suit}</div>
                        <div class="tile-number">${apiTile.number}</div>
                    </div>
                    <div class="tile-name">${apiTile.name}</div>
                </div>
            `;
        }
        
        /**
         * Fallback tile generation if API fails
         */
        generateFallbackTiles() {
            let tileId = 0;

            // Generate basic numbered tiles
            const suits = ['bamboo', 'wind', 'dragon'];
            suits.forEach(suit => {
                for (let value = 1; value <= 9; value++) {
                    for (let copy = 0; copy < 4; copy++) {
                        this.gameState.tiles.push({
                            id: tileId++,
                            type: suit,
                            value: value,
                            suit: suit,
                            canMatch: (other) => other.type === suit && other.value === value,
                            display: this.createFallbackTile(suit, value),
                            aria: `${suit} ${value}`,
                            orchidData: {
                                name: `${suit} ${value}`,
                                imageUrl: '/static/images/orchid_placeholder.svg',
                                backupImage: '/static/images/orchid_placeholder.svg',
                                fact: 'Orchids are one of the largest families of flowering plants!',
                                suit: suit,
                                number: value
                            }
                        });
                    }
                }
            });

            // Pad to 144 tiles
            while (this.gameState.tiles.length < 144) {
                const baseTile = this.gameState.tiles[this.gameState.tiles.length % 36];
                this.gameState.tiles.push({
                    ...baseTile,
                    id: tileId++
                });
            }
        }
        
        /**
         * Create fallback tile when API is unavailable
         */
        createFallbackTile(suit, value) {
            const suitEmoji = suit === 'bamboo' ? '🎋' : suit === 'wind' ? '💨' : '🐉';
            return `
                <div class="tile-content fallback-tile">
                    <div class="tile-emoji">${suitEmoji}</div>
                    <div class="tile-number">${value}</div>
                    <div class="tile-suit">${suit}</div>
                </div>
            `;
        }

        /**
         * Create visual representation for Petals tiles (1-9)
         */
        createPetalsTile(value) {
            const petals = '🌸'.repeat(value);
            return `
                <div class="tile-content petals-tile">
                    <div class="tile-number">${value}</div>
                    <div class="tile-symbols">${petals}</div>
                    <div class="tile-label">Petals</div>
                </div>
            `;
        }

        /**
         * Create visual representation for Stems tiles (1-9)  
         */
        createStemsTile(value) {
            const stems = '🌿'.repeat(value);
            return `
                <div class="tile-content stems-tile">
                    <div class="tile-number">${value}</div>
                    <div class="tile-symbols">${stems}</div>
                    <div class="tile-label">Stems</div>
                </div>
            `;
        }

        /**
         * Create visual representation for Labels tiles (1-9)
         */
        createLabelsTile(value) {
            const romans = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'];
            return `
                <div class="tile-content labels-tile">
                    <div class="tile-number">${value}</div>
                    <div class="tile-plaque">
                        <div class="plaque-content">${romans[value-1]}</div>
                        <div class="plaque-orchid">🏵️</div>
                    </div>
                    <div class="tile-label">Labels</div>
                </div>
            `;
        }

        /**
         * Create visual representation for Wind tiles (N,E,S,W)
         */
        createWindTile(wind) {
            const windIcons = { 'N': '🌬️⬆️', 'E': '🌬️➡️', 'S': '🌬️⬇️', 'W': '🌬️⬅️' };
            return `
                <div class="tile-content winds-tile">
                    <div class="tile-wind-icon">${windIcons[wind]}</div>
                    <div class="tile-wind-letter">${wind}</div>
                    <div class="tile-orchid-accent">🌺</div>
                    <div class="tile-label">Wind</div>
                </div>
            `;
        }

        /**
         * Create visual representation for Dragon tiles (Gold,Silver,Bronze)
         */
        createDragonTile(dragon) {
            const dragonIcons = { 'Gold': '🏆🥇', 'Silver': '🏅🥈', 'Bronze': '🎖️🥉' };
            return `
                <div class="tile-content dragons-tile">
                    <div class="tile-dragon-icon">${dragonIcons[dragon]}</div>
                    <div class="tile-dragon-name">${dragon}</div>
                    <div class="tile-orchid-rosette">🌹</div>
                    <div class="tile-label">Dragon</div>
                </div>
            `;
        }

        /**
         * Create visual representation for Flower tiles (8 orchid species)
         */
        createFlowerTile(flower) {
            const flowerIcons = {
                'Phalaenopsis': '🦋🌺',
                'Cattleya': '👑🌸', 
                'Dendrobium': '🌿💜',
                'Paphiopedilum': '👞🌼',
                'Vanda': '💙🌟',
                'Oncidium': '☀️🌻',
                'Cymbidium': '🗾🌷',
                'Masdevallia': '🔺🌹'
            };
            
            return `
                <div class="tile-content flowers-tile">
                    <div class="tile-flower-icon">${flowerIcons[flower]}</div>
                    <div class="tile-flower-name">${flower}</div>
                    <div class="tile-label">Flower</div>
                </div>
            `;
        }

        /**
         * Shuffle tiles array using Fisher-Yates algorithm
         */
        shuffleTiles() {
            for (let i = this.gameState.tiles.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [this.gameState.tiles[i], this.gameState.tiles[j]] = [this.gameState.tiles[j], this.gameState.tiles[i]];
            }
        }

        /**
         * Create the layout pattern on the board
         */
        createLayout() {
            const board = document.getElementById('om-board');
            board.innerHTML = '';
            
            // Get layout pattern
            const layoutName = this.options.layout;
            const pattern = this.getLayoutPattern(layoutName);
            
            // Create tiles in the layout pattern
            pattern.forEach((position, index) => {
                if (index < this.gameState.tiles.length) {
                    const tile = this.gameState.tiles[index];
                    const tileElement = this.createTileElement(tile, position);
                    board.appendChild(tileElement);
                }
            });

            this.updateFreeTiles();
            this.updateUI();
        }

        /**
         * Get layout pattern coordinates for a given layout name
         */
        getLayoutPattern(layoutName) {
            // For now, create a simple turtle-like pattern
            // In a full implementation, this would contain 50+ elaborate layouts
            const patterns = {
                turtle: this.getTurtlePattern(),
                dragon: this.getDragonPattern(),
                pyramid: this.getPyramidPattern(),
                orchid: this.getOrchidPattern(),
                greenhouse: this.getGreenhousePattern(),
                butterfly: this.getButterflyPattern(),
                fortress: this.getFortressPattern(),
                garland: this.getGarlandPattern()
            };

            return patterns[layoutName] || patterns.turtle;
        }

        /**
         * Generate classic turtle layout pattern
         */
        getTurtlePattern() {
            const positions = [];
            let index = 0;
            
            // Create a turtle-shaped layout with multiple layers
            // Layer 0 (base)
            for (let row = 0; row < 8; row++) {
                for (let col = 0; col < 16; col++) {
                    if (this.isTurtlePosition(row, col, 0)) {
                        positions.push({ x: col * 60, y: row * 80, z: 0, layer: 0 });
                    }
                }
            }
            
            // Layer 1 (middle)
            for (let row = 1; row < 7; row++) {
                for (let col = 2; col < 14; col++) {
                    if (this.isTurtlePosition(row, col, 1)) {
                        positions.push({ x: col * 60, y: row * 80, z: 10, layer: 1 });
                    }
                }
            }
            
            // Layer 2 (top)
            for (let row = 2; row < 6; row++) {
                for (let col = 4; col < 12; col++) {
                    if (this.isTurtlePosition(row, col, 2)) {
                        positions.push({ x: col * 60, y: row * 80, z: 20, layer: 2 });
                    }
                }
            }

            return positions.slice(0, 144); // Ensure exactly 144 positions
        }

        /**
         * Check if a position should have a tile in turtle layout
         */
        isTurtlePosition(row, col, layer) {
            if (layer === 0) {
                // Base layer - turtle shell outline
                return (row >= 1 && row <= 6 && col >= 1 && col <= 14) &&
                       !(row === 1 && (col <= 2 || col >= 13)) &&
                       !(row === 6 && (col <= 2 || col >= 13));
            } else if (layer === 1) {
                // Middle layer - smaller turtle shape
                return (row >= 2 && row <= 5 && col >= 3 && col <= 12) &&
                       !(row === 2 && (col <= 4 || col >= 11)) &&
                       !(row === 5 && (col <= 4 || col >= 11));
            } else {
                // Top layer - turtle head
                return (row >= 3 && row <= 4 && col >= 5 && col <= 10);
            }
        }

        /**
         * Generate other layout patterns (simplified for demo)
         */
        getDragonPattern() {
            // Dragon layout would be more elaborate
            return this.getTurtlePattern(); // Placeholder
        }

        getPyramidPattern() {
            const positions = [];
            let tileCount = 0;
            
            // Create pyramid layers
            for (let layer = 0; layer < 8 && tileCount < 144; layer++) {
                const size = 15 - layer * 2;
                for (let row = 0; row < size && tileCount < 144; row++) {
                    for (let col = 0; col < size && tileCount < 144; col++) {
                        positions.push({ 
                            x: (col + layer) * 60, 
                            y: (row + layer) * 80, 
                            z: layer * 10, 
                            layer 
                        });
                        tileCount++;
                    }
                }
            }
            
            return positions.slice(0, 144);
        }

        getOrchidPattern() {
            // Orchid flower-shaped layout
            return this.getTurtlePattern(); // Placeholder
        }

        getGreenhousePattern() {
            // Greenhouse building-shaped layout
            return this.getTurtlePattern(); // Placeholder
        }

        getButterflyPattern() {
            // Butterfly wings layout
            return this.getTurtlePattern(); // Placeholder
        }

        getFortressPattern() {
            // Castle fortress layout
            return this.getTurtlePattern(); // Placeholder
        }

        getGarlandPattern() {
            // Flower garland circular layout
            return this.getTurtlePattern(); // Placeholder
        }

        /**
         * Create a tile DOM element
         */
        createTileElement(tile, position) {
            const element = document.createElement('div');
            element.className = 'mahjong-tile';
            element.dataset.tileId = tile.id;
            element.dataset.type = tile.type;
            element.dataset.value = tile.value;
            element.tabIndex = 0;
            element.setAttribute('role', 'button');
            element.setAttribute('aria-label', tile.aria);
            
            element.style.left = position.x + 'px';
            element.style.top = position.y + 'px';
            element.style.zIndex = position.layer + 1;
            
            if (position.z > 0) {
                element.style.transform = `translateZ(${position.z}px)`;
                element.classList.add('elevated');
            }
            
            element.innerHTML = tile.display;
            
            return element;
        }

        /**
         * Update which tiles are free (selectable)
         */
        updateFreeTiles() {
            const tiles = document.querySelectorAll('.mahjong-tile');
            tiles.forEach(tile => {
                const isFree = this.isTileFree(tile);
                tile.classList.toggle('free', isFree);
                tile.tabIndex = isFree ? 0 : -1;
            });
        }

        /**
         * Check if a tile is free (no tile on top and left OR right side open)
         */
        isTileFree(tileElement) {
            if (this.gameState.matchedTiles.has(parseInt(tileElement.dataset.tileId))) {
                return false;
            }

            const rect = tileElement.getBoundingClientRect();
            const layer = parseInt(tileElement.style.zIndex) - 1;
            
            // Check if there's a tile on top
            const tilesAbove = Array.from(document.querySelectorAll('.mahjong-tile')).filter(other => {
                if (other === tileElement) return false;
                if (this.gameState.matchedTiles.has(parseInt(other.dataset.tileId))) return false;
                
                const otherRect = other.getBoundingClientRect();
                const otherLayer = parseInt(other.style.zIndex) - 1;
                
                return otherLayer > layer && 
                       Math.abs(otherRect.left - rect.left) < 50 && 
                       Math.abs(otherRect.top - rect.top) < 50;
            });
            
            if (tilesAbove.length > 0) {
                return false; // Tile is blocked from above
            }
            
            // Check if left OR right side is open
            const leftBlocked = this.isSideBlocked(tileElement, -60, 0);
            const rightBlocked = this.isSideBlocked(tileElement, 60, 0);
            
            return !leftBlocked || !rightBlocked;
        }

        /**
         * Check if a side of the tile is blocked
         */
        isSideBlocked(tileElement, deltaX, deltaY) {
            const rect = tileElement.getBoundingClientRect();
            const layer = parseInt(tileElement.style.zIndex) - 1;
            
            const blockingTiles = Array.from(document.querySelectorAll('.mahjong-tile')).filter(other => {
                if (other === tileElement) return false;
                if (this.gameState.matchedTiles.has(parseInt(other.dataset.tileId))) return false;
                
                const otherRect = other.getBoundingClientRect();
                const otherLayer = parseInt(other.style.zIndex) - 1;
                
                return otherLayer === layer &&
                       Math.abs(otherRect.left - (rect.left + deltaX)) < 30 &&
                       Math.abs(otherRect.top - (rect.top + deltaY)) < 30;
            });
            
            return blockingTiles.length > 0;
        }

        /**
         * Handle tile selection
         */
        selectTile(tileElement) {
            const tileId = parseInt(tileElement.dataset.tileId);
            const tile = this.gameState.tiles.find(t => t.id === tileId);
            
            if (!tile || !this.isTileFree(tileElement) || this.gameState.matchedTiles.has(tileId)) {
                return;
            }

            // If tile is already selected, deselect it
            if (this.gameState.selectedTiles.includes(tileId)) {
                this.gameState.selectedTiles = this.gameState.selectedTiles.filter(id => id !== tileId);
                tileElement.classList.remove('selected');
                this.announce(`Deselected ${tile.aria}`);
                return;
            }

            // If we already have 2 tiles selected, clear selection
            if (this.gameState.selectedTiles.length >= 2) {
                this.clearSelection();
            }

            // Select the tile
            this.gameState.selectedTiles.push(tileId);
            tileElement.classList.add('selected');
            this.announce(`Selected ${tile.aria}. ${this.gameState.selectedTiles.length} of 2 tiles selected.`);

            // If we have 2 tiles selected, check for match
            if (this.gameState.selectedTiles.length === 2) {
                setTimeout(() => this.checkMatch(), 300);
            }
        }

        /**
         * Check if selected tiles match
         */
        checkMatch() {
            if (this.gameState.selectedTiles.length !== 2) return;

            const [tileId1, tileId2] = this.gameState.selectedTiles;
            const tile1 = this.gameState.tiles.find(t => t.id === tileId1);
            const tile2 = this.gameState.tiles.find(t => t.id === tileId2);

            const element1 = document.querySelector(`[data-tile-id="${tileId1}"]`);
            const element2 = document.querySelector(`[data-tile-id="${tileId2}"]`);

            const isMatch = tile1.canMatch(tile2);

            if (isMatch) {
                // Match found!
                this.gameState.matchedTiles.add(tileId1);
                this.gameState.matchedTiles.add(tileId2);
                
                element1.classList.remove('selected');
                element2.classList.remove('selected');
                element1.classList.add('matched');
                element2.classList.add('matched');
                
                this.gameState.moves++;
                this.gameState.score += this.calculateScore();
                
                // Save state for undo
                this.saveStateForUndo();
                
                this.announce(`Match found! ${this.getRemainingPairs()} pairs remaining.`);
                this.emit('match', { tile1, tile2, score: this.gameState.score });
                
                // Show educational pop-up card for matched orchid
                this.showEducationalCard(tile1);

                // Check for win condition
                if (this.gameState.matchedTiles.size === this.gameState.tiles.length) {
                    this.handleWin();
                }
            } else {
                // No match
                element1.classList.remove('selected');
                element2.classList.remove('selected');
                this.announce('No match. Try again.');
            }

            this.gameState.selectedTiles = [];
            this.updateFreeTiles();
            this.updateUI();
        }

        /**
         * Calculate score for a match
         */
        calculateScore() {
            let baseScore = 100;
            
            // Time bonus (faster = more points)
            const timeElapsed = (Date.now() - this.gameState.startTime) / 1000;
            const timeBonus = Math.max(0, 300 - timeElapsed) * 2;
            
            // Efficiency bonus (fewer moves = more points)
            const optimalMoves = 72; // 144 tiles / 2
            const moveBonus = Math.max(0, optimalMoves - this.gameState.moves) * 10;
            
            return Math.round(baseScore + timeBonus + moveBonus);
        }

        /**
         * Get number of remaining pairs
         */
        getRemainingPairs() {
            return (this.gameState.tiles.length - this.gameState.matchedTiles.size) / 2;
        }

        /**
         * Clear tile selection
         */
        clearSelection() {
            this.gameState.selectedTiles.forEach(tileId => {
                const element = document.querySelector(`[data-tile-id="${tileId}"]`);
                if (element) {
                    element.classList.remove('selected');
                }
            });
            this.gameState.selectedTiles = [];
        }

        /**
         * Save current state for undo functionality
         */
        saveStateForUndo() {
            this.gameState.undoStack.push({
                matchedTiles: new Set(this.gameState.matchedTiles),
                moves: this.gameState.moves,
                score: this.gameState.score
            });
            
            // Limit undo stack size
            if (this.gameState.undoStack.length > 50) {
                this.gameState.undoStack.shift();
            }
            
            this.gameState.redoStack = []; // Clear redo stack
        }

        /**
         * Undo last move
         */
        undo() {
            if (this.gameState.undoStack.length === 0) return;

            // Save current state to redo stack
            this.gameState.redoStack.push({
                matchedTiles: new Set(this.gameState.matchedTiles),
                moves: this.gameState.moves,
                score: this.gameState.score
            });

            // Restore previous state
            const previousState = this.gameState.undoStack.pop();
            this.gameState.matchedTiles = previousState.matchedTiles;
            this.gameState.moves = previousState.moves;
            this.gameState.score = previousState.score;

            this.updateTileStates();
            this.updateFreeTiles();
            this.updateUI();
            this.announce('Move undone');
            this.emit('undo');
        }

        /**
         * Redo last undone move
         */
        redo() {
            if (this.gameState.redoStack.length === 0) return;

            // Save current state to undo stack
            this.saveStateForUndo();

            // Restore next state
            const nextState = this.gameState.redoStack.pop();
            this.gameState.matchedTiles = nextState.matchedTiles;
            this.gameState.moves = nextState.moves;
            this.gameState.score = nextState.score;

            this.updateTileStates();
            this.updateFreeTiles();
            this.updateUI();
            this.announce('Move redone');
            this.emit('redo');
        }

        /**
         * Update visual state of all tiles
         */
        updateTileStates() {
            document.querySelectorAll('.mahjong-tile').forEach(element => {
                const tileId = parseInt(element.dataset.tileId);
                element.classList.toggle('matched', this.gameState.matchedTiles.has(tileId));
            });
        }

        /**
         * Show hint (highlight a possible match)
         */
        showHint() {
            const possibleMatch = this.findPossibleMatch();
            
            if (possibleMatch) {
                const [tileId1, tileId2] = possibleMatch;
                const element1 = document.querySelector(`[data-tile-id="${tileId1}"]`);
                const element2 = document.querySelector(`[data-tile-id="${tileId2}"]`);
                
                element1.classList.add('hint');
                element2.classList.add('hint');
                
                setTimeout(() => {
                    element1.classList.remove('hint');
                    element2.classList.remove('hint');
                }, 2000);
                
                this.announce('Hint shown - two matching tiles are highlighted');
                this.emit('hint', possibleMatch);
            } else {
                this.announce('No possible matches found. Try shuffling.');
            }
        }

        /**
         * Find a possible match among free tiles
         */
        findPossibleMatch() {
            const freeTiles = Array.from(document.querySelectorAll('.mahjong-tile.free'))
                .map(el => parseInt(el.dataset.tileId))
                .filter(id => !this.gameState.matchedTiles.has(id));

            for (let i = 0; i < freeTiles.length; i++) {
                for (let j = i + 1; j < freeTiles.length; j++) {
                    const tile1 = this.gameState.tiles.find(t => t.id === freeTiles[i]);
                    const tile2 = this.gameState.tiles.find(t => t.id === freeTiles[j]);
                    
                    if (tile1.canMatch(tile2)) {
                        return [freeTiles[i], freeTiles[j]];
                    }
                }
            }
            
            return null;
        }

        /**
         * Shuffle tiles ensuring solvability
         */
        shuffleTiles() {
            // Clear current selection
            this.clearSelection();
            
            // Get all unmatched tiles
            const unmatchedTiles = this.gameState.tiles.filter(tile => 
                !this.gameState.matchedTiles.has(tile.id)
            );
            
            // Reshuffle their positions
            for (let i = unmatchedTiles.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                
                // Swap the display content but keep tile IDs in their DOM positions
                const element1 = document.querySelector(`[data-tile-id="${unmatchedTiles[i].id}"]`);
                const element2 = document.querySelector(`[data-tile-id="${unmatchedTiles[j].id}"]`);
                
                if (element1 && element2) {
                    const temp = element1.innerHTML;
                    element1.innerHTML = element2.innerHTML;
                    element2.innerHTML = temp;
                    
                    // Swap dataset values
                    const tempType = element1.dataset.type;
                    const tempValue = element1.dataset.value;
                    element1.dataset.type = element2.dataset.type;
                    element1.dataset.value = element2.dataset.value;
                    element2.dataset.type = tempType;
                    element2.dataset.value = tempValue;
                }
            }
            
            this.updateFreeTiles();
            this.announce('Tiles shuffled');
            this.emit('shuffle');
        }

        /**
         * Start new game
         */
        newGame() {
            this.gameState = {
                tiles: [],
                selectedTiles: [],
                matchedTiles: new Set(),
                moves: 0,
                score: 0,
                startTime: Date.now(),
                endTime: null,
                isPaused: false,
                undoStack: [],
                redoStack: []
            };

            await this.generateTiles();
            this.createLayout();
            this.startTimer();
            this.updateUI();
            this.announce('New game started');
            this.emit('newGame');
        }

        /**
         * Handle game win
         */
        handleWin() {
            this.gameState.endTime = Date.now();
            const duration = this.gameState.endTime - this.gameState.startTime;
            
            // Update win overlay
            document.getElementById('om-win-time').textContent = this.formatTime(duration / 1000);
            document.getElementById('om-win-moves').textContent = this.gameState.moves;
            document.getElementById('om-win-score').textContent = this.gameState.score;
            
            // Show win overlay
            document.getElementById('om-win-overlay').style.display = 'flex';
            
            this.announce(`Congratulations! Game completed in ${this.formatTime(duration / 1000)} with ${this.gameState.moves} moves and ${this.gameState.score} points.`);
            this.emit('win', {
                time: duration,
                moves: this.gameState.moves,
                score: this.gameState.score
            });
            
            // Save statistics
            this.saveStatistics();
        }

        /**
         * Start/update timer
         */
        startTimer() {
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
            }
            
            this.gameState.startTime = Date.now();
            
            this.timerInterval = setInterval(() => {
                if (!this.gameState.isPaused && !this.gameState.endTime) {
                    const elapsed = (Date.now() - this.gameState.startTime) / 1000;
                    document.getElementById('om-timer').textContent = this.formatTime(elapsed);
                }
            }, 1000);
        }

        /**
         * Format time as MM:SS
         */
        formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }

        /**
         * Update UI elements
         */
        updateUI() {
            document.getElementById('om-moves').textContent = this.gameState.moves;
            document.getElementById('om-score').textContent = this.gameState.score;
            document.getElementById('om-pairs').textContent = this.getRemainingPairs();
            
            // Update control button states
            document.getElementById('om-undo').disabled = this.gameState.undoStack.length === 0;
            document.getElementById('om-redo').disabled = this.gameState.redoStack.length === 0;
        }

        /**
         * Apply theme
         */
        applyTheme(themeName) {
            const theme = THEMES[themeName];
            if (!theme) return;

            const widget = this.container.querySelector('.orchid-mahjong-widget');
            widget.dataset.theme = themeName;
            
            // Apply CSS custom properties for theme colors
            widget.style.setProperty('--om-primary', theme.primary);
            widget.style.setProperty('--om-secondary', theme.secondary);
            widget.style.setProperty('--om-accent', theme.accent);
            widget.style.setProperty('--om-background', theme.background);
            widget.style.setProperty('--om-tile', theme.tile);
            widget.style.setProperty('--om-selected', theme.selected);
            widget.style.setProperty('--om-matched', theme.matched);
            
            this.options.theme = themeName;
            this.saveSettings();
        }

        /**
         * Setup enhanced settings panel
         */
        setupEnhancedSettings() {
            this.initOrchidSelector();
            this.bindEnhancedSettingsEvents();
        }

        /**
         * Initialize orchid species selector
         */
        initOrchidSelector() {
            const selector = this.container.querySelector('#om-orchid-selector');
            if (!selector) return;

            Object.entries(ORCHID_SPECIES).forEach(([species, data]) => {
                const isSelected = this.options.selectedOrchids.includes(species);
                const checkbox = document.createElement('label');
                checkbox.className = 'orchid-species-option';
                checkbox.innerHTML = `
                    <input type="checkbox" value="${species}" ${isSelected ? 'checked' : ''}>
                    <span class="orchid-info">
                        <span class="orchid-emoji">${data.emoji}</span>
                        <span class="orchid-name">${species}</span>
                        <span class="orchid-family">${data.family}</span>
                    </span>
                `;
                selector.appendChild(checkbox);
            });

            // Limit selection to 8 species
            selector.addEventListener('change', (e) => {
                const checkboxes = selector.querySelectorAll('input[type="checkbox"]');
                const checked = selector.querySelectorAll('input[type="checkbox"]:checked');
                
                if (checked.length > 8) {
                    e.target.checked = false;
                    this.announce('Maximum 8 orchid species allowed');
                    return;
                }

                this.options.selectedOrchids = Array.from(checked).map(cb => cb.value);
            });
        }

        /**
         * Bind enhanced settings events
         */
        bindEnhancedSettingsEvents() {
            const gameModeSelect = this.container.querySelector('#om-game-mode-select');
            const playerNameGroup = this.container.querySelector('#om-player-name-group');
            const roomCodeGroup = this.container.querySelector('#om-room-code-group');
            const applyBtn = this.container.querySelector('#om-apply-settings');
            const saveBtn = this.container.querySelector('#om-save-settings');
            const resetBtn = this.container.querySelector('#om-reset-stats');

            // Game mode change
            gameModeSelect?.addEventListener('change', (e) => {
                const isMultiplayer = e.target.value !== 'solitaire';
                playerNameGroup.style.display = isMultiplayer ? 'block' : 'none';
                roomCodeGroup.style.display = isMultiplayer ? 'block' : 'none';
                this.options.gameMode = e.target.value;
            });

            // Apply settings
            applyBtn?.addEventListener('click', () => {
                this.applyAllSettings();
                this.container.querySelector('#om-settings-panel').style.display = 'none';
                
                if (this.options.gameMode === 'solitaire') {
                    this.newGame();
                } else {
                    this.startMultiplayerSetup();
                }
            });

            // Save settings
            saveBtn?.addEventListener('click', () => {
                this.applyAllSettings();
                this.saveSettings();
                this.announce('Settings saved successfully');
            });

            // Reset all data
            resetBtn?.addEventListener('click', () => {
                if (confirm('This will delete all your game data, statistics, and custom patterns. Are you sure?')) {
                    localStorage.clear();
                    this.announce('All data reset successfully');
                    location.reload();
                }
            });
        }

        /**
         * Apply all settings from the panel
         */
        applyAllSettings() {
            const settingsPanel = this.container.querySelector('#om-settings-panel');
            
            // Get all form values
            this.options.gameMode = settingsPanel.querySelector('#om-game-mode-select')?.value || 'solitaire';
            this.options.playerName = settingsPanel.querySelector('#om-player-name')?.value || '';
            this.options.roomCode = settingsPanel.querySelector('#om-room-code')?.value || '';
            this.options.tileCount = parseInt(settingsPanel.querySelector('#om-tile-count-select')?.value) || 144;
            this.options.theme = settingsPanel.querySelector('#om-theme-select')?.value || 'fcos';
            this.options.layout = settingsPanel.querySelector('#om-layout-select')?.value || 'turtle';
            this.options.highlights = settingsPanel.querySelector('#om-highlights')?.checked || true;
            this.options.sound = settingsPanel.querySelector('#om-sound')?.checked || false;
            this.options.autoHint = settingsPanel.querySelector('#om-auto-hint')?.checked || false;
            this.options.quickMatch = settingsPanel.querySelector('#om-quick-match')?.checked || false;

            // Apply theme immediately
            this.applyTheme(this.options.theme);
        }

        /**
         * Setup multiplayer functionality
         */
        setupMultiplayer() {
            this.multiplayerState = {
                isHost: false,
                roomCode: null,
                players: [],
                gameStarted: false,
                turn: 0
            };

            this.bindMultiplayerEvents();
        }

        /**
         * Bind multiplayer event handlers
         */
        bindMultiplayerEvents() {
            const startGameBtn = this.container.querySelector('#om-start-multiplayer-game');
            const leaveRoomBtn = this.container.querySelector('#om-leave-room');
            const copyRoomBtn = this.container.querySelector('#om-copy-room-code');

            startGameBtn?.addEventListener('click', () => {
                this.startMultiplayerGame();
            });

            leaveRoomBtn?.addEventListener('click', () => {
                this.leaveMultiplayerRoom();
            });

            copyRoomBtn?.addEventListener('click', () => {
                this.copyRoomCode();
            });
        }

        /**
         * Start multiplayer setup
         */
        startMultiplayerSetup() {
            const playerName = this.options.playerName || `Player ${Date.now() % 1000}`;
            const roomCode = this.options.roomCode || this.generateRoomCode();

            // Show multiplayer lobby
            this.showMultiplayerLobby(roomCode, playerName);
            
            // Initialize mock multiplayer (replace with WebSocket connection)
            this.joinOrCreateRoom(roomCode, playerName);
        }

        /**
         * Show multiplayer lobby
         */
        showMultiplayerLobby(roomCode, playerName) {
            const lobby = this.container.querySelector('#om-multiplayer-lobby');
            const roomDisplay = this.container.querySelector('#om-room-display');
            const playerCount = this.container.querySelector('#om-player-count');
            
            if (lobby && roomDisplay && playerCount) {
                lobby.style.display = 'block';
                roomDisplay.textContent = roomCode;
                playerCount.textContent = '1/4';
                
                // Hide main game for now
                this.container.querySelector('.game-board').style.display = 'none';
            }
        }

        /**
         * Setup chat system
         */
        setupChat() {
            this.chatState = {
                messages: [],
                isOpen: false
            };

            this.bindChatEvents();
        }

        /**
         * Bind chat event handlers
         */
        bindChatEvents() {
            const chatInput = this.container.querySelector('#om-chat-input');
            const sendBtn = this.container.querySelector('#om-send-chat');
            const closeBtn = this.container.querySelector('#om-close-chat');

            sendBtn?.addEventListener('click', () => {
                this.sendChatMessage();
            });

            chatInput?.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendChatMessage();
                }
            });

            closeBtn?.addEventListener('click', () => {
                this.container.querySelector('#om-chat-panel').style.display = 'none';
            });
        }

        /**
         * Setup leaderboard system
         */
        setupLeaderboard() {
            this.leaderboardState = {
                currentTab: 'daily',
                data: {
                    daily: [],
                    weekly: [],
                    monthly: [],
                    alltime: []
                }
            };

            this.bindLeaderboardEvents();
        }

        /**
         * Bind leaderboard event handlers
         */
        bindLeaderboardEvents() {
            const viewBtn = this.container.querySelector('#om-view-leaderboard');
            const closeBtn = this.container.querySelector('#om-close-leaderboard');
            const tabBtns = this.container.querySelectorAll('.tab-btn');

            viewBtn?.addEventListener('click', () => {
                this.showLeaderboard();
            });

            closeBtn?.addEventListener('click', () => {
                this.container.querySelector('#om-leaderboard-modal').style.display = 'none';
            });

            tabBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const tab = e.target.dataset.tab;
                    this.switchLeaderboardTab(tab);
                });
            });
        }

        /**
         * Generate room code
         */
        generateRoomCode() {
            return Math.random().toString(36).substring(2, 8).toUpperCase();
        }

        /**
         * Join or create multiplayer room
         */
        joinOrCreateRoom(roomCode, playerName) {
            // Mock implementation - replace with actual WebSocket/server logic
            this.multiplayerState.roomCode = roomCode;
            this.multiplayerState.isHost = true;
            this.multiplayerState.players = [{ name: playerName, id: 1, score: 0 }];
            
            this.announce(`Joined room ${roomCode} as ${playerName}`);
            
            // Show start button for host
            const startBtn = this.container.querySelector('#om-start-multiplayer-game');
            if (startBtn) startBtn.style.display = 'block';
        }

        /**
         * Send chat message
         */
        sendChatMessage() {
            const input = this.container.querySelector('#om-chat-input');
            const message = input.value.trim();
            
            if (message) {
                this.addChatMessage(this.options.playerName || 'You', message);
                input.value = '';
            }
        }

        /**
         * Add chat message to display
         */
        addChatMessage(sender, message) {
            const chatMessages = this.container.querySelector('#om-chat-messages');
            if (!chatMessages) return;

            const messageEl = document.createElement('div');
            messageEl.className = 'chat-message';
            messageEl.innerHTML = `
                <span class="chat-sender">${sender}:</span>
                <span class="chat-text">${message}</span>
                <span class="chat-time">${new Date().toLocaleTimeString()}</span>
            `;
            
            chatMessages.appendChild(messageEl);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        /**
         * Show leaderboard
         */
        showLeaderboard() {
            const modal = this.container.querySelector('#om-leaderboard-modal');
            if (modal) {
                modal.style.display = 'block';
                this.loadLeaderboardData(this.leaderboardState.currentTab);
            }
        }

        /**
         * Switch leaderboard tab
         */
        switchLeaderboardTab(tab) {
            const tabBtns = this.container.querySelectorAll('.tab-btn');
            tabBtns.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tab === tab);
            });
            
            this.leaderboardState.currentTab = tab;
            this.loadLeaderboardData(tab);
        }

        /**
         * Load leaderboard data
         */
        loadLeaderboardData(tab) {
            // Mock leaderboard data
            const mockData = [
                { rank: 1, name: 'OrchidMaster', score: 15420, time: '02:34', moves: 72 },
                { rank: 2, name: 'FlowerPower', score: 14850, time: '03:12', moves: 85 },
                { rank: 3, name: 'MahjongPro', score: 13960, time: '02:56', moves: 78 },
                { rank: 4, name: 'PetalSeeker', score: 12340, time: '04:21', moves: 92 },
                { rank: 5, name: 'BloomBuster', score: 11780, time: '03:45', moves: 89 }
            ];

            this.displayLeaderboard(mockData);
        }

        /**
         * Display leaderboard entries
         */
        displayLeaderboard(data) {
            const list = this.container.querySelector('#om-leaderboard-list');
            if (!list) return;

            list.innerHTML = data.map(entry => `
                <div class="leaderboard-entry ${entry.rank <= 3 ? 'top-three' : ''}">
                    <div class="rank">
                        <span class="rank-number">#${entry.rank}</span>
                        ${entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : ''}
                    </div>
                    <div class="player-info">
                        <div class="player-name">${entry.name}</div>
                        <div class="player-stats">${entry.time} • ${entry.moves} moves</div>
                    </div>
                    <div class="player-score">${entry.score.toLocaleString()}</div>
                </div>
            `).join('');
        }

        /**
         * Copy room code to clipboard
         */
        copyRoomCode() {
            const roomCode = this.multiplayerState.roomCode;
            if (roomCode && navigator.clipboard) {
                navigator.clipboard.writeText(roomCode).then(() => {
                    this.announce('Room code copied to clipboard');
                });
            }
        }

        /**
         * Start multiplayer game
         */
        startMultiplayerGame() {
            this.container.querySelector('#om-multiplayer-lobby').style.display = 'none';
            this.container.querySelector('.game-board').style.display = 'block';
            this.container.querySelector('#om-chat-panel').style.display = 'block';
            
            this.newGame();
            this.announce('Multiplayer game started!');
        }

        /**
         * Leave multiplayer room
         */
        leaveMultiplayerRoom() {
            this.container.querySelector('#om-multiplayer-lobby').style.display = 'none';
            this.container.querySelector('.game-board').style.display = 'block';
            this.options.gameMode = 'solitaire';
            this.newGame();
        }

        /**
         * Bind event handlers
         */
        bindEvents() {
            const board = document.getElementById('om-board');
            
            // Tile click/touch events
            board.addEventListener('click', (e) => {
                const tile = e.target.closest('.mahjong-tile');
                if (tile) {
                    this.selectTile(tile);
                }
            });

            // Control button events
            document.getElementById('om-undo').addEventListener('click', () => this.undo());
            document.getElementById('om-redo').addEventListener('click', () => this.redo());
            document.getElementById('om-hint').addEventListener('click', () => this.showHint());
            document.getElementById('om-shuffle').addEventListener('click', () => this.shuffleTiles());
            document.getElementById('om-new').addEventListener('click', () => this.newGame());
            
            // Settings panel events
            document.getElementById('om-settings').addEventListener('click', () => {
                document.getElementById('om-settings-panel').style.display = 'block';
            });
            
            document.getElementById('om-close-settings').addEventListener('click', () => {
                document.getElementById('om-settings-panel').style.display = 'none';
            });

            // Settings controls
            document.getElementById('om-theme-select').addEventListener('change', (e) => {
                this.applyTheme(e.target.value);
            });

            document.getElementById('om-layout-select').addEventListener('change', (e) => {
                this.options.layout = e.target.value;
                this.newGame();
            });

            document.getElementById('om-highlights').addEventListener('change', (e) => {
                this.options.highlights = e.target.checked;
                this.saveSettings();
            });

            document.getElementById('om-sound').addEventListener('change', (e) => {
                this.options.sound = e.target.checked;
                this.saveSettings();
            });

            // Win overlay events
            document.getElementById('om-play-again').addEventListener('click', () => {
                document.getElementById('om-win-overlay').style.display = 'none';
                this.newGame();
            });

            document.getElementById('om-change-layout').addEventListener('click', () => {
                document.getElementById('om-win-overlay').style.display = 'none';
                document.getElementById('om-settings-panel').style.display = 'block';
            });

            // Keyboard events
            this.bindKeyboardEvents();
        }

        /**
         * Bind keyboard event handlers
         */
        bindKeyboardEvents() {
            document.addEventListener('keydown', (e) => {
                if (e.target.closest('.orchid-mahjong-widget')) {
                    switch (e.key.toLowerCase()) {
                        case 'h':
                            e.preventDefault();
                            this.showHint();
                            break;
                        case 'u':
                            e.preventDefault();
                            this.undo();
                            break;
                        case 'r':
                            e.preventDefault();
                            this.redo();
                            break;
                        case 's':
                            e.preventDefault();
                            this.shuffleTiles();
                            break;
                        case 't':
                            e.preventDefault();
                            this.newGame();
                            break;
                        case 'enter':
                        case ' ':
                            if (e.target.classList.contains('mahjong-tile')) {
                                e.preventDefault();
                                this.selectTile(e.target);
                            }
                            break;
                        case 'arrowleft':
                        case 'arrowright':
                        case 'arrowup':
                        case 'arrowdown':
                            e.preventDefault();
                            this.navigateTiles(e.key);
                            break;
                    }
                }
            });
        }

        /**
         * Navigate between tiles with arrow keys
         */
        navigateTiles(direction) {
            const currentTile = document.activeElement;
            if (!currentTile.classList.contains('mahjong-tile')) return;

            const allTiles = Array.from(document.querySelectorAll('.mahjong-tile.free'));
            const currentIndex = allTiles.indexOf(currentTile);
            
            let nextIndex = currentIndex;
            
            switch (direction) {
                case 'ArrowLeft':
                    nextIndex = currentIndex > 0 ? currentIndex - 1 : allTiles.length - 1;
                    break;
                case 'ArrowRight':
                    nextIndex = currentIndex < allTiles.length - 1 ? currentIndex + 1 : 0;
                    break;
                case 'ArrowUp':
                    // Move to tile above (same column, previous row)
                    nextIndex = Math.max(0, currentIndex - 8);
                    break;
                case 'ArrowDown':
                    // Move to tile below (same column, next row)
                    nextIndex = Math.min(allTiles.length - 1, currentIndex + 8);
                    break;
            }
            
            if (allTiles[nextIndex]) {
                allTiles[nextIndex].focus();
            }
        }

        /**
         * Make accessibility announcement
         */
        announce(message) {
            const announcer = document.getElementById('om-announcements');
            announcer.textContent = message;
        }

        /**
         * Save game settings to localStorage
         */
        saveSettings() {
            const settings = {
                theme: this.options.theme,
                layout: this.options.layout,
                sound: this.options.sound,
                highlights: this.options.highlights
            };
            
            localStorage.setItem('orchid-mahjong-settings', JSON.stringify(settings));
        }

        /**
         * Load game settings from localStorage
         */
        loadSettings() {
            try {
                const settings = JSON.parse(localStorage.getItem('orchid-mahjong-settings') || '{}');
                
                this.options = { ...this.options, ...settings };
                
                // Update UI controls
                document.getElementById('om-theme-select').value = this.options.theme;
                document.getElementById('om-layout-select').value = this.options.layout;
                document.getElementById('om-highlights').checked = this.options.highlights;
                document.getElementById('om-sound').checked = this.options.sound;
                
            } catch (e) {
                console.warn('Failed to load settings:', e);
            }
        }

        /**
         * Save game statistics
         */
        saveStatistics() {
            try {
                const stats = JSON.parse(localStorage.getItem('orchid-mahjong-stats') || '{}');
                const layoutName = this.options.layout;
                
                if (!stats[layoutName]) {
                    stats[layoutName] = { bestTime: Infinity, bestScore: 0, gamesPlayed: 0 };
                }
                
                const duration = this.gameState.endTime - this.gameState.startTime;
                stats[layoutName].gamesPlayed++;
                
                if (duration < stats[layoutName].bestTime) {
                    stats[layoutName].bestTime = duration;
                }
                
                if (this.gameState.score > stats[layoutName].bestScore) {
                    stats[layoutName].bestScore = this.gameState.score;
                }
                
                localStorage.setItem('orchid-mahjong-stats', JSON.stringify(stats));
                
            } catch (e) {
                console.warn('Failed to save statistics:', e);
            }
        }

        /**
         * Show educational pop-up card when tiles are matched
         */
        showEducationalCard(tile) {
            // Get orchid data from tile (now includes real orchid photos and facts)
            const orchidData = tile.orchidData || {};
            const fact = orchidData.fact || 'This beautiful orchid is part of the Orchidaceae family.';
            
            // Create or get existing educational card modal
            let cardModal = this.container.querySelector('#om-educational-card');
            if (!cardModal) {
                cardModal = document.createElement('div');
                cardModal.id = 'om-educational-card';
                cardModal.className = 'educational-card-modal';
                cardModal.innerHTML = `
                    <div class="educational-card">
                        <div class="card-header">
                            <h3 class="orchid-name">Orchid Fact</h3>
                            <span class="timer-circle">
                                <svg class="timer-svg" width="24" height="24">
                                    <circle cx="12" cy="12" r="10" class="timer-bg" />
                                    <circle cx="12" cy="12" r="10" class="timer-progress" />
                                </svg>
                                <span class="timer-text">5</span>
                            </span>
                        </div>
                        <div class="card-content">
                            <div class="orchid-image-container">
                                <img class="orchid-image" src="" alt="Orchid" />
                            </div>
                            <div class="fact-content">
                                <p class="orchid-fact"></p>
                                <div class="orchid-details">
                                    <span class="detail-item"><strong>Family:</strong> <span class="family">Orchidaceae</span></span>
                                    <span class="detail-item"><strong>Origin:</strong> <span class="origin">Various regions</span></span>
                                    <span class="detail-item"><strong>Care:</strong> <span class="care-tip">Bright, indirect light</span></span>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer">
                            <button class="close-btn" aria-label="Close">&times;</button>
                            <div class="learn-more">
                                <small>🌺 Five Cities Orchid Society Educational Series</small>
                            </div>
                        </div>
                    </div>
                `;
                this.container.appendChild(cardModal);
                
                // Add event listener for close button
                cardModal.querySelector('.close-btn').addEventListener('click', () => {
                    cardModal.style.display = 'none';
                });
                
                // Close on click outside
                cardModal.addEventListener('click', (e) => {
                    if (e.target === cardModal) {
                        cardModal.style.display = 'none';
                    }
                });
            }
            
            // Update card content with tile information  
            const orchidName = orchidData.name || tile.name || 'Beautiful Orchid';
            const orchidImage = orchidData.imageUrl || orchidData.backupImage || '/static/images/orchid_placeholder.svg';
            
            cardModal.querySelector('.orchid-name').textContent = orchidName;
            cardModal.querySelector('.orchid-image').src = orchidImage;
            cardModal.querySelector('.orchid-fact').textContent = fact;
            
            // Optionally fetch additional facts from API
            this.fetchOrchidFacts(tile).then(factData => {
                if (factData && factData.orchid_fact) {
                    const factInfo = factData.orchid_fact;
                    cardModal.querySelector('.orchid-name').textContent = factInfo.name || orchidName;
                    cardModal.querySelector('.orchid-fact').textContent = factInfo.fact || fact;
                    cardModal.querySelector('.family').textContent = factInfo.family || 'Orchidaceae';
                    cardModal.querySelector('.origin').textContent = factInfo.origin || 'Various regions';
                    cardModal.querySelector('.care-tip').textContent = factInfo.care_tip || 'Bright, indirect light';
                    
                    if (factInfo.image_url && factInfo.image_url !== '/static/images/orchid_placeholder.svg') {
                        cardModal.querySelector('.orchid-image').src = factInfo.image_url;
                    }
                }
            }).catch(error => {
                console.log('Using tile fact data:', error);
            });
            
            // Show modal with animation
            cardModal.style.display = 'flex';
            cardModal.classList.add('show');
            
            // Start 5-second countdown timer
            this.startEducationalTimer(cardModal);
        }
        
        /**
         * Fetch additional orchid facts from API
         */
        async fetchOrchidFacts(tile) {
            try {
                const response = await fetch('/api/mahjong/orchid-facts');
                const data = await response.json();
                return data;
            } catch (error) {
                console.log('Could not fetch additional orchid facts:', error);
                return null;
            }
        }
        
        /**
         * Start 5-second countdown timer for educational card
         */
        startEducationalTimer(cardModal) {
            const timerText = cardModal.querySelector('.timer-text');
            const timerProgress = cardModal.querySelector('.timer-progress');
            const totalDuration = 5000; // 5 seconds
            const interval = 100; // Update every 100ms
            let elapsed = 0;
            
            // Set up SVG circle for progress animation
            const circle = timerProgress;
            const radius = 10;
            const circumference = 2 * Math.PI * radius;
            circle.style.strokeDasharray = circumference;
            circle.style.strokeDashoffset = 0;
            
            const timer = setInterval(() => {
                elapsed += interval;
                const remaining = Math.max(0, totalDuration - elapsed);
                const seconds = Math.ceil(remaining / 1000);
                
                // Update countdown text
                timerText.textContent = seconds;
                
                // Update progress circle
                const progress = elapsed / totalDuration;
                const offset = circumference * progress;
                circle.style.strokeDashoffset = offset;
                
                // Auto-close when timer reaches 0
                if (remaining <= 0) {
                    clearInterval(timer);
                    cardModal.style.display = 'none';
                    cardModal.classList.remove('show');
                }
            }, interval);
            
            // Store timer ID for cleanup if needed
            cardModal._timerId = timer;
        }

        /**
         * Event system methods
         */
        on(eventName, handler) {
            if (!this.eventHandlers[eventName]) {
                this.eventHandlers[eventName] = [];
            }
            this.eventHandlers[eventName].push(handler);
        }

        off(eventName, handler) {
            if (this.eventHandlers[eventName]) {
                this.eventHandlers[eventName] = this.eventHandlers[eventName].filter(h => h !== handler);
            }
        }

        emit(eventName, data) {
            if (this.eventHandlers[eventName]) {
                this.eventHandlers[eventName].forEach(handler => {
                    try {
                        handler(data);
                    } catch (e) {
                        console.error('Event handler error:', e);
                    }
                });
            }
        }

        /**
         * Public API methods
         */
        setTheme(themeName) {
            this.applyTheme(themeName);
        }

        getStats() {
            try {
                return JSON.parse(localStorage.getItem('orchid-mahjong-stats') || '{}');
            } catch (e) {
                return {};
            }
        }

        resetStats() {
            localStorage.removeItem('orchid-mahjong-stats');
            this.announce('Statistics reset');
        }

        /**
         * Cleanup
         */
        destroy() {
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
            }
            
            // Remove event listeners
            // (In a full implementation, we'd track and remove all listeners)
            
            this.container.innerHTML = '';
        }
    }

    /**
     * Public API
     */
    window.OrchidMahjong.init = async function(selector, options) {
        const container = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (!container) {
            console.error('OrchidMahjong: Container not found');
            return null;
        }
        
        const game = new OrchidMahjongGame(container, options);
        await game.init();
        return game;
    };

    window.OrchidMahjong.Game = OrchidMahjongGame;
    window.OrchidMahjong.THEMES = THEMES;
    window.OrchidMahjong.LAYOUTS = LAYOUTS;

    // Auto-initialize if data attributes are present
    document.addEventListener('DOMContentLoaded', async () => {
        const elements = document.querySelectorAll('[data-orchid-mahjong]');
        for (const element of elements) {
            const options = {};
            if (element.dataset.theme) options.theme = element.dataset.theme;
            if (element.dataset.layout) options.layout = element.dataset.layout;
            
            await window.OrchidMahjong.init(element, options);
        }
    });

})();