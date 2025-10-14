import os
import json
import redis
from app.services.data_sources import backfill_1m, fetch_latest_1m
from app.services.resample import resample_ohlcv
from app.services.indicators import compute_macd, compute_macd_772144, compute_advanced_indicators
from app.services.thresholds import load_threshold_rules
from app.services.signal_engine import match_zone, make_signal, validate_cross_timeframe_synchronization
from app.services.strategy_config import get_strategy_for_symbol
from app.services.notify import tg_send_text
from app.services.debug import debug_helper
# SMA System imports
from worker.sma_jobs import job_sma_pipeline
from app.db import init_db
from utils.market_time import is_market_open
from utils.value import fmt_val
# Khởi tạo DB session
init_db(os.getenv("DATABASE_URL"))
from app.db import SessionLocal
from sqlalchemy import text
import pandas as pd
import traceback

# Map tên logic threshold -> TF kỹ thuật
TF_LOGIC_MAP = {
    '1D4hr': '4h',
    '1D1hr': '1h',
    '1D30Min': '30m',
    '1D15Min': '15m',
    '1D5Min': '5m',
    '1D2Min': '2m',
    '1D1Min': '1m'
}

# Trọng số cho từng logic TF - Khung lớn tìm xu hướng, khung nhỏ tìm điểm vào
TF_WEIGHT = {
    '1D4hr': 8,      # Khung lớn - xác định xu hướng chính
    '1D1hr': 7,      # Khung lớn - xác định xu hướng chính  
    '1D30Min': 6,    # Khung trung bình - xác nhận xu hướng
    '1D15Min': 5,    # Khung trung bình - xác nhận xu hướng
    '1D5Min': 4,     # Khung nhỏ - tìm điểm vào lệnh
    '1D2Min': 3,     # Khung nhỏ - tìm điểm vào lệnh
    '1D1Min': 2      # Khung nhỏ - tìm điểm vào lệnh
}

HIGH_TF = {'1D4hr', '1D1hr', '1D30Min', '1D15Min', '1D5Min', '1D2Min', '1D1Min'}  # Tất cả khung giờ

# List of timeframes for processing (removed '1D')
TF_LIST = ['2m','5m','15m','30m','1h','4h']

# Redis client for WebSocket publishing
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'))

def publish_websocket_update(update_type, data):
    """Publish update to Redis for WebSocket clients"""
    try:
        message = {
            'type': update_type,
            'timestamp': pd.Timestamp.now().isoformat(),
            **data
        }
        redis_client.publish('realtime_updates', json.dumps(message))
    except Exception as e:
        print(f"Error publishing WebSocket update: {e}")

def save_signal_to_db(symbol_id, signal_type, score, strategy_id, sig_map):
    """Save signal to database"""
    try:
        with SessionLocal() as s:
            # Get latest price and timeframe for the signal
            latest_price = None
            latest_timeframe = None
            for tf_name, tf_data in sig_map.items():
                if tf_data.get('close'):
                    latest_price = tf_data['close']
                    latest_timeframe = TF_LOGIC_MAP.get(tf_name, '1m')  # Map logic name to technical TF
                    break
            
            # Insert signal with correct column names
            s.execute(text("""
                INSERT INTO signals (symbol_id, timeframe, ts, strategy_id, signal_type, details)
                VALUES (:symbol_id, :timeframe, :ts, :strategy_id, :signal_type, :details)
            """), {
                'symbol_id': symbol_id,
                'timeframe': latest_timeframe or '1m',
                'ts': pd.Timestamp.now(),
                'strategy_id': strategy_id,
                'signal_type': signal_type,
                'details': json.dumps({
                    'price': float(latest_price) if latest_price else None,
                    'score': score,
                    'signal_map': {k: v.get('signal') for k, v in sig_map.items()},
                    'macd_values': {k: {
                        'macd': v.get('macd'),
                        'signal': v.get('signal_line'),
                        'hist': v.get('hist')
                    } for k, v in sig_map.items()},
                    'strength': abs(score),
                    'confidence': min(abs(score) / 10.0, 1.0),
                    'status': 'active',
                    'source': 'auto'
                })
            })
            s.commit()
            print(f"✅ Signal saved to database: {signal_type} for symbol_id {symbol_id}")
    except Exception as e:
        print(f"❌ Error saving signal to database: {e}")


def get_last_tf_signal(symbol_id:int, tf:str, strategy_id:int, tf_threshold_name:str):
    """
    Đọc tín hiệu mới nhất đã lưu cho TF (do eval/engine lưu).
    Nếu bạn đang tự tính tại chỗ, bạn có thể gọi trực tiếp logic eval thay vì đọc DB.
    """
    with SessionLocal() as s:
        row = s.execute(text("""
            SELECT signal_type, ts
            FROM signals
            WHERE symbol_id=:sid AND timeframe=:tf AND strategy_id=:stg
            ORDER BY ts DESC LIMIT 1
        """), {'sid': symbol_id, 'tf': tf, 'stg': strategy_id}).mappings().first()
    if not row:
        return None, None
    return row['signal_type'], row['ts']

def normalize_signal(sig: str):
    if not sig:
        return None
    s = sig.lower()
    if 'bull' in s or 'buy' in s:
        return 'BUY'
    if 'bear' in s or 'sell' in s:
        return 'SELL'
    return None

def aggregate_signals(sig_map: dict):
    score = 0
    votes_buy, votes_sell = 0, 0
    
    # Phân loại khung giờ
    trend_tfs = {'1D4hr', '1D1hr', '1D30Min'}  # Khung lớn - tìm xu hướng
    entry_tfs = {'1D15Min', '1D5Min', '1D2Min', '1D1Min'}  # Khung nhỏ - tìm điểm vào
    
    trend_buy_count, trend_sell_count = 0, 0
    entry_buy_count, entry_sell_count = 0, 0
    
    for tf_name, sig in sig_map.items():
        if not sig:
            continue
        w = TF_WEIGHT.get(tf_name, 1)
        if sig == 'BUY':
            score += w
            votes_buy += 1
            if tf_name in trend_tfs:
                trend_buy_count += 1
            elif tf_name in entry_tfs:
                entry_buy_count += 1
        elif sig == 'SELL':
            score -= w
            votes_sell += 1
            if tf_name in trend_tfs:
                trend_sell_count += 1
            elif tf_name in entry_tfs:
                entry_sell_count += 1
    
    # Yêu cầu: xu hướng từ khung lớn + điểm vào từ khung nhỏ
    # Ít nhất 2/3 khung lớn cùng hướng + ít nhất 2/4 khung nhỏ cùng hướng
    min_trend_consensus = 2  # Ít nhất 2 khung lớn
    min_entry_consensus = 2  # Ít nhất 2 khung nhỏ
    
    if (score > 0 and 
        trend_buy_count >= min_trend_consensus and 
        entry_buy_count >= min_entry_consensus):
        return 'BUY', score, votes_buy, votes_sell
    if (score < 0 and 
        trend_sell_count >= min_trend_consensus and 
        entry_sell_count >= min_entry_consensus):
        return 'SELL', score, votes_buy, votes_sell
    return None, score, votes_buy, votes_sell



def compute_and_store_tf(symbol_id:int, df_1m:pd.DataFrame, tf:str):
    df_tf = resample_ohlcv(df_1m, tf)
    if df_tf is None or df_tf.empty:
        return
    upsert_candles_tf(symbol_id, tf, df_tf)
    calc_macd_and_store(symbol_id, tf)

def job_backfill_data(symbol_id:int, ticker:str, exchange:str):
    """Job riêng để lấy dữ liệu (có thể chạy lâu)"""
    print(f"📊 Starting data backfill for {ticker} ({exchange}), symbol_id={symbol_id}")
    
    try:
        result = backfill_1m(symbol_id, ticker, exchange, source="auto")
        print(f"✅ Backfill completed for {ticker}: {result} rows")
        return f"backfill-ok:{result}"
    except Exception as e:
        print(f"❌ Backfill failed for {ticker}: {e}")
        return f"backfill-error:{str(e)}"

def job_realtime_pipeline(symbol_id:int, ticker:str, exchange:str, strategy_id:int=1, force_run:bool=False):
    print(f"🚀 Starting job for {ticker} ({exchange}), symbol_id={symbol_id}")

    if not force_run and not is_market_open(exchange):
        print(f"⏸ Market closed for {ticker}")
        return "market-closed"

    # Simplified: use unified realtime pipeline (resample + MACD + thresholds)
    try:
        result = job_realtime_pipeline2(symbol_id, ticker, exchange, strategy_id=strategy_id, tf_threshold_name='1D4hr', force_run=force_run)
        print(f"✅ Realtime pipeline completed for {ticker}: {result}")
        return result
    except Exception as e:
        print(f"❌ Realtime pipeline error for {ticker}: {e}")
        return "realtime-error"

    # COMMENTED OUT MACD STRATEGY - UNCOMMENT BELOW TO RE-ENABLE
    """
    # Get strategy configuration for this symbol
    strategy_config = get_strategy_for_symbol(symbol_id)
    if strategy_config:
        print(f"🎯 Using strategy: {strategy_config.name} ({strategy_config.strategy_type.value})")
    else:
        print(f"⚠️ No strategy config found for symbol {symbol_id}, using default")

    #     # Kiểm tra xem có cần lấy dữ liệu không (chỉ khi cần thiết)
    #     from app.services.data_sources import get_data_coverage_days
    #     coverage_days, min_ts, max_ts = get_data_coverage_days(symbol_id)
    #     
    #     # Nếu không có data hoặc dữ liệu quá cũ (> 30 ngày cho US), enqueue job backfill riêng
    #     if exchange in ("NASDAQ", "NYSE"):
    #         import datetime as dt
    #         
    #         if not max_ts:
    #             # Không có data - cần backfill ngay
    #             print(f"📊 [{ticker}] No data found, enqueueing initial backfill job")
    #             from rq import Queue
    #             import redis
    #             import os
    #             r = redis.from_url(os.getenv('REDIS_URL'))
    #             q_backfill = Queue('backfill', connection=r)
    #             q_backfill.enqueue(job_backfill_data, symbol_id, ticker, exchange, job_timeout=1800)  # 30 phút
    #             return "backfill-enqueued"
    #         
    #         # Ensure max_ts is UTC-aware
    #         if max_ts.tzinfo is None:
    #             max_ts = max_ts.replace(tzinfo=dt.timezone.utc)
    #         days_since_last = (dt.datetime.now(dt.timezone.utc) - max_ts).days
    #         if days_since_last > 30:
    #             print(f"📊 [{ticker}] Data is {days_since_last} days old, enqueueing backfill job")
    #             from rq import Queue
    #             import redis
    #             import os
    #             r = redis.from_url(os.getenv('REDIS_URL'))
    #             q_backfill = Queue('backfill', connection=r)
    #             q_backfill.enqueue(job_backfill_data, symbol_id, ticker, exchange, job_timeout=1800)  # 30 phút
    #             return "backfill-enqueued"
    #     
    #     # Lấy dữ liệu mới nhất (chỉ khi cần thiết, thời gian ngắn)
    #     backfill_1m(symbol_id, ticker, exchange, source="auto")
    # 
    #     sig_map = {}
    #     for tf_name, tf in TF_LOGIC_MAP.items():
    #         print(f"🔍 [{ticker}] Processing TF logic={tf_name} (TF kỹ thuật={tf})")
    #         df_new_1m = load_new_candles_for_tf(symbol_id, tf)
    #         if df_new_1m.empty:
    #             print(f"⚠️ [{ticker}] No new 1m candles for TF {tf}")
    #             continue
    #         df_tf_new = resample_ohlcv(df_new_1m, tf, symbol_id)
    #         upsert_candles_tf(symbol_id, tf, df_tf_new)
    #         
    #         # Use advanced indicators based on strategy
    #         if strategy_config and (strategy_config.use_3m2_structure or strategy_config.use_bars_mt):
    #             calc_advanced_indicators_and_store(symbol_id, tf, strategy_config)
    #         else:
    #             calc_macd_and_store(symbol_id, tf)
    #         
    #         # Lấy giá close mới nhất của TF này
    #         # Lấy MACD mới nhất
    #         macd_val, signal_val, hist_val = get_latest_macd(symbol_id, tf) 
    #         last_close = df_tf_new['close'].iloc[-1] if not df_tf_new.empty else None
    #         raw_sig = eval_signal_with_strategy(symbol_id, tf, strategy_id, tf_name, strategy_config)
    #         
    #         # Sử dụng giá trị MACD gốc
    #         
    #         # Gửi Telegram zone alert nếu có zone mới
    #         if raw_sig and raw_sig != 'NEUTRAL':
    #             try:
    #                 from app.services.telegram_zone_service import telegram_zone_service
    #                 
    #                 # Lấy dữ liệu giá cho Telegram alert
    #                 price_data = {
    #                     'close': float(last_close) if last_close else 0,
    #                     'high': float(df_tf_new['high'].iloc[-1]) if not df_tf_new.empty else 0,
    #                     'low': float(df_tf_new['low'].iloc[-1]) if not df_tf_new.empty else 0,
    #                     'volume': float(df_tf_new['volume'].iloc[-1]) if not df_tf_new.empty else 0,
    #                     'candle_time': df_tf_new.index[-1] if not df_tf_new.empty else None
    #                 }
    #                 
    #                 # Tạo zone data với giá trị gốc
    #                 zone_data = {
    #                     'zone': raw_sig.lower(),
    #                     'fmacd': float(macd_val) if macd_val else 0,
    #                     'smacd': float(signal_val) if signal_val else 0,
    #                     'bars': float(hist_val) if hist_val else 0,
    #                     'signal_line': float(signal_val) if signal_val else 0
    #                 }
    #                 
    #                 # Gửi zone alert
    #                 telegram_zone_service.send_zone_alert(ticker, tf_name, zone_data, price_data)
    #                 
    #             except Exception as e:
    #                 print(f"⚠️ Telegram zone alert error for {ticker} {tf_name}: {e}")
    #         
    #         # Lưu giá trị MACD gốc
    #         sig_map[tf_name] = {
    #             "signal": normalize_signal(raw_sig),
    #             "close": last_close,
    #             "macd": macd_val,
    #             "signal_line": signal_val,
    #             "hist": hist_val
    #         }
    # 
    #     # Validate cross-timeframe synchronization if required
    #     if strategy_config and strategy_config.require_synchronization:
    #         signals_by_tf = {k: v["signal"] for k, v in sig_map.items()}
    #         if not validate_cross_timeframe_synchronization(signals_by_tf, strategy_config):
    #             print(f"⚠️ [{ticker}] Cross-timeframe synchronization failed, no signal generated")
    #             return "no-sync-signal"
    # 
    #     # Tổng hợp tín hiệu với strategy weights
    #     if strategy_config:
    #         tf_weights = strategy_config.tf_weights
    #         final_sig, score, vb, vs = aggregate_signals_with_weights({k: v["signal"] for k, v in sig_map.items()}, tf_weights)
    #     else:
    #         final_sig, score, vb, vs = aggregate_signals({k: v["signal"] for k, v in sig_map.items()})
    # 
    #     if final_sig:
    #         # Tạo tin nhắn chi tiết và dễ đọc
    #         signal_emoji = "🟢" if final_sig == "BUY" else "🔴"
    #         signal_text = "MUA" if final_sig == "BUY" else "BÁN"
    #         
    #         # Header với thông tin chính
    #         header = f"{signal_emoji} *{ticker}* - TÍN HIỆU {signal_text}\n"
    #         header += f"📊 Score: {score} | 🟢 Mua: {vb} | 🔴 Bán: {vs}\n"
    #         header += f"⏰ {pd.Timestamp.now(tz='Asia/Ho_Chi_Minh').strftime('%H:%M:%S %d/%m/%Y')}\n"
    #         header += "─" * 30 + "\n"
    #         
    #         # Chi tiết từng timeframe
    #         details = []
    #         for tf_name, data in sig_map.items():
    #             tf_emoji = "📈" if data['signal'] == "BUY" else "📉" if data['signal'] == "SELL" else "➖"
    #             tf_signal = "MUA" if data['signal'] == "BUY" else "BÁN" if data['signal'] == "SELL" else "KHÔNG"
    #             
    #             # Hiển thị giá trị chuẩn hóa (chính) và giá trị gốc (tham khảo)
    #             detail_line = (
    #                 f"{tf_emoji} *{tf_name}*: {tf_signal}\n"
    #                 f"   💰 Giá: {fmt_val(data['close'], '.2f')}\n"
    #                 f"   📊 MACD: {fmt_val(data['macd'], '.3f')} (norm)\n"
    #                 f"   📈 Signal: {fmt_val(data['signal_line'], '.3f')} (norm)\n"
    #                 f"   📉 Hist: {fmt_val(data['hist'], '.3f')} (norm)"
    #             )
    #             
    #             # Thêm thông tin giá trị gốc nếu có
    #             if 'macd_original' in data and data['macd_original'] is not None:
    #                 detail_line += (
    #                     f"\n   📊 MACD gốc: {fmt_val(data['macd_original'], '.3f')}\n"
    #                     f"   📈 Signal gốc: {fmt_val(data['signal_original'], '.3f')}\n"
    #                     f"   📉 Hist gốc: {fmt_val(data['hist_original'], '.3f')}"
    #                 )
    #             
    #             details.append(detail_line)
    #         
    #         detail_str = "\n\n".join(details)
    #         
    #         # Footer với lưu ý
    #         footer = "\n" + "─" * 30 + "\n"
    #         footer += "📊 *Giá trị MACD*: (norm) = chuẩn hóa [-1,1], gốc = giá trị thực\n"
    #         footer += "⚠️ *Lưu ý*: Chỉ là tín hiệu tham khảo, không phải lời khuyên đầu tư"
    #         
        # Xác định thị trường dựa trên exchange
        market_source = "VN" if exchange in ("HOSE", "HNX", "UPCOM") else "US"
        
        # Gửi tín hiệu với flag thị trường
        from app.services.telegram_market_service import telegram_market_service
        
        success = telegram_market_service.send_trading_signal(
            symbol=ticker,
            signal_type=final_sig,
            score=score,
            sig_map=sig_map,
            market_source=market_source,
            exchange=exchange,
            strategy_id=strategy_id
        )
        
        if not success:
            # Fallback to old method if new service fails
            print("⚠️ New Telegram service failed, using fallback")
            msg = header + detail_str + footer
            tg_send_text(msg)
            print(f"📢 {msg}")
        else:
            print(f"📢 Signal sent via new Telegram service for {ticker} ({market_source})")
        
        # Save signal to database
        save_signal_to_db(symbol_id, final_sig, score, strategy_id, sig_map)
    #         
    #         # Gửi multi-timeframe chart khi có tín hiệu
    #         try:
    #             from app.services.multi_timeframe_chart_service import multi_timeframe_chart_service
    #             
    #             # Chỉ gửi khi thị trường mở cửa
    #             if is_market_open(exchange)[0]:
    #                 print(f"📊 Market is open, sending multi-timeframe chart for {ticker}")
    #                 
    #                 # Lấy dữ liệu chart cho tất cả khung thời gian
    #                 chart_data = multi_timeframe_chart_service.get_chart_data_for_all_timeframes(ticker)
    #                 
    #                 if chart_data:
    #                     # Tạo signal info
    #                     signal_info = {
    #                         'signal_type': final_sig,
    #                         'score': score,
    #                         'buy_signals': vb,
    #                         'sell_signals': vs
    #                     }
    #                     
    #                     # Gửi multi-timeframe chart
    #                     success = multi_timeframe_chart_service.send_multi_timeframe_chart(
    #                         symbol=ticker,
    #                         chart_data=chart_data,
    #                         signal_info=signal_info
    #                     )
    #                     
    #                     if success:
    #                         print(f"✅ Multi-timeframe chart sent for {ticker}")
    #                     else:
    #                         print(f"❌ Failed to send multi-timeframe chart for {ticker}")
    #                 else:
    #                     print(f"⚠️ No chart data available for {ticker}")
    #             else:
    #                 print(f"📊 Market is closed, skipping multi-timeframe chart for {ticker}")
    #                 
    #         except Exception as e:
    #             print(f"⚠️ Multi-timeframe chart error for {ticker}: {e}")
    #         
    #         # Publish WebSocket update
    #         publish_websocket_update('new_signal', {
    #             'symbol_id': symbol_id,
    #             'ticker': ticker,
    #             'exchange': exchange,
    #             'signal_type': final_sig,
    #             'score': score,
    #             'buy_signals': vb,
    #             'sell_signals': vs,
    #             'timestamp': pd.Timestamp.now().isoformat(),
    #             'details': sig_map,
    #             'macd_values': {k: {
    #                 'macd': v.get('macd'),
    #                 'signal': v.get('signal_line'),
    #                 'hist': v.get('hist')
    #             } for k, v in sig_map.items()},
    #         })
    #         
    #         # Check and send zone alerts
    #         check_and_send_zone_alerts(symbol_id, ticker, exchange)
    #     else:
    #         print(f"ℹ️ [{ticker}] No consensus signal | {sig_map}")
    #         
    #         # Check zone alerts even without consensus signal
    #         check_and_send_zone_alerts(symbol_id, ticker, exchange)
    #         
    #         # Publish chart data update
    #         publish_websocket_update('symbol_data', {
    #             'symbol': ticker,
    #             'symbol_id': symbol_id,
    #             'exchange': exchange,
    #             'timestamp': pd.Timestamp.now().isoformat()
    #         })
    # 
    #     return final_sig or "no-signal"
    """

def check_and_send_zone_alerts(symbol_id, ticker, exchange):
    """Check for zone transitions and send alerts"""
    try:
        # Get latest price data
        with SessionLocal() as s:
            price_data = s.execute(text("""
                SELECT ts, open, high, low, close, volume
                FROM candles_1m
                WHERE symbol_id = :symbol_id
                AND ts >= DATE_SUB(NOW(), INTERVAL 10 DAY)
                ORDER BY ts DESC
                LIMIT 100
            """), {'symbol_id': symbol_id}).fetchall()
            
            macd_data = s.execute(text("""
                SELECT ts, macd, macd_signal, hist
                FROM indicators_macd
                WHERE symbol_id = :symbol_id
                AND ts >= DATE_SUB(NOW(), INTERVAL 10 DAY)
                ORDER BY ts DESC
                LIMIT 100
            """), {'symbol_id': symbol_id}).fetchall()
        
        if not price_data or not macd_data:
            return
        
        # Convert to DataFrame
        price_df = pd.DataFrame(price_data, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
        macd_df = pd.DataFrame(macd_data, columns=['ts', 'macd', 'macd_signal', 'hist'])
        
        # Analyze zone transitions
        analyze_zone_transition(ticker, price_df, macd_df, exchange)
        
    except Exception as e:
        print(f"❌ Zone alert check failed for {ticker}: {e}")

def analyze_zone_transition(symbol, price_data, macd_data, exchange):
    """Analyze zone transition and send alerts"""
    if len(price_data) < 5 or len(macd_data) < 5:
        print(f"⚠️ [{symbol}] Insufficient data for zone analysis: price={len(price_data)}, macd={len(macd_data)}")
        return
    
    # Get latest data
    latest_price = price_data['close'].iloc[-1]
    latest_macd = macd_data['macd'].iloc[-1]
    latest_signal = macd_data['macd_signal'].iloc[-1]
    latest_hist = macd_data['hist'].iloc[-1]
    
    # Determine current zone
    current_zone = "neutral"
    confidence = "low"
    
    if latest_macd > 0 and latest_signal > 0:
        if abs(latest_hist) > 0.5:
            current_zone = "igr"
            confidence = "high"
        elif abs(latest_hist) > 0.3:
            current_zone = "greed"
            confidence = "medium"
        else:
            current_zone = "bull"
            confidence = "low"
    elif latest_macd < 0 and latest_signal < 0:
        if abs(latest_hist) > 0.5:
            current_zone = "panic"
            confidence = "high"
        elif abs(latest_hist) > 0.3:
            current_zone = "fear"
            confidence = "medium"
        else:
            current_zone = "bear"
            confidence = "low"
    
    # Check for zone transitions in recent data
    recent_zones = []
    for i in range(-5, 0):
        if i < -len(macd_data):
            continue
        
        macd_val = macd_data['macd'].iloc[i]
        signal_val = macd_data['macd_signal'].iloc[i]
        hist_val = macd_data['hist'].iloc[i]
        
        zone = "neutral"
        if macd_val > 0 and signal_val > 0:
            if abs(hist_val) > 0.5:
                zone = "igr"
            elif abs(hist_val) > 0.3:
                zone = "greed"
            else:
                zone = "bull"
        elif macd_val < 0 and signal_val < 0:
            if abs(hist_val) > 0.5:
                zone = "panic"
            elif abs(hist_val) > 0.3:
                zone = "fear"
            else:
                zone = "bear"
        
        recent_zones.append(zone)
    
    # Detect transitions
    
    if len(recent_zones) >= 3:
        # Pattern 1: Approaching Bull Zone
        if (current_zone in ['bull', 'greed', 'igr'] and 
            any(z in ['neutral', 'bear', 'fear'] for z in recent_zones[-3:])):
            
            # Check momentum building
            momentum_count = sum(1 for z in recent_zones[-3:] if z in ['bull', 'greed', 'igr'])
            if momentum_count >= 2:
                # Gửi zone alert với flag thị trường
                market_source = "VN" if exchange in ("HOSE", "HNX", "UPCOM") else "US"
                from app.services.telegram_market_service import telegram_market_service
                telegram_market_service.send_zone_alert(symbol, current_zone, latest_price, latest_macd, market_source, confidence)
        
        # Pattern 2: Approaching Bear Zone
        elif (current_zone in ['bear', 'fear', 'panic'] and 
              any(z in ['neutral', 'bull', 'greed'] for z in recent_zones[-3:])):
            
            # Check momentum building
            momentum_count = sum(1 for z in recent_zones[-3:] if z in ['bear', 'fear', 'panic'])
            if momentum_count >= 2:
                # Gửi zone alert với flag thị trường
                market_source = "VN" if exchange in ("HOSE", "HNX", "UPCOM") else "US"
                from app.services.telegram_market_service import telegram_market_service
                telegram_market_service.send_zone_alert(symbol, current_zone, latest_price, latest_macd, market_source, confidence)
        
        # Pattern 3: Strong Zone Confirmation
        elif (current_zone in ['igr', 'panic'] and confidence == "high"):
            market_source = "VN" if exchange in ("HOSE", "HNX", "UPCOM") else "US"
            from app.services.telegram_market_service import telegram_market_service
            telegram_market_service.send_zone_alert(symbol, current_zone, latest_price, latest_macd, market_source, confidence)
        
        # Pattern 4: Strong Momentum in Bull Zone
        elif (current_zone in ['greed', 'igr'] and confidence in ["medium", "high"] and 
              sum(1 for z in recent_zones[-3:] if z in ['greed', 'igr']) >= 2):
            market_source = "VN" if exchange in ("HOSE", "HNX", "UPCOM") else "US"
            from app.services.telegram_market_service import telegram_market_service
            telegram_market_service.send_zone_alert(symbol, current_zone, latest_price, latest_macd, market_source, confidence)
        
        # Pattern 5: Strong Momentum in Bear Zone  
        elif (current_zone in ['fear', 'panic'] and confidence in ["medium", "high"] and 
              sum(1 for z in recent_zones[-3:] if z in ['fear', 'panic']) >= 2):
            market_source = "VN" if exchange in ("HOSE", "HNX", "UPCOM") else "US"
            from app.services.telegram_market_service import telegram_market_service
            telegram_market_service.send_zone_alert(symbol, current_zone, latest_price, latest_macd, market_source, confidence)

def tg_send_zone_alert(symbol, alert_type, zone, price, macd, confidence="medium"):
    """Send zone alert to Telegram"""
    import os
    import requests
    
    TG_TOKEN = os.getenv('TG_TOKEN')
    TG_CHAT_ID = os.getenv('TG_CHAT_ID')
    
    if not TG_TOKEN or not TG_CHAT_ID:
        print("⚠️ Telegram not configured, skipping zone alert")
        return
    
    zone_icons = {
        "igr": "🚀🔥",
        "greed": "💰🟢", 
        "bull": "🐂📈",
        "pos": "👍🟢",
        "neutral": "⚪️😐",
        "neg": "👎🔻",
        "bear": "🐻📉",
        "fear": "😨🔴",
        "panic": "🆘😱"
    }
    
    confidence_icons = {
        "high": "🎯",
        "medium": "⚠️",
        "low": "❓"
    }
    
    zone_icon = zone_icons.get(zone, "❓")
    confidence_icon = confidence_icons.get(confidence, "❓")
    
    # Create alert message
    message = f"<b>🎯 ZONE ALERT - {symbol}</b>\n\n"
    
    if alert_type == "approaching_bull":
        message += f"<b>🚀 Chuẩn bị vào Bull Zone!</b>\n"
        message += f"<b>💡 Action:</b> Chuẩn bị LONG position\n"
        message += f"<b>🎯 Target:</b> Bull/Greed zones\n"
    elif alert_type == "approaching_bear":
        message += f"<b>🐻 Chuẩn bị vào Bear Zone!</b>\n"
        message += f"<b>💡 Action:</b> Chuẩn bị SHORT position\n"
        message += f"<b>🎯 Target:</b> Bear/Fear zones\n"
    elif alert_type == "strong_zone":
        message += f"<b>⚡ Strong Zone Confirmed!</b>\n"
        message += f"<b>💡 Action:</b> Strong trend continuation\n"
        message += f"<b>🎯 Target:</b> Ride the momentum\n"
    
    message += f"\n<b>🎯 Zone:</b> {zone_icon} {zone.upper()}\n"
    message += f"<b>🎯 Confidence:</b> {confidence_icon} {confidence.upper()}\n"
    # Determine currency based on symbol
    is_vn_stock = symbol.endswith(('VN', 'VNM', 'VCB', 'VIC', 'VHM', 'VJC', 'VRE', 'VPI', 'VPB', 'VSH', 'VTO', 'VHC', 'VND', 'VOS', 'VSC', 'VSI', 'VTB', 'VTV', 'VWS', 'VXF', 'VYS', 'VZB', 'VZC', 'VZD', 'VZE', 'VZF', 'VZG', 'VZH', 'VZI', 'TPB', 'VGC'))
    if is_vn_stock:
        currency = "₫"
        price_display = price * 1000  # Convert to VND (multiply by 1000)
    else:
        currency = "$"
        price_display = price
    message += f"<b>💰 Price:</b> {currency}{price_display:.0f}\n"
    message += f"<b>📈 MACD:</b> {macd:.3f}\n"
    message += f"<b>⏰ Time:</b> {pd.Timestamp.now(tz='Asia/Ho_Chi_Minh').strftime('%H:%M:%S %d/%m/%Y')}\n\n"
    message += "<i>⚠️ Zone alert - Chỉ là cảnh báo tham khảo</i>"
    
    # Send to Telegram
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "HTML"})
        if response.status_code == 200:
            print(f"✅ Zone alert sent to Telegram for {symbol}")
        else:
            print(f"❌ Zone alert failed for {symbol}: {response.status_code}")
    except Exception as e:
        print(f"❌ Zone alert error for {symbol}: {e}")

def load_new_candles_for_tf(symbol_id, tf):
    """Chỉ load phần 1m mới hơn cây TF cuối cùng đã lưu"""
    with SessionLocal() as s:
        last_tf_ts = s.execute(text("""
            SELECT MAX(ts) FROM candles_tf
            WHERE symbol_id=:sid AND timeframe=:tf
        """), {'sid': symbol_id, 'tf': tf}).scalar()

    with SessionLocal() as s:
        if last_tf_ts:
            # Get 1m candles from last TF timestamp onwards
            rows = s.execute(text("""
                SELECT ts, open, high, low, close, volume
                FROM candles_1m
                WHERE symbol_id=:sid AND ts >= :last_tf_ts
                ORDER BY ts ASC
            """), {'sid': symbol_id, 'last_tf_ts': last_tf_ts}).fetchall()
            
            # If we have rows and the first row has the same timestamp as last_tf_ts,
            # it means the last TF candle was already processed, so skip it
            if rows and len(rows) > 0 and rows[0][0] == last_tf_ts:
                rows = rows[1:]  # Skip the first row (already processed)
        else:
            rows = s.execute(text("""
                SELECT ts, open, high, low, close, volume
                FROM candles_1m
                WHERE symbol_id=:sid
                ORDER BY ts ASC
            """), {'sid': symbol_id}).fetchall()

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=['ts','open','high','low','close','volume'])
    df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df['ts'], utc=True))).drop(columns=['ts'])
    return df

def load_recent_candles_tf(symbol_id: int, tf: str, max_bars: int = 300):
    """Load recent aggregated candles for a timeframe from DB to provide indicator history."""
    try:
        if SessionLocal is None:
            from app.db import init_db
            database_url = os.getenv("DATABASE_URL")
            init_db(database_url)
        with SessionLocal() as s:
            rows = s.execute(text(
                """
                SELECT ts, open, high, low, close, volume
                FROM candles_tf
                WHERE symbol_id=:sid AND timeframe=:tf
                ORDER BY ts DESC
                LIMIT :lim
                """
            ), {'sid': symbol_id, 'tf': tf, 'lim': int(max_bars)}).fetchall()
        if not rows:
            return pd.DataFrame()
        rows = rows[::-1]
        df = pd.DataFrame(rows, columns=['ts','open','high','low','close','volume'])
        df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df['ts'], utc=True))).drop(columns=['ts'])
        return df
    except Exception:
        return pd.DataFrame()

def load_candles_1m_df(symbol_id:int, lookback_minutes:int=None):
    """Lấy dữ liệu 1m gần nhất từ DB, chỉ trong cửa sổ lookback_minutes để giảm tải."""
    try:
        print(f"🔍 Loading candles_1m for symbol_id {symbol_id}")
        # Allow override via env, default 1440 minutes (~1 day)
        if lookback_minutes is None:
            try:
                lookback_minutes = int(os.getenv('RT_LOOKBACK_MINUTES', '1440'))
            except Exception:
                lookback_minutes = 1440
        
        # Validate SessionLocal
        if SessionLocal is None:
            print(f"❌ SessionLocal is None, initializing database...")
            from app.db import init_db
            database_url = os.getenv("DATABASE_URL", "mysql+pymysql://trader:password@localhost:3306/trading_signals")
            init_db(database_url)
            print(f"✅ Database initialized")
        
        with SessionLocal() as s:
            print(f"🔗 Database session created for symbol_id {symbol_id}")
            # Tính mốc thời gian bắt đầu theo max(ts) để dùng index
            max_ts = s.execute(text("""
                SELECT MAX(ts) FROM candles_1m WHERE symbol_id=:sid
            """), {'sid': symbol_id}).scalar()
            if max_ts:
                rows = s.execute(text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_1m
                    WHERE symbol_id=:sid AND ts >= DATE_SUB(:max_ts, INTERVAL :lb MINUTE)
                    ORDER BY ts ASC
                """), {'sid': symbol_id, 'max_ts': max_ts, 'lb': int(lookback_minutes)}).fetchall()
            else:
                rows = []
            
            print(f"📊 Retrieved {len(rows)} rows from database")
            
        if not rows:
            print(f"⚠️  No rows found for symbol_id {symbol_id}")
            return pd.DataFrame()
            
        df = pd.DataFrame(rows, columns=['ts','open','high','low','close','volume'])
        df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df['ts'], utc=True))).drop(columns=['ts'])
        
        print(f"✅ Created DataFrame with shape {df.shape}")
        return df
        
    except Exception as e:
        print(f"❌ Error loading candles_1m for symbol_id {symbol_id}: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return pd.DataFrame()

def upsert_candles_tf(symbol_id, tf, df_tf):
    try:
        print(f"💾 Upserting {len(df_tf)} candles for symbol_id {symbol_id}, timeframe {tf}")
        
        # Validate SessionLocal
        if SessionLocal is None:
            print(f"❌ SessionLocal is None, initializing database...")
            from app.db import init_db
            database_url = os.getenv("DATABASE_URL", "mysql+pymysql://trader:password@localhost:3306/trading_signals")
            init_db(database_url)
            print(f"✅ Database initialized")
        
        with SessionLocal() as s:
            print(f"🔗 Database session created for upsert_candles_tf")
            
            for i, (ts, row) in enumerate(df_tf.iterrows()):
                try:
                    s.execute(text("""
                        INSERT INTO candles_tf (symbol_id, timeframe, ts, open, high, low, close, volume)
                        VALUES (:sid, :tf, :ts, :o, :h, :l, :c, :v)
                        ON DUPLICATE KEY UPDATE open=:o, high=:h, low=:l, close=:c, volume=:v
                    """), {
                        'sid': symbol_id, 'tf': tf, 'ts': ts.to_pydatetime(),
                        'o': float(row.open), 'h': float(row.high), 'l': float(row.low),
                        'c': float(row.close), 'v': float(row.volume)
                    })
                except Exception as row_error:
                    print(f"❌ Error processing row {i} for {tf}: {row_error}")
                    print(f"   Row data: {row}")
                    continue
            
            print(f"💾 Committing {len(df_tf)} candles for {tf}")
            s.commit()
            print(f"✅ Successfully upserted candles for {tf}")
            
    except Exception as e:
        print(f"❌ Error upserting candles_tf for symbol_id {symbol_id}, timeframe {tf}: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        raise e

def get_latest_macd(symbol_id, tf):
    with SessionLocal() as s:
        row = s.execute(text("""
            SELECT macd, macd_signal, hist
            FROM indicators_macd
            WHERE symbol_id=:sid AND timeframe=:tf
            ORDER BY ts DESC LIMIT 1
        """), {'sid': symbol_id, 'tf': tf}).first()
    return row if row else (None, None, None)

def calc_macd_and_store(symbol_id, tf):
    with SessionLocal() as s:
        rows = s.execute(text("""
          SELECT ts, close FROM candles_tf
          WHERE symbol_id=:sid AND timeframe=:tf ORDER BY ts ASC
        """), {'sid': symbol_id, 'tf': tf}).fetchall()
    if not rows:
        return
    df = pd.DataFrame(rows, columns=['ts','close'])
    df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df['ts'], utc=True)))
    
    # Tính MACD (mặc định bộ tham số 7-72-144)
    macd_df = compute_macd_772144(df['close'])
    
    with SessionLocal() as s:
        for ts, r in macd_df.iterrows():
            macd_val = float(r['macd'])
            signal_val = float(r['signal'])
            hist_val = float(r['hist'])
            
            s.execute(text("""
            INSERT INTO indicators_macd (symbol_id, timeframe, ts, macd, macd_signal, hist)
            VALUES (:sid, :tf, :ts, :m, :sg, :h)
            ON DUPLICATE KEY UPDATE macd=:m, macd_signal=:sg, hist=:h
            """), {
                'sid': symbol_id, 'tf': tf, 'ts': ts.to_pydatetime(),
                'm': macd_val, 'sg': signal_val, 'h': hist_val
            })
        s.commit()

def eval_signal(symbol_id, tf, strategy_id, tf_threshold_name):
    with SessionLocal() as s:
        m = s.execute(text("""
          SELECT ts, macd, macd_signal, hist
          FROM indicators_macd
          WHERE symbol_id=:sid AND timeframe=:tf
          ORDER BY ts DESC LIMIT 1
        """), {'sid': symbol_id, 'tf': tf}).mappings().first()
    if not m:
        return None
        
    rules = load_threshold_rules(strategy_id, tf_threshold_name)
    try:
        debug_helper.log_step(
            f"MACD latest for tf={tf}",
            {
                'ts': str(m['ts']),
                'macd': float(m['macd']),
                'signal': float(m['macd_signal']),
                'hist': float(m['hist'])
            }
        )
    except Exception:
        pass
    f_zone = match_zone(m['macd'], rules, 'fmacd')
    s_zone = match_zone(m['macd_signal'], rules, 'smacd')
    bars_zone = match_zone(abs(m['hist']), rules, 'bars')
    try:
        debug_helper.log_step(
            f"Zone match for tf={tf}",
            {
                'fmacd_zone': f_zone,
                'smacd_zone': s_zone,
                'bars_zone': bars_zone
            }
        )
    except Exception:
        pass
    return make_signal(f_zone, s_zone, bars_zone)

def get_macd_direction(symbol_id: int, tf: str):
    """Return 'BUY' if hist > 0, 'SELL' if hist < 0, else None, using latest MACD row."""
    with SessionLocal() as s:
        m = s.execute(text(
            """
            SELECT ts, macd, macd_signal, hist
            FROM indicators_macd
            WHERE symbol_id=:sid AND timeframe=:tf
            ORDER BY ts DESC LIMIT 1
            """
        ), {'sid': symbol_id, 'tf': tf}).mappings().first()
    if not m:
        return None
    try:
        debug_helper.log_step(
            f"MACD latest for tf={tf}",
            {'ts': str(m['ts']), 'macd': float(m['macd']), 'signal': float(m['macd_signal']), 'hist': float(m['hist'])}
        )
    except Exception:
        pass
    if m['hist'] is None:
        return None
    if float(m['hist']) > 0:
        return 'BUY'
    if float(m['hist']) < 0:
        return 'SELL'
    return None

def _get_tf_threshold(tf: str, macd_config: dict) -> float:
    """Map timeframe to per-TF threshold from workflow config; fallback to 0.33."""
    if not isinstance(macd_config, dict):
        return 0.33
    key_map = {
        '1m': 'bubefsm1',
        '2m': 'bubefsm2',
        '5m': 'bubefsm5',
        '15m': 'bubefsm15',
        '30m': 'bubefsm30',
        '1h': 'bubefs_1h'
    }
    key = key_map.get(tf)
    try:
        v = macd_config.get(key)
        if v is None:
            return 0.33
        return float(v)
    except Exception:
        return 0.33

def _get_latest_macd_row(symbol_id: int, tf: str):
    with SessionLocal() as s:
        m = s.execute(text(
            """
            SELECT ts, macd, macd_signal, hist
            FROM indicators_macd
            WHERE symbol_id=:sid AND timeframe=:tf
            ORDER BY ts DESC LIMIT 1
            """
        ), {'sid': symbol_id, 'tf': tf}).mappings().first()
    return m

def decide_direction_by_thresholds(symbol_id: int, tf: str, macd_config: dict):
    """Use per-TF thresholds from workflow to decide BUY/SELL: both fmacd and smacd must exceed threshold magnitude."""
    m = _get_latest_macd_row(symbol_id, tf)
    if not m:
        return None
    thr = _get_tf_threshold(tf, macd_config)
    fmacd = float(m['macd']) if m['macd'] is not None else 0.0
    smacd = float(m['macd_signal']) if m['macd_signal'] is not None else 0.0
    try:
        debug_helper.log_step(f"Thresholds for tf={tf}", {'thr': thr, 'fmacd': fmacd, 'smacd': smacd})
    except Exception:
        pass
    # Bull when either above +thr; Bear when either below -thr (OR logic)
    if fmacd >= thr or smacd >= thr:
        return 'BUY'
    if fmacd <= -thr or smacd <= -thr:
        return 'SELL'
    return None

def eval_signal_with_strategy(symbol_id, tf, strategy_id, tf_threshold_name, strategy_config=None):
    """Evaluate signal with strategy-specific logic and MACD normalization"""
    with SessionLocal() as s:
        m = s.execute(text("""
          SELECT ts, macd, macd_signal, hist
          FROM indicators_macd
          WHERE symbol_id=:sid AND timeframe=:tf
          ORDER BY ts DESC LIMIT 1
        """), {'sid': symbol_id, 'tf': tf}).mappings().first()
    if not m:
        return None
    
    # Sử dụng hệ thống thresholds mới cho từng symbol
    from app.services.signal_engine import match_zone_with_thresholds
    
    f_zone = match_zone_with_thresholds(m['macd'], symbol_id, tf, 'fmacd')
    s_zone = match_zone_with_thresholds(m['macd_signal'], symbol_id, tf, 'smacd')
    bars_zone = match_zone_with_thresholds(abs(m['hist']), symbol_id, tf, 'bars')
    
    # Use strategy-specific signal generation
    return make_signal(f_zone, s_zone, bars_zone, strategy_config)

def calc_advanced_indicators_and_store(symbol_id, tf, strategy_config):
    """Calculate and store advanced indicators based on strategy"""
    with SessionLocal() as s:
        rows = s.execute(text("""
          SELECT ts, open, high, low, close, volume FROM candles_tf
          WHERE symbol_id=:sid AND timeframe=:tf ORDER BY ts ASC
        """), {'sid': symbol_id, 'tf': tf}).fetchall()
    if not rows:
        return
    
    df = pd.DataFrame(rows, columns=['ts','open','high','low','close','volume'])
    df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df['ts'], utc=True))).drop(columns=['ts'])
    
    # Calculate advanced indicators
    advanced_df = compute_advanced_indicators(df, symbol_id, strategy_config)
    
    # Store in database (this would need additional tables for advanced indicators)
    # For now, just store basic MACD
    calc_macd_and_store(symbol_id, tf)

def aggregate_signals_with_weights(sig_map: dict, tf_weights: dict):
    """Aggregate signals with custom timeframe weights - Khung lớn tìm xu hướng, khung nhỏ tìm điểm vào"""
    score = 0
    votes_buy, votes_sell = 0, 0
    
    # Phân loại khung giờ
    trend_tfs = {'1D4hr', '1D1hr', '1D30Min'}  # Khung lớn - tìm xu hướng
    entry_tfs = {'1D15Min', '1D5Min', '1D2Min', '1D1Min'}  # Khung nhỏ - tìm điểm vào
    
    trend_buy_count, trend_sell_count = 0, 0
    entry_buy_count, entry_sell_count = 0, 0
    
    for tf_name, sig in sig_map.items():
        if not sig:
            continue
        w = tf_weights.get(tf_name, 1)
        if sig == 'BUY':
            score += w
            votes_buy += 1
            if tf_name in trend_tfs:
                trend_buy_count += 1
            elif tf_name in entry_tfs:
                entry_buy_count += 1
        elif sig == 'SELL':
            score -= w
            votes_sell += 1
            if tf_name in trend_tfs:
                trend_sell_count += 1
            elif tf_name in entry_tfs:
                entry_sell_count += 1
    
    # Yêu cầu: xu hướng từ khung lớn + điểm vào từ khung nhỏ
    min_trend_consensus = 2  # Ít nhất 2 khung lớn
    min_entry_consensus = 2  # Ít nhất 2 khung nhỏ
    
    if (score > 0 and 
        trend_buy_count >= min_trend_consensus and 
        entry_buy_count >= min_entry_consensus):
        return 'BUY', score, votes_buy, votes_sell
    if (score < 0 and 
        trend_sell_count >= min_trend_consensus and 
        entry_sell_count >= min_entry_consensus):
        return 'SELL', score, votes_buy, votes_sell
    return None, score, votes_buy, votes_sell

def get_exchange_for_symbol(symbol_id: int) -> str:
    """
    Lấy exchange cho symbol_id
    """
    with SessionLocal() as s:
        row = s.execute(text("""
            SELECT exchange
            FROM symbols
            WHERE id = :sid
        """), {'sid': symbol_id}).mappings().first()

    if not row or not row['exchange']:
        return 'NASDAQ'  # Default to NASDAQ

    return row['exchange'].upper()

def get_market_for_symbol(symbol_id: int) -> str:
    """
    Trả về 'VN' hoặc 'US' (hoặc tên thị trường khác) cho symbol_id.
    Dựa vào cột exchange trong bảng symbols.
    """
    exchange = get_exchange_for_symbol(symbol_id)
    
    if not exchange:
        return 'US'  # Default

    # Mapping exchange -> market
    if exchange in ('HOSE', 'HNX', 'UPCOM'):
        return 'VN'
    elif exchange in ('NASDAQ', 'NYSE', 'AMEX'):
        return 'US'
    else:
        return 'US'  # Default to US
def job_realtime_pipeline2(symbol_id:int, ticker:str, exchange:str, strategy_id:int, tf_threshold_name:str, force_run:bool=False):
    """Job chạy mỗi phút: lấy 1m mới, resample, tính MACD (theo macd_config nếu có), so sánh threshold, gửi tín hiệu"""
   
    try:
        debug_helper.log_step(f"Starting realtime pipeline for {ticker}", {
            'symbol_id': symbol_id,
            'ticker': ticker,
            'exchange': exchange,
            'strategy_id': strategy_id,
            'tf_threshold_name': tf_threshold_name
        })
        
        # 1. Lấy 1m trực tiếp từ API cho realtime (không đọc DB)
        debug_helper.log_step(f"Fetching realtime 1m from API for {ticker}")
        from app.services.data_sources import get_realtime_df_1m
        df_1m = get_realtime_df_1m(ticker, exchange, minutes=int(os.getenv('RT_FETCH_MINUTES', '180')))
        if df_1m is None or df_1m.empty:
            debug_helper.log_step(f"Realtime API empty for {ticker}", "Fallback to small DB window")
            df_1m = load_candles_1m_df(symbol_id)
        debug_helper.log_step(f"Realtime source ready for {ticker}", f"Rows: {len(df_1m)}")
        
        if df_1m.empty:
            debug_helper.log_step(f"No candles in DB for {ticker}", "Returning no-data")
            return "no-data"
            
        try:
            # Lấy macd_config nếu có (từ active workflows)
            macd_config = _get_macd_config_for_symbol_from_workflows(ticker)
            debug_helper.log_step(f"MACD config for {ticker}", macd_config or {})
            fast = (macd_config or {}).get('fastPeriod', 7)
            slow = (macd_config or {}).get('slowPeriod', 72)
            signal = (macd_config or {}).get('signalPeriod', 144)

            # Khung thời gian áp dụng MACD Multi-TF 3/5 (bỏ 1m)
            tf_work = ['2m','5m','15m','30m','1h']

            per_tf_signals = {}
            for tf in tf_work:
                debug_helper.log_step(f"Processing timeframe {tf} for {ticker}")
                
                try:
                    df_tf_new = resample_ohlcv(df_1m, tf)
                    debug_helper.log_step(f"Resampled {tf} for {ticker}", f"Rows: {len(df_tf_new)}")
                            
                    # Persist new TF candles
                    upsert_candles_tf(symbol_id, tf, df_tf_new)
                    debug_helper.log_step(f"Upserted {tf} candles for {ticker}")
                            
                    # Ghép lịch sử TF để đủ lookback cho MACD
                    lookback_bars = max(slow, signal) * 3
                    df_tf_hist = load_recent_candles_tf(symbol_id, tf, lookback_bars)
                    if not df_tf_hist.empty:
                        df_tf_all = pd.concat([df_tf_hist, df_tf_new])
                        df_tf_all = df_tf_all[~df_tf_all.index.duplicated(keep='last')].sort_index()
                    else:
                        df_tf_all = df_tf_new

                    # Tính và lưu MACD theo bộ tham số trên toàn chuỗi, nhưng chỉ lưu các bar mới
                    _calc_macd_custom_and_store(symbol_id, tf, df_tf_all['close'], fast, slow, signal)
                    debug_helper.log_step(f"Calculated MACD for {tf} {ticker}")
                            
                    # Determine direction by per-TF thresholds from workflow (fmacd/smacd must cross)
                    dir_sig = decide_direction_by_thresholds(symbol_id, tf, macd_config or {})
                    per_tf_signals[tf] = dir_sig
                    debug_helper.log_step(f"Evaluated signals for {tf} {ticker}", dir_sig)
                            
                except Exception as tf_error:
                    debug_helper.log_step(f"Error processing {tf} for {ticker}", error=tf_error)
                    continue
            
            # Đồng thuận 3/5 khung (bỏ 1m)
            votes_buy = sum(1 for v in per_tf_signals.values() if v == 'BUY')
            votes_sell = sum(1 for v in per_tf_signals.values() if v == 'SELL')
            final_sig = None
            if votes_buy >= 3:
                final_sig = 'BUY'
            elif votes_sell >= 3:
                final_sig = 'SELL'

            debug_helper.log_step(f"Consensus 3/5 for {ticker}", {
                'signals': per_tf_signals,
                'votes_buy': votes_buy,
                'votes_sell': votes_sell,
                'final': final_sig
            })

            if final_sig:
                # Lưu tín hiệu tổng hợp
                try:
                    save_signal_to_db(symbol_id, final_sig, votes_buy - votes_sell, strategy_id, {
                        k: {'signal': v} for k, v in per_tf_signals.items()
                    })
                except Exception as e:
                    print(f"⚠️ save_signal_to_db error for {ticker}: {e}")
                # Phase 3: gửi notification qua Observer system (không thay đổi đường lưu DB cũ)
                try:
                    from worker.integration import notify_signal as _notify
                    _ = _notify(
                        symbol=ticker,
                        timeframe='multi',
                        signal_type=final_sig,
                        confidence=float(max(votes_buy, votes_sell) / 5.0),
                        strength=float(abs(votes_buy - votes_sell)),
                        strategy_name='MACD_Multi_TF_Consensus',
                        details={
                            'per_tf_signals': per_tf_signals,
                            'votes_buy': votes_buy,
                            'votes_sell': votes_sell,
                            'exchange': exchange
                        }
                    )
                except Exception as _e:
                    print(f"⚠️ notify_signal error for {ticker}: {_e}")

            debug_helper.log_step(f"Completed pipeline for {ticker}", "Returning success")
            return final_sig or "no-consensus"
            
        except Exception as e:
            debug_helper.log_step(f"Pipeline error for {ticker}", error=e)
            print(f"Error in pipeline for {ticker}: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return "error"
            
    except Exception as e:
        debug_helper.log_step(f"Pipeline error for {ticker}", error=e)
        print(f"Error in pipeline for {ticker}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return "error"

def _get_macd_config_for_symbol_from_workflows(symbol: str):
    """Đọc macd_config từ bảng workflows nếu có node macd-multi chứa symbol."""
    try:
        import json
        with SessionLocal() as s:
            rows = s.execute(text("""
                SELECT name, nodes, properties FROM workflows
                WHERE status='active' AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
            """)).fetchall()

        preferred = [r for r in rows if (r[0] or '').strip().lower() == '25symbols']
        ordered = preferred + [r for r in rows if r not in preferred]

        for name, nodes_json, props_json in ordered:
            nodes = json.loads(nodes_json)
            props = json.loads(props_json)
            macd_nodes = [n for n in nodes if n.get('type') == 'macd-multi']
            for node in macd_nodes:
                cfg = props.get(node['id'], {})
                for sc in cfg.get('symbolThresholds', []):
                    if isinstance(sc, dict) and sc.get('symbol', '').upper() == symbol.upper():
                        merged = dict(cfg)
                        merged.update(sc)
                        merged['__workflow_name'] = name
                        return merged
        return None
    except Exception as e:
        print(f"⚠️ get macd_config error for {symbol}: {e}")
        return None

def _calc_macd_custom_and_store(symbol_id: int, tf: str, close_series, fast: int, slow: int, signal: int):
    """Tính MACD theo tham số custom và lưu indicators_macd."""
    try:
        import pandas as _pd
        # Nếu bộ tham số khớp preset 7-72-144 thì dùng hàm tối ưu sẵn
        if (fast, slow, signal) == (7, 72, 144):
            macd_df = compute_macd_772144(close_series)
        else:
            # Tự tính MACD theo tham số (EMA-based)
            if close_series is None or len(close_series) == 0:
                return
            ser = _pd.Series(close_series).copy()
            # Ensure index aligns with candles (assume close_series has DateTimeIndex)
            if not hasattr(close_series, 'index'):
                return
            ser.index = close_series.index
            ema_fast = ser.ewm(span=fast, adjust=False).mean()
            ema_slow = ser.ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            hist = macd_line - signal_line
            macd_df = _pd.DataFrame({
                'macd': macd_line,
                'signal': signal_line,
                'hist': hist
            })
        if macd_df is None or macd_df.empty:
            return
        # Log last few MACD points for visibility
        try:
            tail = macd_df.tail(3)
            for ts, r in tail.iterrows():
                debug_helper.log_step(
                    f"MACD calc {tf}",
                    {
                        'ts': str(ts),
                        'macd': float(r['macd']),
                        'signal': float(r['signal']),
                        'hist': float(r['hist']),
                        'fast': fast,
                        'slow': slow,
                        'sig': signal
                    }
                )
        except Exception:
            pass
        with SessionLocal() as s:
            for ts, r in macd_df.iterrows():
                s.execute(text("""
                    INSERT INTO indicators_macd (symbol_id, timeframe, ts, macd, macd_signal, hist)
                    VALUES (:sid, :tf, :ts, :m, :sg, :h)
                    ON DUPLICATE KEY UPDATE macd=:m, macd_signal=:sg, hist=:h
                """), {
                    'sid': symbol_id,
                    'tf': tf,
                    'ts': ts.to_pydatetime(),
                    'm': float(r['macd']),
                    'sg': float(r['signal']),
                    'h': float(r['hist'])
                })
            s.commit()
    except Exception as e:
        print(f"⚠️ calc_macd_custom_and_store error {symbol_id} {tf}: {e}")

def job_backfill_all(days:int=365, source:str="auto"):
    """
    Backfill toàn bộ mã active trong bảng symbols.
    days: số ngày cần lấy (mặc định 365 ~ 1 năm)
    source: 'auto' hoặc 'vnstock' / 'polygon' / 'yfinance'
    """
    with SessionLocal() as s:
        symbols = s.execute(text("SELECT id, ticker, exchange FROM symbols WHERE active=1")).fetchall()
    total_inserted = 0
    for sid, ticker, exchange in symbols:
        try:
            print(f"[Backfill] {ticker} ({exchange})...")
            count = backfill_1m(sid, ticker, exchange, source=source)
            print(f"  -> {count} rows inserted/updated")
            total_inserted += count
        except Exception as e:
            print(f"  !! Error backfilling {ticker}: {e}")
    return total_inserted

def job_backfill_symbol(symbol_id:int, ticker:str, exchange:str, days:int=365, source:str="auto"):
    """
    Backfill cho 1 mã cụ thể
    """
    try:
        from app.services.logger import log_backfill_success, log_backfill_error
        
        print(f"[Backfill] {ticker} ({exchange})...")
        count = backfill_1m(symbol_id, ticker, exchange, source=source)
        
        if count > 0:
            log_backfill_success(ticker, exchange, count, {
                'symbol_id': symbol_id,
                'source': source,
                'days': days
            })
        else:
            log_backfill_error(ticker, exchange, Exception("No data returned"), {
                'symbol_id': symbol_id,
                'source': source,
                'days': days
            })
        
        print(f"  -> {count} rows inserted/updated")
        return count
    except Exception as e:
        from app.services.logger import log_backfill_error
        log_backfill_error(ticker, exchange, e, {
            'symbol_id': symbol_id,
            'source': source,
            'days': days
        })
        print(f"  !! Error backfilling {ticker}: {e}")
        return 0

def job_backfill_full_pipeline(days:int=365, source:str="auto", strategy_id:int=1, tf_threshold_name:str="1D4hr"):
    """
    Backfill toàn bộ mã active:
    - Lấy dữ liệu 1m (days ngày)
    - Resample lên các TF
    - Tính MACD
    - So sánh threshold
    - Lưu & gửi tín hiệu
    """
    try:
        print(f"🚀 Starting backfill_full_pipeline...")
        print(f"   Parameters: days={days}, source={source}, strategy_id={strategy_id}, tf_threshold_name={tf_threshold_name}")
        
        # Validate SessionLocal
        if SessionLocal is None:
            print(f"❌ SessionLocal is None, initializing database...")
            from app.db import init_db
            database_url = os.getenv("DATABASE_URL", "mysql+pymysql://trader:password@localhost:3306/trading_signals")
            init_db(database_url)
            print(f"✅ Database initialized")
        
        print(f"🔗 Creating database session for symbols query...")
        with SessionLocal() as s:
            print(f"📊 Querying active symbols...")
            symbols = s.execute(text("SELECT id, ticker, exchange FROM symbols WHERE active=1")).fetchall()
            print(f"✅ Retrieved {len(symbols)} active symbols")
        
        total_symbols = len(symbols)
        successful_symbols = 0
        failed_symbols = []
        
        print(f"🚀 Starting backfill for {total_symbols} symbols...")
        
        for i, (sid, ticker, exchange) in enumerate(symbols, 1):
            try:
                print(f"\n[{i}/{total_symbols}] Processing {ticker} ({exchange})...")
                print(f"   Symbol ID: {sid}")
                
                # Add debug logging
                debug_helper.log_step(f"Backfilling {ticker}", {
                    'symbol_id': sid,
                    'ticker': ticker,
                    'exchange': exchange,
                    'progress': f"{i}/{total_symbols}"
                })
                
                print(f"   📊 Backfilling 1m data...")
                count = backfill_1m(sid, ticker, exchange, source=source)
                print(f"   ✅ {count} rows 1m inserted/updated")
                
                if count == 0:
                    print(f"   ⚠️  No data for {ticker}, skipping pipeline")
                    failed_symbols.append((ticker, "No data"))
                    continue
                
                print(f"   📊 Loading 1m candles from DB...")
                df_1m = load_candles_1m_df(sid)
                if df_1m.empty:
                    print(f"   ⚠️  No candles in DB for {ticker}, skipping pipeline")
                    failed_symbols.append((ticker, "No candles in DB"))
                    continue
                
                print(f"   ✅ Loaded {len(df_1m)} 1m candles")
                
                # Process each timeframe
                tf_success = 0
                for tf in TF_LIST:
                    try:
                        print(f"   📊 Processing timeframe {tf}...")
                        
                        print(f"      🔄 Resampling to {tf}...")
                        df_tf = resample_ohlcv(df_1m, tf)
                        print(f"      ✅ Resampled to {len(df_tf)} {tf} candles")
                                
                        print(f"      💾 Upserting {tf} candles...")
                        upsert_candles_tf(sid, tf, df_tf)
                        print(f"      ✅ Upserted {tf} candles")
                                
                        print(f"      📈 Calculating MACD for {tf}...")
                        calc_macd_and_store(sid, tf)
                        print(f"      ✅ Calculated MACD for {tf}")
                                
                        print(f"      🎯 Evaluating signals for {tf}...")
                        eval_signal(sid, tf, strategy_id, tf_threshold_name)
                        print(f"      ✅ Evaluated signals for {tf}")
                                
                        tf_success += 1
                        print(f"      ✅ {tf} completed successfully")
                                
                    except Exception as tf_error:
                        print(f"      ❌ Error processing {tf} for {ticker}: {tf_error}")
                        print(f"         Error type: {type(tf_error)}")
                        import traceback
                        print(f"         Traceback: {traceback.format_exc()}")
                        debug_helper.log_step(f"Error processing {tf} for {ticker}", error=tf_error)
                        continue
                        
                if tf_success > 0:
                    successful_symbols += 1
                    print(f"   ✅ {ticker} completed ({tf_success}/{len(TF_LIST)} timeframes)")
                else:
                    failed_symbols.append((ticker, "All timeframes failed"))
                    print(f"   ❌ {ticker} failed all timeframes")
                        
            except Exception as e:
                print(f"   ❌ Error processing {ticker}: {e}")
                print(f"      Error type: {type(e)}")
                import traceback
                print(f"      Traceback: {traceback.format_exc()}")
                debug_helper.log_step(f"Error processing {ticker}", error=e)
                failed_symbols.append((ticker, str(e)))
                continue
        
        # Summary
        print("\n" + "="*60)
        print("📊 BACKFILL SUMMARY")
        print("="*60)
        print(f"Total symbols: {total_symbols}")
        print(f"Successful: {successful_symbols}")
        print(f"Failed: {len(failed_symbols)}")
        
        if failed_symbols:
            print(f"\n❌ Failed symbols:")
            for ticker, reason in failed_symbols:
                print(f"  - {ticker}: {reason}")
        
        print(f"\n✅ Backfill + pipeline completed!")
        return f"Processed {successful_symbols}/{total_symbols} symbols successfully"
        
    except Exception as e:
        print(f"❌ Critical error in job_backfill_full_pipeline: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return f"Critical error: {str(e)}"