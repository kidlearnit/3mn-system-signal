#!/usr/bin/env python3
"""
Hybrid API endpoints for SMA + MACD combined strategy
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app.db import SessionLocal
from app.services.hybrid_signal_engine import hybrid_signal_engine
import logging

logger = logging.getLogger(__name__)

hybrid_bp = Blueprint('hybrid', __name__, url_prefix='/api/hybrid')

@hybrid_bp.route('/signals', methods=['GET'])
def get_hybrid_signals():
    """Lấy danh sách hybrid signals"""
    try:
        symbol_id = request.args.get('symbol_id', type=int)
        timeframe = request.args.get('timeframe')
        limit = request.args.get('limit', 50, type=int)
        
        with SessionLocal() as s:
            query = """
                SELECT h.id, h.symbol_id, h.timeframe, h.timestamp, h.hybrid_signal, 
                       h.hybrid_direction, h.hybrid_strength, h.confidence,
                       h.sma_signal, h.macd_signal, h.details,
                       s.ticker, s.exchange
                FROM hybrid_signals h
                JOIN symbols s ON h.symbol_id = s.id
                WHERE 1=1
            """
            params = {}
            
            if symbol_id:
                query += " AND h.symbol_id = :symbol_id"
                params['symbol_id'] = symbol_id
            
            if timeframe:
                query += " AND h.timeframe = :timeframe"
                params['timeframe'] = timeframe
            
            query += " ORDER BY h.timestamp DESC LIMIT :limit"
            params['limit'] = limit
            
            result = s.execute(text(query), params)
            signals = []
            
            for row in result:
                signals.append({
                    'id': row.id,
                    'symbol_id': row.symbol_id,
                    'ticker': row.ticker,
                    'exchange': row.exchange,
                    'timeframe': row.timeframe,
                    'timestamp': row.timestamp.isoformat(),
                    'hybrid_signal': row.hybrid_signal,
                    'hybrid_direction': row.hybrid_direction,
                    'hybrid_strength': float(row.hybrid_strength),
                    'confidence': float(row.confidence),
                    'sma_signal': row.sma_signal,
                    'macd_signal': row.macd_signal,
                    'details': row.details
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'signals': signals,
                    'total': len(signals)
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting hybrid signals: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching hybrid signals: {str(e)}'
        }), 500

@hybrid_bp.route('/signals/<int:symbol_id>', methods=['GET'])
def get_symbol_hybrid_signals(symbol_id):
    """Lấy hybrid signals cho một symbol cụ thể"""
    try:
        timeframe = request.args.get('timeframe')
        limit = request.args.get('limit', 100, type=int)
        
        with SessionLocal() as s:
            query = """
                SELECT h.id, h.timeframe, h.timestamp, h.hybrid_signal, 
                       h.hybrid_direction, h.hybrid_strength, h.confidence,
                       h.sma_signal, h.macd_signal, h.details
                FROM hybrid_signals h
                WHERE h.symbol_id = :symbol_id
            """
            params = {'symbol_id': symbol_id}
            
            if timeframe:
                query += " AND h.timeframe = :timeframe"
                params['timeframe'] = timeframe
            
            query += " ORDER BY h.timestamp DESC LIMIT :limit"
            params['limit'] = limit
            
            result = s.execute(text(query), params)
            signals = []
            
            for row in result:
                signals.append({
                    'id': row.id,
                    'timeframe': row.timeframe,
                    'timestamp': row.timestamp.isoformat(),
                    'hybrid_signal': row.hybrid_signal,
                    'hybrid_direction': row.hybrid_direction,
                    'hybrid_strength': float(row.hybrid_strength),
                    'confidence': float(row.confidence),
                    'sma_signal': row.sma_signal,
                    'macd_signal': row.macd_signal,
                    'details': row.details
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'symbol_id': symbol_id,
                    'signals': signals,
                    'total': len(signals)
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting symbol hybrid signals: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching symbol hybrid signals: {str(e)}'
        }), 500

@hybrid_bp.route('/evaluate/<int:symbol_id>', methods=['POST'])
def evaluate_hybrid_signal(symbol_id):
    """Đánh giá tín hiệu hybrid cho symbol"""
    try:
        data = request.get_json()
        timeframe = data.get('timeframe', '5m')
        
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
        
        # Đánh giá tín hiệu hybrid
        result = hybrid_signal_engine.evaluate_hybrid_signal(
            symbol_id, ticker, exchange, timeframe
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error evaluating hybrid signal: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error evaluating hybrid signal: {str(e)}'
        }), 500

@hybrid_bp.route('/multi-timeframe/<int:symbol_id>', methods=['POST'])
def evaluate_multi_timeframe_hybrid(symbol_id):
    """Đánh giá tín hiệu hybrid multi-timeframe"""
    try:
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
        
        # Đánh giá tín hiệu hybrid multi-timeframe
        result = hybrid_signal_engine.evaluate_multi_timeframe_hybrid(
            symbol_id, ticker, exchange
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error evaluating multi-timeframe hybrid signal: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error evaluating multi-timeframe hybrid signal: {str(e)}'
        }), 500

@hybrid_bp.route('/stats', methods=['GET'])
def get_hybrid_stats():
    """Lấy thống kê hybrid signals"""
    try:
        with SessionLocal() as s:
            # Thống kê tổng quan
            stats_query = """
                SELECT 
                    COUNT(*) as total_signals,
                    COUNT(DISTINCT symbol_id) as total_symbols,
                    COUNT(DISTINCT timeframe) as total_timeframes,
                    AVG(confidence) as avg_confidence,
                    AVG(hybrid_strength) as avg_strength
                FROM hybrid_signals
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            
            stats_result = s.execute(text(stats_query)).first()
            
            # Thống kê theo direction
            direction_query = """
                SELECT 
                    hybrid_direction,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence,
                    AVG(hybrid_strength) as avg_strength
                FROM hybrid_signals
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY hybrid_direction
                ORDER BY count DESC
            """
            
            direction_result = s.execute(text(direction_query))
            direction_stats = []
            
            for row in direction_result:
                direction_stats.append({
                    'direction': row.hybrid_direction,
                    'count': row.count,
                    'avg_confidence': float(row.avg_confidence),
                    'avg_strength': float(row.avg_strength)
                })
            
            # Thống kê theo timeframe
            timeframe_query = """
                SELECT 
                    timeframe,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM hybrid_signals
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY timeframe
                ORDER BY count DESC
            """
            
            timeframe_result = s.execute(text(timeframe_query))
            timeframe_stats = []
            
            for row in timeframe_result:
                timeframe_stats.append({
                    'timeframe': row.timeframe,
                    'count': row.count,
                    'avg_confidence': float(row.avg_confidence)
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'overview': {
                        'total_signals': stats_result.total_signals,
                        'total_symbols': stats_result.total_symbols,
                        'total_timeframes': stats_result.total_timeframes,
                        'avg_confidence': float(stats_result.avg_confidence),
                        'avg_strength': float(stats_result.avg_strength)
                    },
                    'by_direction': direction_stats,
                    'by_timeframe': timeframe_stats
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting hybrid stats: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching hybrid stats: {str(e)}'
        }), 500

@hybrid_bp.route('/performance', methods=['GET'])
def get_hybrid_performance():
    """Lấy hiệu suất của hybrid strategy"""
    try:
        symbol_id = request.args.get('symbol_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        with SessionLocal() as s:
            # Query để tính hiệu suất
            query = """
                SELECT 
                    h.timeframe,
                    h.hybrid_direction,
                    COUNT(*) as signal_count,
                    AVG(h.confidence) as avg_confidence,
                    AVG(h.hybrid_strength) as avg_strength,
                    SUM(CASE WHEN h.hybrid_direction = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
                    SUM(CASE WHEN h.hybrid_direction = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
                    SUM(CASE WHEN h.hybrid_direction = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral_signals
                FROM hybrid_signals h
                WHERE h.timestamp >= DATE_SUB(NOW(), INTERVAL :days DAY)
            """
            params = {'days': days}
            
            if symbol_id:
                query += " AND h.symbol_id = :symbol_id"
                params['symbol_id'] = symbol_id
            
            query += """
                GROUP BY h.timeframe, h.hybrid_direction
                ORDER BY h.timeframe, h.hybrid_direction
            """
            
            result = s.execute(text(query), params)
            performance_data = []
            
            for row in result:
                performance_data.append({
                    'timeframe': row.timeframe,
                    'direction': row.hybrid_direction,
                    'signal_count': row.signal_count,
                    'avg_confidence': float(row.avg_confidence),
                    'avg_strength': float(row.avg_strength),
                    'buy_signals': row.buy_signals,
                    'sell_signals': row.sell_signals,
                    'neutral_signals': row.neutral_signals
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'period_days': days,
                    'symbol_id': symbol_id,
                    'performance': performance_data
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting hybrid performance: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching hybrid performance: {str(e)}'
        }), 500
