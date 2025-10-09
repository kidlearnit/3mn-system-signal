/**
 * Dynamic Node Registry System
 * Centralized node management for Workflow Builder
 */

class NodeRegistry {
    constructor() {
        this.nodes = new Map();
        this.categories = new Map();
        this.initializeDefaultNodes();
    }

    /**
     * Register a new node type
     * @param {string} type - Node type identifier
     * @param {Object} config - Node configuration
     */
    registerNode(type, config) {
        const nodeConfig = {
            type,
            name: config.name,
            icon: config.icon,
            description: config.description,
            category: config.category || 'general',
            properties: config.properties || {},
            formBuilder: config.formBuilder,
            statusBuilder: config.statusBuilder,
            executor: config.executor,
            ...config
        };

        this.nodes.set(type, nodeConfig);
        
        // Add to category
        if (!this.categories.has(nodeConfig.category)) {
            this.categories.set(nodeConfig.category, []);
        }
        this.categories.get(nodeConfig.category).push(type);
    }

    /**
     * Get node configuration
     */
    getNode(type) {
        return this.nodes.get(type);
    }

    /**
     * Get all nodes by category
     */
    getNodesByCategory(category) {
        return this.categories.get(category) || [];
    }

    /**
     * Get all available node types
     */
    getAllNodeTypes() {
        return Array.from(this.nodes.keys());
    }

    /**
     * Get nodes for palette display
     */
    getPaletteNodes() {
        const paletteNodes = [];
        
        // Input Nodes
        const inputNodes = this.getNodesByCategory('input');
        inputNodes.forEach(type => {
            const node = this.getNode(type);
            paletteNodes.push({
                type: node.type,
                icon: node.icon,
                label: node.name,
                category: 'input'
            });
        });

        // Strategy Nodes
        const strategyNodes = this.getNodesByCategory('strategy');
        strategyNodes.forEach(type => {
            const node = this.getNode(type);
            paletteNodes.push({
                type: node.type,
                icon: node.icon,
                label: node.name,
                category: 'strategy'
            });
        });

        // Logic Nodes
        const logicNodes = this.getNodesByCategory('logic');
        logicNodes.forEach(type => {
            const node = this.getNode(type);
            paletteNodes.push({
                type: node.type,
                icon: node.icon,
                label: node.name,
                category: 'logic'
            });
        });

        // Output Nodes
        const outputNodes = this.getNodesByCategory('output');
        outputNodes.forEach(type => {
            const node = this.getNode(type);
            paletteNodes.push({
                type: node.type,
                icon: node.icon,
                label: node.name,
                category: 'output'
            });
        });

        return paletteNodes;
    }

    /**
     * Initialize default nodes
     */
    initializeDefaultNodes() {
        // Input Nodes
        this.registerNode('symbol', {
            name: 'Symbol',
            icon: 'fas fa-coins',
            description: 'Chọn mã cổ phiếu',
            category: 'input',
            properties: {
                ticker: '',
                exchange: 'US',
                market: 'US'
            }
        });

        this.registerNode('data-source', {
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
        });

        // VN Strategy Nodes
        this.registerNode('vn-macd-7tf', {
            name: 'VN MACD 7TF',
            icon: 'fas fa-chart-line',
            description: 'VN MACD 7 Timeframes Strategy',
            category: 'strategy',
            properties: {
                timeframes: ['1m', '2m', '5m', '15m', '30m', '1h', '4h'],
                fastPeriod: 12,
                slowPeriod: 26,
                signalPeriod: 9,
                useZones: true,
                marketTemplate: 'VN',
                minConfidence: 0.6
            }
        });

        this.registerNode('vn-sma-7tf', {
            name: 'VN SMA 7TF',
            icon: 'fas fa-chart-area',
            description: 'VN SMA 7 Timeframes Strategy',
            category: 'strategy',
            properties: {
                timeframes: ['1m', '2m', '5m', '15m', '30m', '1h', '4h'],
                periods: [5, 10, 20, 50, 100, 200, 144],
                weights: { '1m': 2, '2m': 3, '5m': 4, '15m': 5, '30m': 6, '1h': 7, '4h': 8 }
            }
        });

        // Strategy Nodes
        this.registerNode('macd', {
            name: 'MACD',
            icon: 'fas fa-chart-line',
            description: 'MACD Strategy',
            category: 'strategy',
            properties: {
                timeframes: ['1m', '2m', '5m', '15m', '30m', '1h', '4h'],
                fastPeriod: 12,
                slowPeriod: 26,
                signalPeriod: 9,
                useZones: true,
                marketTemplate: 'VN',
                minConfidence: 0.6
            }
        });

        this.registerNode('macd-multi', {
            name: 'MACD Multi-TF',
            icon: 'fas fa-chart-line',
            description: 'MACD Multi-Timeframe Analysis',
            category: 'strategy',
            properties: {
                symbolThresholds: [],
                macdMulti: {
                    fastPeriod: 7,
                    slowPeriod: 113,
                    signalPeriod: 144,
                    timeframes: ['1m', '2m', '5m', '15m', '30m', '1h']
                }
            }
        });

        this.registerNode('multi-indicator', {
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
        });

        this.registerNode('sma', {
            name: 'SMA',
            icon: 'fas fa-chart-area',
            description: 'Moving Average Strategy',
            category: 'strategy',
            properties: {
                timeframes: ['1m', '2m', '5m', '15m', '30m', '1h', '4h'],
                periods: [5, 10, 20, 50, 100, 200, 144],
                weights: { '1m': 2, '2m': 3, '5m': 4, '15m': 5, '30m': 6, '1h': 7, '4h': 8 }
            }
        });

        this.registerNode('rsi', {
            name: 'RSI',
            icon: 'fas fa-chart-bar',
            description: 'RSI Strategy',
            category: 'strategy',
            properties: {
                period: 14,
                timeframes: ['5m', '15m', '30m', '1h', '4h'],
                overbought: 70,
                oversold: 30,
                minConfidence: 0.5
            }
        });

        this.registerNode('bollinger', {
            name: 'Bollinger Bands',
            icon: 'fas fa-chart-pie',
            description: 'Bollinger Bands Strategy',
            category: 'strategy',
            properties: {
                period: 20,
                stdDev: 2,
                timeframes: ['15m', '30m', '1h', '4h'],
                minConfidence: 0.5
            }
        });

        // Logic Nodes
        this.registerNode('condition', {
            name: 'Condition',
            icon: 'fas fa-question-circle',
            description: 'Điều kiện logic',
            category: 'logic',
            properties: {
                condition: '',
                operator: '==',
                value: ''
            }
        });

        this.registerNode('aggregation', {
            name: 'Aggregation',
            icon: 'fas fa-puzzle-piece',
            description: 'Tổng hợp tín hiệu',
            category: 'logic',
            properties: {
                method: 'weighted_average',
                minStrategies: 3,
                consensusThreshold: 0.7,
                confidenceThreshold: 0.6
            }
        });

        this.registerNode('filter', {
            name: 'Filter',
            icon: 'fas fa-filter',
            description: 'Lọc tín hiệu',
            category: 'logic',
            properties: {
                filterType: 'confidence',
                threshold: 0.6,
                operator: '>='
            }
        });

        // Output Nodes
        this.registerNode('output', {
            name: 'Output',
            icon: 'fas fa-signal',
            description: 'Xuất tín hiệu',
            category: 'output',
            properties: {
                outputType: 'signal',
                format: 'json',
                destination: 'database'
            }
        });

        this.registerNode('alert', {
            name: 'Alert',
            icon: 'fas fa-bell',
            description: 'Cảnh báo',
            category: 'output',
            properties: {
                alertType: 'telegram',
                message: '',
                recipients: []
            }
        });
    }

    /**
     * Load nodes from external configuration
     */
    async loadFromConfig(configUrl) {
        try {
            const response = await fetch(configUrl);
            const config = await response.json();
            
            config.nodes.forEach(nodeConfig => {
                this.registerNode(nodeConfig.type, nodeConfig);
            });
        } catch (error) {
            console.warn('Failed to load node configuration:', error);
        }
    }

    /**
     * Export current node configuration
     */
    exportConfig() {
        const config = {
            nodes: Array.from(this.nodes.values())
        };
        return JSON.stringify(config, null, 2);
    }
}

// Global instance
window.nodeRegistry = new NodeRegistry();
