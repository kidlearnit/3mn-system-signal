/**
 * Flexible Multi-Indicator System
 * Supports dynamic indicator configuration per symbol
 */

class FlexibleMultiIndicatorSystem {
    constructor() {
        this.availableIndicators = new Map();
        this.symbolConfigs = new Map();
        this.initializeAvailableIndicators();
    }

    /**
     * Initialize available indicators
     */
    initializeAvailableIndicators() {
        // MACD Multi-TF
        this.availableIndicators.set('macd_multi', {
            name: 'MACD Multi-TF',
            icon: 'fas fa-chart-line',
            description: 'MACD across multiple timeframes',
            defaultConfig: {
                fastPeriod: 7,
                slowPeriod: 113,
                signalPeriod: 144,
                timeframes: ['1m', '2m', '5m', '15m', '30m', '1h'],
                thresholds: {
                    '1m': 0.33, '2m': 0.47, '5m': 0.47, 
                    '15m': 0.22, '30m': 0.47, '1h': 0.07
                }
            },
            weight: 0.3,
            formBuilder: 'createMACDMultiForm',
            analyzer: 'analyzeMACDMulti'
        });

        // SMA
        this.availableIndicators.set('sma', {
            name: 'SMA',
            icon: 'fas fa-chart-area',
            description: 'Simple Moving Average',
            defaultConfig: {
                timeframes: ['1m', '2m', '5m', '15m', '30m', '1h', '4h'],
                periods: [5, 10, 20, 50, 100, 200, 144],
                weights: { '1m': 2, '2m': 3, '5m': 4, '15m': 5, '30m': 6, '1h': 7, '4h': 8 }
            },
            weight: 0.25,
            formBuilder: 'createSMAForm',
            analyzer: 'analyzeSMA'
        });

        // RSI
        this.availableIndicators.set('rsi', {
            name: 'RSI',
            icon: 'fas fa-chart-bar',
            description: 'Relative Strength Index',
            defaultConfig: {
                period: 14,
                timeframes: ['5m', '15m', '30m', '1h', '4h'],
                overbought: 70,
                oversold: 30
            },
            weight: 0.2,
            formBuilder: 'createRSIForm',
            analyzer: 'analyzeRSI'
        });

        // Bollinger Bands
        this.availableIndicators.set('bollinger', {
            name: 'Bollinger Bands',
            icon: 'fas fa-chart-pie',
            description: 'Bollinger Bands Strategy',
            defaultConfig: {
                period: 20,
                stdDev: 2,
                timeframes: ['15m', '30m', '1h', '4h']
            },
            weight: 0.25,
            formBuilder: 'createBollingerForm',
            analyzer: 'analyzeBollinger'
        });

        // Stochastic
        this.availableIndicators.set('stochastic', {
            name: 'Stochastic',
            icon: 'fas fa-chart-line',
            description: 'Stochastic Oscillator',
            defaultConfig: {
                kPeriod: 14,
                dPeriod: 3,
                timeframes: ['5m', '15m', '30m', '1h'],
                overbought: 80,
                oversold: 20
            },
            weight: 0.2,
            formBuilder: 'createStochasticForm',
            analyzer: 'analyzeStochastic'
        });

        // Williams %R
        this.availableIndicators.set('williams_r', {
            name: 'Williams %R',
            icon: 'fas fa-chart-area',
            description: 'Williams %R Oscillator',
            defaultConfig: {
                period: 14,
                timeframes: ['5m', '15m', '30m', '1h'],
                overbought: -20,
                oversold: -80
            },
            weight: 0.15,
            formBuilder: 'createWilliamsRForm',
            analyzer: 'analyzeWilliamsR'
        });
    }

    /**
     * Add symbol configuration
     * @param {string} symbol - Stock symbol
     * @param {Array} indicators - Array of indicator configs
     */
    addSymbolConfig(symbol, indicators) {
        if (indicators.length < 3) {
            throw new Error(`Symbol ${symbol} must have at least 3 indicators`);
        }

        const config = {
            symbol,
            indicators: indicators.map(ind => ({
                type: ind.type,
                enabled: ind.enabled !== false,
                config: { ...this.availableIndicators.get(ind.type).defaultConfig, ...ind.config },
                weight: ind.weight || this.availableIndicators.get(ind.type).weight
            })),
            aggregation: {
                method: 'weighted_average',
                minIndicators: 3,
                consensusThreshold: 0.7,
                confidenceThreshold: 0.6
            }
        };

        this.symbolConfigs.set(symbol, config);
        return config;
    }

    /**
     * Get symbol configuration
     * @param {string} symbol - Stock symbol
     */
    getSymbolConfig(symbol) {
        return this.symbolConfigs.get(symbol);
    }

    /**
     * Get all available indicators
     */
    getAvailableIndicators() {
        return Array.from(this.availableIndicators.values());
    }

    /**
     * Get indicator configuration
     * @param {string} indicatorType - Indicator type
     */
    getIndicatorConfig(indicatorType) {
        return this.availableIndicators.get(indicatorType);
    }

    /**
     * Create configuration form for symbol
     * @param {string} symbol - Stock symbol
     */
    createSymbolConfigurationForm(symbol) {
        const config = this.getSymbolConfig(symbol);
        const availableIndicators = this.getAvailableIndicators();

        return `
            <div class="flexible-multi-indicator-config">
                <div class="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border border-blue-200 mb-4">
                    <h4 class="font-semibold text-blue-800 mb-2 flex items-center">
                        <i class="fas fa-cogs mr-2"></i>
                        Flexible Multi-Indicator Configuration
                    </h4>
                    <p class="text-sm text-blue-700">
                        Symbol: <strong>${symbol}</strong> | 
                        Configure at least 3 indicators for signal generation
                    </p>
                </div>

                <!-- Available Indicators -->
                <div class="mb-6">
                    <h5 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <i class="fas fa-list mr-2"></i>
                        Available Indicators
                    </h5>
                    <div class="grid grid-cols-2 gap-3">
                        ${availableIndicators.map(indicator => `
                            <div class="indicator-card border border-gray-200 rounded-lg p-3 cursor-pointer hover:bg-gray-50" 
                                 data-indicator="${indicator.name.toLowerCase().replace(/\s+/g, '_')}">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <i class="${indicator.icon} text-gray-600 mr-2"></i>
                                        <span class="text-sm font-medium">${indicator.name}</span>
                                    </div>
                                    <div class="flex items-center">
                                        <span class="text-xs text-gray-500 mr-2">Weight: ${indicator.weight}</span>
                                        <input type="checkbox" class="indicator-checkbox" 
                                               data-indicator="${indicator.name.toLowerCase().replace(/\s+/g, '_')}">
                                    </div>
                                </div>
                                <p class="text-xs text-gray-600 mt-1">${indicator.description}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Selected Indicators Configuration -->
                <div class="mb-6">
                    <h5 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <i class="fas fa-cog mr-2"></i>
                        Selected Indicators Configuration
                    </h5>
                    <div id="selectedIndicatorsConfig" class="space-y-4">
                        <!-- Dynamic content will be added here -->
                    </div>
                </div>

                <!-- Aggregation Settings -->
                <div class="mb-6">
                    <h5 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <i class="fas fa-puzzle-piece mr-2"></i>
                        Aggregation Settings
                    </h5>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Method</label>
                            <select id="aggregationMethod" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                <option value="weighted_average">Weighted Average</option>
                                <option value="majority_vote">Majority Vote</option>
                                <option value="consensus">Consensus</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Min Indicators</label>
                            <input type="number" id="minIndicators" value="3" min="3" max="10"
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Consensus Threshold</label>
                            <input type="number" id="consensusThreshold" value="0.7" step="0.1" min="0.5" max="1.0"
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Confidence Threshold</label>
                            <input type="number" id="confidenceThreshold" value="0.6" step="0.1" min="0.3" max="1.0"
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                        </div>
                    </div>
                </div>

                <!-- Actions -->
                <div class="flex gap-2">
                    <button type="button" onclick="flexibleMultiIndicator.addSymbol('${symbol}')" 
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        <i class="fas fa-plus mr-1"></i>Add Symbol
                    </button>
                    <button type="button" onclick="flexibleMultiIndicator.loadDefaultSymbols()" 
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        <i class="fas fa-download mr-1"></i>Load 25 Symbols
                    </button>
                    <button type="button" onclick="flexibleMultiIndicator.saveConfiguration()" 
                            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                        <i class="fas fa-save mr-1"></i>Save Configuration
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Add symbol to configuration
     * @param {string} symbol - Stock symbol
     */
    addSymbol(symbol) {
        const selectedIndicators = this.getSelectedIndicators();
        if (selectedIndicators.length < 3) {
            alert('Please select at least 3 indicators');
            return;
        }

        const indicators = selectedIndicators.map(indicatorType => ({
            type: indicatorType,
            enabled: true,
            config: {},
            weight: this.availableIndicators.get(indicatorType).weight
        }));

        this.addSymbolConfig(symbol, indicators);
        this.showNotification(`Symbol ${symbol} added successfully!`, 'success');
    }

    /**
     * Load default symbols configuration
     */
    loadDefaultSymbols() {
        const defaultSymbols = [
            'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'AMD', 'INTC',
            'CRM', 'ADBE', 'ORCL', 'CSCO', 'IBM', 'QCOM', 'TXN', 'AVGO', 'AMAT', 'MU',
            'LRCX', 'KLAC', 'MCHP', 'SNPS', 'CDNS'
        ];

        const defaultIndicators = [
            { type: 'macd_multi', enabled: true, weight: 0.3 },
            { type: 'sma', enabled: true, weight: 0.25 },
            { type: 'rsi', enabled: true, weight: 0.2 },
            { type: 'bollinger', enabled: true, weight: 0.25 }
        ];

        defaultSymbols.forEach(symbol => {
            this.addSymbolConfig(symbol, defaultIndicators);
        });

        this.showNotification('25 symbols loaded with default configuration!', 'success');
    }

    /**
     * Get selected indicators from form
     */
    getSelectedIndicators() {
        const checkboxes = document.querySelectorAll('.indicator-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.dataset.indicator);
    }

    /**
     * Save configuration
     */
    saveConfiguration() {
        const config = {
            symbols: Array.from(this.symbolConfigs.values()),
            aggregation: {
                method: document.getElementById('aggregationMethod')?.value || 'weighted_average',
                minIndicators: parseInt(document.getElementById('minIndicators')?.value) || 3,
                consensusThreshold: parseFloat(document.getElementById('consensusThreshold')?.value) || 0.7,
                confidenceThreshold: parseFloat(document.getElementById('confidenceThreshold')?.value) || 0.6
            }
        };

        // Save to workflow properties
        if (window.workflowBuilder) {
            const currentNode = window.workflowBuilder.selectedNode;
            if (currentNode) {
                currentNode.properties = config;
                window.workflowBuilder.showNotification('Configuration saved successfully!', 'success');
            }
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        if (window.workflowBuilder && window.workflowBuilder.showNotification) {
            window.workflowBuilder.showNotification(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// Global instance
window.flexibleMultiIndicator = new FlexibleMultiIndicatorSystem();
