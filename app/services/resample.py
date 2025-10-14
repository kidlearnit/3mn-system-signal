import os
import pandas as pd
import datetime as dt
from sqlalchemy import text

from app.db import  init_db
# 🔹 Khởi tạo DB
init_db(os.getenv("DATABASE_URL"))

from app.db import SessionLocal

PANDAS_RULE = {
    '1m': '1min',
    '2m': '2min',
    '5m': '5min',
    '15m': '15min',
    '30m': '30min',
    '1h': '1h',
    '4h': '4h',
    '1D': '1D'
}

UTC = dt.timezone.utc

def ensure_index_utc(df: pd.DataFrame):
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
    return df

def load_overlap_from_db(symbol_id: int, tf: str, overlap_minutes: int):
    """Lấy overlap_minutes nến 1m mới nhất từ DB"""
    with SessionLocal() as s:
        rows = s.execute(text("""
            SELECT ts, open, high, low, close, volume
            FROM candles_1m
            WHERE symbol_id=:sid
            ORDER BY ts DESC
            LIMIT :limit
        """), {'sid': symbol_id, 'limit': overlap_minutes}).fetchall()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=['ts','open','high','low','close','volume'])
    df.set_index('ts', inplace=True)
    df = df.sort_index()
    return ensure_index_utc(df)

def resample_ohlcv(df_1m, tf: str, symbol_id: int = None):
    """
    Resample từ 1m sang TF cao, có overlap từ DB nếu symbol_id được truyền vào.
    Giữ nguyên interface cũ: df_1m là phần mới, tf là khung cần resample.
    """
    rule = PANDAS_RULE[tf]

    # Nếu có symbol_id → load overlap từ DB
    if symbol_id and tf != '1m':
        tf_minutes = int(tf.replace('m','')) if 'm' in tf else int(tf.replace('h',''))*60
        overlap_df = load_overlap_from_db(symbol_id, tf, tf_minutes - 1)
        if not overlap_df.empty:
            df_1m = pd.concat([overlap_df, df_1m]).drop_duplicates()
    
    df_1m = ensure_index_utc(df_1m)

    o = df_1m['open'].resample(rule, label='right', closed='right').first()
    h = df_1m['high'].resample(rule, label='right', closed='right').max()
    l = df_1m['low'].resample(rule, label='right', closed='right').min()
    c = df_1m['close'].resample(rule, label='right', closed='right').last()
    v = df_1m['volume'].resample(rule, label='right', closed='right').sum()

    out = pd.concat([o,h,l,c,v], axis=1).dropna()
    out.columns = ['open','high','low','close','volume']

    # Loại bỏ nến chưa đóng
    if tf != '1m' and not out.empty:
        tf_minutes = int(tf.replace('m','')) if 'm' in tf else int(tf.replace('h',''))*60
        now_utc = dt.datetime.now(tz=UTC)
        if (now_utc - out.index[-1]) < dt.timedelta(minutes=tf_minutes):
            out = out.iloc[:-1]

    return out
