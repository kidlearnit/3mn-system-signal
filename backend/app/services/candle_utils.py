#!/usr/bin/env python3
"""
Candle Utilities - Common functions for candle data operations
"""

import pandas as pd
from sqlalchemy import text
from app.db import SessionLocal

def load_candles_1m_df(symbol_id: int, lookback_minutes: int = 2000):
    """
    Load 1m candles from database for a symbol
    """
    try:
        with SessionLocal() as s:
            rows = s.execute(text("""
                SELECT ts, open, high, low, close, volume 
                FROM candles_1m 
                WHERE symbol_id = :symbol_id 
                ORDER BY ts DESC 
                LIMIT :limit
            """), {'symbol_id': symbol_id, 'limit': lookback_minutes}).fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['ts','open','high','low','close','volume'])
        df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df['ts'], utc=True))).drop(columns=['ts'])
        df = df.sort_index()  # Sort by time ascending
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading candles_1m for symbol_id {symbol_id}: {e}")
        return pd.DataFrame()

def upsert_candles_tf(symbol_id: int, tf: str, df_tf: pd.DataFrame):
    """
    Upsert candles for a specific timeframe
    """
    if df_tf.empty:
        return
    
    # Ensure 'ts' is timezone-naive for MySQL DATETIME
    df_tf['ts'] = df_tf.index.tz_localize(None)
    
    try:
        with SessionLocal() as s:
            for _, row in df_tf.iterrows():
                s.execute(text("""
                    INSERT INTO candles_tf (symbol_id, timeframe, ts, open, high, low, close, volume)
                    VALUES (:symbol_id, :timeframe, :ts, :open, :high, :low, :close, :volume)
                    ON DUPLICATE KEY UPDATE
                        open = VALUES(open),
                        high = VALUES(high),
                        low = VALUES(low),
                        close = VALUES(close),
                        volume = VALUES(volume)
                """), {
                    'symbol_id': symbol_id,
                    'timeframe': tf,
                    'ts': row['ts'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                })
            s.commit()
    except Exception as e:
        print(f"❌ Error upserting candles_tf for {symbol_id} {tf}: {e}")
