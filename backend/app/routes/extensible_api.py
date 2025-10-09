#!/usr/bin/env python3
"""
Extensible API endpoints for multi-strategy signal system
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app.db import init_db
from app.services.extensible_signal_engine import extensible_signal_engine
from app.services.strategy_base import strategy_registry
from app.services.aggregation_engine import AggregationConfig, AggregationMethod
import logging
import os

# Initialize database
init_db(os.getenv("DATABASE_URL"))

# Import SessionLocal after initialization
from app.db import SessionLocal

logger = logging.getLogger(__name__)

extensible_bp = Blueprint('extensible', __name__, url_prefix='/api/extensible')

@extensible_bp.route('/strategies', methods=['GET'])
def get_available_strategies():
    """Lấy danh sách strategies có sẵn"""
    try:
        strategies = extensible_signal_engine.get_available_strategies()
        strategy_info = {}
        
        for strategy_name in strategies:
            info = extensible_signal_engine.get_strategy_info(strategy_name)
            if info:
                strategy_info[strategy_name] = info
        
        return jsonify({
            'status': 'success',
            'data': {
                'strategies': strategy_info,
                'total': len(strategy_info)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting available strategies: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching strategies: {str(e)}'
        }), 500

@extensible_bp.route('/strategies/<strategy_name>', methods=['GET'])
def get_strategy_detail(strategy_name):
    """Lấy chi tiết strategy"""
    try:
        info = extensible_signal_engine.get_strategy_info(strategy_name)
        
        if not info:
            return jsonify({
                'status': 'error',
                'message': 'Strategy not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': info
        })
        
    except Exception as e:
        logger.error(f"Error getting strategy detail: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching strategy detail: {str(e)}'
        }), 500

@extensible_bp.route('/evaluate/<int:symbol_id>', methods=['POST'])
def evaluate_signal(symbol_id):
    """Đánh giá tín hiệu cho symbol"""
    try:
        data = request.get_json()
        timeframe = data.get('timeframe', '5m')
        strategy_names = data.get('strategies')  # None = tất cả active strategies
        
        # Lấy thông tin symbol
        with SessionLocal() as s:
            symbol_row = s.execute(text("""
                SELECT ticker, exchange FROM symbols WHERE id = :symbol_id
            """), {'symbol_id': symbol_id}).first()
            
            if not symbol_row:
                return jsonify({
                    'status': 'error',
                    'message': 'Symbol not found'
                }), 404
            
            ticker = symbol_row.ticker
            exchange = symbol_row.exchange
        
        # Đánh giá tín hiệu
        result = extensible_signal_engine.evaluate_signal(
            symbol_id, ticker, exchange, timeframe, strategy_names
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error evaluating signal: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error evaluating signal: {str(e)}'
        }), 500

@extensible_bp.route('/multi-timeframe/<int:symbol_id>', methods=['POST'])
def evaluate_multi_timeframe(symbol_id):
    """Đánh giá tín hiệu multi-timeframe"""
    try:
        data = request.get_json()
        strategy_names = data.get('strategies')
        
        # Lấy thông tin symbol
        with SessionLocal() as s:
            symbol_row = s.execute(text("""
                SELECT ticker, exchange FROM symbols WHERE id = :symbol_id
            """), {'symbol_id': symbol_id}).first()
            
            if not symbol_row:
                return jsonify({
                    'status': 'error',
                    'message': 'Symbol not found'
                }), 404
            
            ticker = symbol_row.ticker
            exchange = symbol_row.exchange
        
        # Đánh giá multi-timeframe
        result = extensible_signal_engine.evaluate_multi_timeframe(
            symbol_id, ticker, exchange, strategy_names
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error evaluating multi-timeframe signal: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error evaluating multi-timeframe signal: {str(e)}'
        }), 500

@extensible_bp.route('/aggregation/config', methods=['GET'])
def get_aggregation_config():
    """Lấy cấu hình aggregation"""
    try:
        config_info = extensible_signal_engine.get_aggregation_info()
        
        return jsonify({
            'status': 'success',
            'data': config_info
        })
        
    except Exception as e:
        logger.error(f"Error getting aggregation config: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching aggregation config: {str(e)}'
        }), 500

@extensible_bp.route('/aggregation/config', methods=['POST'])
def update_aggregation_config():
    """Cập nhật cấu hình aggregation"""
    try:
        data = request.get_json()
        
        # Tạo config mới
        config = AggregationConfig(
            method=AggregationMethod(data.get('method', 'weighted_average')),
            min_strategies=data.get('min_strategies', 2),
            consensus_threshold=data.get('consensus_threshold', 0.6),
            confidence_threshold=data.get('confidence_threshold', 0.5),
            conflict_penalty=data.get('conflict_penalty', 0.3),
            custom_weights=data.get('custom_weights', {})
        )
        
        # Cập nhật config
        extensible_signal_engine.update_aggregation_config(config)
        
        return jsonify({
            'status': 'success',
            'data': {
                'message': 'Aggregation config updated successfully',
                'config': extensible_signal_engine.get_aggregation_info()
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating aggregation config: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error updating aggregation config: {str(e)}'
        }), 500

@extensible_bp.route('/strategies/add', methods=['POST'])
def add_strategy():
    """Thêm strategy mới (ví dụ cho RSI)"""
    try:
        data = request.get_json()
        strategy_type = data.get('type')
        
        if strategy_type == 'rsi':
            from app.services.strategy_implementations import RSIStrategy
            from app.services.strategy_base import StrategyConfig
            
            config = StrategyConfig(
                name=data.get('name', 'RSI Strategy'),
                description=data.get('description', 'Custom RSI Strategy'),
                version=data.get('version', '1.0.0'),
                weight=data.get('weight', 0.8),
                min_confidence=data.get('min_confidence', 0.6),
                parameters={
                    'rsi_period': data.get('rsi_period', 14),
                    'overbought_level': data.get('overbought_level', 70),
                    'oversold_level': data.get('oversold_level', 30),
                    'strong_overbought': data.get('strong_overbought', 80),
                    'strong_oversold': data.get('strong_oversold', 20)
                }
            )
            
            strategy = RSIStrategy(config)
            success = extensible_signal_engine.add_strategy(strategy)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'data': {
                        'message': 'Strategy added successfully',
                        'strategy_info': strategy.get_strategy_info()
                    }
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to add strategy'
                }), 400
        
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unsupported strategy type: {strategy_type}'
            }), 400
        
    except Exception as e:
        logger.error(f"Error adding strategy: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error adding strategy: {str(e)}'
        }), 500

@extensible_bp.route('/strategies/<strategy_name>', methods=['DELETE'])
def remove_strategy(strategy_name):
    """Xóa strategy"""
    try:
        success = extensible_signal_engine.remove_strategy(strategy_name)
        
        if success:
            return jsonify({
                'status': 'success',
                'data': {
                    'message': f'Strategy {strategy_name} removed successfully'
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Strategy not found or failed to remove'
            }), 404
        
    except Exception as e:
        logger.error(f"Error removing strategy: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error removing strategy: {str(e)}'
        }), 500

@extensible_bp.route('/test', methods=['POST'])
def test_extensible_system():
    """Test hệ thống extensible với dữ liệu mẫu"""
    try:
        data = request.get_json()
        symbol_id = data.get('symbol_id', 1)
        timeframe = data.get('timeframe', '5m')
        strategies = data.get('strategies', ['SMA Strategy', 'MACD Strategy'])
        
        # Lấy thông tin symbol
        with SessionLocal() as s:
            symbol_row = s.execute(text("""
                SELECT ticker, exchange FROM symbols WHERE id = :symbol_id
            """), {'symbol_id': symbol_id}).first()
            
            if not symbol_row:
                return jsonify({
                    'status': 'error',
                    'message': 'Symbol not found'
                }), 404
            
            ticker = symbol_row.ticker
            exchange = symbol_row.exchange
        
        # Test single timeframe
        single_result = extensible_signal_engine.evaluate_signal(
            symbol_id, ticker, exchange, timeframe, strategies
        )
        
        # Test multi-timeframe
        multi_result = extensible_signal_engine.evaluate_multi_timeframe(
            symbol_id, ticker, exchange, strategies
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'single_timeframe': single_result,
                'multi_timeframe': multi_result,
                'available_strategies': extensible_signal_engine.get_available_strategies(),
                'aggregation_config': extensible_signal_engine.get_aggregation_info()
            }
        })
        
    except Exception as e:
        logger.error(f"Error testing extensible system: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error testing system: {str(e)}'
        }), 500
