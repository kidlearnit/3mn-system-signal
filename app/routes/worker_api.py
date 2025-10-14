from flask import Blueprint, request, jsonify
import json
import pymysql
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

worker_bp = Blueprint('worker', __name__, url_prefix='/api/worker')

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'trading_signals'),
        autocommit=True
    )

@worker_bp.route('/list', methods=['GET'])
def list_workers():
    """List all available workers"""
    try:
        # Return list of workers from docker-compose
        workers = [
            {
                'id': 'worker',
                'name': 'Main Worker',
                'type': 'priority',
                'status': 'active',
                'description': 'Main worker for priority jobs'
            },
            {
                'id': 'worker_vn',
                'name': 'Vietnam Market Worker',
                'type': 'vn',
                'status': 'active', 
                'description': 'Worker for Vietnam market (HOSE, HNX, UPCOM)'
            },
            {
                'id': 'worker_us',
                'name': 'US Market Worker',
                'type': 'us',
                'status': 'active',
                'description': 'Worker for US market (NASDAQ, NYSE)'
            },
            {
                'id': 'worker_backfill',
                'name': 'Backfill Worker',
                'type': 'backfill',
                'status': 'active',
                'description': 'Worker for data backfill operations'
            },
            {
                'id': 'scheduler',
                'name': 'Scheduler',
                'type': 'scheduler',
                'status': 'active',
                'description': 'Job scheduler and coordinator'
            }
        ]
        
        return jsonify({
            'success': True,
            'workers': workers
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/<worker_id>/assign-workflow', methods=['POST'])
def assign_workflow_to_worker(worker_id):
    """Assign a workflow to a specific worker"""
    try:
        data = request.get_json()
        workflow_id = data.get('workflow_id')
        
        if not workflow_id:
            return jsonify({'error': 'workflow_id is required'}), 400
        
        # Validate worker exists
        valid_workers = ['worker', 'worker_vn', 'worker_us', 'worker_backfill', 'scheduler']
        if worker_id not in valid_workers:
            return jsonify({'error': f'Invalid worker_id: {worker_id}'}), 400
        
        # Save assignment to database
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Create worker_assignments table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS worker_assignments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        worker_id VARCHAR(50) NOT NULL,
                        workflow_id VARCHAR(100) NOT NULL,
                        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status ENUM('active', 'inactive') DEFAULT 'active',
                        UNIQUE KEY unique_assignment (worker_id, workflow_id)
                    )
                """)
                
                # Insert or update assignment
                cursor.execute("""
                    INSERT INTO worker_assignments (worker_id, workflow_id, status)
                    VALUES (%s, %s, 'active')
                    ON DUPLICATE KEY UPDATE 
                    status = 'active',
                    assigned_at = CURRENT_TIMESTAMP
                """, (worker_id, workflow_id))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Workflow {workflow_id} assigned to worker {worker_id}',
                    'assignment': {
                        'worker_id': worker_id,
                        'workflow_id': workflow_id,
                        'assigned_at': datetime.now().isoformat()
                    }
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/<worker_id>/workflows', methods=['GET'])
def get_worker_workflows(worker_id):
    """Get all workflows assigned to a worker"""
    try:
        conn = get_db_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT wa.*, w.name as workflow_name, w.description
                    FROM worker_assignments wa
                    LEFT JOIN workflows w ON wa.workflow_id = w.id
                    WHERE wa.worker_id = %s AND wa.status = 'active'
                    ORDER BY wa.assigned_at DESC
                """, (worker_id,))
                
                assignments = cursor.fetchall()
                
                return jsonify({
                    'success': True,
                    'worker_id': worker_id,
                    'assignments': assignments
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@worker_bp.route('/<worker_id>/status', methods=['GET'])
def get_worker_status(worker_id):
    """Get worker status and statistics"""
    try:
        # For now, return mock status
        # In production, this would check actual worker status
        status = {
            'worker_id': worker_id,
            'status': 'active',
            'jobs_processed': 0,
            'jobs_failed': 0,
            'last_activity': datetime.now().isoformat(),
            'queue_size': 0
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
