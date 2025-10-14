"""
Data Validation API Routes
API endpoints để validate data trước khi execute workflow
"""

from flask import Blueprint, request, jsonify
import json
from app.services.data_validation import DataValidator

validation_bp = Blueprint('validation', __name__, url_prefix='/api/validation')

@validation_bp.route('/workflow/<workflow_id>', methods=['GET'])
def validate_workflow_data(workflow_id):
    """Validate data requirements for a workflow"""
    try:
        # Load workflow from database
        from app.routes.workflow_api import get_db_connection
        import pymysql
        
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
                
                # Validate data requirements
                validator = DataValidator()
                validation_result = validator.validate_workflow_data_requirements(nodes)
                
                return jsonify({
                    'success': True,
                    'workflow_id': workflow_id,
                    'workflow_name': workflow['name'],
                    'validation': validation_result
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@validation_bp.route('/symbol/<int:symbol_id>/<timeframe>', methods=['GET'])
def validate_symbol_data(symbol_id, timeframe):
    """Validate data for a specific symbol and timeframe"""
    try:
        validator = DataValidator()
        result = validator.validate_symbol_data(symbol_id, timeframe)
        
        return jsonify({
            'success': True,
            'symbol_id': symbol_id,
            'timeframe': timeframe,
            'validation': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@validation_bp.route('/environment', methods=['GET'])
def validate_environment():
    """Validate execution environment"""
    try:
        validator = DataValidator()
        result = validator.validate_execution_environment()
        
        return jsonify({
            'success': True,
            'environment': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@validation_bp.route('/snapshot/<int:symbol_id>/<timeframe>', methods=['GET'])
def get_data_snapshot(symbol_id, timeframe):
    """Get current data snapshot for a symbol"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        validator = DataValidator()
        result = validator.get_data_snapshot(symbol_id, timeframe, limit)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@validation_bp.route('/workflow/<workflow_id>/pre-execute', methods=['POST'])
def pre_execute_validation(workflow_id):
    """Comprehensive validation before workflow execution"""
    try:
        # Load workflow
        from app.routes.workflow_api import get_db_connection
        import pymysql
        
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
                
                validator = DataValidator()
                
                # 1. Validate environment
                env_validation = validator.validate_execution_environment()
                
                # 2. Validate data requirements
                data_validation = validator.validate_workflow_data_requirements(nodes)
                
                # 3. Get data snapshots for all required symbols
                snapshots = {}
                if data_validation.get('workflow_valid', False):
                    for symbol_id in data_validation['requirements']['symbols']:
                        for timeframe in data_validation['requirements']['timeframes']:
                            snapshot = validator.get_data_snapshot(int(symbol_id), timeframe)
                            snapshots[f"{symbol_id}_{timeframe}"] = snapshot
                
                # Determine if execution should proceed
                can_execute = (
                    env_validation.get('environment_valid', False) and
                    data_validation.get('workflow_valid', False)
                )
                
                return jsonify({
                    'success': True,
                    'workflow_id': workflow_id,
                    'can_execute': can_execute,
                    'environment': env_validation,
                    'data_validation': data_validation,
                    'data_snapshots': snapshots,
                    'recommendations': _get_execution_recommendations(env_validation, data_validation)
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _get_execution_recommendations(env_validation, data_validation):
    """Generate execution recommendations based on validation results"""
    recommendations = []
    
    if not env_validation.get('environment_valid', False):
        recommendations.append({
            'type': 'error',
            'message': 'Environment validation failed. Check database and Redis connectivity.',
            'action': 'Fix environment issues before execution'
        })
    
    if not data_validation.get('workflow_valid', False):
        recommendations.append({
            'type': 'warning',
            'message': 'Data validation failed. Some required data is missing or stale.',
            'action': 'Ensure all required data is available and fresh'
        })
    
    # Check for stale data
    validation_results = data_validation.get('validation_results', {})
    for key, result in validation_results.items():
        if not result['valid'] and result.get('data_quality') == 'stale':
            recommendations.append({
                'type': 'warning',
                'message': f'Data for {key} is stale: {result.get("error", "")}',
                'action': 'Wait for fresh data or trigger data refresh'
            })
    
    # Check for insufficient data
    for key, result in validation_results.items():
        if not result['valid'] and result.get('data_quality') == 'insufficient':
            recommendations.append({
                'type': 'warning',
                'message': f'Insufficient data for {key}: {result.get("error", "")}',
                'action': 'Wait for more data or reduce data requirements'
            })
    
    if not recommendations:
        recommendations.append({
            'type': 'success',
            'message': 'All validations passed. Workflow is ready for execution.',
            'action': 'Proceed with execution'
        })
    
    return recommendations
