/**
 * TradingView Chart Application - Object-Oriented Refactored Version
 * Main application class that orchestrates all components
 */
class TradingViewApp {
    constructor() {
        this.technicalAnalysis = new TechnicalAnalysis();
        this.uiController = new UIController();
        this.chartManager = new ChartManager();
        this.dataFetcher = new DataFetcher();
        this.themeManager = new ThemeManager();
        this.watchlistManager = new WatchlistManager();
        this.settingsManager = new SettingsManager();
        this.websocketManager = new WebSocketManager();
        
        // Set up dependencies
        this.chartManager.setTechnicalAnalysis(this.technicalAnalysis);
        this.chartManager.setUIController(this.uiController);
        this.chartManager.setSettingsManager(this.settingsManager);
        this.uiController.setChartManager(this.chartManager);
        this.dataFetcher.setChartManager(this.chartManager);
        this.dataFetcher.setSettingsManager(this.settingsManager);
        this.themeManager.setSettingsManager(this.settingsManager);
        this.websocketManager.setChartManager(this.chartManager);
        this.websocketManager.setDataFetcher(this.dataFetcher);
        
        // Initialize Settings UI Controller
        this.settingsUIController = new SettingsUIController(this.settingsManager, this.chartManager);
        
        // Initialize Indicators Manager
        this.indicatorsManager = new IndicatorsManager(this.chartManager);
        
        // Connect settingsUIController to settingsManager for interval change notifications
        this.settingsManager.settingsUIController = this.settingsUIController;
        
        this.autoUpdateInterval = null;
        this.isModeChanging = false;
        this.modeChangeTimeout = null;
        this.realtimeEnabled = false;
        this.marketHoursChecker = null;
        this.isMarketOpen = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        
        // Apply settings early before loading data
        this.applyInitialSettings();
        
        // Default update frequency to 5s
        this.ensureDefaultAutoFrequency();
        // Turn on auto-update by default
        const autoToggle = document.getElementById('autoUpdate');
        if (autoToggle) {
            autoToggle.checked = true;
            this.handleAutoUpdate(true);
        }

        this.loadInitialData();
        
        // Initialize range slider binding and visibility from settings
        if (this.settingsUIController) {
            this.settingsUIController.initRangeSliderBinding();
            const visible = this.settingsManager.getSettings().rangeSlider;
            this.settingsUIController.toggleRangeSliderUI(visible);
        }
        
        // Start market hours checker for auto-refresh
        this.startMarketHoursChecker();
    }
    
    applyInitialSettings() {
        // Apply settings as soon as charts are ready
        if (this.chartManager.areChartsReady()) {
            this.chartManager.applySettingsForAllIntervals();
        } else {
            // Wait for charts to be ready
            const checkCharts = () => {
                if (this.chartManager.areChartsReady()) {
                    this.chartManager.applySettingsForAllIntervals();
                } else {
                    setTimeout(checkCharts, 100);
                }
            };
            checkCharts();
        }
    }
    
    setupEventListeners() {
        // Data fetching
        document.getElementById('fetchData').addEventListener('click', () => {
            this.fetchData();
        });
        
        // Ticker selection change
        document.getElementById('ticker').addEventListener('change', (event) => {
            const newTicker = event.target.value;
            console.log(`Symbol changed to: ${newTicker}`);
            this.fetchData(newTicker);
        });
        
        // Auto-update
        document.getElementById('autoUpdate').addEventListener('change', (event) => {
            this.handleAutoUpdate(event.target.checked);
        });
        
        // Real-time toggle
        document.getElementById('toggleRealtime').addEventListener('click', () => {
            this.toggleRealtime();
        });
        
        // Test WebSocket button
        document.getElementById('testWebSocket').addEventListener('click', () => {
            this.testWebSocket();
        });
        
        // Bollinger Bands toggle
        document.getElementById('showBB').addEventListener('change', (event) => {
            this.chartManager.toggleBollingerBands(event.target.checked);
        });
        
        // Support/Resistance toggle
        document.getElementById('showSR').addEventListener('change', (event) => {
            this.chartManager.toggleSupportResistance(event.target.checked);
        });
        
        // Timeframe mode change
        document.getElementById('timeframeMode').addEventListener('change', (event) => {
            this.handleModeChange(event.target.value);
        });
        
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => {
            this.themeManager.toggleTheme();
            // Reload settings for new theme and apply them
            this.themeManager.onThemeChange();
            this.settingsUIController.loadSettingsToUI();
            // Theme change is handled by updateChartsTheme, no need to apply settings again
        });
        
        // Window resize
        window.addEventListener('resize', this.debounce(() => {
            this.chartManager.handleResize();
        }, 100));
    }
    
    loadInitialData() {
        window.addEventListener('load', () => {
            setTimeout(() => {
                if (this.areElementsReady() && this.areChartsReady()) {
                    this.fetchData('NVDA', 20, 14);
                    this.watchlistManager.loadWatchlist();
                } else {
                    setTimeout(() => {
                        this.fetchData('NVDA', 20, 14);
                        this.watchlistManager.loadWatchlist();
                    }, 200);
                }
            }, 500);
        });
    }
    
    areElementsReady() {
        const requiredElements = ['ticker', 'emaPeriod', 'rsiPeriod'];
        return requiredElements.every(id => document.getElementById(id));
    }
    
    areChartsReady() {
        return this.chartManager.areChartsReady();
    }
    
    fetchData(ticker = null, emaPeriod = null, rsiPeriod = null) {
        if (!ticker) {
            ticker = document.getElementById('ticker').value;
            emaPeriod = document.getElementById('emaPeriod').value;
            rsiPeriod = document.getElementById('rsiPeriod').value;
        }
        
        // Check if charts are ready
        if (!this.areChartsReady()) {
            setTimeout(() => this.fetchData(ticker, emaPeriod, rsiPeriod), 100);
            return;
        }
        
        this.uiController.showLoadingState();
        
        this.dataFetcher.fetchData(ticker, emaPeriod, rsiPeriod)
            .then(data => {
                this.chartManager.updateCharts(data);
                this.uiController.updateSymbolDisplay(ticker);
                this.uiController.hideLoadingState();
            })
            .catch(error => {
                this.uiController.hideLoadingState();
                this.uiController.showErrorMessage(`Failed to load data: ${error.message}`);
            });
    }
    
    handleAutoUpdate(enabled) {
        if (enabled) {
            const frequency = (parseInt(document.getElementById('updateFrequency').value, 10) || 60) * 1000;
            this.autoUpdateInterval = setInterval(() => {
                this.fetchData();
            }, frequency);
        } else {
            clearInterval(this.autoUpdateInterval);
        }
    }

    // Ensure default to 60s on load
    ensureDefaultAutoFrequency() {
        const input = document.getElementById('updateFrequency');
        if (input && (!input.value || parseInt(input.value, 10) <= 0)) {
            input.value = 60;
        }
    }
    
    toggleRealtime() {
        if (this.realtimeEnabled) {
            // Stop real-time
            console.log('Stopping real-time...');
            this.websocketManager.stopRealtime();
            this.realtimeEnabled = false;
        } else {
            // Start real-time
            const ticker = document.getElementById('ticker').value;
            const intervals = this.chartManager.chartIntervals;
            console.log(`Starting real-time for ${ticker} with intervals:`, intervals);
            
            // Ensure WebSocket is connected first
            if (!this.websocketManager.isConnected) {
                console.log('Connecting WebSocket first...');
                this.websocketManager.connect();
            }
            
            this.websocketManager.startRealtime(ticker, intervals);
            this.realtimeEnabled = true;
        }
    }
    
    testWebSocket() {
        // Test WebSocket connection and data flow
        console.log('Testing WebSocket...');
        
        // Run connection test
        this.websocketManager.testConnection();
        
        if (!this.websocketManager.isConnected) {
            console.log('Connecting to WebSocket...');
            this.websocketManager.connect();
        }
        
        // Show test message
        this.uiController.showErrorMessage('WebSocket test initiated - check console for logs');
        
        // Auto-start real-time for testing
        if (!this.realtimeEnabled) {
            setTimeout(() => {
                this.toggleRealtime();
                console.log('Auto-started real-time for testing');
            }, 1000);
        }
    }
    
    handleModeChange(selectedMode) {
        if (this.isModeChanging) return;
        
        this.isModeChanging = true;
        clearTimeout(this.modeChangeTimeout);
        
        this.modeChangeTimeout = setTimeout(() => {
            this.performModeChange(selectedMode);
        }, 100);
    }
    
    performModeChange(selectedMode) {
        const timeframeModes = {
            short: ['1m', '2m', '5m'],
            core: ['2m', '5m', '15m'],
            long: ['15m', '30m', '60m']
        };
        
        const newIntervals = timeframeModes[selectedMode];
        this.uiController.showModeTransitionLoading();
        
        // Add fade out effect to existing charts
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.style.transition = 'opacity 0.3s ease';
            container.style.opacity = '0.3';
        });
        
        requestAnimationFrame(() => {
            this.chartManager.switchTimeframes(newIntervals);
            this.uiController.updateIntervalBadges(newIntervals);
            
            setTimeout(() => {
                this.fetchData();
                this.uiController.hideModeTransitionLoading();
                this.isModeChanging = false;
            }, 150);
        });
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    startMarketHoursChecker() {
        // Check market hours every minute
        this.marketHoursChecker = setInterval(() => {
            this.checkMarketHours();
        }, 60000); // Check every minute
        
        // Initial check
        this.checkMarketHours();
    }
    
    checkMarketHours() {
        const now = new Date();
        const dayOfWeek = now.getDay(); // 0 = Sunday, 6 = Saturday
        const hour = now.getHours();
        const minute = now.getMinutes();
        const currentTime = hour * 60 + minute;
        
        // Market hours: Monday-Friday, 9:30 AM - 4:00 PM EST
        const marketOpenTime = 9 * 60 + 30; // 9:30 AM
        const marketCloseTime = 16 * 60; // 4:00 PM
        
        const isWeekday = dayOfWeek >= 1 && dayOfWeek <= 5; // Monday to Friday
        const isMarketHours = currentTime >= marketOpenTime && currentTime <= marketCloseTime;
        const wasMarketOpen = this.isMarketOpen;
        
        this.isMarketOpen = isWeekday && isMarketHours;
        
        if (this.isMarketOpen && !wasMarketOpen) {
            console.log('🟢 Market opened - Starting auto-refresh');
            this.startAutoRefreshWhenMarketOpen();
        } else if (!this.isMarketOpen && wasMarketOpen) {
            console.log('🔴 Market closed - Stopping auto-refresh');
            this.stopAutoRefreshWhenMarketClosed();
        }
        
        // Update UI indicator
        this.updateMarketStatusIndicator();
    }
    
    startAutoRefreshWhenMarketOpen() {
        // Start auto-refresh when market opens
        if (!this.autoUpdateInterval) {
            const frequency = 30000; // 30 seconds
            this.autoUpdateInterval = setInterval(() => {
                this.fetchData();
            }, frequency);
            
            console.log('📈 Auto-refresh started (30s interval)');
        }
        
        // Start real-time data if not already running
        if (!this.realtimeEnabled) {
            const ticker = document.getElementById('ticker').value;
            const intervals = this.chartManager.chartIntervals;
            
            if (!this.websocketManager.isConnected) {
                this.websocketManager.connect();
            }
            
            this.websocketManager.startRealtime(ticker, intervals);
            this.realtimeEnabled = true;
            console.log('📡 Real-time data started');
        }
    }
    
    stopAutoRefreshWhenMarketClosed() {
        // Stop auto-refresh when market closes
        if (this.autoUpdateInterval) {
            clearInterval(this.autoUpdateInterval);
            this.autoUpdateInterval = null;
            console.log('⏹️ Auto-refresh stopped');
        }
        
        // Stop real-time data
        if (this.realtimeEnabled) {
            this.websocketManager.stopRealtime();
            this.realtimeEnabled = false;
            console.log('📡 Real-time data stopped');
        }
    }
    
    updateMarketStatusIndicator() {
        // Update market status indicator in UI
        const statusElement = document.getElementById('marketStatus');
        if (statusElement) {
            if (this.isMarketOpen) {
                statusElement.innerHTML = '<span class="text-success">🟢 Market Open</span>';
                statusElement.className = 'badge badge-success';
            } else {
                statusElement.innerHTML = '<span class="text-error">🔴 Market Closed</span>';
                statusElement.className = 'badge badge-error';
            }
        }
    }
    
    cleanup() {
        // Cleanup intervals and connections
        if (this.autoUpdateInterval) {
            clearInterval(this.autoUpdateInterval);
            this.autoUpdateInterval = null;
        }
        
        if (this.marketHoursChecker) {
            clearInterval(this.marketHoursChecker);
            this.marketHoursChecker = null;
        }
        
        if (this.websocketManager) {
            this.websocketManager.disconnect();
        }
        
        console.log('🧹 App cleanup completed');
    }
}

// Initialize the application
const app = new TradingViewApp();

// Make managers globally accessible for error handling
window.chartManager = app.chartManager;
window.watchlistManager = app.watchlistManager;
window.indicatorsManager = app.indicatorsManager;
window.websocketManager = app.websocketManager;

// Listen for symbol selection events
window.addEventListener('symbolSelected', (event) => {
    const { symbol, emaPeriod, rsiPeriod } = event.detail;
    app.fetchData(symbol, emaPeriod, rsiPeriod);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    app.cleanup();
});
