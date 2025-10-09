from flask import Flask, request
from flask_socketio import SocketIO
from flask_cors import CORS
from app.config import load_config
from app.db import init_db, Base
from app.routes.admin import admin_bp
from app.routes.strategy_management import strategy_mgmt_bp
from app.routes.real_data import real_data_bp
from app.routes.websocket_api import websocket_api_bp, register_websocket_events, start_market_data_simulation
from app.routes.htmx_api import htmx_bp
from app.routes.hybrid_api import hybrid_bp
from app.routes.extensible_api import extensible_bp

# Import REST API blueprints
from app.routes.symbols import symbols_api
from app.routes.signals import signals_api
from app.routes.strategies import strategies_api
from app.routes.candles import candles_api
from app.routes.indicators import indicators_api
from app.routes.dashboard import dashboard_api
from app.services.system_monitor import system_monitor
from app.services.websocket_service import init_websocket_service

def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    load_config(app)
    
    # Enable CORS for all routes
    CORS(app, origins=['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000', 'http://127.0.0.1:3001', 'http://frontend:3000'])
    print(f"Initializing database with URL: {app.config['DATABASE_URL']}")
    init_db(app.config['DATABASE_URL'])
    from app.db import SessionLocal
    print(f"SessionLocal initialized: {SessionLocal is not None}")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(strategy_mgmt_bp)  # Strategy management routes without prefix
    app.register_blueprint(real_data_bp)  # Real data routes without prefix
    app.register_blueprint(websocket_api_bp)  # WebSocket API routes without prefix
    app.register_blueprint(htmx_bp)  # HTMX API routes
    app.register_blueprint(hybrid_bp)  # Hybrid API routes
    app.register_blueprint(extensible_bp)  # Extensible API routes
    
    # Import and register workflow API
    from app.routes.workflow_api import workflow_bp
    app.register_blueprint(workflow_bp)  # Workflow API routes
    
    # Register REST API blueprints
    app.register_blueprint(symbols_api.blueprint)  # Symbols REST API
    app.register_blueprint(signals_api.blueprint)  # Signals REST API
    app.register_blueprint(strategies_api.blueprint)  # Strategies REST API
    app.register_blueprint(candles_api.blueprint)  # Candles REST API
    app.register_blueprint(indicators_api.blueprint)  # Indicators REST API
    app.register_blueprint(dashboard_api.blueprint)  # Dashboard REST API
    
    # Initialize WebSocket
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    init_websocket_service(socketio)
    
    # Register chart WebSocket events
    register_websocket_events(socketio)
    # Start market data simulation
    start_market_data_simulation(socketio)
    
    # Start system monitoring
    print("🔍 Starting system monitoring...")
    system_monitor.start_monitoring()
    
    # Add UI routes
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('pages/index.html')
    
    @app.route('/symbols')
    def symbols_page():
        from flask import render_template
        return render_template('pages/symbols.html')
    
    @app.route('/signals')
    def signals_page():
        from flask import render_template
        return render_template('pages/signals.html')
    
    @app.route('/dashboard')
    def dashboard_page():
        from flask import render_template
        return render_template('pages/dashboard.html')
    
    @app.route('/config')
    def config_page():
        from flask import render_template
        return render_template('pages/config.html')
    
    @app.route('/strategy-configuration')
    def strategy_configuration_page():
        from flask import render_template
        return render_template('pages/strategy_configuration.html')
    
    @app.route('/strategies')
    def strategies_page():
        from flask import render_template
        return render_template('strategies/strategy_dashboard.html')
    
    @app.route('/charts')
    def charts_page():
        from flask import render_template
        return render_template('charts/chart.html')
    
    @app.route('/multi-timeframe-charts')
    def multi_timeframe_charts():
        from flask import render_template
        return render_template('charts/multi_timeframe.html')
    
    @app.route('/symbol-strategy-config')
    def symbol_strategy_config_page():
        from flask import render_template
        return render_template('pages/symbol_strategy_config.html')
    
    @app.route('/extensible-strategies')
    def extensible_strategies_page():
        from flask import render_template
        return render_template('pages/extensible_strategies.html')
    
    @app.route('/strategy-setup-guide')
    def strategy_setup_guide_page():
        from flask import render_template
        return render_template('pages/strategy_setup_guide.html')
    
    @app.route('/workflow-builder')
    def workflow_builder_page():
        from flask import render_template
        return render_template('pages/workflow_builder.html')
    
    @app.route('/simple-workflow-builder')
    def simple_workflow_builder_page():
        from flask import render_template
        return render_template('pages/simple_workflow_builder.html')
    
    return app, socketio

app, socketio = create_app()

if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    socketio.run(app, host='0.0.0.0', port=5010, debug=True)
