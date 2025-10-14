"""
Flexible Multi-Indicator API Routes
Handles dynamic multi-indicator workflow execution
"""

from flask import Blueprint, request, jsonify
from app.services.flexible_multi_indicator_service import FlexibleMultiIndicatorService
from app.services.aggregation_engine import AggregationEngine
from app.db import db
from app.models import Workflow, Signal
from app.services.strategy_base import SignalResult
import logging

flexible_multi_indicator_bp = Blueprint('flexible_multi_indicator', __name__)
logger = logging.getLogger(__name__)

@flexible_multi_indicator_bp.route('/api/flexible-multi-indicator/execute', methods=['POST'])
def execute_flexible_multi_indicator():
    """Execute flexible multi-indicator workflow"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['symbols', 'symbolConfigs', 'aggregation']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        symbols = data['symbols']
        symbol_configs = data['symbolConfigs']
        aggregation = data['aggregation']
        
        # Validate minimum indicators requirement
        min_indicators = aggregation.get('minIndicators', 3)
        for symbol in symbols:
            if symbol not in symbol_configs:
                return jsonify({
                    'success': False,
                    'error': f'Configuration missing for symbol: {symbol}'
                }), 400
            
            indicators = symbol_configs[symbol].get('indicators', [])
            if len(indicators) < min_indicators:
                return jsonify({
                    'success': False,
                    'error': f'Symbol {symbol} has only {len(indicators)} indicators, minimum {min_indicators} required'
                }), 400

        # Initialize service
        service = FlexibleMultiIndicatorService()
        
        # Execute workflow
        results = service.execute_workflow(symbols, symbol_configs, aggregation)
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_symbols': len(symbols),
                'signals_generated': len([r for r in results if r.get('signal')]),
                'aggregation_method': aggregation.get('method', 'weighted_average')
            }
        })
        
    except Exception as e:
        logger.error(f'Error executing flexible multi-indicator workflow: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@flexible_multi_indicator_bp.route('/api/flexible-multi-indicator/validate', methods=['POST'])
def validate_flexible_multi_indicator():
    """Validate flexible multi-indicator configuration"""
    try:
        data = request.get_json()
        
        # Validate configuration
        validation_result = FlexibleMultiIndicatorService.validate_configuration(data)
        
        return jsonify({
            'success': True,
            'valid': validation_result['valid'],
            'errors': validation_result.get('errors', []),
            'warnings': validation_result.get('warnings', [])
        })
        
    except Exception as e:
        logger.error(f'Error validating flexible multi-indicator configuration: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@flexible_multi_indicator_bp.route('/api/flexible-multi-indicator/indicators', methods=['GET'])
def get_available_indicators():
    """Get list of available indicators"""
    try:
        service = FlexibleMultiIndicatorService()
        indicators = service.get_available_indicators()
        
        return jsonify({
            'success': True,
            'indicators': indicators
        })
        
    except Exception as e:
        logger.error(f'Error getting available indicators: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@flexible_multi_indicator_bp.route('/api/flexible-multi-indicator/symbols/<symbol>/analyze', methods=['POST'])
def analyze_symbol():
    """Analyze a single symbol with its configured indicators"""
    try:
        symbol = request.view_args['symbol']
        data = request.get_json()
        
        if 'indicators' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing indicators configuration'
            }), 400

        service = FlexibleMultiIndicatorService()
        result = service.analyze_symbol(symbol, data['indicators'])
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'result': result
        })
        
    except Exception as e:
        logger.error(f'Error analyzing symbol {symbol}: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@flexible_multi_indicator_bp.route('/api/flexible-multi-indicator/aggregate', methods=['POST'])
def aggregate_signals():
    """Aggregate signals from multiple indicators"""
    try:
        data = request.get_json()
        
        required_fields = ['signals', 'method', 'weights']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        signals = data['signals']
        method = data['method']
        weights = data['weights']
        thresholds = data.get('thresholds', {})
        
        # Initialize aggregation engine
        engine = AggregationEngine()
        
        # Aggregate signals
        result = engine.aggregate_signals(signals, method, weights, thresholds)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f'Error aggregating signals: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@flexible_multi_indicator_bp.route('/api/flexible-multi-indicator/workflow/<workflow_id>/execute', methods=['POST'])
def execute_workflow_by_id(workflow_id):
    """Execute flexible multi-indicator workflow by ID"""
    try:
        # Get workflow from database
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            return jsonify({
                'success': False,
                'error': 'Workflow not found'
            }), 404

        # Parse workflow configuration
        config = workflow.configuration
        if not config:
            return jsonify({
                'success': False,
                'error': 'Workflow configuration not found'
            }), 400

        # Execute workflow
        service = FlexibleMultiIndicatorService()
        results = service.execute_workflow(
            config.get('symbols', []),
            config.get('symbolConfigs', {}),
            config.get('aggregation', {})
        )
        
        # Store results in database
        for result in results:
            if result.get('signal'):
                signal = Signal(
                    workflow_id=workflow_id,
                    symbol=result['symbol'],
                    signal_type=result['signal']['type'],
                    confidence=result['signal']['confidence'],
                    details=result['signal']['details'],
                    timestamp=result['timestamp']
                )
                db.session.add(signal)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'workflow_id': workflow_id,
            'results': results,
            'summary': {
                'total_symbols': len(config.get('symbols', [])),
                'signals_generated': len([r for r in results if r.get('signal')])
            }
        })
        
    except Exception as e:
        logger.error(f'Error executing workflow {workflow_id}: {str(e)}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
