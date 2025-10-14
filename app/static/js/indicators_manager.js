class IndicatorsManager {
    constructor(chartManager) {
        this.chartManager = chartManager;
        this.appliedIndicators = new Map(); // interval -> indicators
        this.indicatorConfigs = {
            // Moving Averages
            ma: { name: 'Moving Average', params: { period: 20, style: 1 }, type: 'overlay' },
            ema: { name: 'Exponential Moving Average', params: { period: 20, style: 1 }, type: 'overlay' },
            sma: { name: 'Simple Moving Average', params: { period: 20, style: 1 }, type: 'overlay' },
            wma: { name: 'Weighted Moving Average', params: { period: 20, style: 1 }, type: 'overlay' },
            
            // Momentum
            rsi: { name: 'RSI', params: { period: 14 }, type: 'separate' },
            macd: { name: 'MACD', params: { fast: 12, slow: 26, signal: 9 }, type: 'separate' },
            stoch: { name: 'Stochastic', params: { kPeriod: 14, dPeriod: 3 }, type: 'separate' },
            williams: { name: 'Williams %R', params: { period: 14 }, type: 'separate' },
            cci: { name: 'Commodity Channel Index', params: { period: 20 }, type: 'separate' },
            
            // Volatility
            bb: { name: 'Bollinger Bands', params: { period: 20, stdDev: 2 }, type: 'overlay' },
            atr: { name: 'Average True Range', params: { period: 14 }, type: 'separate' },
            
            // Volume
            volume: { name: 'Volume', params: {}, type: 'overlay' },
            obv: { name: 'On Balance Volume', params: {}, type: 'separate' },
            vwap: { name: 'VWAP', params: {}, type: 'overlay' },
            
            // Trend
            adx: { name: 'ADX', params: { period: 14 }, type: 'separate' },
            psar: { name: 'Parabolic SAR', params: { step: 0.02, max: 0.2 }, type: 'overlay' }
        };
        
        this.init();
    }
    
    init() {
        this.clearDefaultIndicators();
        this.setupEventListeners();
        this.loadSavedIndicators(); // Load saved indicators from localStorage
        this.updateAppliedIndicatorsDisplay();
    }
    
    clearDefaultIndicators() {
        // No need to clear indicators anymore - ChartManager now only adds candlestick by default
    }
    
    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('indicatorSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterIndicators(e.target.value);
            });
        }
        
        // Click outside to close dropdown
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('indicatorsDropdown');
            if (dropdown && !dropdown.contains(e.target)) {
                // Only close if not clicking on buttons inside the dropdown
                const isButtonClick = e.target.closest('button') || e.target.closest('input[type="checkbox"]');
                if (!isButtonClick) {
                    // Close dropdown by removing focus
                    const button = dropdown.querySelector('[tabindex="0"]');
                    if (button) {
                        button.blur();
                    }
                }
            }
        });
    }
    
    addIndicator(indicatorType, interval = null) {
        if (!this.indicatorConfigs[indicatorType]) {
            console.warn(`Unknown indicator type: ${indicatorType}`);
            return;
        }
        
        // If no interval specified, add to all intervals across all modes
        const allIntervals = ['1m', '2m', '5m', '15m', '30m', '60m'];
        const intervals = interval ? [interval] : allIntervals;
        
        
        intervals.forEach(targetInterval => {
            if (!this.appliedIndicators.has(targetInterval)) {
                this.appliedIndicators.set(targetInterval, []);
            }
            
            // Create unique ID with timestamp and random number to allow multiple instances
            const indicatorId = `${indicatorType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${targetInterval}`;
            const indicator = {
                id: indicatorId,
                type: indicatorType,
                config: { ...this.indicatorConfigs[indicatorType] },
                interval: targetInterval,
                visible: true
            };
            
            this.appliedIndicators.get(targetInterval).push(indicator);
            
            
            // Try to apply immediately, if data is available
            this.applyIndicatorToChart(indicator);
        });
        
        this.updateAppliedIndicatorsDisplay();
        this.saveIndicatorsToStorage(); // Save to localStorage after adding
        
        // Update indicator info display for all intervals
        intervals.forEach(interval => {
            if (window.chartManager) {
                // Show indicator info immediately when added
                window.chartManager.showIndicatorInfoForInterval(interval);
            }
        });
        
        // If indicators couldn't be applied (no data), try again after a short delay
        setTimeout(() => {
            this.reapplyAllIndicators();
        }, 1000);
    }
    
    reapplyAllIndicators() {
        this.appliedIndicators.forEach((indicators, interval) => {
            indicators.forEach(indicator => {
                this.applyIndicatorToChart(indicator);
            });
            
            // Show indicator info after reapplying
            if (window.chartManager) {
                window.chartManager.showIndicatorInfoForInterval(interval);
            }
        });
        
        // Update display
        this.updateAppliedIndicatorsDisplay();
    }
    
    // Method to reapply indicators for current mode intervals
    reapplyIndicatorsForCurrentMode() {
        const currentIntervals = this.chartManager.chartIntervals || ['2m', '5m', '15m'];
        
        // Check if charts are ready
        if (!this.chartManager.areChartsReady()) {
            setTimeout(() => this.reapplyIndicatorsForCurrentMode(), 200);
            return;
        }
        
        // Add small delay to ensure charts are fully rendered
        setTimeout(() => {
            currentIntervals.forEach(interval => {
                const indicators = this.appliedIndicators.get(interval);
                if (indicators) {
                    indicators.forEach(indicator => {
                        if (indicator.visible !== false) {
                            this.applyIndicatorToChart(indicator);
                        }
                    });
                    
                    // Show indicator info for current mode
                    if (window.chartManager) {
                        window.chartManager.showIndicatorInfoForInterval(interval);
                    }
                }
            });
            
            // Update applied indicators display
            this.updateAppliedIndicatorsDisplay();
        }, 100);
    }
    
    clearIndicatorCache(interval = null) {
        if (!this.indicatorCache) return;
        
        if (interval) {
            // Clear cache for specific interval
            for (const [key, value] of this.indicatorCache) {
                if (key.startsWith(`${interval}_`)) {
                    this.indicatorCache.delete(key);
                }
            }
        } else {
            // Clear all cache
            this.indicatorCache.clear();
        }
    }
    
    removeIndicator(indicatorId, interval) {
        if (!this.appliedIndicators.has(interval)) return;
        
        const indicators = this.appliedIndicators.get(interval);
        const index = indicators.findIndex(ind => ind.id === indicatorId);
        
        if (index !== -1) {
            const indicator = indicators[index];
            this.removeIndicatorFromChart(indicator);
            indicators.splice(index, 1);
            this.updateAppliedIndicatorsDisplay();
        }
    }
    
    toggleIndicatorVisibility(indicatorId, interval, visible) {
        if (!this.appliedIndicators.has(interval)) return;
        
        const indicators = this.appliedIndicators.get(interval);
        const indicator = indicators.find(ind => ind.id === indicatorId);
        
        if (indicator) {
            indicator.visible = visible;
            if (visible) {
                // Show indicator
                this.applyIndicatorToChart(indicator);
            } else {
                // Hide indicator
                this.removeIndicatorFromChart(indicator);
            }
            this.saveIndicatorsToStorage(); // Save visibility state
        }
    }
    
    editIndicatorType(type) {
        // Find first instance of this indicator type to get current config
        let sampleIndicator = null;
        for (const [interval, indicators] of this.appliedIndicators) {
            const indicator = indicators.find(ind => ind.type === type);
            if (indicator) {
                sampleIndicator = indicator;
                break;
            }
        }
        
        if (sampleIndicator) {
            this.showIndicatorSettingsModal(sampleIndicator);
        }
    }
    
    removeIndicator(indicatorId, interval) {
        // Remove specific indicator from specific interval
        if (!this.appliedIndicators.has(interval)) return;
        
        const indicators = this.appliedIndicators.get(interval);
        const indicator = indicators.find(ind => ind.id === indicatorId);
        
        if (indicator) {
            // Remove from chart
            this.removeIndicatorFromChart(indicator);
            
            // Remove from array
            const filteredIndicators = indicators.filter(ind => ind.id !== indicatorId);
            this.appliedIndicators.set(interval, filteredIndicators);
            
            this.updateAppliedIndicatorsDisplay();
            this.saveIndicatorsToStorage(); // Save to localStorage after removing
            
            // Update indicator info display for this interval
            if (window.chartManager) {
                window.chartManager.showIndicatorInfoForInterval(interval);
            }
            
        }
    }
    
    removeIndicatorType(type) {
        // Remove this indicator type from all intervals
        this.appliedIndicators.forEach((indicators, interval) => {
            const indicatorsToRemove = indicators.filter(ind => ind.type === type);
            indicatorsToRemove.forEach(indicator => {
                this.removeIndicatorFromChart(indicator);
            });
            
            // Remove from array
            const filteredIndicators = indicators.filter(ind => ind.type !== type);
            this.appliedIndicators.set(interval, filteredIndicators);
        });
        
        this.updateAppliedIndicatorsDisplay();
        
        // Update indicator info display for all intervals
        this.chartManager.chartIntervals.forEach(interval => {
            if (window.chartManager) {
                // Show indicator info immediately when removed
                window.chartManager.showIndicatorInfoForInterval(interval);
            }
        });
        
        // Don't close the panel - just update the display
    }
    
    toggleIndicatorTypeVisibility(type, visible) {
        // Toggle visibility of this indicator type across all intervals
        this.appliedIndicators.forEach((indicators, interval) => {
            const indicatorsOfType = indicators.filter(ind => ind.type === type);
            indicatorsOfType.forEach(indicator => {
                if (visible) {
                    // Show indicator
                    this.applyIndicatorToChart(indicator);
                } else {
                    // Hide indicator
                    this.removeIndicatorFromChart(indicator);
                }
            });
        });
        
        
        // Update indicator info display for all intervals
        this.chartManager.chartIntervals.forEach(interval => {
            if (window.chartManager) {
                // Show indicator info immediately when toggled
                window.chartManager.showIndicatorInfoForInterval(interval);
            }
        });
    }
    
    
    editIndicator(indicatorId, interval) {
        if (!this.appliedIndicators.has(interval)) return;
        
        const indicators = this.appliedIndicators.get(interval);
        const indicator = indicators.find(ind => ind.id === indicatorId);
        
        if (indicator) {
            this.showIndicatorSettingsModal(indicator);
        }
    }
    
    applyIndicatorToChart(indicator) {
        
        const chart = this.chartManager.charts[indicator.interval];
        if (!chart) {
            console.warn(`Chart not found for interval ${indicator.interval}`);
            return;
        }
        
        // Check if chart has required methods (LightweightCharts v4+ uses addSeries)
        if (typeof chart.addSeries !== 'function') {
            console.error(`Chart for ${indicator.interval} does not have addSeries method`);
            return;
        }
        
        try {
            switch (indicator.type) {
                case 'ma':
                    this.addMovingAverage(chart, indicator);
                    break;
                case 'sma':
                    this.addMovingAverage(chart, indicator);
                    break;
                case 'ema':
                    this.addExponentialMovingAverage(chart, indicator);
                    break;
                case 'rsi':
                    this.addRSI(chart, indicator);
                    break;
                case 'bb':
                    this.addBollingerBands(chart, indicator);
                    break;
                case 'volume':
                    this.addVolume(chart, indicator);
                    break;
                default:
                    console.warn(`Indicator type ${indicator.type} not implemented yet`);
                    return;
            }
            
        } catch (error) {
            console.error(`Error applying indicator ${indicator.type}:`, error);
        }
    }
    
    removeIndicatorFromChart(indicator) {
        // Remove indicator series from chart
        if (indicator.series) {
            try {
                const chart = this.chartManager.charts[indicator.interval];
                if (chart) {
                    if (Array.isArray(indicator.series)) {
                        // Multiple series (like Bollinger Bands)
                        indicator.series.forEach(series => {
                            chart.removeSeries(series);
                        });
                    } else {
                        // Single series
                        chart.removeSeries(indicator.series);
                    }
                }
            } catch (error) {
                console.error(`Error removing indicator series:`, error);
            }
        }
    }
    
    // Indicator implementation methods
    addMovingAverage(chart, indicator) {
        const period = indicator.config.params.period;
        const offset = indicator.config.params.offset || 0;
        const indicatorType = indicator.type === 'sma' ? 'sma' : 'ma';
        const data = this.getIndicatorData(indicator.interval, indicatorType, period, offset);
        
        //     dataLength: data?.length, 
        //     chart: !!chart,
        //     chartType: typeof chart,
        //     chartMethods: chart ? Object.getOwnPropertyNames(chart) : 'null',
        //     interval: indicator.interval
        // });
        
        if (data && data.length > 0) {
            try {
                // De-duplicate SMA per (interval, period, offset)
                const title = indicator.type === 'sma' 
                    ? (offset > 0 ? `SMA(${period},${offset})` : `SMA(${period})`)
                    : (offset > 0 ? `MA(${period},${offset})` : `MA(${period})`);
                // Include current symbol in the key so changing ticker doesn't lose/reuse wrong series
                const currentSymbol = (document.getElementById('ticker')?.value || '').toUpperCase();
                const key = `${currentSymbol}::${indicator.interval}::${title}`;

                if (!this.chartManager.series.indicatorsByKey) {
                    this.chartManager.series.indicatorsByKey = {};
                }

                const existing = this.chartManager.series.indicatorsByKey[key];
                if (existing) {
                    try {
                        // Reuse existing series and just update data
                        existing.setData(data);
                        indicator.series = existing;
                        // Also map this indicator id to the existing series for crosshair sync
                        if (!this.chartManager.series.indicators) {
                            this.chartManager.series.indicators = {};
                        }
                        this.chartManager.series.indicators[indicator.id] = existing;
                        return;
                    } catch (reuseError) {
                        // If old series is detached (e.g., after symbol change), create a new one
                        delete this.chartManager.series.indicatorsByKey[key];
                    }
                }

                // Create new series if not exists yet
                const series = chart.addSeries(LightweightCharts.LineSeries, {
                    color: this.getIndicatorColor(indicator.type, 'default', period),
                    lineWidth: 2,
                    title: '',
                    lastValueVisible: true,
                    priceLineVisible: false,
                    titleVisible: false
                });

                if (!this.chartManager.series.indicators) {
                    this.chartManager.series.indicators = {};
                }
                this.chartManager.series.indicators[indicator.id] = series;
                this.chartManager.series.indicatorsByKey[key] = series;

                series.setData(data);
                indicator.series = series;
            } catch (error) {
                console.error(`Error adding MA series:`, error);
            }
        } else {
            console.warn(`No data available for MA(${period})`);
        }
    }
    
    addExponentialMovingAverage(chart, indicator) {
        const period = indicator.config.params.period;
        const data = this.getIndicatorData(indicator.interval, 'ema', period);
        
        if (data && data.length > 0) {
            // Always create new series for indicators
            const series = chart.addSeries(LightweightCharts.LineSeries, {
                color: this.getIndicatorColor(indicator.type),
                lineWidth: 2,
                title: `EMA(${period})`,
                lastValueVisible: false,
                priceLineVisible: false
            });
            
            // Store series reference in ChartManager for crosshair sync (by indicator ID)
            if (!this.chartManager.series.indicators) {
                this.chartManager.series.indicators = {};
            }
            this.chartManager.series.indicators[indicator.id] = series;
            
            series.setData(data);
            indicator.series = series;
        }
    }
    
    addRSI(chart, indicator) {
        const period = indicator.config.params.period;
        const data = this.getIndicatorData(indicator.interval, 'rsi', period);
        
        if (data && data.length > 0) {
            const series = chart.addSeries(LightweightCharts.LineSeries, {
                color: this.getIndicatorColor(indicator.type),
                lineWidth: 2,
                title: `RSI(${period})`,
                lastValueVisible: false,
                priceLineVisible: false
            });
            
            series.setData(data);
            indicator.series = series;
        }
    }
    
    addBollingerBands(chart, indicator) {
        const period = indicator.config.params.period;
        const stdDev = indicator.config.params.stdDev;
        const data = this.getIndicatorData(indicator.interval, 'bb', period, stdDev);
        
        if (data && data.upper && data.middle && data.lower) {
            // Check if we can reuse existing BB series from ChartManager
            let upperSeries = this.chartManager.series.bbUpper[indicator.interval];
            let middleSeries = this.chartManager.series.bbMiddle[indicator.interval];
            let lowerSeries = this.chartManager.series.bbLower[indicator.interval];
            
            // If no existing series, create new ones
            if (!upperSeries) {
                upperSeries = chart.addSeries(LightweightCharts.LineSeries, {
                    color: this.getIndicatorColor(indicator.type, 'upper'),
                    lineWidth: 1,
                    title: `BB Upper(${period})`,
                    lastValueVisible: false,
                    priceLineVisible: false
                });
            }
            
            if (!middleSeries) {
                middleSeries = chart.addSeries(LightweightCharts.LineSeries, {
                    color: this.getIndicatorColor(indicator.type, 'middle'),
                    lineWidth: 1,
                    title: `BB Middle(${period})`,
                    lastValueVisible: false,
                    priceLineVisible: false
                });
            }
            
            if (!lowerSeries) {
                lowerSeries = chart.addSeries(LightweightCharts.LineSeries, {
                    color: this.getIndicatorColor(indicator.type, 'lower'),
                    lineWidth: 1,
                    title: `BB Lower(${period})`,
                    lastValueVisible: false,
                    priceLineVisible: false
                });
            }
            
            upperSeries.setData(data.upper);
            middleSeries.setData(data.middle);
            lowerSeries.setData(data.lower);
            
            indicator.series = [upperSeries, middleSeries, lowerSeries];
        }
    }
    
    addVolume(chart, indicator) {
        const data = this.getIndicatorData(indicator.interval, 'volume');
        
        if (data && data.length > 0) {
            // Check if we can reuse existing volume series from ChartManager
            let series = this.chartManager.series.volume[indicator.interval];
            
            // If no existing series, create new one
            if (!series) {
                series = chart.addSeries(LightweightCharts.HistogramSeries, {
                    color: this.getIndicatorColor(indicator.type),
                    title: 'Volume'
                });
            }
            
            series.setData(data);
            indicator.series = series;
        }
    }
    
    getIndicatorData(interval, type, ...params) {
        // Get data from chart manager's cached data
        const cache = this.chartManager.dataCache[interval];
        if (!cache) {
            console.warn(`No data cache found for interval ${interval}`);
            return null;
        }
        
        // Try different possible data structures
        let candlestickData = cache.candlestick || cache.data || cache;
        
        // If it's an array, use it directly
        if (Array.isArray(candlestickData)) {
            // Data is already in correct format
        } else if (candlestickData && typeof candlestickData === 'object') {
            // Try to find array data in the object
            const possibleKeys = ['candlestick', 'data', 'ohlc', 'bars'];
            for (const key of possibleKeys) {
                if (Array.isArray(candlestickData[key])) {
                    candlestickData = candlestickData[key];
                    break;
                }
            }
        }
        
        if (!Array.isArray(candlestickData) || candlestickData.length === 0) {
            console.warn(`No valid candlestick data found for interval ${interval}`);
            return null;
        }
        
        // Create cache key for this calculation
        const cacheKey = `${interval}_${type}_${params.join('_')}`;
        
        // Check if we already calculated this indicator
        if (!this.indicatorCache) {
            this.indicatorCache = new Map();
        }
        
        if (this.indicatorCache.has(cacheKey)) {
            return this.indicatorCache.get(cacheKey);
        }
        
        // Calculate indicator
        let result;
        switch (type) {
            case 'ma':
                result = this.calculateMovingAverage(candlestickData, params[0], params[1] || 0);
                break;
            case 'sma':
                result = this.calculateMovingAverage(candlestickData, params[0], params[1] || 0);
                break;
            case 'ema':
                result = this.calculateEMA(candlestickData, params[0]);
                break;
            case 'rsi':
                result = this.calculateRSI(candlestickData, params[0]);
                break;
            case 'bb':
                result = this.calculateBollingerBands(candlestickData, params[0], params[1]);
                break;
            case 'volume':
                result = this.formatVolumeData(candlestickData);
                break;
            default:
                console.warn(`Unknown indicator type: ${type}`);
                return null;
        }
        
        // Cache the result
        if (result) {
            this.indicatorCache.set(cacheKey, result);
        }
        
        return result;
    }
    
    getIndicatorColor(type, variant = 'default', period = null) {
        const colors = {
            ma: '#FF6B6B',
            sma: {
                18: '#FF4444',   // Bright Red
                36: '#00AA44',   // Bright Green
                48: '#0066FF',   // Bright Blue
                144: '#FF8800',  // Orange
                default: '#FF6B6B'
            },
            ema: '#4ECDC4',
            rsi: '#45B7D1',
            bb: {
                upper: '#FF9F43',
                middle: '#FF6B6B',
                lower: '#FF9F43'
            },
            volume: '#95A5A6'
        };
        
        if (type === 'sma' && period) {
            return colors.sma[period] || colors.sma.default;
        }
        
        return colors[type] && typeof colors[type] === 'object' 
            ? colors[type][variant] || colors[type].default
            : colors[type] || '#95A5A6';
    }
    
    // Calculation methods
    calculateMovingAverage(data, period, offset = 0, interval = '1m') {
        if (!data || data.length < period) return [];
        
        const result = [];
        
        // Calculate MA values first
        for (let i = period - 1; i < data.length; i++) {
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += data[i - j].close;
            }
            
            result.push({
                time: data[i].time,
                value: sum / period
            });
        }
        
        // Apply offset by shifting time forward (like Yahoo Finance)
        if (offset > 0) {
            // Shift the time forward by offset positions
            const shiftedResult = [];
            
            for (let i = 0; i < result.length; i++) {
                const targetIndex = i + offset;
                if (targetIndex < result.length) {
                    shiftedResult.push({
                        time: result[targetIndex].time,  // Use future time
                        value: result[i].value           // Keep current value
                    });
                } else {
                    // Extend into the future beyond available data
                    const lastTime = result[result.length - 1].time;
                    const timeDiff = result[1] ? result[1].time - result[0].time : 60000; // Default 1 minute
                    const futureTime = lastTime + (targetIndex - result.length + 1) * timeDiff;
                    
                    shiftedResult.push({
                        time: futureTime,
                        value: result[i].value
                    });
                }
            }
            
            return shiftedResult;
        }
        
        return result;
    }
    
    
    calculateEMA(data, period) {
        if (!data || data.length < period) return [];
        
        const result = [];
        const multiplier = 2 / (period + 1);
        
        // First EMA is SMA
        let sum = 0;
        for (let i = 0; i < period; i++) {
            sum += data[i].close;
        }
        result.push({
            time: data[period - 1].time,
            value: sum / period
        });
        
        // Calculate EMA for remaining data
        for (let i = period; i < data.length; i++) {
            const ema = (data[i].close * multiplier) + (result[result.length - 1].value * (1 - multiplier));
            result.push({
                time: data[i].time,
                value: ema
            });
        }
        return result;
    }
    
    calculateRSI(data, period) {
        if (!data || data.length < period + 1) return [];
        
        const result = [];
        const gains = [];
        const losses = [];
        
        // Calculate price changes
        for (let i = 1; i < data.length; i++) {
            const change = data[i].close - data[i - 1].close;
            gains.push(change > 0 ? change : 0);
            losses.push(change < 0 ? Math.abs(change) : 0);
        }
        
        // Calculate initial average gain and loss
        let avgGain = 0;
        let avgLoss = 0;
        for (let i = 0; i < period; i++) {
            avgGain += gains[i];
            avgLoss += losses[i];
        }
        avgGain /= period;
        avgLoss /= period;
        
        // Calculate RSI
        for (let i = period; i < gains.length; i++) {
            avgGain = (avgGain * (period - 1) + gains[i]) / period;
            avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
            
            const rs = avgGain / avgLoss;
            const rsi = 100 - (100 / (1 + rs));
            
            result.push({
                time: data[i + 1].time,
                value: rsi
            });
        }
        return result;
    }
    
    calculateBollingerBands(data, period, stdDev) {
        if (!data || data.length < period) return { upper: [], middle: [], lower: [] };
        
        const ma = this.calculateMovingAverage(data, period);
        const upper = [];
        const lower = [];
        
        for (let i = period - 1; i < data.length; i++) {
            // Calculate standard deviation
            let sum = 0;
            for (let j = 0; j < period; j++) {
                const diff = data[i - j].close - ma[i - period + 1].value;
                sum += diff * diff;
            }
            const variance = sum / period;
            const standardDeviation = Math.sqrt(variance);
            
            const maValue = ma[i - period + 1].value;
            upper.push({
                time: data[i].time,
                value: maValue + (standardDeviation * stdDev)
            });
            lower.push({
                time: data[i].time,
                value: maValue - (standardDeviation * stdDev)
            });
        }
        
        return {
            upper,
            middle: ma,
            lower
        };
    }
    
    formatVolumeData(data) {
        if (!data) return [];
        
        return data.map(item => ({
            time: item.time,
            value: item.volume || 0,
            color: item.close >= item.open ? '#26a69a' : '#ef5350'
        }));
    }
    
    updateAppliedIndicatorsDisplay() {
        const container = document.getElementById('appliedIndicators');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Group indicators by type and parameters to avoid duplicates
        const uniqueIndicators = new Map();
        
        this.appliedIndicators.forEach((indicators, interval) => {
            indicators.forEach(indicator => {
                // Create a unique key based on type and parameters
                const key = `${indicator.type}_${JSON.stringify(indicator.config.params)}`;
                
                if (!uniqueIndicators.has(key)) {
                    uniqueIndicators.set(key, {
                        ...indicator,
                        key: key,
                        intervals: [interval]
                    });
                } else {
                    // Add interval to existing indicator only if not already present
                    const existingIndicator = uniqueIndicators.get(key);
                    if (!existingIndicator.intervals.includes(interval)) {
                        existingIndicator.intervals.push(interval);
                    }
                }
            });
        });
        
        const allIndicators = Array.from(uniqueIndicators.values());
        
        if (allIndicators.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500 text-xs py-4">No indicators applied</div>';
            return;
        }
        
        // Display one line per unique indicator configuration
        allIndicators.forEach((indicator) => {
            const indicatorElement = document.createElement('div');
            indicatorElement.className = 'flex items-center justify-between p-2 bg-base-200 rounded text-xs mb-1';
            
            // Format display name like Yahoo Finance: ma (18,ma,5)
            let displayName;
            if (indicator.type === 'ma') {
                const period = indicator.config.params.period;
                const style = indicator.config.params.style || 1;
                displayName = `MA${period} (${period},ma,${style})`;
            } else if (indicator.type === 'ema') {
                const period = indicator.config.params.period;
                const style = indicator.config.params.style || 1;
                displayName = `EMA${period} (${period},ema,${style})`;
            } else if (indicator.type === 'rsi') {
                const period = indicator.config.params.period;
                displayName = `RSI${period} (${period})`;
            } else if (indicator.type === 'macd') {
                const fast = indicator.config.params.fast;
                const slow = indicator.config.params.slow;
                const signal = indicator.config.params.signal;
                displayName = `MACD (${fast},${slow},${signal})`;
            } else if (indicator.type === 'bb') {
                const period = indicator.config.params.period;
                const stdDev = indicator.config.params.stdDev;
                displayName = `BB${period} (${period},${stdDev})`;
            } else {
                const params = Object.values(indicator.config.params).join(',');
                displayName = `${indicator.type.toUpperCase()} (${params})`;
            }
            
            // Show intervals where this indicator is applied
            const intervalsText = indicator.intervals.join(', ');
            
            indicatorElement.innerHTML = `
                <div class="flex items-center gap-2">
                    <input type="checkbox" 
                           id="toggle_${indicator.key}" 
                           class="toggle toggle-xs" 
                           checked 
                           onchange="event.stopPropagation(); indicatorsManager.toggleIndicatorTypeVisibility('${indicator.type}', this.checked)">
                    <i class="fas fa-chart-line text-xs"></i>
                    <span class="font-medium">${displayName}</span>
                    <span class="text-xs text-gray-500">(${intervalsText})</span>
                </div>
                <div class="flex items-center gap-1">
                    <button onclick="event.preventDefault(); event.stopPropagation(); indicatorsManager.editIndicatorType('${indicator.type}')" 
                            class="btn btn-xs btn-ghost" title="Edit">
                        <i class="fas fa-edit text-xs"></i>
                    </button>
                    <button onclick="event.preventDefault(); event.stopPropagation(); indicatorsManager.removeIndicatorType('${indicator.type}')" 
                            class="btn btn-xs btn-ghost text-error" title="Remove">
                        <i class="fas fa-times text-xs"></i>
                    </button>
                </div>
            `;
            
            container.appendChild(indicatorElement);
        });
    }
    
    filterIndicators(searchTerm) {
        const buttons = document.querySelectorAll('[onclick^="addIndicator"]');
        buttons.forEach(button => {
            const text = button.textContent.toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            button.style.display = matches ? 'flex' : 'none';
        });
    }
    
    showIndicatorSettingsModal(indicator) {
        // Create modal for indicator settings
        const modal = document.createElement('div');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box">
                <h3 class="font-bold text-lg mb-4">${indicator.config.name} Settings</h3>
                <div class="space-y-4">
                    ${this.generateParameterInputs(indicator)}
                </div>
                <div class="modal-action">
                    <button class="btn btn-primary" onclick="indicatorsManager.saveIndicatorSettings('${indicator.id}', '${indicator.interval}')">
                        Save
                    </button>
                    <button class="btn btn-ghost" onclick="this.closest('.modal').remove()">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    generateParameterInputs(indicator) {
        const config = indicator.config;
        let inputs = '';
        
        Object.entries(config.params).forEach(([key, value]) => {
            inputs += `
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">${key.charAt(0).toUpperCase() + key.slice(1)}</span>
                    </label>
                    <input type="number" 
                           id="param_${key}" 
                           class="input input-bordered" 
                           value="${value}" 
                           min="1" 
                           max="200" />
                </div>
            `;
        });
        
        return inputs;
    }
    
    saveIndicatorSettings(indicatorId, interval) {
        const indicators = this.appliedIndicators.get(interval);
        const indicator = indicators.find(ind => ind.id === indicatorId);
        
        if (indicator) {
            // Get new parameters from modal
            const newParams = {};
            Object.keys(indicator.config.params).forEach(key => {
                const input = document.getElementById(`param_${key}`);
                if (input) {
                    newParams[key] = parseInt(input.value);
                }
            });
            
            // Store the old type for reference
            const oldType = indicator.type;
            
            // Remove ALL indicators of the same type across ALL intervals first
            this.appliedIndicators.forEach((indicatorsList, targetInterval) => {
                const indicatorsToRemove = indicatorsList.filter(ind => ind.type === oldType);
                indicatorsToRemove.forEach(targetIndicator => {
                    this.removeIndicatorFromChart(targetIndicator);
                });
                // Remove from appliedIndicators
                this.appliedIndicators.set(targetInterval, 
                    indicatorsList.filter(ind => ind.type !== oldType)
                );
            });
            
            // Now add the updated indicator to ALL intervals
            const allIntervals = ['1m', '2m', '5m', '15m', '30m', '60m'];
            allIntervals.forEach(targetInterval => {
                if (!this.appliedIndicators.has(targetInterval)) {
                    this.appliedIndicators.set(targetInterval, []);
                }
                
                // Create new indicator with updated parameters
                const newIndicatorId = `${oldType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${targetInterval}`;
                const newIndicator = {
                    id: newIndicatorId,
                    type: oldType,
                    config: { 
                        ...this.indicatorConfigs[oldType],
                        params: { ...newParams }
                    },
                    interval: targetInterval,
                    visible: true
                };
                
                this.appliedIndicators.get(targetInterval).push(newIndicator);
                this.applyIndicatorToChart(newIndicator);
                
                // Update indicator info display
                if (window.chartManager) {
                    window.chartManager.showIndicatorInfoForInterval(targetInterval);
                }
            });
            
            // Update applied indicators display and save to localStorage
            this.updateAppliedIndicatorsDisplay();
            this.saveIndicatorsToStorage();
            
            // Close modal
            document.querySelector('.modal').remove();
        }
    }
    
    
    // Public methods for global access
    getAppliedIndicators(interval) {
        return this.appliedIndicators.get(interval) || [];
    }
    
    clearAllIndicators(interval = null) {
        if (interval) {
            if (this.appliedIndicators.has(interval)) {
                const indicators = this.appliedIndicators.get(interval);
                indicators.forEach(indicator => this.removeIndicatorFromChart(indicator));
                this.appliedIndicators.set(interval, []);
            }
        } else {
            this.appliedIndicators.forEach((indicators, interval) => {
                indicators.forEach(indicator => this.removeIndicatorFromChart(indicator));
            });
            this.appliedIndicators.clear();
        }
        
        this.updateAppliedIndicatorsDisplay();
        this.saveIndicatorsToStorage(); // Save to localStorage after clearing
    }
    
    // Save indicators to localStorage
    saveIndicatorsToStorage() {
        try {
            const indicatorsData = {};
            this.appliedIndicators.forEach((indicators, interval) => {
                indicatorsData[interval] = indicators.map(indicator => ({
                    id: indicator.id,
                    type: indicator.type,
                    config: indicator.config,
                    interval: indicator.interval,
                    visible: indicator.visible
                }));
            });
            localStorage.setItem('savedIndicators', JSON.stringify(indicatorsData));
        } catch (error) {
            console.error('Error saving indicators to localStorage:', error);
        }
    }
    
    // Load indicators from localStorage
    loadSavedIndicators() {
        try {
            const savedData = localStorage.getItem('savedIndicators');
            if (savedData) {
                const indicatorsData = JSON.parse(savedData);
                
                // Check if we have any SMA indicators
                let hasSMAIndicators = false;
                Object.values(indicatorsData).forEach(indicators => {
                    if (indicators && indicators.some(ind => ind.type === 'sma')) {
                        hasSMAIndicators = true;
                    }
                });
                
                if (hasSMAIndicators) {
                    // Clear current indicators first
                    this.appliedIndicators.clear();
                    
                    // Load indicators for each interval
                    Object.entries(indicatorsData).forEach(([interval, indicators]) => {
                        if (indicators && indicators.length > 0) {
                            this.appliedIndicators.set(interval, indicators);
                        }
                    });
                    
                    
                    // Try to apply indicators after a short delay to ensure charts are ready
                    setTimeout(() => {
                        this.reapplyAllIndicators();
                    }, 1000);
                } else {
                    // No SMA indicators found, create default ones
                    this.createDefaultSMAIndicators();
                }
            } else {
                // No saved data, create default SMA indicators
                this.createDefaultSMAIndicators();
            }
        } catch (error) {
            console.error('Error loading indicators from localStorage:', error);
            // If there's an error, create default indicators
            this.createDefaultSMAIndicators();
        }
    }
    
    // Create default SMA indicators
    createDefaultSMAIndicators() {
        
        // Clear current indicators first
        this.appliedIndicators.clear();
        
        // Define default SMA indicators
        const defaultSMAs = [
            { period: 18, offset: 13, name: 'SMA18' },
            { period: 36, offset: 11, name: 'SMA36' },
            { period: 48, offset: 11, name: 'SMA48' },
            { period: 144, offset: 0, name: 'SMA144' }
        ];
        
        // Apply to all intervals
        const allIntervals = ['1m', '2m', '5m', '15m', '30m', '60m'];
        
        allIntervals.forEach(interval => {
            this.appliedIndicators.set(interval, []);
            
            defaultSMAs.forEach((sma, index) => {
                const indicatorId = `sma_${sma.period}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${interval}`;
                const indicator = {
                    id: indicatorId,
                    type: 'sma',
                    config: {
                        name: sma.name,
                        params: { 
                            period: sma.period, 
                            style: 1,
                            offset: sma.offset
                        },
                        type: 'overlay'
                    },
                    interval: interval,
                    visible: true
                };
                
                this.appliedIndicators.get(interval).push(indicator);
            });
        });
        
        
        // Save to localStorage
        this.saveIndicatorsToStorage();
        
        // Apply indicators after a short delay to ensure charts are ready
        setTimeout(() => {
            this.reapplyAllIndicators();
        }, 1000);
    }
    
    // Force create default SMA indicators (can be called from console)
    forceCreateDefaultSMA() {
        localStorage.removeItem('savedIndicators'); // Clear saved data
        this.createDefaultSMAIndicators();
    }
}

// Global functions for onclick handlers
function addIndicator(type) {
    if (window.indicatorsManager) {
        window.indicatorsManager.addIndicator(type);
    }
}
