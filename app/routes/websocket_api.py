"""
WebSocket API for Real-time Chart Data
Handles WebSocket connections for live market data when market is open
"""

from flask import Blueprint, request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from datetime import datetime, timedelta
import random
import json
import threading
import time
from app.models import Symbol, Candle1m, CandleTF, TFEnum
from app import db

websocket_api_bp = Blueprint('websocket_api', __name__)

# Global variables for WebSocket management
active_connections = {}
market_data_threads = {}
is_market_open = False

# ==============================================
# WEBSOCKET EVENTS
# ==============================================

def register_websocket_events(socketio):
    """Register all WebSocket events"""
    
    @socketio.on('connect', namespace='/chart')
    def handle_connect():
        """Handle client connection"""
        print(f"Client connected: {request.sid}")
        
        # Check if market is open
        market_status = check_market_status()
        
        if market_status['is_open']:
            # Add to active connections
            active_connections[request.sid] = {
                'connected_at': datetime.now(),
                'subscribed_symbols': set(),
                'subscribed_intervals': set()
            }
            
            emit('connection_status', {
                'status': 'connected',
                'market_open': True,
                'message': 'Connected to real-time data feed'
            })
        else:
            emit('connection_status', {
                'status': 'connected',
                'market_open': False,
                'message': 'Connected but market is closed. Historical data only.',
                'next_open': market_status['next_open']
            })
    
    @socketio.on('disconnect', namespace='/chart')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"Client disconnected: {request.sid}")
        
        if request.sid in active_connections:
            # Clean up subscriptions
            del active_connections[request.sid]
    
    @socketio.on('subscribe_symbol', namespace='/chart')
    def handle_subscribe_symbol(data):
        """Subscribe to real-time data for a symbol"""
        try:
            symbol = data.get('symbol')
            interval = data.get('interval', '1h')
            
            if not symbol:
                emit('error', {'message': 'Symbol is required'})
                return
            
            # Validate symbol exists
            symbol_obj = Symbol.query.filter_by(ticker=symbol).first()
            if not symbol_obj:
                emit('error', {'message': f'Symbol {symbol} not found'})
                return
            
            # Add to user's subscriptions
            if request.sid in active_connections:
                active_connections[request.sid]['subscribed_symbols'].add(symbol)
                active_connections[request.sid]['subscribed_intervals'].add(interval)
                
                # Join room for this symbol
                room_name = f"{symbol}_{interval}"
                join_room(room_name)
                
                emit('subscription_confirmed', {
                    'symbol': symbol,
                    'interval': interval,
                    'message': f'Subscribed to {symbol} {interval} data'
                })
                
                # Send latest candle immediately
                latest_candle = get_latest_candle_data(symbol, interval)
                if latest_candle:
                    emit('candle_update', latest_candle)
            
        except Exception as e:
            emit('error', {'message': str(e)})
    
    @socketio.on('unsubscribe_symbol', namespace='/chart')
    def handle_unsubscribe_symbol(data):
        """Unsubscribe from symbol data"""
        try:
            symbol = data.get('symbol')
            interval = data.get('interval', '1h')
            
            if request.sid in active_connections:
                active_connections[request.sid]['subscribed_symbols'].discard(symbol)
                active_connections[request.sid]['subscribed_intervals'].discard(interval)
                
                # Leave room
                room_name = f"{symbol}_{interval}"
                leave_room(room_name)
                
                emit('unsubscription_confirmed', {
                    'symbol': symbol,
                    'interval': interval,
                    'message': f'Unsubscribed from {symbol} {interval} data'
                })
        
        except Exception as e:
            emit('error', {'message': str(e)})
    
    @socketio.on('get_market_status', namespace='/chart')
    def handle_get_market_status():
        """Get current market status"""
        market_status = check_market_status()
        emit('market_status', market_status)
    
    @socketio.on('request_historical_data', namespace='/chart')
    def handle_request_historical_data(data):
        """Request historical data for a symbol"""
        try:
            symbol = data.get('symbol')
            interval = data.get('interval', '1h')
            limit = data.get('limit', 100)
            
            if not symbol:
                emit('error', {'message': 'Symbol is required'})
                return
            
            # Get historical data
            historical_data = get_historical_data(symbol, interval, limit)
            emit('historical_data', {
                'symbol': symbol,
                'interval': interval,
                'data': historical_data
            })
        
        except Exception as e:
            emit('error', {'message': str(e)})

# ==============================================
# MARKET DATA SIMULATION
# ==============================================

def start_market_data_simulation(socketio):
    """Start market data simulation thread"""
    def market_data_worker():
        global is_market_open
        
        while True:
            try:
                # Check market status
                market_status = check_market_status()
                is_market_open = market_status['is_open']
                
                if is_market_open and active_connections:
                    # Generate and broadcast market data
                    broadcast_market_data(socketio)
                
                # Sleep for 1 second
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in market data worker: {e}")
                time.sleep(5)
    
    # Start the thread
    thread = threading.Thread(target=market_data_worker, daemon=True)
    thread.start()
    print("Market data simulation started")

def broadcast_market_data(socketio):
    """Broadcast market data to all connected clients"""
    try:
        # Get all active symbols
        all_symbols = set()
        for connection in active_connections.values():
            all_symbols.update(connection['subscribed_symbols'])
        
        # Generate data for each symbol
        for symbol in all_symbols:
            # Get all intervals for this symbol
            all_intervals = set()
            for connection in active_connections.values():
                if symbol in connection['subscribed_symbols']:
                    all_intervals.update(connection['subscribed_intervals'])
            
            for interval in all_intervals:
                # Generate new candle data
                new_candle = generate_realtime_candle(symbol, interval)
                
                if new_candle:
                    # Broadcast to room
                    room_name = f"{symbol}_{interval}"
                    socketio.emit('candle_update', new_candle, room=room_name, namespace='/chart')
    
    except Exception as e:
        print(f"Error broadcasting market data: {e}")

def generate_realtime_candle(symbol, interval):
    """Generate real-time candle data"""
    try:
        # Get latest candle from database
        symbol_obj = Symbol.query.filter_by(ticker=symbol).first()
        if not symbol_obj:
            return None
        
        # Get latest candle based on interval
        if interval == '1m':
            latest_candle = Candle1m.query.filter_by(
                symbol_id=symbol_obj.id
            ).order_by(Candle1m.ts.desc()).first()
        else:
            tf_enum = convert_interval_to_tf_enum(interval)
            latest_candle = CandleTF.query.filter_by(
                symbol_id=symbol_obj.id,
                timeframe=tf_enum
            ).order_by(CandleTF.ts.desc()).first()
        
        if latest_candle:
            # Update existing candle with new data
            base_price = float(latest_candle.close)
        else:
            # Create new candle
            base_price = 100.0 + hash(symbol) % 1000
        
        # Generate new OHLCV data
        price_change = random.uniform(-0.02, 0.02)  # ±2% change
        new_price = base_price * (1 + price_change)
        
        # Simulate realistic OHLCV
        open_price = base_price
        close_price = new_price
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
        volume = random.uniform(1000, 10000)
        
        # Create candle data
        candle_data = {
            'symbol': symbol,
            'interval': interval,
            'time': int(datetime.now().timestamp()),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': round(volume, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to database (optional)
        save_candle_to_database(symbol_obj.id, interval, candle_data)
        
        return candle_data
        
    except Exception as e:
        print(f"Error generating realtime candle: {e}")
        return None

def convert_interval_to_tf_enum(interval):
    """Convert interval string to TFEnum"""
    interval_map = {
        '1m': TFEnum.m1,
        '2m': TFEnum.m2,
        '5m': TFEnum.m5,
        '15m': TFEnum.m15,
        '30m': TFEnum.m30,
        '1h': TFEnum.h1,
        '4h': TFEnum.h4,
        '1d': TFEnum.d1
    }
    return interval_map.get(interval, TFEnum.h1)

def save_candle_to_database(symbol_id, interval, candle_data):
    """Save candle data to database"""
    try:
        # Check if candle already exists for this timestamp
        timestamp = datetime.fromtimestamp(candle_data['time'])
        
        if interval == '1m':
            existing_candle = Candle1m.query.filter_by(
                symbol_id=symbol_id,
                ts=timestamp
            ).first()
        else:
            tf_enum = convert_interval_to_tf_enum(interval)
            existing_candle = CandleTF.query.filter_by(
                symbol_id=symbol_id,
                timeframe=tf_enum,
                ts=timestamp
            ).first()
        
        if existing_candle:
            # Update existing candle
            existing_candle.open = candle_data['open']
            existing_candle.high = candle_data['high']
            existing_candle.low = candle_data['low']
            existing_candle.close = candle_data['close']
            existing_candle.volume = candle_data['volume']
        else:
            # Create new candle
            if interval == '1m':
                new_candle = Candle1m(
                    symbol_id=symbol_id,
                    ts=timestamp,
                    open=candle_data['open'],
                    high=candle_data['high'],
                    low=candle_data['low'],
                    close=candle_data['close'],
                    volume=candle_data['volume']
                )
            else:
                tf_enum = convert_interval_to_tf_enum(interval)
                new_candle = CandleTF(
                    symbol_id=symbol_id,
                    timeframe=tf_enum,
                    ts=timestamp,
                    open=candle_data['open'],
                    high=candle_data['high'],
                    low=candle_data['low'],
                    close=candle_data['close'],
                    volume=candle_data['volume']
                )
            db.session.add(new_candle)
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error saving candle to database: {e}")
        db.session.rollback()

# ==============================================
# HELPER FUNCTIONS
# ==============================================

def check_market_status():
    """Check if market is currently open"""
    now = datetime.now()
    weekday = now.weekday()  # 0 = Monday, 6 = Sunday
    hour = now.hour
    minute = now.minute
    
    # Check if it's a weekday
    if weekday >= 5:  # Saturday or Sunday
        is_open = False
        next_open = now + timedelta(days=7 - weekday)
        next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
    else:
        # Check if it's within market hours (9:30 AM - 4:00 PM)
        market_open = (hour > 9) or (hour == 9 and minute >= 30)
        market_close = hour < 16
        
        is_open = market_open and market_close
        
        if is_open:
            next_open = now + timedelta(days=1)
            next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
        else:
            if hour < 9 or (hour == 9 and minute < 30):
                # Before market open today
                next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            else:
                # After market close today
                next_open = now + timedelta(days=1)
                next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
    
    return {
        'is_open': is_open,
        'status': 'OPEN' if is_open else 'CLOSED',
        'next_open': next_open.isoformat(),
        'timestamp': now.isoformat()
    }

def get_latest_candle_data(symbol, interval):
    """Get latest candle data for a symbol"""
    try:
        symbol_obj = Symbol.query.filter_by(ticker=symbol).first()
        if not symbol_obj:
            return None
        
        # Get latest candle based on interval
        if interval == '1m':
            latest_candle = Candle1m.query.filter_by(
                symbol_id=symbol_obj.id
            ).order_by(Candle1m.ts.desc()).first()
        else:
            tf_enum = convert_interval_to_tf_enum(interval)
            latest_candle = CandleTF.query.filter_by(
                symbol_id=symbol_obj.id,
                timeframe=tf_enum
            ).order_by(CandleTF.ts.desc()).first()
        
        if latest_candle:
            return {
                'symbol': symbol,
                'interval': interval,
                'time': int(latest_candle.ts.timestamp()),
                'open': float(latest_candle.open),
                'high': float(latest_candle.high),
                'low': float(latest_candle.low),
                'close': float(latest_candle.close),
                'volume': float(latest_candle.volume) if latest_candle.volume else 0,
                'timestamp': latest_candle.ts.isoformat()
            }
        
        return None
        
    except Exception as e:
        print(f"Error getting latest candle data: {e}")
        return None

def get_historical_data(symbol, interval, limit=100):
    """Get historical data for a symbol"""
    try:
        symbol_obj = Symbol.query.filter_by(ticker=symbol).first()
        if not symbol_obj:
            return []
        
        # Get candles based on interval
        if interval == '1m':
            candles = Candle1m.query.filter_by(
                symbol_id=symbol_obj.id
            ).order_by(Candle1m.ts.desc()).limit(limit).all()
        else:
            tf_enum = convert_interval_to_tf_enum(interval)
            candles = CandleTF.query.filter_by(
                symbol_id=symbol_obj.id,
                timeframe=tf_enum
            ).order_by(CandleTF.ts.desc()).limit(limit).all()
        
        historical_data = []
        for candle in reversed(candles):
            historical_data.append({
                'time': int(candle.ts.timestamp()),
                'open': float(candle.open),
                'high': float(candle.high),
                'low': float(candle.low),
                'close': float(candle.close),
                'volume': float(candle.volume) if candle.volume else 0
            })
        
        return historical_data
        
    except Exception as e:
        print(f"Error getting historical data: {e}")
        return []

def get_connection_stats():
    """Get WebSocket connection statistics"""
    return {
        'active_connections': len(active_connections),
        'market_open': is_market_open,
        'connections': [
            {
                'sid': sid,
                'connected_at': conn['connected_at'].isoformat(),
                'subscribed_symbols': list(conn['subscribed_symbols']),
                'subscribed_intervals': list(conn['subscribed_intervals'])
            }
            for sid, conn in active_connections.items()
        ]
    }
