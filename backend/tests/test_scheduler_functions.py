#!/usr/bin/env python3
"""
Unit tests for scheduler functions
"""

import unittest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSchedulerFunctions(unittest.TestCase):
    """Test cases for scheduler functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_workflow_config = {
            'fastPeriod': 7,
            'slowPeriod': 113,
            'signalPeriod': 144,
            'symbolThresholds': [
                {'symbol': 'AAPL', 'bubefsm2': 0.85, 'bubefsm5': 0.85, 'bubefsm15': 0.85, 'bubefsm30': 0.85, 'bubefs_1h': 0.85},
                {'symbol': 'MSFT', 'bubefsm2': 1.74, 'bubefsm5': 1.74, 'bubefsm15': 1.74, 'bubefsm30': 1.74, 'bubefs_1h': 1.74}
            ]
        }
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_ensure_macd_symbols_exist_new_symbols(self, mock_session_local):
        """Test ensuring MACD symbols exist with new symbols"""
        from worker.scheduler_multi import _ensure_macd_symbols_exist
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock database query - symbol doesn't exist
        mock_session.execute.return_value.fetchone.return_value = None
        
        result = _ensure_macd_symbols_exist(self.sample_workflow_config)
        
        # Should return number of symbols added
        self.assertEqual(result, 2)
        
        # Verify INSERT was called for each symbol
        self.assertEqual(mock_session.execute.call_count, 4)  # 2 SELECT + 2 INSERT
        mock_session.commit.assert_called_once()
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_ensure_macd_symbols_exist_existing_symbols(self, mock_session_local):
        """Test ensuring MACD symbols exist with existing symbols"""
        from worker.scheduler_multi import _ensure_macd_symbols_exist
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock database query - symbol exists but not active
        mock_session.execute.return_value.fetchone.return_value = (1, 0)  # (id, active)
        
        result = _ensure_macd_symbols_exist(self.sample_workflow_config)
        
        # Should return number of symbols activated
        self.assertEqual(result, 2)
        
        # Verify UPDATE was called for each symbol
        self.assertEqual(mock_session.execute.call_count, 4)  # 2 SELECT + 2 UPDATE
        mock_session.commit.assert_called_once()
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_ensure_macd_symbols_exist_already_active(self, mock_session_local):
        """Test ensuring MACD symbols exist with already active symbols"""
        from worker.scheduler_multi import _ensure_macd_symbols_exist
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock database query - symbol exists and is active
        mock_session.execute.return_value.fetchone.return_value = (1, 1)  # (id, active)
        
        result = _ensure_macd_symbols_exist(self.sample_workflow_config)
        
        # Should return 0 (no changes needed)
        self.assertEqual(result, 0)
        
        # Verify only SELECT was called
        self.assertEqual(mock_session.execute.call_count, 2)  # 2 SELECT only
        mock_session.commit.assert_called_once()
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_ensure_macd_symbols_exist_duplicate_error(self, mock_session_local):
        """Test ensuring MACD symbols exist with duplicate entry error"""
        from worker.scheduler_multi import _ensure_macd_symbols_exist
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock database query - symbol doesn't exist
        mock_session.execute.return_value.fetchone.return_value = None
        
        # Mock INSERT to raise duplicate entry error
        from pymysql.err import IntegrityError
        mock_session.execute.side_effect = [
            None,  # First SELECT
            IntegrityError(1062, "Duplicate entry 'AAPL' for key 'symbols.ticker'"),  # First INSERT
            None,  # Second SELECT
            None   # Second INSERT
        ]
        
        result = _ensure_macd_symbols_exist(self.sample_workflow_config)
        
        # Should handle error gracefully and continue
        self.assertGreaterEqual(result, 0)
        mock_session.commit.assert_called_once()
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_check_macd_multi_active_true(self, mock_session_local):
        """Test checking if MACD Multi-TF is active - returns True"""
        from worker.scheduler_multi import _check_macd_multi_active
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock database query - active workflows found
        mock_session.execute.return_value.fetchone.return_value = (2,)  # 2 active workflows
        
        result = _check_macd_multi_active()
        
        self.assertTrue(result)
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_check_macd_multi_active_false(self, mock_session_local):
        """Test checking if MACD Multi-TF is active - returns False"""
        from worker.scheduler_multi import _check_macd_multi_active
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock database query - no active workflows
        mock_session.execute.return_value.fetchone.return_value = (0,)  # 0 active workflows
        
        result = _check_macd_multi_active()
        
        self.assertFalse(result)
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_check_macd_multi_active_none(self, mock_session_local):
        """Test checking if MACD Multi-TF is active - returns False when None"""
        from worker.scheduler_multi import _check_macd_multi_active
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock database query - None result
        mock_session.execute.return_value.fetchone.return_value = None
        
        result = _check_macd_multi_active()
        
        self.assertFalse(result)
    
    @patch('worker.scheduler_multi._ensure_macd_symbols_exist')
    @patch('worker.scheduler_multi.SessionLocal')
    @patch('worker.scheduler_multi.q_priority')
    def test_enqueue_macd_multi_jobs_success(self, mock_queue, mock_session_local, mock_ensure_symbols):
        """Test enqueuing MACD Multi-TF jobs successfully"""
        from worker.scheduler_multi import _enqueue_macd_multi_jobs
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock workflow data
        mock_workflow_data = [
            ('workflow-1', 'Test Workflow', 
             json.dumps([{'id': 'node-1', 'type': 'macd-multi'}]),
             json.dumps({'node-1': self.sample_workflow_config}))
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_workflow_data
        
        # Mock symbol ensuring
        mock_ensure_symbols.return_value = 2
        
        # Mock queue
        mock_job = MagicMock()
        mock_queue.enqueue.return_value = mock_job
        
        result = _enqueue_macd_multi_jobs()
        
        # Should return number of jobs enqueued
        self.assertEqual(result, 1)
        
        # Verify queue.enqueue was called
        mock_queue.enqueue.assert_called_once()
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_enqueue_macd_multi_jobs_no_workflows(self, mock_session_local):
        """Test enqueuing MACD Multi-TF jobs with no active workflows"""
        from worker.scheduler_multi import _enqueue_macd_multi_jobs
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock no workflows found
        mock_session.execute.return_value.fetchall.return_value = []
        
        result = _enqueue_macd_multi_jobs()
        
        # Should return 0
        self.assertEqual(result, 0)
    
    @patch('worker.scheduler_multi.SessionLocal')
    def test_enqueue_macd_multi_jobs_no_symbol_thresholds(self, mock_session_local):
        """Test enqueuing MACD Multi-TF jobs with no symbol thresholds"""
        from worker.scheduler_multi import _enqueue_macd_multi_jobs
        
        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock workflow data with empty symbol thresholds
        empty_config = self.sample_workflow_config.copy()
        empty_config['symbolThresholds'] = []
        
        mock_workflow_data = [
            ('workflow-1', 'Test Workflow', 
             json.dumps([{'id': 'node-1', 'type': 'macd-multi'}]),
             json.dumps({'node-1': empty_config}))
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_workflow_data
        
        result = _enqueue_macd_multi_jobs()
        
        # Should return 0 (no jobs enqueued due to empty thresholds)
        self.assertEqual(result, 0)
    
    def test_workflow_config_parsing(self):
        """Test workflow configuration parsing"""
        from worker.scheduler_multi import _enqueue_macd_multi_jobs
        
        # Test JSON parsing
        nodes_json = json.dumps([{'id': 'node-1', 'type': 'macd-multi'}])
        properties_json = json.dumps({'node-1': self.sample_workflow_config})
        
        nodes = json.loads(nodes_json)
        properties = json.loads(properties_json)
        
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]['type'], 'macd-multi')
        self.assertIn('node-1', properties)
        self.assertIn('symbolThresholds', properties['node-1'])

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
