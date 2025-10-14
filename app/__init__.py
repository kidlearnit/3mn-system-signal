from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from routes.websocket_api import websocket_api_bp, register_websocket_events, start_market_data_simulation
except ImportError as e:
    # Fallback if import fails
    print(f"Import error: {e}")
    websocket_api_bp = None

try:
    from routes.worker_api import worker_bp
except ImportError as e:
    print(f"Worker API import error: {e}")
    worker_bp = None

try:
    from routes.workflow_api import workflow_bp
except ImportError as e:
    print(f"Workflow API import error: {e}")
    workflow_bp = None

try:
    from routes.validation_api import validation_bp
except ImportError as e:
    print(f"Validation API import error: {e}")
    validation_bp = None

# Optional: Flexible Multi-Indicator API (disabled by default to avoid noisy imports)
FLEX_MULTI_ENABLED = os.getenv("FLEX_MULTI_ENABLED", "0") == "1"
flexible_multi_indicator_bp = None
if FLEX_MULTI_ENABLED:
    try:
        from routes.flexible_multi_indicator_api import flexible_multi_indicator_bp
    except ImportError:
        # Keep silent unless explicitly enabled, then user will check logs
        flexible_multi_indicator_bp = None

def create_app():
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app, origins=['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000', 'http://127.0.0.1:3001'])
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins=['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000', 'http://127.0.0.1:3001'])
    
    # Register blueprints
    if websocket_api_bp:
        app.register_blueprint(websocket_api_bp)
        # Register WebSocket events
        register_websocket_events(socketio)
        # Start market data simulation
        start_market_data_simulation(socketio)
    
    if worker_bp:
        app.register_blueprint(worker_bp)
    
    if workflow_bp:
        app.register_blueprint(workflow_bp)
    
    if validation_bp:
        app.register_blueprint(validation_bp)
    
    if flexible_multi_indicator_bp:
        app.register_blueprint(flexible_multi_indicator_bp)
    
    # Store socketio instance for later use
    app.socketio = socketio
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Use SocketIO to run the app
    app.socketio.run(app, host='0.0.0.0', port=5010, debug=True)
