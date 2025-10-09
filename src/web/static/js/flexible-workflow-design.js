/**
 * Flexible Workflow Design
 * Supports dynamic symbol and indicator configuration
 */

class FlexibleWorkflowDesign {
    constructor() {
        this.workflowTypes = new Map();
        this.initializeWorkflowTypes();
    }

    /**
     * Initialize workflow types
     */
    initializeWorkflowTypes() {
        // Type 1: Single Symbol Multi-Indicator
        this.workflowTypes.set('single_symbol_multi_indicator', {
            name: 'Single Symbol Multi-Indicator',
            description: 'One symbol with multiple indicators',
            structure: {
                input: ['symbol'],
                processing: ['flexible_multi_indicator'],
                output: ['signal_output', 'alert']
            },
            minIndicators: 3,
            maxIndicators: 10,
            example: {
                symbol: 'AAPL',
                indicators: ['macd_multi', 'sma', 'rsi', 'bollinger'],
                aggregation: 'weighted_average'
            }
        });

        // Type 2: Multi Symbol Multi-Indicator
        this.workflowTypes.set('multi_symbol_multi_indicator', {
            name: 'Multi Symbol Multi-Indicator',
            description: 'Multiple symbols, each with multiple indicators',
            structure: {
                input: ['symbol_list'],
                processing: ['flexible_multi_indicator'],
                output: ['signal_output', 'alert']
            },
            minSymbols: 1,
            maxSymbols: 100,
            minIndicators: 3,
            maxIndicators: 10,
            example: {
                symbols: ['AAPL', 'MSFT', 'GOOGL'],
                indicators: ['macd_multi', 'sma', 'rsi'],
                aggregation: 'consensus'
            }
        });

        // Type 3: Portfolio Multi-Indicator
        this.workflowTypes.set('portfolio_multi_indicator', {
            name: 'Portfolio Multi-Indicator',
            description: 'Portfolio with sector-based indicator configuration',
            structure: {
                input: ['portfolio_config'],
                processing: ['sector_analyzer', 'flexible_multi_indicator'],
                output: ['portfolio_signal', 'alert']
            },
            minSymbols: 10,
            maxSymbols: 500,
            minIndicators: 3,
            maxIndicators: 15,
            example: {
                portfolio: 'S&P 500',
                sectors: {
                    'Technology': ['macd_multi', 'sma', 'rsi', 'bollinger'],
                    'Healthcare': ['macd_multi', 'sma', 'stochastic'],
                    'Finance': ['macd_multi', 'sma', 'williams_r']
                },
                aggregation: 'sector_weighted'
            }
        });
    }

    /**
     * Create workflow configuration
     * @param {string} type - Workflow type
     * @param {Object} config - Configuration
     */
    createWorkflow(type, config) {
        const workflowType = this.workflowTypes.get(type);
        if (!workflowType) {
            throw new Error(`Unknown workflow type: ${type}`);
        }

        const workflow = {
            id: this.generateWorkflowId(),
            type,
            name: config.name || `${workflowType.name} - ${new Date().toISOString()}`,
            description: config.description || workflowType.description,
            created: new Date().toISOString(),
            status: 'draft',
            configuration: this.buildConfiguration(type, config),
            nodes: this.buildNodes(type, config),
            connections: this.buildConnections(type, config)
        };

        return workflow;
    }

    /**
     * Build configuration based on workflow type
     */
    buildConfiguration(type, config) {
        switch (type) {
            case 'single_symbol_multi_indicator':
                return {
                    symbol: config.symbol,
                    indicators: config.indicators,
                    aggregation: config.aggregation || 'weighted_average',
                    minIndicators: config.minIndicators || 3,
                    consensusThreshold: config.consensusThreshold || 0.7
                };

            case 'multi_symbol_multi_indicator':
                return {
                    symbols: config.symbols,
                    indicators: config.indicators,
                    aggregation: config.aggregation || 'consensus',
                    minIndicators: config.minIndicators || 3,
                    consensusThreshold: config.consensusThreshold || 0.7,
                    symbolConfigs: config.symbolConfigs || {}
                };

            case 'portfolio_multi_indicator':
                return {
                    portfolio: config.portfolio,
                    sectors: config.sectors,
                    aggregation: config.aggregation || 'sector_weighted',
                    minIndicators: config.minIndicators || 3,
                    consensusThreshold: config.consensusThreshold || 0.7,
                    sectorWeights: config.sectorWeights || {}
                };

            default:
                return config;
        }
    }

    /**
     * Build nodes based on workflow type
     */
    buildNodes(type, config) {
        const nodes = [];

        switch (type) {
            case 'single_symbol_multi_indicator':
                nodes.push({
                    id: 'symbol_1',
                    type: 'symbol',
                    x: 100,
                    y: 100,
                    properties: {
                        ticker: config.symbol,
                        exchange: 'US',
                        market: 'US'
                    }
                });

                nodes.push({
                    id: 'multi_indicator_1',
                    type: 'flexible_multi_indicator',
                    x: 300,
                    y: 100,
                    properties: {
                        symbol: config.symbol,
                        indicators: config.indicators,
                        aggregation: config.aggregation
                    }
                });

                nodes.push({
                    id: 'output_1',
                    type: 'signal_output',
                    x: 500,
                    y: 100,
                    properties: {
                        outputType: 'signal',
                        format: 'json',
                        destination: 'database'
                    }
                });

                break;

            case 'multi_symbol_multi_indicator':
                // Add symbol nodes
                config.symbols.forEach((symbol, index) => {
                    nodes.push({
                        id: `symbol_${index + 1}`,
                        type: 'symbol',
                        x: 100,
                        y: 100 + (index * 150),
                        properties: {
                            ticker: symbol,
                            exchange: 'US',
                            market: 'US'
                        }
                    });
                });

                // Add multi-indicator node
                nodes.push({
                    id: 'multi_indicator_1',
                    type: 'flexible_multi_indicator',
                    x: 300,
                    y: 200,
                    properties: {
                        symbols: config.symbols,
                        indicators: config.indicators,
                        aggregation: config.aggregation,
                        symbolConfigs: config.symbolConfigs
                    }
                });

                // Add output node
                nodes.push({
                    id: 'output_1',
                    type: 'signal_output',
                    x: 500,
                    y: 200,
                    properties: {
                        outputType: 'signal',
                        format: 'json',
                        destination: 'database'
                    }
                });

                break;

            case 'portfolio_multi_indicator':
                // Add portfolio config node
                nodes.push({
                    id: 'portfolio_1',
                    type: 'portfolio_config',
                    x: 100,
                    y: 100,
                    properties: {
                        portfolio: config.portfolio,
                        sectors: config.sectors,
                        sectorWeights: config.sectorWeights
                    }
                });

                // Add sector analyzer
                nodes.push({
                    id: 'sector_analyzer_1',
                    type: 'sector_analyzer',
                    x: 300,
                    y: 100,
                    properties: {
                        sectors: config.sectors,
                        aggregation: config.aggregation
                    }
                });

                // Add multi-indicator node
                nodes.push({
                    id: 'multi_indicator_1',
                    type: 'flexible_multi_indicator',
                    x: 500,
                    y: 100,
                    properties: {
                        portfolio: config.portfolio,
                        sectors: config.sectors,
                        indicators: config.indicators,
                        aggregation: config.aggregation
                    }
                });

                // Add output node
                nodes.push({
                    id: 'output_1',
                    type: 'portfolio_signal',
                    x: 700,
                    y: 100,
                    properties: {
                        outputType: 'portfolio_signal',
                        format: 'json',
                        destination: 'database'
                    }
                });

                break;
        }

        return nodes;
    }

    /**
     * Build connections based on workflow type
     */
    buildConnections(type, config) {
        const connections = [];

        switch (type) {
            case 'single_symbol_multi_indicator':
                connections.push({
                    id: 'conn_1',
                    from: 'symbol_1',
                    to: 'multi_indicator_1',
                    type: 'data'
                });
                connections.push({
                    id: 'conn_2',
                    from: 'multi_indicator_1',
                    to: 'output_1',
                    type: 'signal'
                });
                break;

            case 'multi_symbol_multi_indicator':
                config.symbols.forEach((symbol, index) => {
                    connections.push({
                        id: `conn_${index + 1}`,
                        from: `symbol_${index + 1}`,
                        to: 'multi_indicator_1',
                        type: 'data'
                    });
                });
                connections.push({
                    id: `conn_${config.symbols.length + 1}`,
                    from: 'multi_indicator_1',
                    to: 'output_1',
                    type: 'signal'
                });
                break;

            case 'portfolio_multi_indicator':
                connections.push({
                    id: 'conn_1',
                    from: 'portfolio_1',
                    to: 'sector_analyzer_1',
                    type: 'config'
                });
                connections.push({
                    id: 'conn_2',
                    from: 'sector_analyzer_1',
                    to: 'multi_indicator_1',
                    type: 'data'
                });
                connections.push({
                    id: 'conn_3',
                    from: 'multi_indicator_1',
                    to: 'output_1',
                    type: 'signal'
                });
                break;
        }

        return connections;
    }

    /**
     * Generate unique workflow ID
     */
    generateWorkflowId() {
        return `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get workflow types
     */
    getWorkflowTypes() {
        return Array.from(this.workflowTypes.values());
    }

    /**
     * Validate workflow configuration
     * @param {Object} workflow - Workflow configuration
     */
    validateWorkflow(workflow) {
        const errors = [];
        const workflowType = this.workflowTypes.get(workflow.type);

        if (!workflowType) {
            errors.push(`Unknown workflow type: ${workflow.type}`);
            return errors;
        }

        // Validate minimum requirements
        if (workflow.configuration.indicators.length < workflowType.minIndicators) {
            errors.push(`Minimum ${workflowType.minIndicators} indicators required`);
        }

        if (workflow.configuration.indicators.length > workflowType.maxIndicators) {
            errors.push(`Maximum ${workflowType.maxIndicators} indicators allowed`);
        }

        // Validate symbols
        if (workflow.type === 'multi_symbol_multi_indicator') {
            if (workflow.configuration.symbols.length < workflowType.minSymbols) {
                errors.push(`Minimum ${workflowType.minSymbols} symbols required`);
            }
            if (workflow.configuration.symbols.length > workflowType.maxSymbols) {
                errors.push(`Maximum ${workflowType.maxSymbols} symbols allowed`);
            }
        }

        return errors;
    }
}

// Global instance
window.flexibleWorkflowDesign = new FlexibleWorkflowDesign();
