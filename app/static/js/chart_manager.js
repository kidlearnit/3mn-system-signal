/**
 * Chart Manager - Handles all chart operations
 */
class ChartManager {
    constructor() {
        this.charts = {};
        this.macdCharts = {};
        this.dataCache = {}; // cache series data by interval for crosshair sync
        this.series = {
            candlestick: {},
            ema: {},
            ma20: {},
            ma50: {},
            ma200: {},
            volume: {},
            bbUpper: {},
            bbMiddle: {},
            bbLower: {},
            macdLine: {},
            macdSignal: {},
            macdHistogram: {}
        };
        this.supportResistanceLines = {};
        this.chartIntervals = ['2m', '5m', '15m'];
        this.chartIds = ['chart1', 'chart2', 'chart3'];
        this.macdChartIds = ['macdChart1', 'macdChart2', 'macdChart3'];
        this.technicalAnalysis = null;
        this.uiController = null;
        this.settingsManager = null;
        
        // Debounce settings application to prevent race conditions
        this.applySettingsTimeout = null;
        
        this.initCharts();
        this.setupThemeListener();
    }
    
    setTechnicalAnalysis(technicalAnalysis) {
        this.technicalAnalysis = technicalAnalysis;
    }
    
    setUIController(uiController) {
        this.uiController = uiController;
    }
    
    setSettingsManager(settingsManager) {
        this.settingsManager = settingsManager;
    }
    
    areChartsReady() {
        // Check if LightweightCharts library is loaded
        if (typeof LightweightCharts === 'undefined') {
            return false;
        }
        
        return this.chartIntervals.every(interval => 
            this.charts[interval] && 
            this.series.candlestick[interval] && 
            this.macdCharts[interval] && 
            this.series.macdLine[interval]
        );
    }
    
    initCharts() {
        this.chartIntervals.forEach((interval, index) => {
            this.createChartForInterval(interval, index);
        });
    }
    
    createChartForInterval(interval, index) {
        const chartId = this.chartIds[index];
        const macdChartId = this.macdChartIds[index];
        
        // Main price chart
        const chartElement = document.getElementById(chartId);
        if (chartElement) {
            this.preserveOverlay(chartElement, `priceInfo${index + 1}`);
            
            const chartOptions = this.getMainChartOptions(chartElement);
            this.charts[interval] = LightweightCharts.createChart(chartElement, chartOptions);
            
            this.addMainChartSeries(interval);
        }
        
        // MACD chart
        const macdElement = document.getElementById(macdChartId);
        if (macdElement) {
            this.preserveOverlay(macdElement, `macdInfo${index + 1}`);
            
            const macdOptions = this.getMacdChartOptions(macdElement);
            this.macdCharts[interval] = LightweightCharts.createChart(macdElement, macdOptions);
            
            this.addMacdChartSeries(interval);
        }
        
        // Apply settings to new charts immediately
        if (this.settingsManager) {
            // Apply settings for this specific interval
            this.applySettingsForInterval(interval);
            // Don't apply zoom level immediately to avoid chart recreation
            // Zoom level will be applied when user interacts with range slider
        }
        
        // Setup crosshair sync after series are created
        setTimeout(() => {
            this.setupChartSync(interval);
            // Setup enhanced crosshair after chart sync
            this.setupEnhancedCrosshair(interval);
        }, 100);
    }
    
    preserveOverlay(element, overlayId) {
        const overlay = element.querySelector(`#${overlayId}`);
        element.innerHTML = '';
        if (overlay) {
            element.appendChild(overlay);
        }
    }
    
    getThemeColors(isDarkMode = null) {
        // If isDarkMode is provided, use it; otherwise detect from DOM
        const isDark = isDarkMode !== null ? isDarkMode : document.body.classList.contains('dark');
        return {
            background: isDark ? '#1f2937' : '#f3f4f6',
            textColor: isDark ? '#f3f4f6' : '#1f2937',
            gridColor: isDark ? 'rgba(55, 65, 81, 0.5)' : 'rgba(209, 213, 219, 0.5)',
            borderColor: isDark ? 'rgba(55, 65, 81, 0.5)' : 'rgba(209, 213, 219, 0.5)',
            crosshairColor: isDark ? 'rgba(229, 231, 235, 0.95)' : 'rgba(75, 85, 99, 0.7)'
        };
    }
    
    getMainChartOptions(element) {
        const colors = this.getThemeColors();
        return {
            layout: {
                background: { type: 'solid', color: colors.background },
                textColor: colors.textColor,
                fontFamily: 'Inter, sans-serif',
            },
            grid: {
                vertLines: {
                    color: colors.gridColor,
                    style: 1,
                },
                horzLines: {
                    color: colors.gridColor,
                    style: 1,
                },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: colors.crosshairColor,
                    width: 1.5,
                    style: 2,
                },
                horzLine: {
                    color: colors.crosshairColor,
                    width: 1.5,
                    style: 2,
                },
            },
            timeScale: {
                visible: false,
                borderColor: colors.borderColor,
                timeVisible: false,
                secondsVisible: false,
                rightOffset: 20,
            },
            rightPriceScale: {
                borderColor: colors.borderColor,
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                    left: 0.1,
                    right: 0.1,
                },
                fitContent: true,
                autoScale: true,
                alignLabels: true,
            },
            width: element.clientWidth,
            height: element.clientHeight,
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: true,
            },
            handleScale: {
                axisPressedMouseMove: true,
                mouseWheel: true,
                pinch: true,
            },
        };
    }
    
    getMacdChartOptions(element) {
        const colors = this.getThemeColors();
        return {
            layout: {
                background: { type: 'solid', color: colors.background },
                textColor: colors.textColor,
                fontFamily: 'Inter, sans-serif',
            },
            grid: {
                vertLines: {
                    color: colors.gridColor,
                    style: 1,
                },
                horzLines: {
                    color: colors.gridColor,
                    style: 1,
                },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: colors.crosshairColor,
                    width: 1.5,
                    style: 2,
                },
                horzLine: {
                    color: colors.crosshairColor,
                    width: 1.5,
                    style: 2,
                },
            },
            timeScale: {
                visible: true,
                borderColor: colors.borderColor,
                timeVisible: true,
                secondsVisible: false,
                rightOffset: 20,
                tickMarkFormatter: this.formatTickMark,
            },
            rightPriceScale: {
                borderColor: colors.borderColor,
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                    left: 0.1,
                    right: 0.1,
                },
                fitContent: true,
                autoScale: true,
                alignLabels: true,
            },
            width: element.clientWidth,
            height: element.clientHeight,
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: false,
            },
            handleScale: {
                axisPressedMouseMove: true,
                mouseWheel: true,
                pinch: true,
            },
        };
    }
    
    formatTickMark(time, tickMarkType, locale) {
        const date = new Date(time * 1000);
        
        switch (tickMarkType) {
            case 0: // Year
                return date.getFullYear().toString();
            case 1: // Month
                return date.toLocaleDateString('en-US', { month: 'short' });
            case 2: // Day
                return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}`;
            case 3: // Hour
                return date.toLocaleTimeString('en-US', { 
                    hour: 'numeric', 
                    minute: '2-digit',
                    hour12: true 
                });
            case 4: // Minute
                return date.toLocaleTimeString('en-US', { 
                    hour: 'numeric', 
                    minute: '2-digit',
                    hour12: true 
                });
            default:
                const day = date.getDate().toString().padStart(2, '0');
                const month = (date.getMonth() + 1).toString().padStart(2, '0');
                const time = date.toLocaleTimeString('en-US', { 
                    hour: 'numeric', 
                    minute: '2-digit',
                    hour12: true 
                });
                return `${day}/${month} ${time}`;
        }
    }
    
    addMainChartSeries(interval) {
        // Only add candlestick series - other indicators will be added via IndicatorsManager
        this.series.candlestick[interval] = this.charts[interval].addSeries(
            LightweightCharts.CandlestickSeries,
            {
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                lastValueVisible: true,
                priceLineVisible: false
            }
        );
        
        // Initialize other series as null - they will be added when needed
        this.series.ema[interval] = null;
        this.series.ma20[interval] = null;
        this.series.ma50[interval] = null;
        this.series.ma200[interval] = null;
        this.series.volume[interval] = null;
        this.series.bbUpper[interval] = null;
        this.series.bbMiddle[interval] = null;
        this.series.bbLower[interval] = null;
    }
    
    addMacdChartSeries(interval) {
        this.series.macdHistogram[interval] = this.macdCharts[interval].addSeries(
            LightweightCharts.HistogramSeries,
            { 
                color: '#26a69a',
                priceFormat: { type: 'volume' },
                lastValueVisible: true,
                priceLineVisible: false,
            }
        );
        
        this.series.macdLine[interval] = this.macdCharts[interval].addSeries(
            LightweightCharts.LineSeries,
            { color: '#3b82f6', lineWidth: 2, priceLineVisible: false, lastValueVisible: false }
        );
        
        this.series.macdSignal[interval] = this.macdCharts[interval].addSeries(
            LightweightCharts.LineSeries,
            { color: '#f59e0b', lineWidth: 2, priceLineVisible: false, lastValueVisible: false }
        );
    }
    
    setupChartSync(interval) {
        // Sync timeScale between main chart and MACD chart
        if (this.charts[interval] && this.macdCharts[interval]) {
            this.syncTimeScale(this.charts[interval], this.macdCharts[interval]);
            this.syncRightOffset(interval);
            
            // Validate time alignment after setup
            setTimeout(() => {
                this.validateTimeAlignment(interval);
            }, 500);
        }
    }
    
    validateTimeAlignment(interval) {
        // Validate that MACD is aligned with last candle
        if (this.charts[interval] && this.macdCharts[interval]) {
            const candlestickSeries = this.series.candlestick[interval];
            const macdLineSeries = this.series.macdLine[interval];
            
            if (candlestickSeries && macdLineSeries) {
                const candleData = candlestickSeries.data();
                const macdData = macdLineSeries.data();
                
                if (candleData && macdData && candleData.length > 0 && macdData.length > 0) {
                    const lastCandleTime = candleData[candleData.length - 1].time;
                    const lastMacdTime = macdData[macdData.length - 1].time;
                    
                    if (lastCandleTime === lastMacdTime) {
                        console.log(`✅ Time alignment validated for ${interval}: ${lastCandleTime}`);
                    } else {
                        console.warn(`⚠️ Time alignment issue for ${interval}:`, {
                            lastCandle: lastCandleTime,
                            lastMacd: lastMacdTime
                        });
                        
                        // Force alignment
                        this.forceTimeScaleAlignment(interval);
                    }
                }
            }
        }
    }
    
    syncRightOffset(interval) {
        // Sync rightOffset between main chart and MACD chart
        if (this.charts[interval] && this.macdCharts[interval]) {
            const mainTimeScale = this.charts[interval].timeScale();
            const macdTimeScale = this.macdCharts[interval].timeScale();
            
            // Get rightOffset from main chart
            const rightOffset = mainTimeScale.options().rightOffset;
            
            // Apply same rightOffset to MACD chart
            if (rightOffset !== undefined) {
                macdTimeScale.applyOptions({ rightOffset: rightOffset });
                
                // Debug rightOffset alignment
                console.log(`🔧 RightOffset sync for ${interval}:`, {
                    main: rightOffset,
                    macd: macdTimeScale.options().rightOffset,
                    aligned: rightOffset === macdTimeScale.options().rightOffset
                });
            }
        }
    }

    // Crosshair sync using cached data at given time
    syncCrosshairByTime(targetChart, interval, targetSeriesKey, time) {
        if (!time) {
            targetChart.clearCrosshairPosition();
            return;
        }
        const cache = this.dataCache[interval] || {};
        let value;
        if (targetSeriesKey === 'candlestick') {
            const candles = cache.candlestick || [];
            const item = candles.find(d => d.time === time);
            value = item ? item.close : undefined;
        } else if (targetSeriesKey === 'macdLine') {
            const macd = (cache.macd && cache.macd.macd_line) || [];
            const item = macd.find(d => d.time === time);
            value = item ? item.value : undefined;
        }
        const series = targetSeriesKey === 'candlestick' ? this.series.candlestick[interval] : this.series.macdLine[interval];
        if (series && value !== undefined) {
            targetChart.setCrosshairPosition(value, time, series);
        } else {
            targetChart.clearCrosshairPosition();
        }
    }
    
    // Chart management methods
    updateCharts(data) {
        this.chartIntervals.forEach(interval => {
            if (data[interval]) {
                this.updateChartData(interval, data[interval]);
            }
        });
    }
    
    updateChartData(interval, data) {
        if (this.series.candlestick[interval] && data.candlestick) {
            this.series.candlestick[interval].setData(data.candlestick);
        }
        if (this.series.ema[interval] && data.ema) {
            this.series.ema[interval].setData(data.ema);
        }
        if (this.series.ma20[interval] && data.ma20) {
            this.series.ma20[interval].setData(data.ma20);
        }
        if (this.series.ma50[interval] && data.ma50) {
            this.series.ma50[interval].setData(data.ma50);
        }
        if (this.series.ma200[interval] && data.ma200) {
            this.series.ma200[interval].setData(data.ma200);
        }
        if (this.series.macdLine[interval] && data.macd) {
            this.series.macdLine[interval].setData(data.macd.macd_line);
        }
        if (this.series.macdSignal[interval] && data.macd) {
            this.series.macdSignal[interval].setData(data.macd.signal_line);
        }
        if (this.series.macdHistogram[interval] && data.macd) {
            const histogramData = data.macd.histogram.map(item => ({
                time: item.time,
                value: item.value,
                color: item.value >= 0 ? '#26a69a' : '#ef5350'
            }));
            this.series.macdHistogram[interval].setData(histogramData);
        }
        if (this.series.volume[interval] && data.volume) {
            this.series.volume[interval].setData(data.volume);
        }
        if (this.series.bbUpper[interval] && data.bb_upper) {
            this.series.bbUpper[interval].setData(data.bb_upper);
        }
        if (this.series.bbMiddle[interval] && data.bb_middle) {
            this.series.bbMiddle[interval].setData(data.bb_middle);
        }
        if (this.series.bbLower[interval] && data.bb_lower) {
            this.series.bbLower[interval].setData(data.bb_lower);
        }
        
        // Sync rightOffset between main chart and MACD chart
        this.syncRightOffset(interval);
        
        // Force align MACD with last candle
        this.forceAlignMacdWithLastCandle(interval);
        
        // Validate rightOffset consistency
        this.validateRightOffsetConsistency(interval);
        
        // Draw support and resistance lines if enabled
        const showSR = document.getElementById('showSR').checked;
        if (showSR && data.candlestick) {
            this.drawSupportResistanceLines(interval, data.candlestick);
        }
        
        // Cache data for crosshair sync
        this.dataCache[interval] = {
            candlestick: data.candlestick || (this.dataCache[interval] ? this.dataCache[interval].candlestick : undefined),
            macd: data.macd || (this.dataCache[interval] ? this.dataCache[interval].macd : undefined),
            macdLine: data.macd?.macd_line || (this.dataCache[interval] ? this.dataCache[interval].macdLine : undefined)
        };
        
        // Debug: log cache status
        //     candlestick: this.dataCache[interval].candlestick?.length || 0,
        //     macd: this.dataCache[interval].macd ? 'object' : 'null',
        //     macdLine: this.dataCache[interval].macdLine?.length || 0,
        //     dataKeys: Object.keys(data),
        //     macdKeys: data.macd ? Object.keys(data.macd) : 'null'
        // });

        // Update price info
        if (this.uiController) {
            this.uiController.updatePriceInfo(interval, data);
        }
        
        // Clear indicator cache and reapply indicators if indicators manager exists
        if (window.indicatorsManager) {
            window.indicatorsManager.clearIndicatorCache(interval);
            this.reapplyIndicators(interval);
        }
        
        // Update indicator info display
        this.showIndicatorInfoForInterval(interval);
    }
    
    reapplyIndicators(interval) {
        if (!window.indicatorsManager) return;
        
        const appliedIndicators = window.indicatorsManager.getAppliedIndicators(interval);
        appliedIndicators.forEach(indicator => {
            // Clear existing series
            if (indicator.series) {
                try {
                    const chart = this.charts[interval];
                    if (chart) {
                        if (Array.isArray(indicator.series)) {
                            indicator.series.forEach(series => {
                                chart.removeSeries(series);
                            });
                        } else {
                            chart.removeSeries(indicator.series);
                        }
                    }
                } catch (error) {
                     // console.error(`Error removing indicator series during reapply:`, error);
                }
            }
            
            // Reapply indicator
            window.indicatorsManager.applyIndicatorToChart(indicator);
        });
    }
    
    switchTimeframes(newIntervals) {
        // Destroy all existing charts first
        Object.keys(this.charts).forEach(interval => {
            this.destroyChart(interval);
        });
        
        // Update chart intervals and IDs
        this.chartIntervals = newIntervals;
        this.chartIds = newIntervals.map((_, index) => `chart${index + 1}`);
        this.macdChartIds = newIntervals.map((_, index) => `macdChart${index + 1}`);
        
        // Recreate all charts for new intervals
        this.chartIntervals.forEach((interval, index) => {
            this.createChartForInterval(interval, index);
        });
        
        // Notify settings UI controller about interval change
        if (this.settingsManager && this.settingsManager.settingsUIController) {
            this.settingsManager.settingsUIController.onIntervalChange(newIntervals[0]);
        }
        
        // Update WebSocket intervals for real-time data
        if (window.websocketManager && window.websocketManager.isRealtimeActive()) {
            window.websocketManager.updateIntervals(newIntervals);
        }
        
        // Reapply indicators for new mode after charts are ready
        setTimeout(() => {
            if (window.indicatorsManager) {
                window.indicatorsManager.reapplyIndicatorsForCurrentMode();
            }
        }, 500);
    }
    
    destroyChart(interval) {
        // Clear support/resistance lines first
        this.clearSupportResistanceLines(interval);
        
        if (this.charts[interval]) {
            this.charts[interval].remove();
            delete this.charts[interval];
        }
        if (this.macdCharts[interval]) {
            this.macdCharts[interval].remove();
            delete this.macdCharts[interval];
        }
        
        // Clean up series
        Object.keys(this.series).forEach(seriesType => {
            delete this.series[seriesType][interval];
        });
        
        // Clean up support/resistance lines
        delete this.supportResistanceLines[interval];
    }
    
    toggleBollingerBands(show) {
        this.chartIntervals.forEach(interval => {
            if (this.series.bbUpper[interval]) {
                this.series.bbUpper[interval].applyOptions({ visible: show });
            }
            if (this.series.bbMiddle[interval]) {
                this.series.bbMiddle[interval].applyOptions({ visible: show });
            }
            if (this.series.bbLower[interval]) {
                this.series.bbLower[interval].applyOptions({ visible: show });
            }
        });
    }
    
    toggleSupportResistance(show) {
        this.chartIntervals.forEach(interval => {
            if (show) {
                const candlestickData = this.series.candlestick[interval] ? this.series.candlestick[interval].data() : null;
                if (candlestickData && candlestickData.length > 0) {
                    this.drawSupportResistanceLines(interval, candlestickData);
                }
            } else {
                this.clearSupportResistanceLines(interval);
            }
        });
    }
    
    drawSupportResistanceLines(interval, candlestickData) {
        if (!this.charts[interval] || !candlestickData) return;
        
        this.clearSupportResistanceLines(interval);
        
        const srLevels = this.technicalAnalysis.calculateSupportResistance(candlestickData, 15);
        
        // Initialize support/resistance lines array if it doesn't exist
        if (!this.supportResistanceLines[interval]) {
            this.supportResistanceLines[interval] = [];
        }
        
        // Draw support lines (green)
        srLevels.support.forEach(level => {
            const line = this.charts[interval].addPriceLine({
                price: level.price,
                color: '#10b981',
                lineWidth: 1,
                lineStyle: 2,
                axisLabelVisible: true,
                title: `Support: ${level.price.toFixed(2)}`,
            });
            this.supportResistanceLines[interval].push(line);
        });
        
        // Draw resistance lines (red)
        srLevels.resistance.forEach(level => {
            const line = this.charts[interval].addPriceLine({
                price: level.price,
                color: '#ef4444',
                lineWidth: 1,
                lineStyle: 2,
                axisLabelVisible: true,
                title: `Resistance: ${level.price.toFixed(2)}`,
            });
            this.supportResistanceLines[interval].push(line);
        });
    }
    
    clearSupportResistanceLines(interval) {
        if (this.supportResistanceLines[interval] && this.charts[interval]) {
            this.supportResistanceLines[interval].forEach(line => {
                try {
                    this.charts[interval].removePriceLine(line);
                } catch (e) {
                    // Line might already be removed
                }
            });
        }
        this.supportResistanceLines[interval] = [];
    }
    
    handleResize() {
        this.chartIntervals.forEach((interval, index) => {
            const chartId = this.chartIds[index];
            const macdChartId = this.macdChartIds[index];
            
            if (this.charts[interval]) {
                const chartElement = document.getElementById(chartId);
                if (chartElement) {
                    const newWidth = chartElement.clientWidth;
                    const newHeight = chartElement.clientHeight;
                    if (newWidth > 0 && newHeight > 0) {
                        this.charts[interval].resize(newWidth, newHeight);
                    }
                }
            }
            
            if (this.macdCharts[interval]) {
                const macdElement = document.getElementById(macdChartId);
                if (macdElement) {
                    const newWidth = macdElement.clientWidth;
                    const newHeight = macdElement.clientHeight;
                    if (newWidth > 0 && newHeight > 0) {
                        this.macdCharts[interval].resize(newWidth, newHeight);
                    }
                }
            }
            
            // Sync rightOffset after resize
            this.syncRightOffset(interval);
        });
    }
    
    // Crosshair and sync methods
    syncTimeScale(chart1, chart2) {
        let isUpdating = false;
        
        chart1.timeScale().subscribeVisibleLogicalRangeChange(timeRange => {
            if (isUpdating) return;
            isUpdating = true;
            try {
                chart2.timeScale().setVisibleLogicalRange(timeRange);
            } catch (e) {
                 // console.warn('Error syncing time scale from chart1 to chart2:', e);
            }
            setTimeout(() => { isUpdating = false; }, 10);
        });

        chart2.timeScale().subscribeVisibleLogicalRangeChange(timeRange => {
            if (isUpdating) return;
            isUpdating = true;
            try {
                chart1.timeScale().setVisibleLogicalRange(timeRange);
            } catch (e) {
                 // console.warn('Error syncing time scale from chart2 to chart1:', e);
            }
            setTimeout(() => { isUpdating = false; }, 10);
        });
        
        // Sync rightOffset when timeScale changes
        chart1.timeScale().subscribeVisibleLogicalRangeChange(() => {
            this.syncRightOffsetForCharts(chart1, chart2);
        });
        
        chart2.timeScale().subscribeVisibleLogicalRangeChange(() => {
            this.syncRightOffsetForCharts(chart1, chart2);
        });
    }
    
    syncRightOffsetForCharts(chart1, chart2) {
        // Sync rightOffset between two charts
        const timeScale1 = chart1.timeScale();
        const timeScale2 = chart2.timeScale();
        
        const rightOffset1 = timeScale1.options().rightOffset;
        const rightOffset2 = timeScale2.options().rightOffset;
        
        if (rightOffset1 !== rightOffset2) {
            timeScale2.applyOptions({ rightOffset: rightOffset1 });
        }
    }
    
    forceRightOffsetTo20(interval) {
        // Force both charts to have rightOffset: 20 for consistency
        if (this.charts[interval] && this.macdCharts[interval]) {
            const mainTimeScale = this.charts[interval].timeScale();
            const macdTimeScale = this.macdCharts[interval].timeScale();
            
            // Force rightOffset to 20
            mainTimeScale.applyOptions({ rightOffset: 20 });
            macdTimeScale.applyOptions({ rightOffset: 20 });
            
            console.log(`🔧 Forced rightOffset to 20 for ${interval}:`, {
                main: mainTimeScale.options().rightOffset,
                macd: macdTimeScale.options().rightOffset
            });
        }
    }
    
    validateRightOffsetConsistency(interval) {
        // Validate that both charts have consistent rightOffset
        if (this.charts[interval] && this.macdCharts[interval]) {
            const mainTimeScale = this.charts[interval].timeScale();
            const macdTimeScale = this.macdCharts[interval].timeScale();
            
            const mainRightOffset = mainTimeScale.options().rightOffset;
            const macdRightOffset = macdTimeScale.options().rightOffset;
            
            if (mainRightOffset !== macdRightOffset) {
                console.warn(`⚠️ RightOffset mismatch for ${interval}:`, {
                    main: mainRightOffset,
                    macd: macdRightOffset
                });
                
                // Force sync
                this.forceRightOffsetTo20(interval);
            } else if (mainRightOffset !== 20) {
                console.warn(`⚠️ RightOffset not 20 for ${interval}:`, {
                    main: mainRightOffset,
                    macd: macdRightOffset
                });
                
                // Force to 20
                this.forceRightOffsetTo20(interval);
            } else {
                console.log(`✅ RightOffset consistent for ${interval}: ${mainRightOffset}`);
            }
        }
    }
    
    forceAlignMacdWithLastCandle(interval) {
        // Force align MACD with last candle to ensure proper time alignment
        if (this.charts[interval] && this.macdCharts[interval]) {
            const mainChart = this.charts[interval];
            const macdChart = this.macdCharts[interval];
            
            // Get last candle time
            const candlestickSeries = this.series.candlestick[interval];
            if (candlestickSeries) {
                const candleData = candlestickSeries.data();
                if (candleData && candleData.length > 0) {
                    const lastCandleTime = candleData[candleData.length - 1].time;
                    
                    // Get MACD data
                    const macdLineSeries = this.series.macdLine[interval];
                    if (macdLineSeries) {
                        const macdData = macdLineSeries.data();
                        if (macdData && macdData.length > 0) {
                            const lastMacdTime = macdData[macdData.length - 1].time;
                            
                            // Check if times match
                            if (lastCandleTime !== lastMacdTime) {
                                console.warn(`⚠️ MACD time mismatch for ${interval}:`, {
                                    lastCandle: lastCandleTime,
                                    lastMacd: lastMacdTime
                                });
                                
                                // Force time scale alignment
                                setTimeout(() => {
                                    this.forceTimeScaleAlignment(interval);
                                }, 100);
                            } else {
                                console.log(`✅ MACD aligned with last candle for ${interval}`);
                            }
                        }
                    }
                }
            }
        }
    }
    
    forceTimeScaleAlignment(interval) {
        // Force time scale alignment between main chart and MACD chart
        if (this.charts[interval] && this.macdCharts[interval]) {
            const mainTimeScale = this.charts[interval].timeScale();
            const macdTimeScale = this.macdCharts[interval].timeScale();
            
            // Get visible range from main chart
            const visibleRange = mainTimeScale.getVisibleRange();
            if (visibleRange) {
                // Apply same range to MACD chart
                macdTimeScale.setVisibleRange(visibleRange);
            }
            
            // Force fit content to ensure proper alignment
            mainTimeScale.fitContent();
            macdTimeScale.fitContent();
            
            console.log(`🔄 Forced time scale alignment for ${interval}`);
        }
    }
    
    getCrosshairDataPoint(series, param) {
        if (!param.time) {
            return null;
        }
        const dataPoint = param.seriesData.get(series);
        return dataPoint || null;
    }
    
    syncCrosshair(chart, series, dataPoint) {
        if (dataPoint && dataPoint.value && dataPoint.time) {
            chart.setCrosshairPosition(dataPoint.value, dataPoint.time, series);
            return;
        }
        if (!this.settingsManager || !this.settingsManager.getSettings().stickyCrosshair) {
            chart.clearCrosshairPosition();
        }
    }
    
    // Enhanced crosshair with magnet functionality
    setupEnhancedCrosshair(interval) {
        const chart = this.charts[interval];
        const macdChart = this.macdCharts[interval];
        if (!chart || !macdChart) {
             // console.warn(`Charts not ready for interval ${interval}`);
            return;
        }
        
        if (!this.series.candlestick[interval] || !this.series.macdLine[interval]) {
             // console.warn(`Series not ready for interval ${interval}`);
            return;
        }
        
        const settings = this.settingsManager ? this.settingsManager.getSettings() : {};
        
        // Track which chart is being moved to prevent infinite loops
        let isMainChartMoving = false;
        let isMacdChartMoving = false;
        
        // Main chart crosshair
        chart.subscribeCrosshairMove((param) => {
            if (!param.point || !settings.showCrosshair || isMacdChartMoving) return;
            
            isMainChartMoving = true;
            
            // Debug: Main chart crosshair move
            
            let targetTime = param.time;
            let targetPrice = param.point.y;
            
            // Apply magnet to data if enabled
            if (settings.crosshairMagnet && param.seriesData && this.series.candlestick[interval]) {
                const candlestickData = param.seriesData.get(this.series.candlestick[interval]);
                if (candlestickData && candlestickData.time) {
                    targetTime = candlestickData.time;
                    targetPrice = candlestickData.close;
                }
            }
            
            // Sync to MACD chart
            if (macdChart && targetTime && this.series.macdLine[interval]) {
                // Always use cache fallback for Main → MACD sync since param.seriesData may not contain MACD data
                const cache = this.dataCache[interval] || {};
                const macdCache = cache.macdLine;
                
                
                if (macdCache && macdCache.length > 0) {
                    let closestData = null;
                    let minDiff = Infinity;
                    
                    for (const data of macdCache) {
                        if (data && data.time && data.value !== undefined) {
                            const timeDiff = Math.abs(data.time - targetTime);
                            if (timeDiff < minDiff) {
                                minDiff = timeDiff;
                                closestData = data;
                            }
                        }
                    }
                    
                    if (closestData && closestData.value !== undefined) {
                        // Use the actual data time instead of targetTime for better alignment
                        macdChart.setCrosshairPosition(closestData.value, closestData.time, this.series.macdLine[interval]);
                    }
                } else {
                    // If no macdLine cache, try macd object structure
                    const macdObject = cache.macd;
                    if (macdObject && macdObject.macd_line && macdObject.macd_line.length > 0) {
                        let closestData = null;
                        let minDiff = Infinity;
                        
                        for (const data of macdObject.macd_line) {
                            if (data && data.time && data.value !== undefined) {
                                const timeDiff = Math.abs(data.time - targetTime);
                                if (timeDiff < minDiff) {
                                    minDiff = timeDiff;
                                    closestData = data;
                                }
                            }
                        }
                        
                        if (closestData && closestData.value !== undefined) {
                            // Use the actual data time instead of targetTime for better alignment
                            macdChart.setCrosshairPosition(closestData.value, closestData.time, this.series.macdLine[interval]);
                        }
                    }
                }
            }
            
            // Update price info
            this.updatePriceInfoOnHover(interval, param.seriesData, param);
            
            // Update indicator info
            this.updateIndicatorInfoOnHover(interval, param.seriesData, param);
            
            // Reset flag after a short delay
            setTimeout(() => {
                isMainChartMoving = false;
            }, 10);
        });
        
        // MACD chart crosshair
        macdChart.subscribeCrosshairMove((param) => {
            if (!param.point || !settings.showCrosshair || isMainChartMoving) return;
            
            isMacdChartMoving = true;
            
            let targetTime = param.time;
            let targetPrice = param.point.y;
            
            // Apply magnet to data if enabled
            if (settings.crosshairMagnet && param.seriesData && this.series.macdLine[interval]) {
                const macdData = param.seriesData.get(this.series.macdLine[interval]);
                if (macdData && macdData.time) {
                    targetTime = macdData.time;
                    targetPrice = macdData.value;
                }
            }
            
            // Ensure we have a valid targetTime for sync
            if (!targetTime) {
                targetTime = param.time;
            }
            
            // Sync to main chart
            if (chart && targetTime && this.series.candlestick[interval]) {
                // Try to get candlestick data from seriesData first
                let candlestickData = null;
                if (param.seriesData) {
                    candlestickData = param.seriesData.get(this.series.candlestick[interval]);
                }
                
                if (candlestickData && candlestickData.close && candlestickData.close > 0) {
                    // Use the actual data time instead of targetTime for better alignment
                    chart.setCrosshairPosition(candlestickData.close, candlestickData.time, this.series.candlestick[interval]);
                } else {
                    // Fallback: find closest candlestick data from cache
                    const cache = this.dataCache[interval] || {};
                    const candlestickCache = cache.candlestick;
                    
                    if (candlestickCache && candlestickCache.length > 0) {
                        let closestData = null;
                        let minDiff = Infinity;
                        
                        for (const data of candlestickCache) {
                            if (data && data.time && data.close) {
                                const timeDiff = Math.abs(data.time - targetTime);
                                if (timeDiff < minDiff) {
                                    minDiff = timeDiff;
                                    closestData = data;
                                }
                            }
                        }
                        
                        if (closestData && closestData.close > 0) {
                            // Use the actual data time instead of targetTime for better alignment
                            chart.setCrosshairPosition(closestData.close, closestData.time, this.series.candlestick[interval]);
                        }
                    }
                }
            }
            
            // Update MACD info
            this.updateMacdInfoOnHover(interval, param.seriesData, param);
            
            // Reset flag after a short delay
            setTimeout(() => {
                isMacdChartMoving = false;
            }, 10);
        });
        
        // Handle mouse leave for sticky crosshair
        if (!settings.stickyCrosshair) {
            // Add mouse leave handlers to clear crosshair
            chart.subscribeCrosshairMove((param) => {
                if (!param.point) {
                    chart.clearCrosshairPosition();
                    macdChart.clearCrosshairPosition();
                }
            });
            
            macdChart.subscribeCrosshairMove((param) => {
                if (!param.point) {
                    chart.clearCrosshairPosition();
                    macdChart.clearCrosshairPosition();
                }
            });
        }
    }
    
    updatePriceInfoOnHover(interval, seriesData, param) {
        const chartIndex = this.chartIntervals.indexOf(interval) + 1;
        
        if (!seriesData || !this.series.candlestick[interval] || !this.uiController) {
             // console.warn(`updatePriceInfoOnHover: Missing data for interval ${interval}`, {
            //     seriesData: !!seriesData,
            //     candlestick: !!this.series.candlestick[interval],
            //     uiController: !!this.uiController
            // });
            return;
        }
        
        const candlestickData = seriesData.get(this.series.candlestick[interval]);
        const volumeData = this.series.volume[interval] ? seriesData.get(this.series.volume[interval]) : null;
        
        if (candlestickData) {
            this.uiController.safeSetTextContent(`open${chartIndex}`, candlestickData.open.toFixed(2));
            this.uiController.safeSetTextContent(`high${chartIndex}`, candlestickData.high.toFixed(2));
            this.uiController.safeSetTextContent(`low${chartIndex}`, candlestickData.low.toFixed(2));
            this.uiController.safeSetTextContent(`close${chartIndex}`, candlestickData.close.toFixed(2));
        }
        
        if (volumeData) {
            this.uiController.safeSetTextContent(`volume${chartIndex}`, this.uiController.formatVolume(volumeData.value));
        }
    }
    
    updateMacdInfoOnHover(interval, seriesData, param) {
        const chartIndex = this.chartIntervals.indexOf(interval) + 1;
        
        if (!seriesData || !this.series.macdLine[interval] || !this.uiController) {
             // console.warn(`updateMacdInfoOnHover: Missing data for interval ${interval}`, {
            //     seriesData: !!seriesData,
            //     macdLine: !!this.series.macdLine[interval],
            //     uiController: !!this.uiController
            // });
            return;
        }
        
        const macdLineData = seriesData.get(this.series.macdLine[interval]);
        const macdSignalData = this.series.macdSignal[interval] ? seriesData.get(this.series.macdSignal[interval]) : null;
        const macdHistogramData = this.series.macdHistogram[interval] ? seriesData.get(this.series.macdHistogram[interval]) : null;
        
        if (macdLineData && macdSignalData && macdHistogramData) {
            const macdText = `${macdLineData.value.toFixed(2)} ${macdSignalData.value.toFixed(2)} ${macdHistogramData.value.toFixed(2)}`;
            this.uiController.safeSetTextContent(`macdValues${chartIndex}`, macdText);
        }
    }
    
    updateIndicatorInfoOnHover(interval, seriesData, param) {
        const chartIndex = this.chartIntervals.indexOf(interval) + 1;
        const indicatorContainer = document.getElementById(`indicatorInfoContainer${chartIndex}`);
        
        // Debug: Check all containers
        const allContainers = {
            container1: !!document.getElementById('indicatorInfoContainer1'),
            container2: !!document.getElementById('indicatorInfoContainer2'),
            container3: !!document.getElementById('indicatorInfoContainer3')
        };
        
        const chartContainers = {
            chart1: !!document.getElementById('chart1'),
            chart2: !!document.getElementById('chart2'),
            chart3: !!document.getElementById('chart3')
        };
        
        //     chartIntervals: this.chartIntervals,
        //     intervalIndex: this.chartIntervals.indexOf(interval),
        //     indicatorContainer: !!indicatorContainer,
        //     seriesData: !!seriesData,
        //     indicatorsManager: !!window.indicatorsManager,
        //     allContainers: allContainers,
        //     chartContainers: chartContainers
        // });
        
        if (!indicatorContainer) {
            // Try to find the specific container with a delay
            setTimeout(() => {
                const retryContainer = document.getElementById(`indicatorInfoContainer${chartIndex}`);
                if (retryContainer) {
                    this.updateIndicatorInfoInContainer(retryContainer, interval, seriesData, param);
                } else {
                    // Create container dynamically
                    this.createDynamicIndicatorContainer(chartIndex, interval, seriesData, param);
                }
            }, 100);
            return;
        }
        
        this.updateIndicatorInfoInContainer(indicatorContainer, interval, seriesData, param);
    }
    
    createDynamicIndicatorContainer(chartIndex, interval, seriesData, param) {
        
        // Try to find the chart container first
        const chartContainer = document.getElementById(`chart${chartIndex}`);
        
        if (!chartContainer) {
            return;
        }
        
        // Create container inside chart container
        const container = document.createElement('div');
        container.id = `indicatorInfoContainer${chartIndex}`;
        container.className = 'absolute top-12 left-2 z-50';
        container.style.position = 'absolute';
        container.style.top = '24px';
        container.style.left = '4px';
        container.style.zIndex = '50';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '1px';
        
        chartContainer.appendChild(container);
        
        this.updateIndicatorInfoInContainer(container, interval, seriesData, param);
    }
    
    // New method to show indicator info immediately when indicators are added
    showIndicatorInfoForInterval(interval) {
        
        const chartIndex = this.chartIntervals.indexOf(interval) + 1;
        const container = document.getElementById(`indicatorInfoContainer${chartIndex}`);
        
        
        if (container) {
            // Show indicator info immediately (without hover data)
            this.updateIndicatorInfoInContainer(container, interval, null, null);
        } else {
            // Try to create dynamic container
            this.createDynamicIndicatorContainer(chartIndex, interval, null, null);
        }
    }
    
    updateIndicatorInfoInContainer(container, interval, seriesData, param) {
        
        // Clear existing indicator info
        container.innerHTML = '';
        
        // Get all active indicators for this interval from IndicatorsManager
        if (window.indicatorsManager && window.indicatorsManager.appliedIndicators.has(interval)) {
            const indicators = window.indicatorsManager.appliedIndicators.get(interval);
            
            indicators.forEach((indicator, index) => {
                // Get indicator data from series
                let indicatorValue = null;
                let indicatorName = '';
                
                if (indicator.type === 'ma') {
                    const period = indicator.config.params.period;
                    const style = indicator.config.params.style || 1;
                    indicatorName = `MA${period} (${period},ma,${style})`;
                    
                    // Use the series directly from indicator object
                    const series = indicator.series;
                    
                    
                    if (series && seriesData) {
                        const data = seriesData.get(series);
                        if (data && data.value !== undefined) {
                            indicatorValue = data.value;
                        }
                    } else if (series) {
                        // Try to get last value from series when no hover data
                        try {
                            const lastValue = series.data().slice(-1)[0];
                            if (lastValue && lastValue.value !== undefined) {
                                indicatorValue = lastValue.value;
                            }
                        } catch (e) {
                        }
                    }
                    // Always show indicator name, even without hover data
                } else if (indicator.type === 'sma') {
                    const period = indicator.config.params.period;
                    const offset = indicator.config.params.offset || 0;
                    indicatorName = `ma (${period},ma,${offset})`;
                    
                    // Use the series directly from indicator object
                    const series = indicator.series;
                    
                    
                    if (series && seriesData) {
                        const data = seriesData.get(series);
                        if (data && data.value !== undefined) {
                            indicatorValue = data.value;
                        }
                    } else if (series) {
                        // Try to get last value from series when no hover data
                        try {
                            const lastValue = series.data().slice(-1)[0];
                            if (lastValue && lastValue.value !== undefined) {
                                indicatorValue = lastValue.value;
                            }
                        } catch (e) {
                        }
                    }
                    // Always show indicator name, even without hover data
                } else if (indicator.type === 'ema') {
                    const period = indicator.config.params.period;
                    const style = indicator.config.params.style || 1;
                    indicatorName = `EMA${period} (${period},ema,${style})`;
                    
                    // Use the series directly from indicator object
                    const series = indicator.series;
                    
                    if (series && seriesData) {
                        const data = seriesData.get(series);
                        if (data && data.value !== undefined) {
                            indicatorValue = data.value;
                        }
                    }
                    // Always show indicator name, even without hover data
                } else if (indicator.type === 'rsi') {
                    const period = indicator.config.params.period;
                    indicatorName = `rsi (${period})`;
                    
                    const series = indicator.series;
                    
                    if (series && seriesData) {
                        const data = seriesData.get(series);
                        if (data && data.value !== undefined) {
                            indicatorValue = data.value;
                        }
                    }
                } else if (indicator.type === 'bb') {
                    const period = indicator.config.params.period;
                    const stdDev = indicator.config.params.stdDev;
                    indicatorName = `bb (${period},${stdDev})`;
                    
                    // For Bollinger Bands, we might have multiple series
                    if (indicator.series && Array.isArray(indicator.series) && indicator.series.length > 0) {
                        // Use the middle band (index 1) for display
                        const middleSeries = indicator.series[1];
                        if (middleSeries && seriesData) {
                            const data = seriesData.get(middleSeries);
                            if (data && data.value !== undefined) {
                                indicatorValue = data.value;
                            }
                        }
                    }
                }
                
                
                // Create individual indicator info element (always show, like priceInfo)
                
                if (indicatorName) {
                    const indicatorInfoElement = document.createElement('div');
                    indicatorInfoElement.className = 'bg-white bg-opacity-20 backdrop-blur-sm text-black text-xs px-0.5 py-0.5 rounded z-10 font-mono border border-black border-opacity-20 flex items-center gap-0.5 mb-0.5';
                    indicatorInfoElement.id = `mainfo-${indicator.id}`;
                    
                    const isVisible = indicator.visible !== false; // Default to visible
                    const eyeIcon = isVisible ? '👁️' : '🙈';
                    
                    
                    // Always show indicator info, with or without value
                    const valueText = (indicatorValue !== null && indicatorValue !== undefined) 
                        ? `: ${indicatorValue.toFixed(2)}` 
                        : ': -';
                    
                    // Get color for indicator title based on type and period
                    let titleColor = '';
                    if (indicator.type === 'sma') {
                        const period = indicator.config.params.period;
                        if (period === 18) titleColor = 'color: #FF4444;'; // Bright Red
                        else if (period === 36) titleColor = 'color: #00AA44;'; // Bright Green
                        else if (period === 48) titleColor = 'color: #0066FF;'; // Bright Blue
                        else if (period === 144) titleColor = 'color: #FF8800;'; // Orange
                        else titleColor = 'color: #FF6B6B;'; // Default Red
                    } else if (indicator.type === 'ma') {
                        titleColor = 'color: #FF6B6B;'; // Red
                    } else if (indicator.type === 'ema') {
                        titleColor = 'color: #4ECDC4;'; // Teal
                    } else {
                        titleColor = 'color: #95A5A6;'; // Gray
                    }
                    
                    // Use Font Awesome icons
                    const visibilityIcon = isVisible ? 'fas fa-eye' : 'fas fa-eye-slash';
                    
                    indicatorInfoElement.innerHTML = `
                        <span class="cursor-pointer hover:bg-white hover:bg-opacity-30 px-0.5 rounded flex-1" 
                              onclick="window.chartManager.editIndicatorInline('${indicatorName}', '${interval}', ${index}, '${indicator.id}')" 
                              title="Click to edit ${indicatorName}"
                              style="${titleColor}">
                            ${indicatorName}${valueText}
                        </span>
                        <div class="flex items-center gap-0.5">
                            <i class="fas fa-edit cursor-pointer hover:bg-white hover:bg-opacity-30 px-0.5 py-0.5 rounded text-blue-600 text-xs" 
                               onclick="window.chartManager.editIndicatorInline('${indicatorName}', '${interval}', ${index}, '${indicator.id}')" 
                               title="Edit"></i>
                            <i class="${visibilityIcon} cursor-pointer hover:bg-white hover:bg-opacity-30 px-0.5 py-0.5 rounded text-gray-600 text-xs" 
                               onclick="window.chartManager.toggleIndicatorVisibility('${indicator.id}', '${interval}')" 
                               title="Toggle"></i>
                            <i class="fas fa-times cursor-pointer hover:bg-white hover:bg-opacity-30 px-0.5 py-0.5 rounded text-red-600 text-xs" 
                               onclick="window.chartManager.removeIndicator('${indicator.id}', '${interval}')" 
                               title="Remove"></i>
                        </div>
                    `;
                    
                    container.appendChild(indicatorInfoElement);
                } else {
                }
            });
        } else {
            //     hasManager: !!window.indicatorsManager,
            //     hasInterval: window.indicatorsManager ? window.indicatorsManager.appliedIndicators.has(interval) : false
            // });
        }
        
    }
    
    editIndicatorInline(indicatorName, interval, index, indicatorId = null) {
        
        // Find the indicator in IndicatorsManager
        if (window.indicatorsManager) {
            let targetIndicator = null;
            
            if (indicatorId) {
                // Direct lookup by ID in specific interval
                const indicators = window.indicatorsManager.appliedIndicators.get(interval);
                if (indicators) {
                    targetIndicator = indicators.find(ind => ind.id === indicatorId);
                }
            } else {
                // Fallback to name-based lookup in specific interval
                const indicatorType = indicatorName.toLowerCase().replace(/\d+/g, ''); // Remove numbers
                const period = indicatorName.match(/\d+/)?.[0]; // Extract period
                
                const indicators = window.indicatorsManager.appliedIndicators.get(interval);
                if (indicators) {
                    targetIndicator = indicators.find(ind => 
                        ind.type === indicatorType && 
                        ind.config.params.period == period
                    );
                }
            }
            
            
            if (targetIndicator) {
                // Show inline edit form
                this.showInlineEditForm(targetIndicator, interval, index);
            } else {
            }
        } else {
        }
    }
    
    showInlineEditForm(indicator, interval, index) {
        const chartIndex = this.chartIntervals.indexOf(interval) + 1;
        const indicatorContainer = document.getElementById(`indicatorInfoContainer${chartIndex}`);
        
        if (!indicatorContainer) return;
        
        // Create inline edit form
        const editForm = document.createElement('div');
        editForm.className = 'bg-base-100 border border-base-300 rounded p-2 shadow-lg';
        editForm.id = `editForm_${indicator.id}`;
        
        // Create proper indicator name
        const period = indicator.config.params.period;
        const style = indicator.config.params.style || 1;
        const indicatorName = `${indicator.type} (${period},${indicator.type},${style})`;
        
        editForm.innerHTML = `
            <div class="text-xs font-semibold mb-2">Edit ${indicatorName}</div>
            <div class="flex items-center gap-2 mb-2">
                <label class="text-xs">Period:</label>
                <input type="number" id="inline_period_${indicator.id}" 
                       value="${indicator.config.params.period}" 
                       min="1" max="500" 
                       class="input input-xs w-16">
            </div>
            <div class="flex items-center gap-2 mb-2">
                <label class="text-xs">Style:</label>
                <select id="inline_style_${indicator.id}" class="select select-xs w-20">
                    <option value="1" ${indicator.config.params.style == 1 ? 'selected' : ''}>Solid</option>
                    <option value="2" ${indicator.config.params.style == 2 ? 'selected' : ''}>Dashed</option>
                    <option value="3" ${indicator.config.params.style == 3 ? 'selected' : ''}>Dotted</option>
                </select>
            </div>
            <div class="flex gap-1">
                <button onclick="window.chartManager.saveInlineEdit('${indicator.id}', '${interval}')" 
                        class="btn btn-xs btn-primary">Save</button>
                <button onclick="window.chartManager.cancelInlineEdit('${indicator.id}', '${interval}')" 
                        class="btn btn-xs btn-ghost">Cancel</button>
            </div>
        `;
        
        // Add edit form to container
        indicatorContainer.appendChild(editForm);
    }
    
    saveInlineEdit(indicatorId, interval) {
        const periodInput = document.getElementById(`inline_period_${indicatorId}`);
        const styleSelect = document.getElementById(`inline_style_${indicatorId}`);
        
        if (!periodInput || !styleSelect) return;
        
        const newPeriod = parseInt(periodInput.value);
        const newStyle = parseInt(styleSelect.value);
        
        // Update indicator in IndicatorsManager
        if (window.indicatorsManager) {
            // Find the specific indicator by ID (not by type)
            const indicators = window.indicatorsManager.appliedIndicators.get(interval);
            if (indicators) {
                const indicator = indicators.find(ind => ind.id === indicatorId);
                if (indicator) {
                    
                    // Update only this specific indicator instance
                    indicator.config.params.period = newPeriod;
                    indicator.config.params.style = newStyle;
                    
                    // Reapply only this specific indicator
                    window.indicatorsManager.removeIndicatorFromChart(indicator);
                    window.indicatorsManager.applyIndicatorToChart(indicator);
                    
                    // Update display for this interval only
                    window.indicatorsManager.updateAppliedIndicatorsDisplay();
                    this.showIndicatorInfoForInterval(interval);
                } else {
                }
            } else {
            }
        }
        
        // Restore normal display
        this.cancelInlineEdit(indicatorId, interval);
    }
    
    cancelInlineEdit(indicatorId, interval) {
        const editForm = document.getElementById(`editForm_${indicatorId}`);
        if (editForm) {
            editForm.remove();
        }
    }

    // Method to toggle indicator visibility
    toggleIndicatorVisibility(indicatorId, interval) {
        
        // Find the indicator in the manager
        const indicators = window.indicatorsManager.appliedIndicators.get(interval);
        if (!indicators) {
            return;
        }
        
        const indicator = indicators.find(ind => ind.id === indicatorId);
        if (!indicator) {
            return;
        }
        
        // Toggle visibility
        indicator.visible = !indicator.visible;
        
        // Update the series visibility
        const chart = this.charts[interval];
        if (chart && indicator.series) {
            if (Array.isArray(indicator.series)) {
                // Multiple series (like Bollinger Bands)
                indicator.series.forEach(series => {
                    series.applyOptions({
                        visible: indicator.visible
                    });
                });
            } else {
                // Single series
                indicator.series.applyOptions({
                    visible: indicator.visible
                });
            }
        }
        
        // Update the eye icon in mainfo
        this.updateMainfoEyeIcon(indicatorId, indicator.visible);
        
        // Update mainfo display for this interval
        this.showIndicatorInfoForInterval(interval);
    }

    // Method to update eye icon in mainfo
    updateMainfoEyeIcon(indicatorId, isVisible) {
        const mainfoElement = document.getElementById(`mainfo-${indicatorId}`);
        if (mainfoElement) {
            const eyeIcon = isVisible ? '👁️' : '🙈';
            const eyeSpan = mainfoElement.querySelector('span[onclick*="toggleIndicatorVisibility"]');
            if (eyeSpan) {
                eyeSpan.textContent = eyeIcon;
            }
        }
    }
    
    // Apply settings to all charts with debouncing
    applySettings() {
        if (!this.settingsManager) return;
        
        // Clear existing timeout
        if (this.applySettingsTimeout) {
            clearTimeout(this.applySettingsTimeout);
        }
        
        // Debounce settings application
        this.applySettingsTimeout = setTimeout(() => {
            this.chartIntervals.forEach(interval => {
                this.applySettingsForInterval(interval);
                // Don't apply zoom level to avoid chart recreation
                // Zoom level will be applied when user interacts with range slider
            });
        }, 50); // 50ms debounce
    }
    
    // Apply settings immediately (no debounce) - for critical updates
    applySettingsImmediate() {
        if (!this.settingsManager) return;
        
        // Clear any pending debounced application
        if (this.applySettingsTimeout) {
            clearTimeout(this.applySettingsTimeout);
            this.applySettingsTimeout = null;
        }
        
        this.chartIntervals.forEach(interval => {
            this.applySettingsForInterval(interval);
            // Don't apply zoom level to avoid chart recreation
            // Zoom level will be applied when user interacts with range slider
        });
    }
    
    // Apply settings to a specific interval
    applySettingsForInterval(interval) {
        if (!this.settingsManager) return;
        
        const settings = this.settingsManager.getSettings();
        const chart = this.charts[interval];
        const macdChart = this.macdCharts[interval];
        if (!chart || !macdChart) return;

        // Show/Hide crosshair
        const crosshairVisible = settings.showCrosshair;
        const colors = this.getThemeColors(); // Use current DOM state
        const makeCrosshair = (visible) => ({
            mode: visible ? LightweightCharts.CrosshairMode.Normal : LightweightCharts.CrosshairMode.Hidden,
            vertLine: {
                color: visible ? colors.crosshairColor : 'rgba(0,0,0,0)',
                width: visible ? 1.5 : 0,
                style: 2,
            },
            horzLine: {
                color: visible ? colors.crosshairColor : 'rgba(0,0,0,0)',
                width: visible ? 1.5 : 0,
                style: 2,
            },
        });
        chart.applyOptions({ crosshair: makeCrosshair(crosshairVisible) });
        macdChart.applyOptions({ crosshair: makeCrosshair(crosshairVisible) });
        
        // If crosshair is disabled, clear any existing crosshair positions
        if (!crosshairVisible) {
            chart.clearCrosshairPosition();
            macdChart.clearCrosshairPosition();
        } else {
            // If crosshair is enabled, re-setup enhanced crosshair
            setTimeout(() => {
                this.setupEnhancedCrosshair(interval);
            }, 50);
        }

        // Y-axis scale mode
        const modeMap = {
            linear: LightweightCharts.PriceScaleMode.Normal,
            logarithmic: LightweightCharts.PriceScaleMode.Logarithmic,
            percentage: LightweightCharts.PriceScaleMode.Percentage,
        };
        const mode = modeMap[settings.yScaleMode] || LightweightCharts.PriceScaleMode.Normal;
        chart.applyOptions({ 
            rightPriceScale: { 
                mode, 
                invertScale: !!settings.invertScale 
            } 
        });
        macdChart.applyOptions({ 
            rightPriceScale: { 
                mode: LightweightCharts.PriceScaleMode.Normal, 
                invertScale: !!settings.invertScale 
            } 
        });

        // Gray background strips
        if (settings.grayBackgroundStrips) {
            // Add time-based background highlighting
            this.addBackgroundStrips(interval);
        } else {
            this.removeBackgroundStrips(interval);
        }
        
        // Extended Hours
        if (settings.extendedHours) {
            this.enableExtendedHours(interval);
        } else {
            this.disableExtendedHours(interval);
        }
        
        // Force sync rightOffset after applying settings
        this.syncRightOffset(interval);
        
        // Force rightOffset to 20 for consistency
        this.forceRightOffsetTo20(interval);
        
        // Hide Outliers
        if (settings.hideOutliers) {
            this.hideOutliers(interval);
        } else {
            this.showOutliers(interval);
        }
    }
    
    addBackgroundStrips(interval) {
        // Apply to main chart
        const mainContainer = document.getElementById(this.chartIds[this.chartIntervals.indexOf(interval)]);
        if (mainContainer) {
            this.addBackgroundStripsToContainer(mainContainer);
        }
        
        // Apply to MACD chart
        const macdContainer = document.getElementById(this.macdChartIds[this.chartIntervals.indexOf(interval)]);
        if (macdContainer) {
            this.addBackgroundStripsToContainer(macdContainer);
        }
    }
    
    addBackgroundStripsToContainer(container) {
        let overlay = container.querySelector('.gray-strips-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'gray-strips-overlay absolute inset-0 pointer-events-none';
            container.appendChild(overlay);
        }
        overlay.style.zIndex = '1';
        overlay.innerHTML = '';
        // Simple vertical stripes every N% width as placeholder
        const stripes = 10;
        for (let i = 0; i < stripes; i += 2) {
            const strip = document.createElement('div');
            strip.style.position = 'absolute';
            strip.style.top = '0';
            strip.style.bottom = '0';
            strip.style.left = `${(i / stripes) * 100}%`;
            strip.style.width = `${100 / stripes}%`;
            strip.style.background = document.body.classList.contains('dark') ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)';
            overlay.appendChild(strip);
        }
    }
    
    removeBackgroundStrips(interval) {
        // Remove from main chart
        const mainContainer = document.getElementById(this.chartIds[this.chartIntervals.indexOf(interval)]);
        if (mainContainer) {
            const overlay = mainContainer.querySelector('.gray-strips-overlay');
            if (overlay) overlay.remove();
        }
        
        // Remove from MACD chart
        const macdContainer = document.getElementById(this.macdChartIds[this.chartIntervals.indexOf(interval)]);
        if (macdContainer) {
            const overlay = macdContainer.querySelector('.gray-strips-overlay');
            if (overlay) overlay.remove();
        }
    }
    
    enableExtendedHours(interval) {
        const chart = this.charts[interval];
        const macdChart = this.macdCharts[interval];
        if (!chart || !macdChart) return;
        
        // Enable extended hours trading (pre/post market)
        chart.applyOptions({
            timeScale: {
                rightOffset: 20, // Keep consistent with initial setting
                barSpacing: 6,
                fixLeftEdge: false,
                lockVisibleTimeRangeOnResize: true,
                rightBarStaysOnScroll: true,
                borderVisible: false,
                borderColor: '#fff000',
                visible: false,
                timeVisible: false,
                secondsVisible: false
            }
        });
        
        macdChart.applyOptions({
            timeScale: {
                rightOffset: 20, // Keep consistent with initial setting
                barSpacing: 6,
                fixLeftEdge: false,
                lockVisibleTimeRangeOnResize: true,
                rightBarStaysOnScroll: true,
                borderVisible: false,
                borderColor: '#fff000',
                visible: true,
                timeVisible: true,
                secondsVisible: false
            }
        });
    }
    
    disableExtendedHours(interval) {
        const chart = this.charts[interval];
        const macdChart = this.macdCharts[interval];
        if (!chart || !macdChart) return;
        
        // Disable extended hours (regular market hours only)
        chart.applyOptions({
            timeScale: {
                rightOffset: 20, // Keep consistent with initial setting
                barSpacing: 6,
                fixLeftEdge: false,
                lockVisibleTimeRangeOnResize: true,
                rightBarStaysOnScroll: true,
                borderVisible: false,
                borderColor: '#fff000',
                visible: false,
                timeVisible: false,
                secondsVisible: false
            }
        });
        
        macdChart.applyOptions({
            timeScale: {
                rightOffset: 20, // Keep consistent with initial setting
                barSpacing: 6,
                fixLeftEdge: false,
                lockVisibleTimeRangeOnResize: true,
                rightBarStaysOnScroll: true,
                borderVisible: false,
                borderColor: '#fff000',
                visible: true,
                timeVisible: true,
                secondsVisible: false
            }
        });
    }
    
    hideOutliers(interval) {
        const chart = this.charts[interval];
        if (!chart) return;
        
        // Apply price scale options to hide outliers
        chart.applyOptions({
            rightPriceScale: {
                mode: LightweightCharts.PriceScaleMode.Normal,
                autoScale: true,
                invertScale: false,
                alignLabels: true,
                borderVisible: false,
                borderColor: '#555',
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            }
        });
    }
    
    showOutliers(interval) {
        const chart = this.charts[interval];
        if (!chart) return;
        
        // Reset price scale to show all data including outliers
        chart.applyOptions({
            rightPriceScale: {
                mode: LightweightCharts.PriceScaleMode.Normal,
                autoScale: true,
                invertScale: false,
                alignLabels: true,
                borderVisible: false,
                borderColor: '#555',
                scaleMargins: {
                    top: 0.05,
                    bottom: 0.05,
                },
            }
        });
    }

    // Reset view for all charts
    resetViewAll() {
        this.chartIntervals.forEach(interval => {
            const chart = this.charts[interval];
            const macdChart = this.macdCharts[interval];
            if (!chart || !macdChart) return;
            try {
                chart.timeScale().fitContent();
                macdChart.timeScale().fitContent();
            } catch (e) {}
        });
    }

    // Zoom via percent (range slider). 100% = fit content, 10% = zoomed in
    applyZoomPercent(percent, targetInterval = null) {
        const clamped = Math.min(100, Math.max(10, Number(percent) || 100));
        const intervals = targetInterval ? [targetInterval] : this.chartIntervals;
        
        intervals.forEach(interval => {
            const chart = this.charts[interval];
            if (!chart) return;
            const timeScale = chart.timeScale();
            const visibleRange = timeScale.getVisibleLogicalRange();
            if (!visibleRange) {
                try { timeScale.fitContent(); } catch (e) {}
                return;
            }
            const currentBars = visibleRange.to - visibleRange.from;
            // Target bars based on percent (more percent -> more bars visible)
            const targetBars = (currentBars / clamped) * 100;
            const center = (visibleRange.to + visibleRange.from) / 2;
            const newFrom = center - targetBars / 2;
            const newTo = center + targetBars / 2;
            try {
                timeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
            } catch (e) {}
        });
    }
    
    // Fit last N bars on all charts
    fitLastBars(bars) {
        this.chartIntervals.forEach(interval => {
            const chart = this.charts[interval];
            const macdChart = this.macdCharts[interval];
            if (!chart || !macdChart) return;
            
            try {
                const timeScale = chart.timeScale();
                const macdTimeScale = macdChart.timeScale();
                
                // Get the logical range
                const logicalRange = timeScale.getVisibleLogicalRange();
                if (!logicalRange) {
                    timeScale.fitContent();
                    macdTimeScale.fitContent();
                    return;
                }
                
                // Calculate new range to show last N bars
                const newTo = logicalRange.to;
                const newFrom = newTo - bars;
                
                // Apply to both charts
                timeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
                macdTimeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
                
            } catch (e) {
                 // console.warn(`Error fitting last ${bars} bars for ${interval}:`, e);
            }
        });
    }
    
    setupThemeListener() {
        window.addEventListener('themeChanged', (event) => {
            this.updateChartsTheme(event.detail.isDark);
        });
    }
    
    updateChartsTheme(isDark) {
        this.chartIntervals.forEach(interval => {
            const chart = this.charts[interval];
            const macdChart = this.macdCharts[interval];
            if (!chart || !macdChart) return;
            
            // Use consistent theme colors with explicit theme state
            const colors = this.getThemeColors(isDark);
            const chartOptions = {
                layout: {
                    background: { type: 'solid', color: colors.background },
                    textColor: colors.textColor
                },
                grid: {
                    vertLines: { color: colors.gridColor },
                    horzLines: { color: colors.gridColor }
                },
                rightPriceScale: {
                    borderColor: colors.borderColor
                },
                timeScale: {
                    borderColor: colors.borderColor
                }
            };
            
            chart.applyOptions(chartOptions);
            macdChart.applyOptions(chartOptions);
        });
        
        // Apply settings immediately after theme change to ensure consistency
        // But don't apply zoom levels to avoid chart recreation
        this.applySettingsForAllIntervals();
    }
    
    // Apply settings to all intervals without zoom levels
    applySettingsForAllIntervals() {
        if (!this.settingsManager) return;
        
        this.chartIntervals.forEach(interval => {
            this.applySettingsForInterval(interval);
        });
    }
    
    // Apply saved zoom level for specific interval
    applyZoomLevelForInterval(interval) {
        if (!this.settingsManager) return;
        
        const chart = this.charts[interval];
        const macdChart = this.macdCharts[interval];
        if (!chart || !macdChart) return;
        
        const zoomPercent = this.settingsManager.getZoomLevel(interval);
        const zoomValue = Math.round(zoomPercent * 100);
        
        // Apply zoom using the existing method for this specific interval
        this.applyZoomPercent(zoomValue, interval);
    }
    
    // Fit last N bars for specific interval
    fitLastBarsForInterval(bars, interval) {
        const chart = this.charts[interval];
        const macdChart = this.macdCharts[interval];
        if (!chart || !macdChart) return;
        
        try {
            const timeScale = chart.timeScale();
            const macdTimeScale = macdChart.timeScale();
            
            // Get the last N bars
            const logicalRange = timeScale.getVisibleLogicalRange();
            if (!logicalRange) return;
            
            const newTo = logicalRange.to;
            const newFrom = Math.max(0, newTo - bars);
            
            // Apply to both charts
            timeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
            macdTimeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
            
        } catch (e) {
             // console.warn(`Error fitting last ${bars} bars for ${interval}:`, e);
        }
    }
    
    // Reset view for specific interval
    resetViewForInterval(interval) {
        const chart = this.charts[interval];
        const macdChart = this.macdCharts[interval];
        if (!chart || !macdChart) return;
        
        try {
            chart.timeScale().fitContent();
            macdChart.timeScale().fitContent();
        } catch (e) {
             // console.warn(`Error resetting view for ${interval}:`, e);
        }
    }
}
