"""
WebSocket service for real-time data streaming
"""
import json
import redis
from flask_socketio import SocketIO, emit, join_room, leave_room
from app.db import SessionLocal
from sqlalchemy import text
import os

# Redis connection for pub/sub
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'))

class WebSocketService:
    def __init__(self, socketio):
        self.socketio = socketio
        self.setup_handlers()
        self.setup_redis_subscriber()
    
    def setup_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            emit('connected', {'message': 'Connected to real-time data stream'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('join_symbol')
        def handle_join_symbol(data):
            """Join a symbol room for real-time chart updates"""
            symbol = data.get('symbol')
            if symbol:
                room = f"symbol_{symbol}"
                join_room(room)
                print(f"Client {request.sid} joined chart room: {room}")
                
                # Send initial chart data from database
                initial_data = self.get_initial_chart_data(symbol)
                emit('symbol_data', initial_data, room=room)
        
        @self.socketio.on('leave_symbol')
        def handle_leave_symbol(data):
            """Leave a symbol room"""
            symbol = data.get('symbol')
            if symbol:
                room = f"symbol_{symbol}"
                leave_room(room)
                print(f"Client {request.sid} left room: {room}")
        
        @self.socketio.on('join_signals')
        def handle_join_signals():
            """Join signals room for real-time signal updates"""
            join_room('signals')
            print(f"Client {request.sid} joined signals room")
            
            # Send recent signals
            recent_signals = self.get_recent_signals()
            emit('signals_update', recent_signals, room='signals')
        
        @self.socketio.on('leave_signals')
        def handle_leave_signals():
            """Leave signals room"""
            leave_room('signals')
            print(f"Client {request.sid} left signals room")
    
    def get_initial_chart_data(self, symbol):
        """Get initial chart data from database for WebSocket clients"""
        try:
            with SessionLocal() as s:
                # Get symbol info
                symbol_info = s.execute(text("""
                    SELECT id, ticker, exchange FROM symbols WHERE ticker = :symbol
                """), {'symbol': symbol}).fetchone()
                
                if not symbol_info:
                    return {'error': 'Symbol not found'}
                
                symbol_id = symbol_info[0]
                
                # Get latest candle data
                latest_candle = s.execute(text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_1m
                    WHERE symbol_id = :symbol_id
                    ORDER BY ts DESC
                    LIMIT 1
                """), {'symbol_id': symbol_id}).fetchone()
                
                if not latest_candle:
                    return {'error': 'No data available'}
                
                ts, open_price, high, low, close, volume = latest_candle
                
                # Get recent candles for chart (last 1000 candles)
                recent_candles = s.execute(text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_1m
                    WHERE symbol_id = :symbol_id
                    ORDER BY ts DESC
                    LIMIT 1000
                """), {'symbol_id': symbol_id}).fetchall()
                
                candles_data = []
                volumes_data = []
                
                for candle in recent_candles:
                    ts, open_price, high, low, close, volume = candle
                    candles_data.append({
                        'time': int(ts.timestamp()),
                        'open': float(open_price),
                        'high': float(high),
                        'low': float(low),
                        'close': float(close)
                    })
                    volumes_data.append({
                        'time': int(ts.timestamp()),
                        'value': float(volume)
                    })
                
                # Get MACD data for chart
                macd_data = []
                macd_candles = s.execute(text("""
                    SELECT ts, macd, macd_signal, hist
                    FROM indicators_macd
                    WHERE symbol_id = :symbol_id AND timeframe = '1m'
                    ORDER BY ts DESC
                    LIMIT 1000
                """), {'symbol_id': symbol_id}).fetchall()
                
                for macd in macd_candles:
                    ts, macd_val, signal_val, hist_val = macd
                    macd_data.append({
                        'time': int(ts.timestamp()),
                        'macd': float(macd_val) if macd_val else 0,
                        'signal': float(signal_val) if signal_val else 0,
                        'histogram': float(hist_val) if hist_val else 0
                    })
                
                return {
                    'symbol': symbol,
                    'symbol_id': symbol_id,
                    'candles': candles_data,
                    'volumes': volumes_data,
                    'macd': macd_data
                }
                
        except Exception as e:
            print(f"Error getting initial chart data for {symbol}: {e}")
            return {'error': str(e)}

    def get_initial_symbol_data(self, symbol):
        """Get initial symbol data from database"""
        try:
            with SessionLocal() as s:
                # Get symbol info
                symbol_info = s.execute(text("""
                    SELECT id, ticker, exchange FROM symbols WHERE ticker = :symbol
                """), {'symbol': symbol}).fetchone()
                
                if not symbol_info:
                    return {'error': 'Symbol not found'}
                
                symbol_id = symbol_info[0]
                
                # Get latest candle data
                latest_candle = s.execute(text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_1m
                    WHERE symbol_id = :symbol_id
                    ORDER BY ts DESC
                    LIMIT 1
                """), {'symbol_id': symbol_id}).fetchone()
                
                if not latest_candle:
                    return {'error': 'No data available'}
                
                ts, open_price, high, low, close, volume = latest_candle
                
                # Get recent candles for chart
                recent_candles = s.execute(text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_1m
                    WHERE symbol_id = :symbol_id
                    ORDER BY ts DESC
                    LIMIT 100
                """), {'symbol_id': symbol_id}).fetchall()
                
                candles_data = []
                volumes_data = []
                
                for candle in recent_candles:
                    ts, open_price, high, low, close, volume = candle
                    candles_data.append({
                        'time': int(ts.timestamp()),
                        'open': float(open_price),
                        'high': float(high),
                        'low': float(low),
                        'close': float(close)
                    })
                    volumes_data.append({
                        'time': int(ts.timestamp()),
                        'value': float(volume)
                    })
                
                # Get recent signals for this symbol
                recent_signals = s.execute(text("""
                    SELECT s.id, s.signal_type, s.created_at, s.price, s.volume,
                           st.name as strategy_name
                    FROM signals s
                    JOIN strategies st ON s.strategy_id = st.id
                    WHERE s.symbol_id = :symbol_id
                    ORDER BY s.created_at DESC
                    LIMIT 10
                """), {'symbol_id': symbol_id}).fetchall()
                
                signals_data = []
                for signal in recent_signals:
                    signals_data.append({
                        'id': signal[0],
                        'signal_type': signal[1],
                        'created_at': signal[2].isoformat() if signal[2] else None,
                        'price': float(signal[3]) if signal[3] else None,
                        'volume': float(signal[4]) if signal[4] else None,
                        'strategy_name': signal[5]
                    })
                
                return {
                    'symbol': symbol,
                    'symbol_id': symbol_id,
                    'latest_candle': {
                        'time': int(ts.timestamp()),
                        'open': float(open_price),
                        'high': float(high),
                        'low': float(low),
                        'close': float(close),
                        'volume': float(volume)
                    },
                    'candles': candles_data,
                    'volumes': volumes_data,
                    'recent_signals': signals_data
                }
                
        except Exception as e:
            print(f"Error getting initial data for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_recent_signals(self, limit=20):
        """Get recent signals from database"""
        try:
            with SessionLocal() as s:
                signals = s.execute(text("""
                    SELECT s.id, s.signal_type, s.created_at, s.price, s.volume,
                           st.name as strategy_name, sy.ticker, sy.exchange
                    FROM signals s
                    JOIN strategies st ON s.strategy_id = st.id
                    JOIN symbols sy ON s.symbol_id = sy.id
                    ORDER BY s.created_at DESC
                    LIMIT :limit
                """), {'limit': limit}).fetchall()
                
                signals_data = []
                for signal in signals:
                    signals_data.append({
                        'id': signal[0],
                        'signal_type': signal[1],
                        'created_at': signal[2].isoformat() if signal[2] else None,
                        'price': float(signal[3]) if signal[3] else None,
                        'volume': float(signal[4]) if signal[4] else None,
                        'strategy_name': signal[5],
                        'ticker': signal[6],
                        'exchange': signal[7]
                    })
                
                return signals_data
                
        except Exception as e:
            print(f"Error getting recent signals: {e}")
            return []
    
    def setup_redis_subscriber(self):
        """Setup Redis subscriber for real-time updates"""
        import threading
        
        def redis_subscriber():
            pubsub = redis_client.pubsub()
            pubsub.subscribe('realtime_updates')
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        self.handle_realtime_update(data)
                    except Exception as e:
                        print(f"Error processing Redis message: {e}")
        
        # Start Redis subscriber in background thread
        thread = threading.Thread(target=redis_subscriber, daemon=True)
        thread.start()
    
    def handle_realtime_update(self, data):
        """Handle real-time update from Redis"""
        update_type = data.get('type')
        
        if update_type == 'symbol_data':
            symbol = data.get('symbol')
            if symbol:
                room = f"symbol_{symbol}"
                self.socketio.emit('symbol_update', data, room=room)
        
        elif update_type == 'new_signal':
            self.socketio.emit('new_signal', data, room='signals')
        
        elif update_type == 'system_status':
            self.socketio.emit('system_status_update', data)
    
    def broadcast_symbol_update(self, symbol, data):
        """Broadcast symbol update to all clients in the symbol room"""
        room = f"symbol_{symbol}"
        self.socketio.emit('symbol_update', data, room=room)
    
    def broadcast_new_signal(self, signal_data):
        """Broadcast new signal to all clients in signals room"""
        self.socketio.emit('new_signal', signal_data, room='signals')
    
    def broadcast_system_status(self, status_data):
        """Broadcast system status update"""
        self.socketio.emit('system_status_update', status_data)

# Global WebSocket service instance
websocket_service = None

def init_websocket_service(socketio):
    """Initialize WebSocket service"""
    global websocket_service
    websocket_service = WebSocketService(socketio)
    return websocket_service

def get_websocket_service():
    """Get WebSocket service instance"""
    return websocket_service
