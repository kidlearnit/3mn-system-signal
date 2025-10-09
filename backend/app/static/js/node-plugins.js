/**
 * Node Plugin System
 * Allows dynamic loading of node types
 */

class NodePluginManager {
    constructor() {
        this.plugins = new Map();
        this.loadedPlugins = new Set();
    }

    /**
     * Register a node plugin
     * @param {string} pluginName - Plugin identifier
     * @param {Object} pluginConfig - Plugin configuration
     */
    registerPlugin(pluginName, pluginConfig) {
        this.plugins.set(pluginName, {
            name: pluginName,
            version: pluginConfig.version || '1.0.0',
            nodes: pluginConfig.nodes || [],
            dependencies: pluginConfig.dependencies || [],
            init: pluginConfig.init || (() => {}),
            ...pluginConfig
        });
    }

    /**
     * Load a plugin
     * @param {string} pluginName - Plugin to load
     */
    async loadPlugin(pluginName) {
        if (this.loadedPlugins.has(pluginName)) {
            return; // Already loaded
        }

        const plugin = this.plugins.get(pluginName);
        if (!plugin) {
            throw new Error(`Plugin ${pluginName} not found`);
        }

        // Check dependencies
        for (const dep of plugin.dependencies) {
            if (!this.loadedPlugins.has(dep)) {
                await this.loadPlugin(dep);
            }
        }

        // Initialize plugin
        if (plugin.init) {
            await plugin.init();
        }

        // Register nodes
        plugin.nodes.forEach(nodeConfig => {
            if (window.nodeRegistry) {
                window.nodeRegistry.registerNode(nodeConfig.type, nodeConfig);
            }
        });

        this.loadedPlugins.add(pluginName);
        console.log(`Plugin ${pluginName} loaded successfully`);
    }

    /**
     * Load all available plugins
     */
    async loadAllPlugins() {
        for (const pluginName of this.plugins.keys()) {
            try {
                await this.loadPlugin(pluginName);
            } catch (error) {
                console.error(`Failed to load plugin ${pluginName}:`, error);
            }
        }
    }

    /**
     * Get loaded plugins
     */
    getLoadedPlugins() {
        return Array.from(this.loadedPlugins);
    }
}

// Example plugin definitions
const corePlugins = {
    'basic-nodes': {
        version: '1.0.0',
        nodes: [
            {
                type: 'symbol',
                name: 'Symbol',
                icon: 'fas fa-coins',
                description: 'Chọn mã cổ phiếu',
                category: 'input',
                properties: {
                    ticker: '',
                    exchange: 'US',
                    market: 'US'
                }
            },
            {
                type: 'data-source',
                name: 'Data Source',
                icon: 'fas fa-database',
                description: 'Nguồn dữ liệu',
                category: 'input',
                properties: {
                    source: 'yfinance',
                    api_key: '',
                    rate_limit: 100,
                    timeout: 30
                }
            }
        ]
    },

    'strategy-nodes': {
        version: '1.0.0',
        dependencies: ['basic-nodes'],
        nodes: [
            {
                type: 'macd',
                name: 'MACD',
                icon: 'fas fa-chart-line',
                description: 'MACD Strategy',
                category: 'strategy',
                properties: {
                    timeframes: ['1m', '2m', '5m', '15m', '30m', '1h', '4h'],
                    fastPeriod: 12,
                    slowPeriod: 26,
                    signalPeriod: 9
                }
            },
            {
                type: 'sma',
                name: 'SMA',
                icon: 'fas fa-chart-area',
                description: 'Moving Average Strategy',
                category: 'strategy',
                properties: {
                    timeframes: ['1m', '2m', '5m', '15m', '30m', '1h', '4h'],
                    periods: [5, 10, 20, 50, 100, 200, 144]
                }
            }
        ]
    },

    'multi-indicator-plugin': {
        version: '1.0.0',
        dependencies: ['strategy-nodes'],
        nodes: [
            {
                type: 'multi-indicator',
                name: 'Multi-Indicator',
                icon: 'fas fa-layer-group',
                description: 'Multi-Indicator Analysis (MACD+SMA+RSI+BB)',
                category: 'strategy',
                properties: {
                    symbolThresholds: [],
                    macdMulti: {
                        fastPeriod: 7,
                        slowPeriod: 113,
                        signalPeriod: 144,
                        timeframes: ['1m', '2m', '5m', '15m', '30m', '1h']
                    },
                    sma: {
                        timeframes: ['1m', '2m', '5m', '15m', '30m', '1h', '4h'],
                        periods: [5, 10, 20, 50, 100, 200, 144]
                    },
                    rsi: {
                        period: 14,
                        timeframes: ['5m', '15m', '30m', '1h', '4h'],
                        overbought: 70,
                        oversold: 30
                    },
                    bollinger: {
                        period: 20,
                        stdDev: 2,
                        timeframes: ['15m', '30m', '1h', '4h']
                    },
                    aggregation: {
                        method: 'weighted_average',
                        minStrategies: 3,
                        consensusThreshold: 0.7,
                        confidenceThreshold: 0.6,
                        customWeights: {
                            'macd_multi': 0.3,
                            'sma': 0.25,
                            'rsi': 0.2,
                            'bollinger': 0.25
                        }
                    }
                }
            }
        ],
        init: async () => {
            console.log('Multi-Indicator plugin initialized');
            // Plugin-specific initialization code
        }
    }
};

// Global plugin manager
window.pluginManager = new NodePluginManager();

// Register core plugins
Object.entries(corePlugins).forEach(([name, config]) => {
    window.pluginManager.registerPlugin(name, config);
});
