#!/usr/bin/env python3
"""
SMA Jobs Pipeline - Tích hợp SMA system vào production
"""

import os
import json
import redis
import pandas as pd
from sqlalchemy import text
import traceback

from app.services.data_sources import fetch_latest_1m
from app.services.candle_utils import load_candles_1m_df, upsert_candles_tf
from app.services.resample import resample_ohlcv
from app.services.sma_indicators import sma_indicator_service
from app.services.sma_signal_engine import sma_signal_engine
from app.services.sma_telegram_service import sma_telegram_service
from app.services.email_service import email_service
from app.services.strategy_config import get_strategy_for_symbol
from app.db import SessionLocal, init_db
from utils.market_time import is_market_open
from app.services.debug import debug_helper

# Initialize DB session if not already done (important for worker processes)
if SessionLocal is None:
    init_db(os.getenv("DATABASE_URL"))

# List of timeframes for SMA processing
TF_LIST_SMA = ['1m', '2m', '5m', '15m', '30m', '1h', '4h']
TF_LOGIC_MAP_SMA = {
    '1D4hr': '4h',
    '1D1hr': '1h',
    '1D30Min': '30m',
    '1D15Min': '15m',
    '1D5': '5m',      # 1D5 = 5m
    '1D2': '2m',      # 1D2 = 2m
    '1D1': '1m'       # 1D1 = 1m
}

# Redis client for WebSocket publishing (use localhost for testing)
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    redis_client = redis.from_url(redis_url)
    # Test connection
    redis_client.ping()
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    redis_client = None

def publish_sma_signal_to_websocket(symbol_id: int, ticker: str, exchange: str, timeframe: str, signal_data: dict):
    """Publishes SMA signal data to Redis for WebSocket clients."""
    if redis_client is None:
        debug_helper.log_step(f"Redis not available, skipping WebSocket publish for {ticker} {timeframe}")
        return
        
    try:
        message = {
            "symbol_id": symbol_id,
            "ticker": ticker,
            "exchange": exchange,
            "timeframe": timeframe,
            "signal_type": signal_data.get('signal_type'),
            "signal_direction": signal_data.get('signal_direction'),
            "signal_strength": float(signal_data.get('signal_strength', 0.0)),
            "timestamp": pd.Timestamp.now(tz='UTC').isoformat(),
            "strategy": "SMA"
        }
        redis_client.publish('sma_signals', json.dumps(message))
        debug_helper.log_step(f"Published SMA signal for {ticker} {timeframe} to WebSocket")
    except Exception as e:
        debug_helper.log_step(f"Error publishing SMA signal to WebSocket for {ticker} {timeframe}", error=e)

def store_sma_indicators(symbol_id: int, timeframe: str, df: pd.DataFrame):
    """Stores SMA indicators into the database."""
    if df.empty:
        return

    # Ensure 'ts' is timezone-naive for MySQL DATETIME
    df['ts'] = df.index.tz_localize(None)

    # Prepare data for upsert
    data_to_upsert = df[['ts', 'close', 'm1', 'm2', 'm3', 'ma144', 'avg_m1_m2_m3']].copy()
    data_to_upsert = data_to_upsert.dropna()  # Remove rows with NaN values

    if data_to_upsert.empty:
        debug_helper.log_step(f"No valid SMA data to store for {symbol_id} {timeframe}")
        return

    try:
        with SessionLocal() as s:
            # Upsert SMA indicators
            for _, row in data_to_upsert.iterrows():
                s.execute(text("""
                    INSERT INTO indicators_sma (symbol_id, timeframe, ts, close, m1, m2, m3, ma144, avg_m1_m2_m3)
                    VALUES (:symbol_id, :timeframe, :ts, :close, :m1, :m2, :m3, :ma144, :avg_m1_m2_m3)
                    ON DUPLICATE KEY UPDATE
                        close = VALUES(close),
                        m1 = VALUES(m1),
                        m2 = VALUES(m2),
                        m3 = VALUES(m3),
                        ma144 = VALUES(ma144),
                        avg_m1_m2_m3 = VALUES(avg_m1_m2_m3),
                        updated_at = CURRENT_TIMESTAMP
                """), {
                    'symbol_id': symbol_id,
                    'timeframe': timeframe,
                    'ts': row['ts'],
                    'close': float(row['close']),
                    'm1': float(row['m1']),
                    'm2': float(row['m2']),
                    'm3': float(row['m3']),
                    'ma144': float(row['ma144']),
                    'avg_m1_m2_m3': float(row['avg_m1_m2_m3'])
                })
            s.commit()
            debug_helper.log_step(f"Stored {len(data_to_upsert)} SMA indicators for {symbol_id} {timeframe}")
    except Exception as e:
        debug_helper.log_step(f"Error storing SMA indicators for {symbol_id} {timeframe}", error=e)

def store_sma_signal(symbol_id: int, timeframe: str, signal_data: dict, current_price: float):
    """Stores SMA signal into the database."""
    try:
        with SessionLocal() as s:
            s.execute(text("""
                INSERT INTO sma_signals (symbol_id, timeframe, timestamp, signal_type, signal_direction, 
                                       signal_strength, current_price, ma18, ma36, ma48, ma144, avg_ma)
                VALUES (:symbol_id, :timeframe, :timestamp, :signal_type, :signal_direction, 
                       :signal_strength, :current_price, :ma18, :ma36, :ma48, :ma144, :avg_ma)
                ON DUPLICATE KEY UPDATE
                    signal_type = VALUES(signal_type),
                    signal_direction = VALUES(signal_direction),
                    signal_strength = VALUES(signal_strength),
                    current_price = VALUES(current_price),
                    ma18 = VALUES(ma18),
                    ma36 = VALUES(ma36),
                    ma48 = VALUES(ma48),
                    ma144 = VALUES(ma144),
                    avg_ma = VALUES(avg_ma),
                    updated_at = CURRENT_TIMESTAMP
            """), {
                'symbol_id': symbol_id,
                'timeframe': timeframe,
                'timestamp': pd.Timestamp.now(tz='UTC').tz_localize(None),
                'signal_type': signal_data.get('signal_type'),
                'signal_direction': signal_data.get('signal_direction'),
                'signal_strength': float(signal_data.get('signal_strength', 0.0)),
                'current_price': float(current_price),
                'ma18': float(signal_data.get('m1', 0.0)),
                'ma36': float(signal_data.get('m2', 0.0)),
                'ma48': float(signal_data.get('m3', 0.0)),
                'ma144': float(signal_data.get('ma144', 0.0)),
                'avg_ma': float(signal_data.get('avg_m1_m2_m3', 0.0))
            })
            s.commit()
            debug_helper.log_step(f"Stored SMA signal for {symbol_id} {timeframe}: {signal_data.get('signal_type')}")
    except Exception as e:
        debug_helper.log_step(f"Error storing SMA signal for {symbol_id} {timeframe}", error=e)

def job_sma_pipeline(symbol_id: int, ticker: str, exchange: str):
    """
    SMA Pipeline Job - Chạy mỗi phút cho SMA system
    """
    try:
        debug_helper.log_step(f"Starting SMA pipeline for {ticker}", {
            'symbol_id': symbol_id,
            'ticker': ticker,
            'exchange': exchange
        })
        
        # 1. Lấy nến 1m mới nhất
        debug_helper.log_step(f"Fetching latest 1m data for {ticker}")
        count = fetch_latest_1m(symbol_id, ticker, exchange)
        debug_helper.log_step(f"Latest 1m data fetch result for {ticker}", f"Count: {count}")

        # 2. Load 1m candles từ DB
        debug_helper.log_step(f"Loading 1m candles from DB for {ticker}")
        df_1m = load_candles_1m_df(symbol_id)
        debug_helper.log_step(f"Loaded 1m candles for {ticker}", f"Rows: {len(df_1m)}")
        
        if df_1m.empty:
            debug_helper.log_step(f"No candles in DB for {ticker}", "Returning no-data")
            return "no-data"
        
        # 3. Process all timeframes and collect MA structures for multi-timeframe analysis
        ma_structures = {}
        try:
            for tf in TF_LIST_SMA:
                debug_helper.log_step(f"Processing SMA timeframe {tf} for {ticker}")
                
                try:
                    # Resample data
                    df_tf = resample_ohlcv(df_1m, tf)
                    debug_helper.log_step(f"Resampled {tf} for {ticker}", f"Rows: {len(df_tf)}")
                    
                    # Upsert candles
                    upsert_candles_tf(symbol_id, tf, df_tf)
                    debug_helper.log_step(f"Upserted {tf} candles for {ticker}")
                    
                    # Calculate SMA indicators
                    sma_results = sma_indicator_service.calculate_all_smas(df_tf)
                    
                    # Add SMA columns to dataframe
                    df_sma = df_tf.copy()
                    for name, series in sma_results.items():
                        df_sma[name] = series
                    
                    # Store SMA indicators
                    store_sma_indicators(symbol_id, tf, df_sma)
                    debug_helper.log_step(f"Calculated and stored SMA for {tf} {ticker}")
                    
                    # Collect MA structure for multi-timeframe analysis
                    if not df_sma.empty:
                        ma_structure = {
                            'cp': float(df_sma['close'].iloc[-1]),
                            'm1': float(sma_results['m1'].iloc[-1]) if 'm1' in sma_results else 0.0,
                            'm2': float(sma_results['m2'].iloc[-1]) if 'm2' in sma_results else 0.0,
                            'm3': float(sma_results['m3'].iloc[-1]) if 'm3' in sma_results else 0.0,
                            'ma144': float(sma_results['ma144'].iloc[-1]) if 'ma144' in sma_results else 0.0,
                            'avg_m1_m2_m3': float(sma_results['avg_m1_m2_m3'].iloc[-1]) if 'avg_m1_m2_m3' in sma_results else 0.0
                        }
                        ma_structures[tf] = ma_structure
                        debug_helper.log_step(f"Collected MA structure for {tf} {ticker}")
                    else:
                        debug_helper.log_step(f"No SMA data for {tf} {ticker}")
                    
                except Exception as tf_error:
                    debug_helper.log_step(f"Error processing SMA {tf} for {ticker}", error=tf_error)
                    continue
            
            # 4. Multi-timeframe analysis
            if ma_structures:
                debug_helper.log_step(f"Starting multi-timeframe analysis for {ticker}")
                
                # Evaluate multi-timeframe signals
                multi_signals = sma_signal_engine.evaluate_multi_timeframe(ma_structures)
                debug_helper.log_step(f"Multi-timeframe signals for {ticker}", f"Signals: {len(multi_signals)}")
                
                # Check for triple confirmation
                triple_bullish = sma_signal_engine.check_triple_bullish(ma_structures)
                triple_bearish = sma_signal_engine.check_triple_bearish(ma_structures)
                debug_helper.log_step(f"Triple signals for {ticker}", f"Bullish: {triple_bullish}, Bearish: {triple_bearish}")
                
                # Process each timeframe signal
                for tf, signal_type in multi_signals.items():
                    if tf in ma_structures:
                        ma_structure = ma_structures[tf]
                        signal_direction = sma_signal_engine.get_signal_direction(signal_type)
                        signal_strength = sma_signal_engine.get_signal_strength(signal_type)
                        
                        signal_data = {
                            'signal_type': signal_type.value,
                            'signal_direction': signal_direction,
                            'signal_strength': signal_strength,
                            **ma_structure
                        }
                        
                        # Store signal
                        store_sma_signal(symbol_id, tf, signal_data, ma_structure['cp'])
                        
                        # Publish to WebSocket
                        publish_sma_signal_to_websocket(symbol_id, ticker, exchange, tf, signal_data)
                        
                        # Send Telegram alerts ONLY for Confirmed and Triple signals (Email disabled - using digest instead)
                        if signal_type.value in ['confirmed_bullish', 'confirmed_bearish', 'triple_bullish', 'triple_bearish']:
                            try:
                                # Create clean signal data for Telegram
                                telegram_signal_data = {
                                    'signal_type': signal_type.value,
                                    'signal_direction': signal_direction,
                                    'signal_strength': signal_strength,
                                    'close': ma_structure['cp'],
                                    'm1': ma_structure['m1'],
                                    'm2': ma_structure['m2'],
                                    'm3': ma_structure['m3'],
                                    'ma144': ma_structure['ma144'],
                                    'avg_m1_m2_m3': ma_structure['avg_m1_m2_m3']
                                }
                                sma_telegram_service.send_sma_signal(ticker, exchange, tf, telegram_signal_data)
                                
                                # Email alerts disabled - using digest instead
                                # Individual emails are now sent via email digest every 10 minutes
                                debug_helper.log_step(f"Sent SMA Telegram alert for {ticker} {tf} - {signal_type.value} (email via digest)")
                            except Exception as tg_error:
                                debug_helper.log_step(f"Error sending SMA Telegram alert for {ticker} {tf}", error=tg_error)
                        else:
                            debug_helper.log_step(f"Skipping Telegram alert for {ticker} {tf} - {signal_type.value} (not confirmed signal)")
                        
                        debug_helper.log_step(f"Processed multi-timeframe signal for {tf} {ticker}: {signal_type.value} ({signal_direction})")
                
                # Send triple confirmation alerts
                if triple_bullish:
                    try:
                        # Get details for triple bullish
                        details = []
                        for tf in ['1m', '2m', '5m']:
                            if tf in ma_structures:
                                ma = ma_structures[tf]
                                details.append({
                                    'tf': tf,
                                    'price': ma['cp'],
                                    'avg_vs_ma144': f"{ma['avg_m1_m2_m3']:.2f} vs {ma['ma144']:.2f}"
                                })
                        
                        sma_telegram_service.send_triple_confirmation_alert(ticker, exchange, details, "triple_bullish")
                        debug_helper.log_step(f"Sent triple bullish alert for {ticker}")
                    except Exception as e:
                        debug_helper.log_step(f"Error sending triple bullish alert for {ticker}", error=e)
                
                if triple_bearish:
                    try:
                        # Get details for triple bearish
                        details = []
                        for tf in ['1m', '2m', '5m']:
                            if tf in ma_structures:
                                ma = ma_structures[tf]
                                details.append({
                                    'tf': tf,
                                    'price': ma['cp'],
                                    'avg_vs_ma144': f"{ma['avg_m1_m2_m3']:.2f} vs {ma['ma144']:.2f}"
                                })
                        
                        sma_telegram_service.send_triple_confirmation_alert(ticker, exchange, details, "triple_bearish")
                        debug_helper.log_step(f"Sent triple bearish alert for {ticker}")
                    except Exception as e:
                        debug_helper.log_step(f"Error sending triple bearish alert for {ticker}", error=e)
                
                debug_helper.log_step(f"Completed multi-timeframe analysis for {ticker}")
            else:
                debug_helper.log_step(f"No MA structures collected for {ticker}")
            
            debug_helper.log_step(f"Completed SMA pipeline for {ticker}", "Returning success")
            return "success"
            
        except Exception as e:
            debug_helper.log_step(f"SMA pipeline error for {ticker}", error=e)
            print(f"Error in SMA pipeline for {ticker}: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return "error"
            
    except Exception as e:
        debug_helper.log_step(f"SMA pipeline error for {ticker}", error=e)
        print(f"Error in SMA pipeline for {ticker}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return "error"

def job_sma_multi_timeframe_analysis(symbol_id: int, ticker: str, exchange: str):
    """
    Multi-timeframe SMA Analysis - Phân tích tín hiệu từ nhiều timeframes
    """
    try:
        debug_helper.log_step(f"Starting multi-timeframe SMA analysis for {ticker}")
        
        # Collect MA structures from all timeframes
        ma_structures = {}
        
        for tf in TF_LIST_SMA:
            try:
                with SessionLocal() as s:
                    # Get latest SMA data for this timeframe
                    row = s.execute(text("""
                        SELECT ts, close, m1, m2, m3, ma144, avg_m1_m2_m3
                        FROM indicators_sma
                        WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                        ORDER BY ts DESC LIMIT 1
                    """), {'symbol_id': symbol_id, 'timeframe': tf}).mappings().first()
                    
                    if row:
                        ma_structures[tf] = {
                            'cp': float(row['close']),
                            'm1': float(row['m1']),
                            'm2': float(row['m2']),
                            'm3': float(row['m3']),
                            'ma144': float(row['ma144']),
                            'avg_m1_m2_m3': float(row['avg_m1_m2_m3'])
                        }
            except Exception as e:
                debug_helper.log_step(f"Error getting MA structure for {ticker} {tf}", error=e)
                continue
        
        if not ma_structures:
            debug_helper.log_step(f"No MA structures found for {ticker}")
            return "no-data"
        
        # Evaluate multi-timeframe signals
        multi_signals = sma_signal_engine.evaluate_multi_timeframe(ma_structures)
        
        # Check for triple confirmation
        triple_bullish = sma_signal_engine.check_triple_bullish(ma_structures)
        triple_bearish = sma_signal_engine.check_triple_bearish(ma_structures)
        
        # Send triple confirmation alerts
        if triple_bullish:
            try:
                # Get details for triple bullish
                details = []
                for tf in ['1D1Min', '1D2Min', '1D5Min']:
                    if tf in ma_structures:
                        ma = ma_structures[tf]
                        details.append({
                            'tf': tf,
                            'price': ma['cp'],
                            'avg_vs_ma144': f"{ma['avg_m1_m2_m3']:.2f} vs {ma['ma144']:.2f}"
                        })
                
                sma_telegram_service.send_triple_confirmation_alert(ticker, exchange, details, "triple_bullish")
                debug_helper.log_step(f"Sent triple bullish alert for {ticker}")
            except Exception as e:
                debug_helper.log_step(f"Error sending triple bullish alert for {ticker}", error=e)
        
        if triple_bearish:
            try:
                # Get details for triple bearish
                details = []
                for tf in ['1D1Min', '1D2Min', '1D5Min']:
                    if tf in ma_structures:
                        ma = ma_structures[tf]
                        details.append({
                            'tf': tf,
                            'price': ma['cp'],
                            'avg_vs_ma144': f"{ma['avg_m1_m2_m3']:.2f} vs {ma['ma144']:.2f}"
                        })
                
                sma_telegram_service.send_triple_confirmation_alert(ticker, exchange, details, "triple_bearish")
                debug_helper.log_step(f"Sent triple bearish alert for {ticker}")
            except Exception as e:
                debug_helper.log_step(f"Error sending triple bearish alert for {ticker}", error=e)
        
        debug_helper.log_step(f"Completed multi-timeframe SMA analysis for {ticker}")
        return "success"
        
    except Exception as e:
        debug_helper.log_step(f"Error in multi-timeframe SMA analysis for {ticker}", error=e)
        print(f"Error in multi-timeframe SMA analysis for {ticker}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return "error"

def job_sma_backfill(symbol_id: int, ticker: str, exchange: str, days: int = 30):
    """
    SMA Backfill Job - Tính toán SMA cho dữ liệu lịch sử
    """
    try:
        from app.services.logger import log_backfill_success, log_backfill_error
        
        debug_helper.log_step(f"Starting SMA backfill for {ticker} ({days} days)")
        
        # Load historical data
        df_1m = load_candles_1m_df(symbol_id)
        
        if df_1m.empty:
            log_backfill_error(ticker, exchange, Exception("No historical data found"), {
                'symbol_id': symbol_id,
                'days': days,
                'job_type': 'sma_backfill'
            })
            debug_helper.log_step(f"No historical data for {ticker}")
            return "no-data"
        
        # Process each timeframe
        for tf in TF_LIST_SMA:
            try:
                debug_helper.log_step(f"Backfilling SMA for {ticker} {tf}")
                
                # Resample data
                df_tf = resample_ohlcv(df_1m, tf)
                
                # Calculate SMA indicators
                sma_results = sma_indicator_service.calculate_all_smas(df_tf)
                
                # Add SMA columns to dataframe
                df_sma = df_tf.copy()
                for name, series in sma_results.items():
                    df_sma[name] = series
                
                # Store SMA indicators
                store_sma_indicators(symbol_id, tf, df_sma)
                
                debug_helper.log_step(f"Backfilled SMA for {ticker} {tf}: {len(df_sma)} records")
                
            except Exception as e:
                debug_helper.log_step(f"Error backfilling SMA for {ticker} {tf}", error=e)
                continue
        
        log_backfill_success(ticker, exchange, len(df_1m), {
            'symbol_id': symbol_id,
            'days': days,
            'job_type': 'sma_backfill',
            'timeframes': TF_LIST_SMA
        })
        
        debug_helper.log_step(f"Completed SMA backfill for {ticker}")
        return "success"
        
    except Exception as e:
        from app.services.logger import log_backfill_error
        log_backfill_error(ticker, exchange, e, {
            'symbol_id': symbol_id,
            'days': days,
            'job_type': 'sma_backfill'
        })
        debug_helper.log_step(f"Error in SMA backfill for {ticker}", error=e)
        print(f"Error in SMA backfill for {ticker}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return "error"