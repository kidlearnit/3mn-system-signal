"""
Real Data API Routes
API endpoints để lấy dữ liệu thật từ database cho charts và monitoring
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import text
import json
from datetime import datetime, timedelta
import random
import time

# Optional heavy deps imported lazily in YF path

real_data_bp = Blueprint('real_data', __name__)

# Simple in-memory cache for realtime YF to avoid hammering
_yf_cache = {}
_YF_TTL_SECONDS = 60

# ==============================================
# REAL CANDLE DATA
# ==============================================

@real_data_bp.route('/api/real/candles', methods=['GET'])
def get_real_candles():
    """Lấy dữ liệu nến thật từ database hoặc Yahoo Finance (source=yf)"""
    try:
        symbol = request.args.get('symbol', 'AAPL')
        timeframe = request.args.get('timeframe', '5m')
        limit = int(request.args.get('limit', 100))
        source = request.args.get('source', 'db')
        historical_days = int(request.args.get('historical_days', 365))  # Default 1 year

        # Fast path: Yahoo Finance realtime with 5s cache
        if source == 'yf':
            return _get_candles_from_yf(symbol, timeframe, limit)
        
        # Hybrid path: Historical from DB + Realtime from YF
        if source == 'hybrid':
            return _get_hybrid_candles(symbol, timeframe, limit, historical_days)
        
        # Kết nối database
        from app.db import SessionLocal
        session = SessionLocal()
        
        try:
            # Tìm symbol_id
            symbol_result = session.execute(text("""
                SELECT id FROM symbols WHERE ticker = :symbol LIMIT 1
            """), {'symbol': symbol}).fetchone()
            
            if not symbol_result:
                return jsonify({
                    'status': 'error',
                    'message': f'Symbol {symbol} not found'
                }), 404
            
            symbol_id = symbol_result[0]
            
            # Lấy dữ liệu candles từ database với giới hạn thời gian
            query = text("""
                SELECT ts, open, high, low, close, volume
                FROM candles_tf 
                WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                AND ts >= DATE_SUB(NOW(), INTERVAL :historical_days DAY)
                ORDER BY ts DESC 
                LIMIT :limit
            """)
            
            result = session.execute(query, {
                'symbol_id': symbol_id,
                'timeframe': timeframe,
                'limit': limit,
                'historical_days': historical_days
            }).fetchall()
            
            if not result:
                return jsonify({
                    'status': 'error',
                    'message': f'No data found for {symbol} {timeframe} in last {historical_days} days'
                }), 404
            
            # Chuyển đổi dữ liệu
            candles = []
            for row in result:
                candles.append({
                    'timestamp': row.ts.isoformat(),
                    'open': float(row.open),
                    'high': float(row.high),
                    'low': float(row.low),
                    'close': float(row.close),
                    'volume': float(row.volume) if row.volume else 0
                })
            
            # Reverse để có thứ tự thời gian tăng dần
            candles.reverse()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'candles': candles,
                    'count': len(candles),
                    'note': 'Real data from database'
                }
            })
            
        finally:
            session.close()
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching candles: {str(e)}'
        }), 500


def _get_candles_from_yf(symbol: str, timeframe: str, limit: int):
    """Fetch recent candles from Yahoo Finance and resample to timeframe.
    - Uses 5-second in-memory cache per (symbol,timeframe,limit)
    - Supports minute-based timeframes like 1m,2m,5m,15m,30m,60m
    """
    try:
        key = (symbol.upper(), timeframe, int(limit))
        now = time.time()
        cached = _yf_cache.get(key)
        if cached and (now - cached['ts'] < _YF_TTL_SECONDS):
            return jsonify(cached['resp'])

        # Lazy imports
        import pandas as pd
        from app.services.data_sources import get_realtime_df_1m

        # Fetch recent 1m data (last ~max minutes we might need)
        # Heuristic: request up to 300 minutes to cover resampling windows
        base_minutes = max(120, min(600, limit * 2))
        df = get_realtime_df_1m(symbol, 'US', minutes=base_minutes)

        if df is None or df.empty:
            resp = {
                'status': 'error',
                'message': f'No YF data for {symbol}'
            }
            return jsonify(resp), 404

        # Ensure datetime index and expected columns
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)

        # Map timeframe to minutes
        tf_map = {
            '1m': '1min', '2m': '2min', '5m': '5min', '10m': '10min', '15m': '15min',
            '30m': '30min', '60m': '60min', '1h': '60min'
        }
        if timeframe not in tf_map:
            # Fallback: use 5m if unsupported
            resample_rule = '5min'
        else:
            resample_rule = tf_map[timeframe]

        # Resample from 1m to requested timeframe
        def ohlc_agg(x: pd.Series):
            return pd.Series({
                'open': x.iloc[0],
                'high': x.max(),
                'low': x.min(),
                'close': x.iloc[-1]
            })

        ohlc = df['close'].resample(resample_rule).apply(lambda x: pd.Series({}))  # placeholder to ensure freq
        ohlc = df[['open','high','low','close']].resample(resample_rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()

        if 'volume' in df.columns:
            vol = df[['volume']].resample(resample_rule).sum().fillna(0)
            merged = ohlc.join(vol, how='left')
        else:
            merged = ohlc.copy()
            merged['volume'] = 0

        merged = merged.dropna()
        merged = merged.tail(limit)

        candles = []
        for ts, row in merged.iterrows():
            # ts is UTC; output ISO string
            candles.append({
                'timestamp': ts.to_pydatetime().replace(tzinfo=None).isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']) if pd.notna(row['volume']) else 0.0
            })

        resp = {
            'status': 'success',
            'data': {
                'symbol': symbol,
                'timeframe': timeframe,
                'candles': candles,
                'count': len(candles),
                'note': 'Realtime from Yahoo Finance with 60s cache'
            }
        }

        _yf_cache[key] = {'ts': now, 'resp': resp}
        return jsonify(resp)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'YF error: {str(e)}'
        }), 500


def _get_hybrid_candles(symbol: str, timeframe: str, limit: int, historical_days: int):
    """Kết hợp dữ liệu lịch sử từ database và realtime từ Yahoo Finance.
    - Lấy dữ liệu 1 năm từ database làm nền tảng
    - Cập nhật nến cuối cùng bằng dữ liệu realtime từ YF
    """
    try:
        # Lấy dữ liệu lịch sử từ database
        from app.db import SessionLocal
        session = SessionLocal()
        
        try:
            # Tìm symbol_id
            symbol_result = session.execute(text("""
                SELECT id FROM symbols WHERE ticker = :symbol LIMIT 1
            """), {'symbol': symbol}).fetchone()
            
            if not symbol_result:
                # Fallback to YF only if symbol not in DB
                return _get_candles_from_yf(symbol, timeframe, limit)
            
            symbol_id = symbol_result[0]
            
            # Lấy dữ liệu lịch sử từ database (1 năm)
            historical_query = text("""
                SELECT ts, open, high, low, close, volume
                FROM candles_tf 
                WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                AND ts >= DATE_SUB(NOW(), INTERVAL :historical_days DAY)
                ORDER BY ts DESC 
                LIMIT :limit
            """)
            
            historical_result = session.execute(historical_query, {
                'symbol_id': symbol_id,
                'timeframe': timeframe,
                'limit': limit,
                'historical_days': historical_days
            }).fetchall()
            
            historical_candles = []
            if historical_result:
                for row in historical_result:
                    historical_candles.append({
                        'timestamp': row.ts.isoformat(),
                        'open': float(row.open),
                        'high': float(row.high),
                        'low': float(row.low),
                        'close': float(row.close),
                        'volume': float(row.volume) if row.volume else 0
                    })
                # Reverse để có thứ tự thời gian tăng dần
                historical_candles.reverse()
            
        finally:
            session.close()
        
        # Lấy dữ liệu realtime từ YF để cập nhật nến cuối
        try:
            yf_data = _get_candles_from_yf(symbol, timeframe, 5)  # Lấy 5 nến gần nhất
            yf_response = yf_data.get_json()
            
            if yf_response and yf_response.get('status') == 'success':
                yf_candles = yf_response['data']['candles']
                
                if yf_candles and historical_candles:
                    # Merge: thay thế nến cuối cùng từ DB bằng nến mới nhất từ YF
                    last_historical_time = historical_candles[-1]['timestamp']
                    latest_yf_time = yf_candles[-1]['timestamp']
                    
                    # Nếu YF có dữ liệu mới hơn, cập nhật
                    if latest_yf_time > last_historical_time:
                        # Thay thế nến cuối cùng
                        historical_candles[-1] = yf_candles[-1]
                        
                        # Thêm các nến mới nếu có
                        for yf_candle in yf_candles:
                            if yf_candle['timestamp'] > last_historical_time:
                                # Kiểm tra xem đã có chưa
                                if not any(c['timestamp'] == yf_candle['timestamp'] for c in historical_candles):
                                    historical_candles.append(yf_candle)
                
                elif not historical_candles and yf_candles:
                    # Nếu không có dữ liệu lịch sử, dùng YF
                    historical_candles = yf_candles
                    
        except Exception as yf_error:
            print(f"YF update failed, using historical only: {yf_error}")
        
        # Trả về kết quả cuối cùng
        return jsonify({
            'status': 'success',
            'data': {
                'symbol': symbol,
                'timeframe': timeframe,
                'candles': historical_candles,
                'count': len(historical_candles),
                'note': f'Hybrid: {historical_days} days historical + YF realtime'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Hybrid error: {str(e)}'
        }), 500

# ==============================================
# REAL MACD DATA
# ==============================================

@real_data_bp.route('/api/real/macd', methods=['GET'])
def get_real_macd():
    """Lấy dữ liệu MACD từ database, hoặc hybrid (db + YF realtime)"""
    try:
        symbol = request.args.get('symbol', 'AAPL')
        timeframe = request.args.get('timeframe', '5m')
        limit = int(request.args.get('limit', 100))
        source = request.args.get('source', 'db')
        historical_days = int(request.args.get('historical_days', 365))

        if source == 'yf':
            return _get_macd_from_yf(symbol, timeframe, limit)
        if source == 'hybrid':
            return _get_macd_hybrid(symbol, timeframe, limit, historical_days)

        # Mặc định: lấy từ DB
        from app.db import SessionLocal
        session = SessionLocal()
        try:
            # Tìm symbol_id
            symbol_result = session.execute(text("""
                SELECT id FROM symbols WHERE ticker = :symbol LIMIT 1
            """), {'symbol': symbol}).fetchone()
            if not symbol_result:
                return jsonify({'status': 'error', 'message': f'Symbol {symbol} not found'}), 404

            symbol_id = symbol_result[0]

            query = text("""
                SELECT ts, macd, macd_signal, hist
                FROM indicators_macd 
                WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                AND ts >= DATE_SUB(NOW(), INTERVAL :historical_days DAY)
                ORDER BY ts DESC 
                LIMIT :limit
            """)
            result = session.execute(query, {
                'symbol_id': symbol_id,
                'timeframe': timeframe,
                'limit': limit,
                'historical_days': historical_days
            }).fetchall()

            if not result:
                return jsonify({'status': 'error', 'message': f'No MACD data found for {symbol} {timeframe}'}), 404

            macd_data = []
            for row in result:
                macd_data.append({
                    'timestamp': row.ts.isoformat(),
                    'macd': float(row.macd),
                    'macd_signal': float(row.macd_signal),
                    'histogram': float(row.hist)
                })
            macd_data.reverse()

            return jsonify({'status': 'success', 'data': {'symbol': symbol, 'timeframe': timeframe, 'macd': macd_data, 'count': len(macd_data), 'note': 'MACD from database'}})
        finally:
            session.close()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error fetching MACD: {str(e)}'}), 500


def _get_macd_from_yf(symbol: str, timeframe: str, limit: int):
    """Tính MACD từ giá YF (resample theo timeframe)"""
    try:
        import pandas as pd
        from app.services.data_sources import get_realtime_df_1m

        # Fetch 1m prices and resample
        base_minutes = max(180, min(1200, limit * 5))
        df = get_realtime_df_1m(symbol, 'US', minutes=base_minutes)
        if df is None or df.empty:
            return jsonify({'status': 'error', 'message': f'No YF data for {symbol}'}), 404

        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)

        tf_map = {
            '1m': '1min', '2m': '2min', '5m': '5min', '10m': '10min', '15m': '15min',
            '30m': '30min', '60m': '60min', '1h': '60min'
        }
        resample_rule = tf_map.get(timeframe, '5min')

        ohlc = df[['open','high','low','close']].resample(resample_rule).agg({
            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
        }).dropna()

        # Compute MACD (12,26,9) on close
        close = ohlc['close']
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        macd_df = pd.DataFrame({
            'macd': macd_line, 'macd_signal': signal_line, 'histogram': histogram
        }).dropna().tail(limit)

        macd = []
        for ts, row in macd_df.iterrows():
            macd.append({
                'timestamp': ts.to_pydatetime().replace(tzinfo=None).isoformat(),
                'macd': float(row['macd']),
                'macd_signal': float(row['macd_signal']),
                'histogram': float(row['histogram'])
            })

        return jsonify({'status': 'success', 'data': {'symbol': symbol, 'timeframe': timeframe, 'macd': macd, 'count': len(macd), 'note': 'MACD from YF (computed)'}})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'YF MACD error: {str(e)}'}), 500


def _get_macd_hybrid(symbol: str, timeframe: str, limit: int, historical_days: int):
    """Kết hợp MACD từ DB (lịch sử) và YF (realtime)."""
    try:
        # 1) Load MACD historical from DB
        from app.db import SessionLocal
        session = SessionLocal()
        try:
            symbol_result = session.execute(text("""
                SELECT id FROM symbols WHERE ticker = :symbol LIMIT 1
            """), {'symbol': symbol}).fetchone()
            if not symbol_result:
                return _get_macd_from_yf(symbol, timeframe, limit)
            symbol_id = symbol_result[0]

            query = text("""
                SELECT ts, macd, macd_signal, hist
                FROM indicators_macd 
                WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                AND ts >= DATE_SUB(NOW(), INTERVAL :historical_days DAY)
                ORDER BY ts DESC 
                LIMIT :limit
            """)
            result = session.execute(query, {
                'symbol_id': symbol_id,
                'timeframe': timeframe,
                'limit': limit,
                'historical_days': historical_days
            }).fetchall()

            macd_hist = []
            if result:
                for row in result:
                    macd_hist.append({
                        'timestamp': row.ts.isoformat(),
                        'macd': float(row.macd),
                        'macd_signal': float(row.macd_signal),
                        'histogram': float(row.hist)
                    })
                macd_hist.reverse()
        finally:
            session.close()

        # 2) Load realtime MACD from YF (last few points) and merge
        try:
            yf_resp = _get_macd_from_yf(symbol, timeframe, 5)
            yf_json = yf_resp.get_json()
            if yf_json and yf_json.get('status') == 'success':
                yf_list = yf_json['data']['macd']
                if yf_list and macd_hist:
                    last_hist_time = macd_hist[-1]['timestamp']
                    last_yf_time = yf_list[-1]['timestamp']
                    if last_yf_time >= last_hist_time:
                        macd_hist[-1] = yf_list[-1]
                    for item in yf_list:
                        if item['timestamp'] > last_hist_time and not any(d['timestamp'] == item['timestamp'] for d in macd_hist):
                            macd_hist.append(item)
                elif not macd_hist and yf_list:
                    macd_hist = yf_list
        except Exception as e:
            print(f"Hybrid MACD YF merge error: {e}")

        return jsonify({'status': 'success', 'data': {'symbol': symbol, 'timeframe': timeframe, 'macd': macd_hist, 'count': len(macd_hist), 'note': f'MACD Hybrid: {historical_days} days DB + YF realtime'}})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Hybrid MACD error: {str(e)}'}), 500

# ==============================================
# REAL BARS DATA
# ==============================================

@real_data_bp.route('/api/real/bars', methods=['GET'])
def get_real_bars():
    """Lấy dữ liệu Bars - Mock data"""
    try:
        symbol = request.args.get('symbol', 'AAPL')
        timeframe = request.args.get('timeframe', '5m')
        limit = int(request.args.get('limit', 100))
        
        # Generate mock Bars data
        import random
        
        bars_data = []
        current_time = datetime.now()
        
        for i in range(limit):
            bars_data.append({
                'timestamp': (current_time - timedelta(minutes=i*5)).isoformat(),
                'bars': round(random.uniform(0, 10), 2)
            })
        
        # Reverse để có thứ tự thời gian tăng dần
        bars_data.reverse()
        
        return jsonify({
            'status': 'success',
            'data': {
                'symbol': symbol,
                'timeframe': timeframe,
                'bars': bars_data,
                'count': len(bars_data),
                'note': 'Database integration in progress - using mock data'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching Bars: {str(e)}'
        }), 500

# ==============================================
# WORKER MONITORING
# ==============================================

@real_data_bp.route('/api/real/worker-status', methods=['GET'])
def get_worker_status():
    """Lấy trạng thái worker_us real-time từ database"""
    try:
        # For now, return mock data with database integration message
        symbols = [
            {
                'ticker': 'AAPL',
                'exchange': 'NASDAQ',
                'active': True,
                'candle_count': 125000,
                'last_update': datetime.now().isoformat()
            },
            {
                'ticker': 'GOOGL',
                'exchange': 'NASDAQ',
                'active': True,
                'candle_count': 98000,
                'last_update': datetime.now().isoformat()
            },
            {
                'ticker': 'MSFT',
                'exchange': 'NASDAQ',
                'active': True,
                'candle_count': 110000,
                'last_update': datetime.now().isoformat()
            }
        ]
        
        stats = {
            'total_symbols': 9,
            'active_symbols': 7,
            'symbols_with_data': 6,
            'latest_data_time': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'symbols': symbols,
                'stats': stats,
                'timestamp': datetime.now().isoformat(),
                'note': 'Database integration in progress - using mock data'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching worker status: {str(e)}'
        }), 500

# ==============================================
# COMBINED DATA FOR CHARTS
# ==============================================

@real_data_bp.route('/api/real/chart-data', methods=['GET'])
def get_chart_data():
    """Lấy dữ liệu tổng hợp cho charts - Simple test"""
    try:
        return jsonify({
            'status': 'success',
            'data': {
                'symbol': 'AAPL',
                'timeframe': '5m',
                'candles': [{'timestamp': '2024-01-01T00:00:00', 'open': 150.0, 'high': 155.0, 'low': 148.0, 'close': 152.0, 'volume': 1000}],
                'macd': [{'timestamp': '2024-01-01T00:00:00', 'macd': 0.5, 'macd_signal': 0.3, 'histogram': 0.2}],
                'bars': [{'timestamp': '2024-01-01T00:00:00', 'bars': 5.0}],
                'count': 1,
                'note': 'Simple test data'
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

@real_data_bp.route('/api/real/test', methods=['GET'])
def test_api():
    """Test API đơn giản"""
    return jsonify({'status': 'success', 'message': 'Test API working'})

# ==============================================
# REAL-TIME SIGNALS
# ==============================================

@real_data_bp.route('/api/real/signals', methods=['GET'])
def get_real_signals():
    """Lấy signals - Mock data"""
    try:
        symbol = request.args.get('symbol', '')
        strategy_id = request.args.get('strategy_id', '')
        limit = int(request.args.get('limit', 50))
        
        # Generate mock signals data
        import random
        
        signals = []
        current_time = datetime.now()
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        signal_types = ['BUY', 'SELL', 'HOLD']
        strategies = ['MACD Strategy', 'RSI Strategy', 'Bollinger Bands']
        
        for i in range(min(limit, 20)):  # Max 20 mock signals
            signals.append({
                'id': i + 1,
                'symbol': random.choice(symbols),
                'timeframe': random.choice(['1m', '5m', '15m', '1h']),
                'timestamp': (current_time - timedelta(minutes=i*10)).isoformat(),
                'strategy_id': random.randint(1, 3),
                'strategy_name': random.choice(strategies),
                'signal_type': random.choice(signal_types),
                'details': {
                    'confidence': round(random.uniform(0.5, 0.99), 2),
                    'price': round(random.uniform(100, 200), 2),
                    'volume': random.randint(100, 1000)
                }
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'signals': signals,
                'count': len(signals),
                'timestamp': datetime.now().isoformat(),
                'note': 'Database integration in progress - using mock data'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching signals: {str(e)}'
        }), 500
