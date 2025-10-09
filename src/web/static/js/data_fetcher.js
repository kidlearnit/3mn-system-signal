/**
 * Data Fetcher - Handles API calls and data processing
 */
class DataFetcher {
    constructor() {
        this.baseUrl = '/api/real';
        this.chartManager = null;
        this.settingsManager = null;
    }
    
    setChartManager(chartManager) {
        this.chartManager = chartManager;
    }
    
    setSettingsManager(settingsManager) {
        this.settingsManager = settingsManager;
    }
    
    async fetchData(ticker, emaPeriod, rsiPeriod) {
        const chartIntervals = this.chartManager ? this.chartManager.chartIntervals : ['2m', '5m', '15m'];
        
        // Fetch both candles and MACD data
        const promises = chartIntervals.map(interval => {
            return Promise.all([
                this.fetchIntervalData(ticker, interval, emaPeriod, rsiPeriod),
                this.fetchMacdData(ticker, interval)
            ]);
        });
        
        try {
            const results = await Promise.all(promises);
            const data = {};
            
            results.forEach(([candlesResult, macdResult], index) => {
                const interval = chartIntervals[index];
                
                if (candlesResult && candlesResult.error) {
                    console.error(`Error fetching candles for ${interval}:`, candlesResult.error);
                } else if (candlesResult && candlesResult.data) {
                    data[interval] = candlesResult.data;
                }
                
                if (macdResult && macdResult.error) {
                    console.warn(`No MACD data available for ${interval}:`, macdResult.error.message);
                    // Don't treat MACD errors as fatal - continue without MACD data
                } else if (macdResult && macdResult.data) {
                    if (!data[interval]) data[interval] = {};
                    data[interval].macd = macdResult.data;
                }
            });
            
            return data;
        } catch (error) {
            console.error('Error in fetchData:', error);
            return {};
        }
    }
    
    async fetchIntervalData(ticker, interval, emaPeriod, rsiPeriod) {
        try {
            const params = new URLSearchParams();
            params.set('symbol', ticker);
            params.set('timeframe', interval);
            params.set('limit', '500'); // Increased for 1 year historical data
            
            if (this.settingsManager) {
                const s = this.settingsManager.getSettings();
                if (s.extendedHours) params.set('extendedHours', '1');
                if (s.hideOutliers) params.set('hideOutliers', '1');
            }
            
            // Use hybrid mode: historical from DB + realtime from YF
            params.set('source', 'hybrid');
            params.set('historical_days', '365'); // 1 year historical data
            const response = await fetch(`${this.baseUrl}/candles?${params.toString()}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (!result || !result.data || !result.data.candles || result.data.candles.length === 0) {
                throw new Error(`No data available for ${interval}`);
            }
            
            // Transform the data to match expected format
            const data = {
                candlestick: result.data.candles.map(candle => ({
                    time: new Date(candle.timestamp).getTime() / 1000,
                    open: candle.open,
                    high: candle.high,
                    low: candle.low,
                    close: candle.close
                })),
                volume: result.data.candles.map(candle => ({
                    time: new Date(candle.timestamp).getTime() / 1000,
                    value: candle.volume
                }))
            };
            
            return { data };
        } catch (error) {
            return { error };
        }
    }
    
    async fetchMacdData(ticker, interval) {
        try {
            const params = new URLSearchParams();
            params.set('symbol', ticker);
            params.set('timeframe', interval);
            params.set('limit', '500');
            params.set('source', 'hybrid');
            params.set('historical_days', '365');
            
            const response = await fetch(`${this.baseUrl}/macd?${params.toString()}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (!result || !result.data || !result.data.macd || result.data.macd.length === 0) {
                throw new Error(`No MACD data available for ${interval}`);
            }
            
            // Transform the MACD data to match expected format (original format)
            const data = {
                macd_line: result.data.macd.map(item => ({
                    time: new Date(item.timestamp).getTime() / 1000,
                    value: item.macd
                })),
                signal_line: result.data.macd.map(item => ({
                    time: new Date(item.timestamp).getTime() / 1000,
                    value: item.macd_signal
                })),
                histogram: result.data.macd.map(item => ({
                    time: new Date(item.timestamp).getTime() / 1000,
                    value: item.histogram
                }))
            };
            
            return { data };
        } catch (error) {
            return { error };
        }
    }
}
