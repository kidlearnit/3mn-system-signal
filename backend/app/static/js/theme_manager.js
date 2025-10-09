/**
 * Theme Manager - Handles dark/light theme switching
 */
class ThemeManager {
    constructor() {
        this.currentTheme = this.loadThemePreference();
        this.initializeTheme();
    }
    
    getCurrentTheme() {
        return document.body.classList.contains('dark') ? 'dark' : 'light';
    }
    
    initializeTheme() {
        // Set initial theme based on current state
        const isDark = this.currentTheme === 'dark';
        document.body.setAttribute('data-theme', this.currentTheme);
        this.updateThemeIcons(isDark);
    }
    
    toggleTheme() {
        if (this.currentTheme === 'light') {
            this.switchToDarkTheme();
        } else {
            this.switchToLightTheme();
        }
    }
    
    switchToDarkTheme() {
        document.body.classList.add('dark');
        document.body.setAttribute('data-theme', 'dark');
        this.currentTheme = 'dark';
        this.updateThemeIcons(true);
        this.updateChartsTheme(true);
        this.saveThemePreference('dark');
    }
    
    switchToLightTheme() {
        document.body.classList.remove('dark');
        document.body.setAttribute('data-theme', 'light');
        this.currentTheme = 'light';
        this.updateThemeIcons(false);
        this.updateChartsTheme(false);
        this.saveThemePreference('light');
    }
    
    updateThemeIcons(isDark) {
        const darkIcon = document.querySelector('.dark-icon');
        const lightIcon = document.querySelector('.light-icon');
        
        if (darkIcon && lightIcon) {
            if (isDark) {
                darkIcon.classList.add('hidden');
                lightIcon.classList.remove('hidden');
            } else {
                darkIcon.classList.remove('hidden');
                lightIcon.classList.add('hidden');
            }
        }
    }
    
    saveThemePreference(theme) {
        try {
            localStorage.setItem('tradingview-theme', theme);
        } catch (e) {
            console.warn('Failed to save theme preference:', e);
        }
    }
    
    loadThemePreference() {
        try {
            const saved = localStorage.getItem('tradingview-theme');
            if (saved && (saved === 'dark' || saved === 'light')) {
                return saved;
            }
        } catch (e) {
            console.warn('Failed to load theme preference:', e);
        }
        return 'light';
    }
    
    updateChartsTheme(isDark) {
        // Dispatch event for ChartManager to handle chart theme updates
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { isDark } }));
    }
    
    setSettingsManager(settingsManager) {
        this.settingsManager = settingsManager;
    }
    
    onThemeChange() {
        // Reload settings for the new theme
        if (this.settingsManager) {
            this.settingsManager.reloadForTheme();
        }
    }
}
