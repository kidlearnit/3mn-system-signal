/**
 * Settings UI Controller - Handles settings panel interactions
 */
class SettingsUIController {
    constructor(settingsManager, chartManager) {
        this.settingsManager = settingsManager;
        this.chartManager = chartManager;
        this.init();
    }
    
    init() {
        this.loadSettingsToUI();
        this.setupEventListeners();
        this.updatePresetButtons();
    }
    
    loadSettingsToUI() {
        const settings = this.settingsManager.getSettings();
        
        // Load checkboxes
        document.getElementById('showCrosshair').checked = settings.showCrosshair;
        document.getElementById('stickyCrosshair').checked = settings.stickyCrosshair;
        document.getElementById('crosshairMagnet').checked = settings.crosshairMagnet;
        document.getElementById('grayBackgroundStrips').checked = settings.grayBackgroundStrips;
        document.getElementById('rangeSlider').checked = settings.rangeSlider;
        document.getElementById('extendedHours').checked = settings.extendedHours;
        document.getElementById('hideOutliers').checked = settings.hideOutliers;
        document.getElementById('invertScale').checked = settings.invertScale;
        
        // Load radio buttons
        const yScaleRadios = document.querySelectorAll('input[name="yScaleMode"]');
        yScaleRadios.forEach(radio => {
            radio.checked = radio.value === settings.yScaleMode;
        });
        
        // Update preset indicator
        this.updatePresetButtons();
    }
    
    setupEventListeners() {
        // Chart Preferences
        document.getElementById('showCrosshair').addEventListener('change', (e) => {
            this.settingsManager.updateSetting('showCrosshair', e.target.checked);
            this.chartManager.applySettings();
        });
        
        document.getElementById('stickyCrosshair').addEventListener('change', (e) => {
            this.settingsManager.updateSetting('stickyCrosshair', e.target.checked);
            this.chartManager.applySettings();
        });
        
        document.getElementById('crosshairMagnet').addEventListener('change', (e) => {
            this.settingsManager.updateSetting('crosshairMagnet', e.target.checked);
            this.chartManager.applySettings();
        });
        
        document.getElementById('grayBackgroundStrips').addEventListener('change', (e) => {
            this.settingsManager.updateSetting('grayBackgroundStrips', e.target.checked);
            this.chartManager.applySettings();
        });
        
        document.getElementById('rangeSlider').addEventListener('change', (e) => {
            this.settingsManager.updateSetting('rangeSlider', e.target.checked);
            this.chartManager.applySettings();
            this.toggleRangeSliderUI(e.target.checked);
        });
        
        document.getElementById('extendedHours').addEventListener('change', (e) => {
            this.settingsManager.updateSetting('extendedHours', e.target.checked);
            this.chartManager.applySettings();
        });
        
        document.getElementById('hideOutliers').addEventListener('change', (e) => {
            this.settingsManager.updateSetting('hideOutliers', e.target.checked);
            this.chartManager.applySettings();
        });
        
        // Y-axis Scale
        document.querySelectorAll('input[name="yScaleMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.settingsManager.updateSetting('yScaleMode', e.target.value);
                    this.chartManager.applySettings();
                }
            });
        });
        
        document.getElementById('invertScale').addEventListener('change', (e) => {
            this.settingsManager.updateSetting('invertScale', e.target.checked);
            this.chartManager.applySettings();
        });
        
        // Actions
        document.getElementById('resetSettings').addEventListener('click', () => {
            this.resetSettings();
        });
        
        // Reset view button
        const resetViewBtn = document.getElementById('resetView');
        if (resetViewBtn) {
            resetViewBtn.addEventListener('click', () => {
                this.chartManager.resetViewAll();
            });
        }
        
        document.getElementById('closeSettings').addEventListener('click', () => {
            this.closeSettings();
        });
        
        // Preset buttons
        document.getElementById('presetDefault').addEventListener('click', () => {
            this.applyPreset('default');
        });
        
        document.getElementById('presetClean').addEventListener('click', () => {
            this.applyPreset('clean');
        });
        
        document.getElementById('presetTechnical').addEventListener('click', () => {
            this.applyPreset('technical');
        });
    }
    
    resetSettings() {
        if (confirm('Reset all settings to defaults?')) {
            this.settingsManager.resetToDefaults();
            this.loadSettingsToUI();
            this.chartManager.applySettings();
        }
    }
    
    closeSettings() {
        // Close dropdown by clicking outside
        document.activeElement.blur();
    }

    toggleRangeSliderUI(visible) {
        const container = document.getElementById('rangeSliderContainer');
        if (!container) return;
        container.classList.toggle('hidden', !visible);
    }

    initRangeSliderBinding() {
        const slider = document.getElementById('rangeSliderInput');
        const zoomLevel = document.getElementById('zoomLevel');
        if (!slider || !zoomLevel) return;
        
        // Load saved zoom level for current interval
        this.updateRangeSliderValue();
        
        slider.addEventListener('input', (e) => {
            const percent = Number(e.target.value);
            const zoomPercent = percent / 100; // convert to 0.0-1.0 range
            zoomLevel.textContent = `${percent}%`;
            
            // Save zoom level for current interval
            const currentInterval = this.settingsManager.getCurrentInterval();
            this.settingsManager.setZoomLevel(currentInterval, zoomPercent);
            
            // Apply zoom to current interval only
            this.chartManager.applyZoomPercent(percent, currentInterval);
        });
        
        // Fit buttons - apply to current interval only
        document.getElementById('fitLast20')?.addEventListener('click', () => {
            const currentInterval = this.settingsManager.getCurrentInterval();
            this.chartManager.fitLastBarsForInterval(20, currentInterval);
            this.settingsManager.setFitLastBars(20);
        });
        
        document.getElementById('fitLast50')?.addEventListener('click', () => {
            const currentInterval = this.settingsManager.getCurrentInterval();
            this.chartManager.fitLastBarsForInterval(50, currentInterval);
            this.settingsManager.setFitLastBars(50);
        });
        
        document.getElementById('fitLast100')?.addEventListener('click', () => {
            const currentInterval = this.settingsManager.getCurrentInterval();
            this.chartManager.fitLastBarsForInterval(100, currentInterval);
            this.settingsManager.setFitLastBars(100);
        });
        
        document.getElementById('fitAll')?.addEventListener('click', () => {
            const currentInterval = this.settingsManager.getCurrentInterval();
            this.chartManager.resetViewForInterval(currentInterval);
            this.settingsManager.setFitLastBars(null);
        });
    }
    
    updateRangeSliderValue() {
        const slider = document.getElementById('rangeSliderInput');
        const zoomLevel = document.getElementById('zoomLevel');
        
        if (slider && zoomLevel) {
            const currentInterval = this.settingsManager.getCurrentInterval();
            const zoomPercent = this.settingsManager.getZoomLevel(currentInterval);
            const sliderValue = Math.round(zoomPercent * 100);
            
            slider.value = sliderValue;
            zoomLevel.textContent = `${sliderValue}%`;
        }
    }
    
    // Method to call when switching intervals
    onIntervalChange(newInterval) {
        this.settingsManager.setCurrentInterval(newInterval);
        this.updateRangeSliderValue();
        // Apply saved zoom level for the new interval
        this.applyZoomLevelForCurrentInterval();
    }
    
    // Apply zoom level for current interval
    applyZoomLevelForCurrentInterval() {
        const currentInterval = this.settingsManager.getCurrentInterval();
        const zoomPercent = this.settingsManager.getZoomLevel(currentInterval);
        const zoomValue = Math.round(zoomPercent * 100);
        
        // Apply zoom to current interval
        this.chartManager.applyZoomPercent(zoomValue, currentInterval);
    }
    
    applyPreset(presetKey) {
        this.settingsManager.applyPreset(presetKey);
        this.loadSettingsToUI();
        this.chartManager.applySettings();
        
        // Show feedback
        const presetName = this.settingsManager.getPresets()[presetKey].name;
        this.showPresetFeedback(presetName);
    }
    
    updatePresetButtons() {
        const currentPreset = this.settingsManager.getCurrentPresetName();
        const currentPresetElement = document.getElementById('currentPreset');
        if (currentPresetElement) {
            currentPresetElement.textContent = `Current: ${currentPreset}`;
        }
        
        // Update button states
        const presetButtons = ['presetDefault', 'presetClean', 'presetTechnical'];
        presetButtons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                const presetKey = buttonId.replace('preset', '').toLowerCase();
                const isActive = this.settingsManager.getPresets()[presetKey].name === currentPreset;
                button.classList.toggle('btn-primary', isActive);
                button.classList.toggle('btn-outline', !isActive);
            }
        });
    }
    
    showPresetFeedback(presetName) {
        // Create temporary feedback
        const feedback = document.createElement('div');
        feedback.className = 'absolute top-2 right-2 bg-success text-success-content px-2 py-1 rounded text-xs z-50';
        feedback.textContent = `Applied: ${presetName}`;
        document.body.appendChild(feedback);
        
        setTimeout(() => {
            feedback.remove();
        }, 2000);
    }
}
