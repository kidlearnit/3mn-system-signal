/**
 * Workflow Builder Core
 * Modular architecture for better maintainability
 */

class WorkflowBuilderCore {
    constructor() {
        this.modules = new Map();
        this.eventBus = new EventTarget();
        this.config = {};
        this.initialized = false;
    }

    /**
     * Register a module
     * @param {string} name - Module name
     * @param {Object} module - Module instance
     */
    registerModule(name, module) {
        if (this.modules.has(name)) {
            console.warn(`Module ${name} already registered`);
            return;
        }

        this.modules.set(name, module);
        
        // Initialize module if builder is already initialized
        if (this.initialized && module.init) {
            module.init(this);
        }
    }

    /**
     * Get a module
     * @param {string} name - Module name
     */
    getModule(name) {
        return this.modules.get(name);
    }

    /**
     * Initialize the workflow builder
     */
    async init(config = {}) {
        this.config = { ...this.config, ...config };
        
        // Initialize all registered modules
        for (const [name, module] of this.modules) {
            if (module.init) {
                try {
                    await module.init(this);
                    console.log(`Module ${name} initialized`);
                } catch (error) {
                    console.error(`Failed to initialize module ${name}:`, error);
                }
            }
        }

        this.initialized = true;
        this.emit('initialized');
    }

    /**
     * Emit an event
     * @param {string} eventName - Event name
     * @param {*} data - Event data
     */
    emit(eventName, data = null) {
        this.eventBus.dispatchEvent(new CustomEvent(eventName, { detail: data }));
    }

    /**
     * Listen to an event
     * @param {string} eventName - Event name
     * @param {Function} callback - Event callback
     */
    on(eventName, callback) {
        this.eventBus.addEventListener(eventName, callback);
    }

    /**
     * Remove event listener
     * @param {string} eventName - Event name
     * @param {Function} callback - Event callback
     */
    off(eventName, callback) {
        this.eventBus.removeEventListener(eventName, callback);
    }
}

/**
 * Node Management Module
 */
class NodeManagementModule {
    constructor() {
        this.nodes = new Map();
        this.nodeCounter = 0;
    }

    async init(builder) {
        this.builder = builder;
        
        // Listen for node creation events
        this.builder.on('createNode', this.handleCreateNode.bind(this));
        this.builder.on('deleteNode', this.handleDeleteNode.bind(this));
        this.builder.on('updateNode', this.handleUpdateNode.bind(this));
    }

    createNode(type, x, y) {
        const nodeId = `node_${++this.nodeCounter}`;
        const node = {
            id: nodeId,
            type,
            x,
            y,
            properties: this.getDefaultProperties(type),
            connections: {
                inputs: [],
                outputs: []
            }
        };

        this.nodes.set(nodeId, node);
        this.builder.emit('nodeCreated', { node });
        return node;
    }

    deleteNode(nodeId) {
        const node = this.nodes.get(nodeId);
        if (node) {
            this.nodes.delete(nodeId);
            this.builder.emit('nodeDeleted', { node });
        }
    }

    updateNode(nodeId, updates) {
        const node = this.nodes.get(nodeId);
        if (node) {
            Object.assign(node, updates);
            this.builder.emit('nodeUpdated', { node });
        }
    }

    getNode(nodeId) {
        return this.nodes.get(nodeId);
    }

    getAllNodes() {
        return Array.from(this.nodes.values());
    }

    getDefaultProperties(type) {
        // Get default properties from node registry
        const nodeConfig = window.nodeRegistry?.getNode(type);
        return nodeConfig?.properties || {};
    }

    handleCreateNode(event) {
        const { type, x, y } = event.detail;
        this.createNode(type, x, y);
    }

    handleDeleteNode(event) {
        const { nodeId } = event.detail;
        this.deleteNode(nodeId);
    }

    handleUpdateNode(event) {
        const { nodeId, updates } = event.detail;
        this.updateNode(nodeId, updates);
    }
}

/**
 * Canvas Management Module
 */
class CanvasManagementModule {
    constructor() {
        this.canvas = null;
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
    }

    async init(builder) {
        this.builder = builder;
        this.canvas = document.getElementById('workflowCanvas');
        
        if (!this.canvas) {
            throw new Error('Canvas element not found');
        }

        this.setupEventListeners();
        this.builder.emit('canvasReady', { canvas: this.canvas });
    }

    setupEventListeners() {
        // Canvas event listeners
        this.canvas.addEventListener('click', this.handleCanvasClick.bind(this));
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
    }

    handleCanvasClick(event) {
        this.builder.emit('canvasClick', { event });
    }

    handleMouseDown(event) {
        this.builder.emit('canvasMouseDown', { event });
    }

    handleMouseMove(event) {
        this.builder.emit('canvasMouseMove', { event });
    }

    handleMouseUp(event) {
        this.builder.emit('canvasMouseUp', { event });
    }

    zoomIn() {
        this.zoomLevel = Math.min(this.zoomLevel * 1.2, 3);
        this.updateTransform();
    }

    zoomOut() {
        this.zoomLevel = Math.max(this.zoomLevel / 1.2, 0.1);
        this.updateTransform();
    }

    resetZoom() {
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
        this.updateTransform();
    }

    updateTransform() {
        if (this.canvas) {
            this.canvas.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.zoomLevel})`;
        }
    }
}

/**
 * Palette Management Module
 */
class PaletteManagementModule {
    constructor() {
        this.paletteContainer = null;
    }

    async init(builder) {
        this.builder = builder;
        this.paletteContainer = document.getElementById('actionsNodes');
        
        if (!this.paletteContainer) {
            throw new Error('Palette container not found');
        }

        this.renderPalette();
        this.builder.emit('paletteReady', { container: this.paletteContainer });
    }

    renderPalette() {
        if (!window.nodeRegistry) {
            console.warn('Node registry not available');
            return;
        }

        const paletteNodes = window.nodeRegistry.getPaletteNodes();
        this.paletteContainer.innerHTML = paletteNodes.map(node => 
            `<div class="dropdown-item" data-type="${node.type}">
                <i class="${node.icon} text-gray-600"></i>${node.label}
            </div>`
        ).join('');

        // Add click handlers
        this.paletteContainer.querySelectorAll('.dropdown-item').forEach(el => {
            el.addEventListener('click', () => {
                const type = el.dataset.type;
                this.builder.emit('createNode', { type, x: 80, y: 80 });
            });
        });
    }
}

// Global workflow builder instance
window.workflowBuilderCore = new WorkflowBuilderCore();

// Register core modules
window.workflowBuilderCore.registerModule('nodeManagement', new NodeManagementModule());
window.workflowBuilderCore.registerModule('canvasManagement', new CanvasManagementModule());
window.workflowBuilderCore.registerModule('paletteManagement', new PaletteManagementModule());
