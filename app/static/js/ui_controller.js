/**
 * UI Controller - Handles UI interactions and updates
 */
class UIController {
    constructor() {
        this.chartManager = null; // Will be set by main app
    }
    
    setChartManager(chartManager) {
        this.chartManager = chartManager;
    }
    
    safeSetTextContent(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
            return true;
        }
        return false;
    }
    
    formatVolume(volume) {
        if (volume >= 1e9) {
            return (volume / 1e9).toFixed(1) + 'B';
        } else if (volume >= 1e6) {
            return (volume / 1e6).toFixed(1) + 'M';
        } else if (volume >= 1e3) {
            return (volume / 1e3).toFixed(1) + 'K';
        } else {
            return volume.toFixed(0);
        }
    }
    
    updateSymbolDisplay(symbol) {
        for (let i = 1; i <= 3; i++) {
            this.safeSetTextContent(`symbol${i}`, symbol);
        }
    }
    
    updateIntervalBadges(intervals) {
        intervals.forEach((interval, index) => {
            // Update the badge text in the interval badge elements
            const badgeElement = document.querySelector(`#chart${index + 1}`).previousElementSibling;
            if (badgeElement && badgeElement.classList.contains('interval-badge')) {
                // Find the span with font-semibold class (regardless of color class)
                const badge = badgeElement.querySelector('span.font-semibold');
                if (badge) {
                    badge.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
                    badge.style.opacity = '0.5';
                    badge.style.transform = 'scale(0.95)';
                    
                    setTimeout(() => {
                        badge.textContent = interval;
                        badge.style.opacity = '1';
                        badge.style.transform = 'scale(1)';
                    }, 100);
                }
            }
        });
    }
    
    showModeTransitionLoading() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            let loadingOverlay = container.querySelector('.mode-loading-overlay');
            if (!loadingOverlay) {
                loadingOverlay = document.createElement('div');
                loadingOverlay.className = 'mode-loading-overlay absolute inset-0 bg-base-100 bg-opacity-90 flex items-center justify-center z-20';
                loadingOverlay.innerHTML = `
                    <div class="flex flex-col items-center gap-2">
                        <span class="loading loading-spinner loading-md text-primary"></span>
                        <span class="text-sm text-base-content opacity-70">Switching mode...</span>
                    </div>
                `;
                container.style.position = 'relative';
                container.appendChild(loadingOverlay);
            }
            loadingOverlay.style.display = 'flex';
        });
    }
    
    hideModeTransitionLoading() {
        const loadingOverlays = document.querySelectorAll('.mode-loading-overlay');
        loadingOverlays.forEach(overlay => {
            overlay.style.display = 'none';
        });
        
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.style.transition = 'opacity 0.5s ease';
            container.style.opacity = '1';
        });
    }
    
    showLoadingState() {
        const fetchBtn = document.getElementById('fetchData');
        const originalContent = fetchBtn.innerHTML;
        fetchBtn.innerHTML = '<span class="loading loading-spinner loading-xs"></span>';
        fetchBtn.disabled = true;
        fetchBtn.setAttribute('data-original-content', originalContent);
    }
    
    hideLoadingState() {
        const fetchBtn = document.getElementById('fetchData');
        const originalContent = fetchBtn.getAttribute('data-original-content');
        if (originalContent) {
            fetchBtn.innerHTML = originalContent;
            fetchBtn.removeAttribute('data-original-content');
        }
        fetchBtn.disabled = false;
    }
    
    showErrorMessage(message) {
        let errorDiv = document.getElementById('error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'error-message';
            errorDiv.className = 'alert alert-error shadow-lg fixed top-4 right-4 z-50 max-w-sm';
            document.body.appendChild(errorDiv);
        }
        
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
            <button class="btn btn-sm btn-ghost" onclick="this.parentElement.remove()">×</button>
        `;
        
        setTimeout(() => {
            if (errorDiv && errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    updatePriceInfo(interval, data) {
        const chartIntervals = this.chartManager ? this.chartManager.chartIntervals : ['2m', '5m', '15m'];
        const chartIndex = chartIntervals.indexOf(interval) + 1;
        
        if (data.candlestick && data.candlestick.length > 0) {
            const latest = data.candlestick[data.candlestick.length - 1];
            this.safeSetTextContent(`open${chartIndex}`, latest.open.toFixed(2));
            this.safeSetTextContent(`high${chartIndex}`, latest.high.toFixed(2));
            this.safeSetTextContent(`low${chartIndex}`, latest.low.toFixed(2));
            this.safeSetTextContent(`close${chartIndex}`, latest.close.toFixed(2));
            
            if (data.volume && data.volume.length > 0) {
                const latestVolume = data.volume[data.volume.length - 1];
                this.safeSetTextContent(`volume${chartIndex}`, this.formatVolume(latestVolume.value));
            } else {
                this.safeSetTextContent(`volume${chartIndex}`, 'N/A');
            }
        }
        
        if (data.macd && data.macd.macd_line && data.macd.macd_line.length > 0) {
            const latestMacd = data.macd.macd_line[data.macd.macd_line.length - 1];
            const latestSignal = data.macd.signal_line[data.macd.signal_line.length - 1];
            const latestHistogram = data.macd.histogram[data.macd.histogram.length - 1];
            
            const macdText = `${latestMacd.value.toFixed(2)} ${latestSignal.value.toFixed(2)} ${latestHistogram.value.toFixed(2)}`;
            this.safeSetTextContent(`macdValues${chartIndex}`, macdText);
        }
    }
}
