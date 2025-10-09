/**
 * Settings Manager - Handles chart settings and localStorage
 */
class SettingsManager {
    constructor() {
        this.defaultSettings = {
            showCrosshair: true,
            stickyCrosshair: true,
            crosshairMagnet: true, // snap to nearest data point
            yScaleMode: 'linear', // linear | logarithmic | percentage
            invertScale: false,
            grayBackgroundStrips: false,
            rangeSlider: false,
            rangeWindow: null, // number of bars to show; null means auto
            extendedHours: false,
            hideOutliers: false,
            zoomLevels: {}, // per-interval zoom levels: { '2m': 0.3, '5m': 0.5, '15m': 0.7 }
            fitLastBars: 50, // default bars to fit
            currentInterval: '2m' // track current active interval
        };
        
        this.presets = {
            default: {
                name: 'Default',
                description: 'Standard Yahoo Finance-like settings',
                settings: {
                    showCrosshair: true,
                    stickyCrosshair: true,
                    crosshairMagnet: true,
                    yScaleMode: 'linear',
                    invertScale: false,
                    grayBackgroundStrips: false,
                    rangeSlider: false,
                    extendedHours: false,
                    hideOutliers: false
                }
            },
            clean: {
                name: 'Clean',
                description: 'Minimal interface for focused analysis',
                settings: {
                    showCrosshair: false,
                    stickyCrosshair: false,
                    crosshairMagnet: false,
                    yScaleMode: 'linear',
                    invertScale: false,
                    grayBackgroundStrips: false,
                    rangeSlider: false,
                    extendedHours: false,
                    hideOutliers: true
                }
            },
            technical: {
                name: 'Technical',
                description: 'Advanced settings for technical analysis',
                settings: {
                    showCrosshair: true,
                    stickyCrosshair: true,
                    crosshairMagnet: true,
                    yScaleMode: 'logarithmic',
                    invertScale: false,
                    grayBackgroundStrips: true,
                    rangeSlider: true,
                    extendedHours: true,
                    hideOutliers: false
                }
            }
        };
        
        this.settings = this.loadSettings();
    }
    
    loadSettings() {
        try {
            const currentTheme = this.getCurrentTheme();
            const saved = localStorage.getItem(`tradingview-settings-${currentTheme}`);
            if (saved) {
                const parsed = JSON.parse(saved);
                return { ...this.defaultSettings, ...parsed };
            }
        } catch (error) {
            console.warn('Failed to load settings from localStorage:', error);
        }
        return { ...this.defaultSettings };
    }
    
    saveSettings() {
        try {
            const currentTheme = this.getCurrentTheme();
            localStorage.setItem(`tradingview-settings-${currentTheme}`, JSON.stringify(this.settings));
        } catch (error) {
            console.warn('Failed to save settings to localStorage:', error);
        }
    }
    
    updateSetting(key, value) {
        this.settings[key] = value;
        this.saveSettings();
        return this.settings;
    }
    
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        this.saveSettings();
        return this.settings;
    }
    
    resetToDefaults() {
        this.settings = { ...this.defaultSettings };
        this.saveSettings();
        return this.settings;
    }
    
    getSettings() {
        return { ...this.settings };
    }
    
    getCurrentTheme() {
        return document.body.classList.contains('dark') ? 'dark' : 'light';
    }
    
    // Reload settings when theme changes
    reloadForTheme() {
        this.settings = this.loadSettings();
        return this.settings;
    }
    
    // Apply a preset
    applyPreset(presetKey) {
        if (this.presets[presetKey]) {
            this.settings = { ...this.defaultSettings, ...this.presets[presetKey].settings };
            this.saveSettings();
            return this.settings;
        }
        return null;
    }
    
    // Get all available presets
    getPresets() {
        return this.presets;
    }
    
    // Get current preset name (if any)
    getCurrentPresetName() {
        for (const [key, preset] of Object.entries(this.presets)) {
            if (this.isPresetMatch(preset.settings)) {
                return preset.name;
            }
        }
        return 'Custom';
    }
    
    // Check if current settings match a preset
    isPresetMatch(presetSettings) {
        for (const [key, value] of Object.entries(presetSettings)) {
            if (this.settings[key] !== value) {
                return false;
            }
        }
        return true;
    }
    
    // Zoom level management
    setZoomLevel(interval, level) {
        if (!this.settings.zoomLevels) {
            this.settings.zoomLevels = {};
        }
        this.settings.zoomLevels[interval] = level;
        this.saveSettings();
    }
    
    getZoomLevel(interval) {
        return this.settings.zoomLevels?.[interval] || 0.5; // default 50% zoom (0.5)
    }
    
    setFitLastBars(bars) {
        this.settings.fitLastBars = bars;
        this.saveSettings();
    }
    
    getFitLastBars() {
        return this.settings.fitLastBars || 50;
    }
    
    // Per-interval zoom level management
    setZoomLevel(interval, level) {
        if (!this.settings.zoomLevels) {
            this.settings.zoomLevels = {};
        }
        this.settings.zoomLevels[interval] = Math.max(0.1, Math.min(1.0, level)); // clamp between 0.1 and 1.0
        this.saveSettings();
    }
    
    setCurrentInterval(interval) {
        this.settings.currentInterval = interval;
        this.saveSettings();
    }
    
    getCurrentInterval() {
        return this.settings.currentInterval || '2m';
    }
    
    // Quick zoom presets
    getZoomPresets() {
        return {
            'fit20': { name: 'Fit Last 20', bars: 20 },
            'fit50': { name: 'Fit Last 50', bars: 50 },
            'fit100': { name: 'Fit Last 100', bars: 100 },
            'fitAll': { name: 'Fit All', bars: null }
        };
    }
}
