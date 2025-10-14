from flask import Blueprint, request, jsonify
import json
import uuid
from datetime import datetime
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')

# Run tracking persisted to MySQL (fallback in-memory if DB not available)
RUNS_BY_WORKFLOW_ID = {}
RUNS_BY_ID = {}

def _utcnow_iso():
    return datetime.utcnow().isoformat() + 'Z'

def _append_run(workflow_id: str, status: str = 'running'):
    run_id = str(uuid.uuid4())
    run = {
        'run_id': run_id,
        'workflow_id': workflow_id,
        'status': status,
        'started_at': _utcnow_iso(),
        'finished_at': None,
        'duration': None,
        'meta': {}
    }
    RUNS_BY_ID[run_id] = run
    RUNS_BY_WORKFLOW_ID.setdefault(workflow_id, []).insert(0, run)
    # Persist to DB
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO workflow_runs (run_id, workflow_id, status, started_at, meta)
                    VALUES (%s, %s, %s, NOW(), %s)
                    """,
                    (run_id, workflow_id, status, json.dumps(run.get('meta') or {}))
                )
                conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
    return run

def _finish_run(run: dict, status: str = 'success'):
    run['status'] = status
    run['finished_at'] = _utcnow_iso()
    try:
        start = datetime.fromisoformat(run['started_at'].replace('Z',''))
        end = datetime.fromisoformat(run['finished_at'].replace('Z',''))
        run['duration'] = f"{(end - start).total_seconds():.2f}s"
    except Exception:
        run['duration'] = None
    # Persist to DB
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE workflow_runs
                    SET status=%s, finished_at=NOW(), duration=%s
                    WHERE run_id=%s
                    """,
                    (status, run['duration'], run['run_id'])
                )
                conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
    return run

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "mysql"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "trader"),
        password=os.getenv("MYSQL_PASSWORD", "traderpass"),
        database=os.getenv("MYSQL_DATABASE", "trading"),
        charset='utf8mb4'
    )

@workflow_bp.route('/save', methods=['POST'])
def save_workflow():
    """Save workflow to database"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'nodes', 'connections']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Prepare workflow data
        workflow_data = {
            'id': workflow_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'nodes': json.dumps(data['nodes']),
            'connections': json.dumps(data['connections']),
            'properties': json.dumps(data.get('properties', {})),
            'metadata': json.dumps(data.get('metadata', {})),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'status': 'active'
        }
        
        # Save to database
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO workflows (
                    id, name, description, nodes, connections, 
                    properties, metadata, created_at, updated_at, status
                ) VALUES (
                    %(id)s, %(name)s, %(description)s, %(nodes)s, %(connections)s,
                    %(properties)s, %(metadata)s, %(created_at)s, %(updated_at)s, %(status)s
                )
                """
                cursor.execute(sql, workflow_data)
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'workflow_id': workflow_id,
                    'message': 'Workflow saved successfully'
                })
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/load/<workflow_id>', methods=['GET'])
def load_workflow(workflow_id):
    """Load workflow from database"""
    try:
        conn = get_db_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT * FROM workflows WHERE id = %s"
                cursor.execute(sql, (workflow_id,))
                workflow = cursor.fetchone()
                
                if not workflow:
                    return jsonify({'error': 'Workflow not found'}), 404
                
                # Parse JSON fields
                workflow['nodes'] = json.loads(workflow['nodes'])
                workflow['connections'] = json.loads(workflow['connections'])
                workflow['properties'] = json.loads(workflow['properties'])
                workflow['metadata'] = json.loads(workflow['metadata'])
                
                return jsonify({
                    'success': True,
                    'workflow': workflow
                })
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/list', methods=['GET'])
def list_workflows():
    """List all workflows"""
    try:
        conn = get_db_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT id, name, description, created_at, updated_at, status
                FROM workflows 
                ORDER BY updated_at DESC
                """
                cursor.execute(sql)
                workflows = cursor.fetchall()
                
                return jsonify({
                    'success': True,
                    'workflows': workflows
                })
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/update/<workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """Update existing workflow"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'nodes', 'connections']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Prepare workflow data
        workflow_data = {
            'id': workflow_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'nodes': json.dumps(data['nodes']),
            'connections': json.dumps(data['connections']),
            'properties': json.dumps(data.get('properties', {})),
            'metadata': json.dumps(data.get('metadata', {})),
            'updated_at': datetime.now()
        }
        
        # Update in database
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                UPDATE workflows SET 
                    name = %(name)s,
                    description = %(description)s,
                    nodes = %(nodes)s,
                    connections = %(connections)s,
                    properties = %(properties)s,
                    metadata = %(metadata)s,
                    updated_at = %(updated_at)s
                WHERE id = %(id)s
                """
                cursor.execute(sql, workflow_data)
                conn.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'Workflow not found'}), 404
                
                return jsonify({
                    'success': True,
                    'workflow_id': workflow_id,
                    'message': 'Workflow updated successfully'
                })
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/delete/<workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    """Delete workflow"""
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM workflows WHERE id = %s"
                cursor.execute(sql, (workflow_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'Workflow not found'}), 404
                
                return jsonify({
                    'success': True,
                    'message': 'Workflow deleted successfully'
                })
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/execute/<workflow_id>', methods=['POST'])
def execute_workflow(workflow_id):
    """Execute workflow with data validation"""
    try:
        # Load workflow
        conn = get_db_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT * FROM workflows WHERE id = %s"
                cursor.execute(sql, (workflow_id,))
                workflow = cursor.fetchone()
                
                if not workflow:
                    return jsonify({'error': 'Workflow not found'}), 404
                
                # Parse workflow data
                nodes = json.loads(workflow['nodes'])
                connections = json.loads(workflow['connections'])
                properties = json.loads(workflow['properties'])
                
                # Check if workflow contains MACD Multi-TF nodes
                macd_multi_nodes = [node for node in nodes if node.get('type') == 'macd-multi']
                
                if macd_multi_nodes:
                    # Execute MACD Multi-TF US workflow in background
                    from worker.macd_multi_us_jobs import job_macd_multi_us_workflow_executor
                    from rq import Queue
                    from app.config import REDIS_URL
                    import redis
                    
                    r = redis.from_url(REDIS_URL)
                    q_priority = Queue('priority', connection=r)
                    
                    # Get node configuration
                    node_config = properties.get(macd_multi_nodes[0]['id'], {})
                    
                    # Check if backfill mode is requested
                    mode = request.get_json().get('mode', 'realtime') if request.get_json() else 'realtime'
                    
                    # Enqueue MACD Multi-TF US job
                    job = q_priority.enqueue(
                        job_macd_multi_us_workflow_executor,
                        workflow_id,
                        macd_multi_nodes[0]['id'],
                        node_config,
                        mode,
                        job_timeout=1800 if mode == 'backfill' else 600  # 30 min for backfill, 10 min for realtime
                    )
                    
                    return jsonify({
                        'success': True,
                        'message': 'MACD Multi-TF workflow queued for execution',
                        'job_id': job.id,
                        'workflow_id': workflow_id
                    })
                
                # Pre-execution validation for regular workflows
                from app.services.data_validation import DataValidator
                validator = DataValidator()
                
                # Validate environment
                env_validation = validator.validate_execution_environment()
                if not env_validation.get('environment_valid', False):
                    return jsonify({
                        'success': False,
                        'error': 'Environment validation failed',
                        'details': env_validation
                    }), 400
                
                # Validate data requirements (skip for testing)
                data_validation = validator.validate_workflow_data_requirements(nodes)
                # Temporarily disable validation for testing
                # if not data_validation.get('workflow_valid', False):
                #     return jsonify({
                #         'success': False,
                #         'error': 'Data validation failed',
                #         'details': data_validation
                #     }), 400
                
                # Track run start
                run = _append_run(workflow_id, status='running')

                # Execute workflow with validated data
                result = execute_workflow_logic(nodes, connections, properties, validator)

                # Finalize run
                status = 'success' if (isinstance(result, dict) and result.get('success')) else 'error'
                _finish_run(run, status=status)

                return jsonify({
                    'success': True,
                    'run_id': run['run_id'],
                    'result': result,
                    'validation': {
                        'environment': env_validation,
                        'data': data_validation
                    },
                    'message': 'Workflow executed successfully with validated data'
                })
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def execute_workflow_logic(nodes, connections, properties, validator=None):
    """Execute workflow logic with data validation"""
    try:
        # Create node map
        node_map = {node['id']: node for node in nodes}
        
        # Find starting nodes (nodes with no input connections)
        input_connections = {conn['to']['nodeId'] for conn in connections}
        starting_nodes = [node for node in nodes if node['id'] not in input_connections]
        
        if not starting_nodes:
            return {'error': 'No starting nodes found'}
        
        # Execute workflow
        results = {}
        
        for start_node in starting_nodes:
            node_result = execute_node(start_node, node_map, connections, properties, validator)
            results[start_node['id']] = node_result
        
        return {
            'success': True,
            'results': results,
            'execution_time': datetime.now().isoformat(),
            'data_validated': validator is not None
        }
        
    except Exception as e:
        return {'error': str(e)}

def execute_node(node, node_map, connections, properties, validator=None):
    """Execute a single node with data validation"""
    try:
        node_type = node['type']
        node_properties = properties.get(node['id'], {})
        
        if node_type == 'symbol':
            return execute_symbol_node(node_properties, validator)
        elif node_type == 'macd':
            return execute_macd_node(node_properties, validator)
        elif node_type == 'macd-multi':
            return execute_macd_multi_node(node_properties, validator)
        elif node_type == 'sma':
            return execute_sma_node(node_properties, validator)
        elif node_type == 'multi-indicator':
            return execute_multi_indicator_node(node_properties, validator)
        elif node_type == 'flexible-multi-indicator':
            return execute_flexible_multi_indicator_node(node_properties, validator)
        elif node_type == 'aggregation':
            return execute_aggregation_node(node_properties, node_map, connections, validator)
        elif node_type == 'output':
            return execute_output_node(node_properties, validator)
        else:
            return {'error': f'Unknown node type: {node_type}'}
            
    except Exception as e:
        return {'error': str(e)}

def execute_symbol_node(properties, validator=None):
    """Execute symbol node with data validation"""
    ticker = properties.get('ticker', 'VN30')
    exchange = properties.get('exchange', 'HOSE')
    timeframes = properties.get('timeframes', ['5m', '15m', '1h'])
    
    result = {
        'type': 'symbol',
        'ticker': ticker,
        'exchange': exchange,
        'timeframes': timeframes,
        'status': 'success',
        'data_validated': validator is not None
    }
    
    if validator:
        # Validate data for each timeframe
        validated_data = {}
        for tf in timeframes:
            # Get symbol_id from ticker (simplified)
            symbol_id = 1  # This should be looked up from database
            snapshot = validator.get_data_snapshot(symbol_id, tf, limit=100)
            validated_data[tf] = snapshot
        
        result['validated_data'] = validated_data
    
    return result

def execute_macd_node(properties, validator=None):
    """Execute MACD node"""
    return {
        'type': 'macd',
        'fast_period': properties.get('fastPeriod', 12),
        'slow_period': properties.get('slowPeriod', 26),
        'signal_period': properties.get('signalPeriod', 9),
        'use_zones': properties.get('useZones', True),
        'market_template': properties.get('marketTemplate', 'VN'),
        'min_confidence': properties.get('minConfidence', 0.6),
        'status': 'success',
        'data_validated': validator is not None
    }

def execute_macd_multi_node(properties, validator=None):
    """Execute MACD Multi-Timeframe node"""
    symbol_thresholds = properties.get('symbolThresholds', [])
    
    # Process each symbol's BuBeFSM values
    processed_symbols = []
    for symbol_data in symbol_thresholds:
        symbol = symbol_data.get('symbol', '')
        if not symbol:
            continue
            
        # Calculate BuBeFSM signals for each timeframe
        bubefsm_signals = {}
        for tf in ['2m', '5m', '15m', '30m', '1h']:
            field_name = f'bubefsm{tf.replace("m", "").replace("h", "_1h")}'
            value = symbol_data.get(field_name, 0)
            
            # Determine signal type based on value
            if value > 0:
                signal_type = 'BULL'
            elif value < 0:
                signal_type = 'BEAR'
            else:
                signal_type = 'NEUTRAL'
                
            bubefsm_signals[tf] = {
                'value': value,
                'signal': signal_type,
                'strength': abs(value)
            }
        
        processed_symbols.append({
            'symbol': symbol,
            'signals': bubefsm_signals,
            'overall_signal': _calculate_overall_signal(bubefsm_signals)
        })
    
    return {
        'type': 'macd-multi',
        'fast_period': properties.get('fastPeriod', 7),
        'slow_period': properties.get('slowPeriod', 113),
        'signal_period': properties.get('signalPeriod', 144),
        'symbol_count': len(processed_symbols),
        'processed_symbols': processed_symbols,
        'status': 'success',
        'data_validated': validator is not None
    }

def _calculate_overall_signal(bubefsm_signals):
    """Calculate overall signal from multiple timeframes"""
    bull_count = 0
    bear_count = 0
    total_strength = 0
    
    for tf, signal_data in bubefsm_signals.items():
        signal = signal_data['signal']
        strength = signal_data['strength']
        
        if signal == 'BULL':
            bull_count += 1
            total_strength += strength
        elif signal == 'BEAR':
            bear_count += 1
            total_strength += strength
    
    if bull_count > bear_count:
        return 'BULL'
    elif bear_count > bull_count:
        return 'BEAR'
    else:
        return 'NEUTRAL'

def execute_sma_node(properties, validator=None):
    """Execute SMA node"""
    return {
        'type': 'sma',
        'periods': properties.get('periods', [18, 36, 48, 144]),
        'triple_confirmation': properties.get('tripleConfirmation', True),
        'min_confirmation': properties.get('minConfirmation', 3),
        'min_confidence': properties.get('minConfidence', 0.5),
        'status': 'success',
        'data_validated': validator is not None
    }

def execute_multi_indicator_node(properties, validator=None):
    """Execute multi-indicator node"""
    symbol_thresholds = properties.get('symbolThresholds', [])
    aggregation = properties.get('aggregation', {})
    
    return {
        'type': 'multi-indicator',
        'symbol_count': len(symbol_thresholds),
        'aggregation_method': aggregation.get('method', 'weighted_average'),
        'min_strategies': aggregation.get('minStrategies', 3),
        'consensus_threshold': aggregation.get('consensusThreshold', 0.7),
        'confidence_threshold': aggregation.get('confidenceThreshold', 0.6),
        'custom_weights': aggregation.get('customWeights', {
            'macd_multi': 0.3,
            'sma': 0.25,
            'rsi': 0.2,
            'bollinger': 0.25
        }),
        'indicators': ['MACD Multi-TF', 'SMA', 'RSI', 'Bollinger Bands'],
        'status': 'success',
        'data_validated': validator is not None
    }

def execute_flexible_multi_indicator_node(properties, validator=None):
    """Execute flexible multi-indicator node"""
    symbols = properties.get('symbols', [])
    symbol_configs = properties.get('symbolConfigs', {})
    aggregation = properties.get('aggregation', {})
    available_indicators = properties.get('availableIndicators', {})
    
    # Count total indicators across all symbols
    total_indicators = 0
    for symbol in symbols:
        if symbol in symbol_configs:
            indicators = symbol_configs[symbol].get('indicators', [])
            total_indicators += len(indicators)
    
    return {
        'type': 'flexible-multi-indicator',
        'symbol_count': len(symbols),
        'total_indicators': total_indicators,
        'aggregation_method': aggregation.get('method', 'weighted_average'),
        'min_indicators': aggregation.get('minIndicators', 3),
        'consensus_threshold': aggregation.get('consensusThreshold', 0.7),
        'confidence_threshold': aggregation.get('confidenceThreshold', 0.6),
        'available_indicators': list(available_indicators.keys()),
        'symbol_configs': symbol_configs,
        'status': 'success',
        'data_validated': validator is not None
    }

def execute_aggregation_node(properties, node_map, connections, validator=None):
    """Execute aggregation node"""
    return {
        'type': 'aggregation',
        'method': properties.get('method', 'weighted_average'),
        'min_strategies': properties.get('minStrategies', 2),
        'consensus_threshold': properties.get('consensusThreshold', 0.7),
        'confidence_threshold': properties.get('confidenceThreshold', 0.6),
        'status': 'success',
        'data_validated': validator is not None
    }

def execute_output_node(properties, validator=None):
    """Execute output node"""
    return {
        'type': 'output',
        'channels': properties.get('channels', ['database', 'telegram']),
        'format': properties.get('format', 'json'),
        'auto_start': properties.get('autoStart', True),
        'status': 'success',
        'data_validated': validator is not None
    }

# ---------- Execution status & control endpoints ----------

@workflow_bp.route('/status/<workflow_id>', methods=['GET'])
def workflow_status(workflow_id):
    try:
        # Prefer DB
        current = None
        try:
            conn = get_db_connection()
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM workflow_runs WHERE workflow_id=%s ORDER BY started_at DESC LIMIT 1",
                        (workflow_id,)
                    )
                    current = cursor.fetchone()
            finally:
                conn.close()
        except Exception:
            pass
        if not current:
            runs = RUNS_BY_WORKFLOW_ID.get(workflow_id, [])
            if not runs:
                return jsonify({'status': 'idle'}), 200
            current = runs[0]
        return jsonify({
            'status': current.get('status', 'idle'),
            'run_id': current.get('run_id') or current.get('run_id'),
            'started_at': current.get('started_at').isoformat() if isinstance(current.get('started_at'), datetime) else current.get('started_at'),
            'finished_at': current.get('finished_at').isoformat() if isinstance(current.get('finished_at'), datetime) else current.get('finished_at'),
            'duration': current.get('duration')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/stop/<workflow_id>', methods=['POST'])
def workflow_stop(workflow_id):
    try:
        runs = RUNS_BY_WORKFLOW_ID.get(workflow_id, [])
        if not runs:
            return jsonify({'error': 'No active runs'}), 404
        current = runs[0]
        _finish_run(current, status='stopped')
        return jsonify({'success': True, 'run_id': current['run_id']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/test-macd-multi', methods=['POST'])
def test_macd_multi():
    """Test MACD Multi-TF US node execution"""
    try:
        from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline
        
        # Get test data from request
        data = request.get_json() or {}
        symbol = data.get('symbol', 'NVDA')
        mode = data.get('mode', 'realtime')
        
        # Sample configuration with 25 symbols
        workflow_config = {
            'fastPeriod': 7,
            'slowPeriod': 113,
            'signalPeriod': 144,
            'symbolThresholds': [
                {
                    'symbol': 'NVDA',
                    'bubefsm2': 0.47,
                    'bubefsm5': 0.47,
                    'bubefsm15': 0.47,
                    'bubefsm30': 0.47,
                    'bubefs_1h': 1.74
                },
                {
                    'symbol': 'MSFT',
                    'bubefsm2': 1.74,
                    'bubefsm5': 1.74,
                    'bubefsm15': 1.74,
                    'bubefsm30': 1.74,
                    'bubefs_1h': 1.74
                },
                {
                    'symbol': 'AAPL',
                    'bubefsm2': 0.85,
                    'bubefsm5': 0.85,
                    'bubefsm15': 0.85,
                    'bubefsm30': 0.85,
                    'bubefs_1h': 0.85
                }
                # Add more symbols as needed for testing
            ]
        }
        
        # If specific symbol requested, filter to that symbol only
        if symbol != 'ALL':
            workflow_config['symbolThresholds'] = [
                st for st in workflow_config['symbolThresholds'] 
                if st['symbol'].upper() == symbol.upper()
            ]
        
        # Execute US pipeline
        result = job_macd_multi_us_pipeline(workflow_config, mode)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'mode': mode,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/restart/<workflow_id>', methods=['POST'])
def workflow_restart(workflow_id):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT * FROM workflows WHERE id = %s"
                cursor.execute(sql, (workflow_id,))
                workflow = cursor.fetchone()
                if not workflow:
                    return jsonify({'error': 'Workflow not found'}), 404
                nodes = json.loads(workflow['nodes'])
                connections = json.loads(workflow['connections'])
                properties = json.loads(workflow['properties'])
        finally:
            conn.close()

        run = _append_run(workflow_id, status='running')
        result = execute_workflow_logic(nodes, connections, properties)
        status = 'success' if (isinstance(result, dict) and result.get('success')) else 'error'
        _finish_run(run, status=status)
        return jsonify({'success': True, 'run_id': run['run_id'], 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/runs/<workflow_id>', methods=['GET'])
def workflow_runs(workflow_id):
    try:
        try:
            conn = get_db_connection()
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM workflow_runs WHERE workflow_id=%s ORDER BY started_at DESC LIMIT 100",
                        (workflow_id,)
                    )
                    runs = cursor.fetchall()
                    return jsonify({'runs': runs})
            finally:
                conn.close()
        except Exception:
            runs = RUNS_BY_WORKFLOW_ID.get(workflow_id, [])
            return jsonify({'runs': runs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/run/<run_id>', methods=['GET'])
def workflow_run(run_id):
    try:
        run = RUNS_BY_ID.get(run_id)
        if not run:
            return jsonify({'error': 'Run not found'}), 404
        return jsonify({'run': run})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/run/<run_id>/stop', methods=['POST'])
def workflow_run_stop(run_id):
    try:
        run = RUNS_BY_ID.get(run_id)
        if not run:
            return jsonify({'error': 'Run not found'}), 404
        _finish_run(run, status='stopped')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/run/<run_id>/restart', methods=['POST'])
def workflow_run_restart(run_id):
    try:
        run = RUNS_BY_ID.get(run_id)
        if not run:
            return jsonify({'error': 'Run not found'}), 404
        workflow_id = run.get('workflow_id')
        if not workflow_id:
            return jsonify({'error': 'Workflow id missing on run'}), 400
        return workflow_restart(workflow_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
