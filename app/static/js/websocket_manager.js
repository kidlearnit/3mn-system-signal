/**
 * WebSocket Manager - Handles real-time data streaming
 */
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.isSubscribed = false;
        this.currentTicker = 'NVDA';
        this.currentIntervals = ['2m', '5m', '15m'];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.chartManager = null;
        this.dataFetcher = null;
        
        // Candle aggregation buffers for different timeframes
        this.candleBuffers = {
            '1m': [],
            '2m': [],
            '5m': [],
            '15m': [],
            '30m': [],
            '1h': [],
            '4h': [],
            '1d': []
        };
        
        // Interval multipliers (how many 1m candles needed for each timeframe)
        this.intervalMultipliers = {
            '1m': 1,
            '2m': 2,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        };
    }

    setChartManager(chartManager) {
        this.chartManager = chartManager;
    }

    setDataFetcher(dataFetcher) {
        this.dataFetcher = dataFetcher;
    }

    connect() {
        if (this.socket && this.isConnected) {
            return;
        }

        // Disconnect existing socket first
        if (this.socket) {
            this.socket.disconnect();
        }

        this.socket = io('/', {
            transports: ['websocket', 'polling'],
            timeout: 20000,
            forceNew: true,
            pingInterval: 25000,
            pingTimeout: 120000
        });
        
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            console.log('WebSocket connected');
            console.log('Socket ID:', this.socket.id);
            this.updateConnectionStatus(true);
            
            // Wait a bit for server to register the connection
            setTimeout(() => {
                // Auto-subscribe if we have current ticker and intervals
                if (this.currentTicker && this.currentIntervals) {
                    console.log('Auto-subscribing to real-time data...');
                    this.doSubscribe(this.currentTicker, this.currentIntervals);
                }
            }, 500);
        });

        this.socket.on('disconnect', () => {
            this.isConnected = false;
            this.isSubscribed = false;
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        });

        this.socket.on('connected', (data) => {
            console.log('Server confirmed connection:', data.message);
        });

        this.socket.on('subscribed', (data) => {
            console.log('Subscribed to real-time data:', data);
            console.log('Socket ID when subscribed:', this.socket.id);
            this.isSubscribed = true;
            this.updateSubscriptionStatus(true);
        });

        this.socket.on('unsubscribed', (data) => {
            console.log('Unsubscribed from real-time data:', data);
            this.isSubscribed = false;
            this.updateSubscriptionStatus(false);
        });

        this.socket.on('realtime_data', (data) => {
            console.log('Received realtime_data event:', data);
            console.log('Socket ID when receiving data:', this.socket.id);
            this.handleRealtimeData(data);
        });

        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data.message);
            this.showError(data.message);
        });
        
        // Debug: Listen to all events
        this.socket.onAny((eventName, ...args) => {
            console.log(`WebSocket event received: ${eventName}`, args);
        });
        
        // Test: Direct event listener for realtime_data
        this.socket.on('realtime_data', (data) => {
            console.log('DIRECT LISTENER: Received realtime_data:', data);
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.isConnected = false;
            this.isSubscribed = false;
            this.updateConnectionStatus(false);
            this.updateSubscriptionStatus(false);
        }
    }

    subscribe(ticker, intervals) {
        if (!this.isConnected) {
            this.connect();
            // Wait for connection before subscribing
            setTimeout(() => {
                if (this.isConnected) {
                    this.doSubscribe(ticker, intervals);
                }
            }, 1000);
        } else {
            this.doSubscribe(ticker, intervals);
        }
    }

    doSubscribe(ticker, intervals) {
        this.currentTicker = ticker;
        this.currentIntervals = intervals;
        
        this.socket.emit('subscribe_realtime', {
            ticker: ticker,
            intervals: intervals
        });
    }

    unsubscribe() {
        if (this.socket && this.isConnected) {
            this.socket.emit('unsubscribe_realtime');
        }
    }

    updateIntervals(intervals) {
        if (this.socket && this.isConnected) {
            this.currentIntervals = intervals;
            this.socket.emit('update_intervals', {
                intervals: intervals
            });
            console.log('Updated intervals to:', intervals);
        }
    }

    handleRealtimeData(data) {
        console.log('handleRealtimeData called with:', data);
        
        if (!this.chartManager) {
            console.log('No chartManager available');
            return;
        }

        // Validate data
        if (!data || !data.ticker || !data.close) {
            console.warn('Invalid realtime data received:', data);
            return;
        }

        const { ticker, interval, timestamp, open, high, low, close, volume, market_hours, market_state, change, changePercent } = data;
        
        // Only process 1m data from server
        if (interval !== '1m') {
            console.log(`Ignoring non-1m data: ${interval}`);
            return;
        }
        
        console.log(`Received 1m real-time data: ${ticker} - $${close} (${market_state})`);
        
        // Create 1m candle with enhanced data
        const oneMinuteCandle = {
            time: timestamp,
            open: open,
            high: high,
            low: low,
            close: close,
            volume: volume,
            market_hours: market_hours,
            market_state: market_state,
            change: change,
            changePercent: changePercent
        };
        
        // Add to 1m buffer
        this.candleBuffers['1m'].push(oneMinuteCandle);
        
        // Update 1m chart directly
        this.updateChartWithCandle('1m', oneMinuteCandle);
        
        // Aggregate to higher timeframes
        this.aggregateToHigherTimeframes(oneMinuteCandle);
    }
    
    aggregateToHigherTimeframes(oneMinuteCandle) {
        // Process each higher timeframe
        Object.keys(this.intervalMultipliers).forEach(timeframe => {
            if (timeframe === '1m') return; // Skip 1m as it's already processed
            
            const multiplier = this.intervalMultipliers[timeframe];
            const buffer = this.candleBuffers[timeframe];
            
            // Add 1m candle to buffer
            buffer.push(oneMinuteCandle);
            
            // Check if we have enough 1m candles to create a new higher timeframe candle
            if (buffer.length >= multiplier) {
                // Create aggregated candle
                const aggregatedCandle = this.createAggregatedCandle(buffer.slice(-multiplier), timeframe);
                
                // Update the chart for this timeframe
                this.updateChartWithCandle(timeframe, aggregatedCandle);
                
                // Clear buffer for next cycle
                this.candleBuffers[timeframe] = [];
            }
        });
    }
    
    createAggregatedCandle(candles, timeframe) {
        if (candles.length === 0) return null;
        
        // Sort candles by time
        candles.sort((a, b) => a.time - b.time);
        
        const firstCandle = candles[0];
        const lastCandle = candles[candles.length - 1];
        
        // Calculate OHLC
        const open = firstCandle.open;
        const close = lastCandle.close;
        const high = Math.max(...candles.map(c => c.high));
        const low = Math.min(...candles.map(c => c.low));
        const volume = candles.reduce((sum, c) => sum + (c.volume || 0), 0);
        
        // Round timestamp to timeframe boundary
        const timeframeMs = this.getTimeframeMs(timeframe);
        const roundedTime = Math.floor(firstCandle.time / timeframeMs) * timeframeMs;
        
        return {
            time: roundedTime,
            open: open,
            high: high,
            low: low,
            close: close,
            volume: volume
        };
    }
    
    getTimeframeMs(timeframe) {
        const multipliers = {
            '1m': 60 * 1000,
            '2m': 2 * 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000
        };
        return multipliers[timeframe] || 60 * 1000;
    }
    
    updateChartWithCandle(timeframe, candle) {
        const chart = this.chartManager.charts[timeframe];
        const candlestickSeries = this.chartManager.series.candlestick[timeframe];
        
        if (chart && candlestickSeries) {
            try {
                const existingData = candlestickSeries.data();
                if (existingData.length > 0) {
                    const lastCandle = existingData[existingData.length - 1];
                    
                    // If same timestamp (within timeframe), update the last candle
                    const timeframeMs = this.getTimeframeMs(timeframe);
                    if (Math.abs(lastCandle.time - candle.time) < timeframeMs) {
                        candlestickSeries.update(candle);
                        console.log(`Updated existing ${timeframe} candle: $${candle.close}`);
                    } else {
                        // Add new candle
                        candlestickSeries.update(candle);
                        console.log(`Added new ${timeframe} candle: $${candle.close}`);
                    }
                } else {
                    // First candle
                    candlestickSeries.update(candle);
                    console.log(`First ${timeframe} candle: $${candle.close}`);
                }

                // Update volume if available
                if (candle.volume && this.chartManager.series.volume[timeframe]) {
                    const volumeSeries = this.chartManager.series.volume[timeframe];
                    volumeSeries.update({
                        time: candle.time,
                        value: candle.volume
                    });
                }

                // Update price info
                if (this.chartManager.uiController) {
                    this.chartManager.uiController.updatePriceInfo(timeframe, {
                        candlestick: [candle],
                        volume: candle.volume ? [{ value: candle.volume }] : []
                    });
                }

                // Update indicators if they exist
                this.updateIndicators(timeframe, candle);

                // Show real-time indicator
                this.showRealtimeIndicator(timeframe, candle.close);

            } catch (error) {
                console.error(`Error updating ${timeframe} chart with real-time data:`, error);
            }
        }
    }

    showRealtimeIndicator(interval, price) {
        // Show a small indicator that data was updated
        const chartContainer = document.getElementById(`chart${this.chartManager.chartIntervals.indexOf(interval) + 1}`);
        if (chartContainer) {
            // Remove existing indicator
            const existingIndicator = chartContainer.querySelector('.realtime-indicator');
            if (existingIndicator) {
                existingIndicator.remove();
            }

            // Create new indicator
            const indicator = document.createElement('div');
            indicator.className = 'realtime-indicator absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded shadow-lg z-50';
            indicator.textContent = `LIVE: $${price}`;
            indicator.style.animation = 'fadeInOut 2s ease-in-out';
            
            chartContainer.appendChild(indicator);

            // Remove after animation
            setTimeout(() => {
                if (indicator && indicator.parentElement) {
                    indicator.remove();
                }
            }, 2000);
        }
    }

    updateIndicators(interval, candle) {
        // Update moving averages and other indicators
        if (window.indicatorsManager) {
            const indicators = window.indicatorsManager.appliedIndicators.get(interval);
            if (indicators) {
                indicators.forEach(indicator => {
                    if (indicator.visible && indicator.series) {
                        // Recalculate indicator with new data
                        // This is a simplified update - in production you'd want more sophisticated logic
                        try {
                            const newData = window.indicatorsManager.getIndicatorData(
                                interval, 
                                indicator.type, 
                                indicator.config.params.period || 20,
                                indicator.config.params.offset || 0
                            );
                            
                            if (newData && newData.length > 0) {
                                indicator.series.setData(newData);
                            }
                        } catch (error) {
                            console.error('Error updating indicator:', error);
                        }
                    }
                });
            }
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.showError('Connection lost. Please refresh the page.');
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('websocket-status');
        if (statusElement) {
            statusElement.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
            statusElement.className = connected ? 'text-success' : 'text-error';
        }
    }

    updateSubscriptionStatus(subscribed) {
        const statusElement = document.getElementById('subscription-status');
        if (statusElement) {
            statusElement.textContent = subscribed ? '📡 Live Data' : '⏸️ Paused';
            statusElement.className = subscribed ? 'text-info' : 'text-warning';
        }
    }

    showError(message) {
        // Show error message in UI
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-error shadow-lg fixed top-4 right-4 z-50 max-w-sm';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
            <button class="btn btn-sm btn-ghost" onclick="this.parentElement.remove()">×</button>
        `;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv && errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }

    // Public methods for external control
    startRealtime(ticker, intervals) {
        console.log(`Starting real-time for ${ticker} with intervals:`, intervals);
        this.currentTicker = ticker;
        this.currentIntervals = intervals;
        this.subscribe(ticker, intervals);
    }

    stopRealtime() {
        this.unsubscribe();
    }

    isRealtimeActive() {
        return this.isConnected && this.isSubscribed;
    }

    // Debug method to test connection
    testConnection() {
        console.log('=== WebSocket Connection Test ===');
        console.log('Socket exists:', !!this.socket);
        console.log('Is connected:', this.isConnected);
        console.log('Is subscribed:', this.isSubscribed);
        console.log('Current ticker:', this.currentTicker);
        console.log('Current intervals:', this.currentIntervals);
        
        if (this.socket) {
            console.log('Socket ID:', this.socket.id);
            console.log('Socket connected:', this.socket.connected);
        }
        
        if (this.chartManager) {
            console.log('Available charts:', Object.keys(this.chartManager.charts));
            console.log('Available series:', Object.keys(this.chartManager.series.candlestick));
        }
        
        console.log('=== End Test ===');
    }
    
    // Test method to manually trigger realtime_data
    testRealtimeData() {
        console.log('=== Testing Real-time Data ===');
        if (this.socket && this.socket.connected) {
            console.log('Socket is connected, ID:', this.socket.id);
            console.log('Testing with fake data...');
            
            // Simulate receiving realtime_data
            const fakeData = {
                ticker: 'NVDA',
                interval: '2m',
                timestamp: Date.now(),
                open: 450.0,
                high: 455.0,
                low: 445.0,
                close: 452.0,
                volume: 1000000
            };
            
            console.log('Simulating realtime_data:', fakeData);
            this.handleRealtimeData(fakeData);
        } else {
            console.log('Socket is not connected');
        }
        console.log('=== End Test ===');
    }
}
