import logging
import os
import pandas as pd
import requests
import datetime as dt
import pytz
import yfinance as yf
from sqlalchemy import text
from ..db import init_db
init_db(os.getenv("DATABASE_URL"))
from app.db import SessionLocal
# Nếu dùng vnstock (cài: pip install vnstock)
try:
    from vnstock import Quote
except ImportError:
    Quote = None

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
VNSTOCK_ENABLED = os.getenv("VNSTOCK_ENABLED", "true").lower() == "true"
YF_ENABLED = os.getenv("YF_ENABLED", "true").lower() == "true"

UTC = pytz.UTC

def ensure_utc(dt_obj):
    """Ép datetime về UTC-aware"""
    if dt_obj is None:
        return None
    if dt_obj.tzinfo is None:
        return dt_obj.replace(tzinfo=dt.timezone.utc)
    return dt_obj.astimezone(dt.timezone.utc)

def ensure_index_utc(df):
    """Ép index DataFrame về UTC-aware"""
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
    return df

def save_candles_1m(symbol_id:int, df:pd.DataFrame):
    """Lưu DataFrame OHLCV vào bảng candles_1m với bulk insert an toàn"""
    if df.empty:
        return 0
    
    logging.info(f"Saving {len(df)} rows for symbol_id {symbol_id}")
    
    # Chuẩn bị dữ liệu
    records = []
    for ts, row in df.iterrows():
        records.append({
            'symbol_id': symbol_id,
            'ts': ts.to_pydatetime(),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume']) if not pd.isna(row['volume']) else None
        })
    
    # Bulk insert với error handling
    success_count = 0
    batch_size = 1000  # Tăng batch size để tăng tốc
    
    with SessionLocal() as s:
        try:
            stmt = text("""
                INSERT INTO candles_1m (symbol_id, ts, open, high, low, close, volume)
                VALUES (:symbol_id, :ts, :open, :high, :low, :close, :volume)
                ON DUPLICATE KEY UPDATE 
                    open=VALUES(open), 
                    high=VALUES(high), 
                    low=VALUES(low), 
                    close=VALUES(close), 
                    volume=VALUES(volume)
            """)
            
            # Chia thành các batch nhỏ hơn
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                try:
                    result = s.execute(stmt, batch)
                    success_count += len(batch)
                    logging.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
                    
                    # Commit sau mỗi batch để tránh transaction quá lớn
                    s.commit()
                    
                except Exception as batch_error:
                    s.rollback()
                    logging.error(f"Error in batch {i//batch_size + 1}: {batch_error}")
                    
                    # Thử insert từng record trong batch bị lỗi
                    for j, record in enumerate(batch):
                        try:
                            s.execute(stmt, record)
                            success_count += 1
                        except Exception as single_error:
                            logging.error(f"Failed to insert single record {i+j}: {single_error}")
                    s.commit()
                    
        except Exception as e:
            logging.error(f"Critical error in save_candles_1m: {e}")
            s.rollback()
            return success_count
    
    logging.info(f"Successfully saved {success_count} records for symbol_id {symbol_id}")
    return success_count
# ---------------------------
# VNSTOCK
# ---------------------------
def fetch_vnstock_1m(ticker:str, start:dt.datetime, end:dt.datetime) -> pd.DataFrame:
    """Lấy dữ liệu 1m từ vnstock"""
    try:
        if not Quote:
            raise RuntimeError("vnstock chưa được cài đặt")
        
        # Format dates for vnstock API
        start_str = start.strftime('%Y-%m-%d')
        end_str = end.strftime('%Y-%m-%d')
		
        logging.info(f"start_str: {start_str}, end_str: {end_str}")
        print(f"Fetching {ticker} from vnstock...")
        
        # Try different sources if VCI fails
        sources = ['VCI', 'TCBS', 'SSI']
        last_error = None
        
        for source in sources:
            try:
                print(f"Trying vnstock source: {source}")
                quote = Quote(symbol=ticker, source=source)
                df = quote.history(start=start_str, end=end_str, interval='1m')
                
                if not df.empty:
                    print(f"Successfully fetched data from {source}")
                    break
                else:
                    print(f"No data from {source}, trying next source...")
                    continue
                    
            except Exception as source_error:
                print(f"Error with source {source}: {source_error}")
                last_error = source_error
                if source == sources[-1]:  # Last source
                    # Send SMS alert for vnstock failure
                    try:
                        from app.services.sms_service import SMSService
                        sms_service = SMSService()
                        sms_service.send_vnstock_down_alert(ticker, str(source_error))
                    except Exception as sms_error:
                        print(f"Failed to send vnstock SMS alert: {sms_error}")
                    raise source_error
                continue
        
        if df.empty:
            print(f"No data returned for {ticker} from any vnstock source")
            # Send SMS alert for no data
            try:
                from app.services.sms_service import SMSService
                sms_service = SMSService()
                sms_service.send_vnstock_no_data_alert(ticker)
            except Exception as sms_error:
                print(f"Failed to send vnstock no data SMS alert: {sms_error}")
            return df
        
        # Rename columns to match expected format
        df = df.rename(columns={
            'time': 'ts', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'
        })
        
        # Convert time column to datetime and set as index
        df['ts'] = pd.to_datetime(df['ts'], utc=True)
        df = df.set_index('ts')[['open','high','low','close','volume']]
        
        print(f"Successfully fetched {len(df)} rows for {ticker} from vnstock")
        return df
        
    except Exception as e:
        print(f"Error fetching {ticker} from vnstock: {e}")
        
        # Send SMS alert for vnstock error
        try:
            from app.services.sms_service import SMSService
            sms_service = SMSService()
            sms_service.send_vnstock_down_alert(ticker, str(e))
        except Exception as sms_error:
            print(f"Failed to send vnstock SMS alert: {sms_error}")
        
        # Check if it's a RetryError and provide more details
        if "RetryError" in str(type(e)):
            print(f"RetryError details: {e}")
            print("This might be due to:")
            print("  - Network timeout")
            print("  - API rate limiting")
            print("  - Server overload")
            print("  - Invalid ticker symbol")
        
        return pd.DataFrame()

# ---------------------------
# POLYGON
# ---------------------------
def fetch_polygon_1m(ticker:str, start:dt.datetime, end:dt.datetime) -> pd.DataFrame:
    """Lấy dữ liệu 1m từ Polygon.io với phân trang"""
    try:
        print(f"Fetching {ticker} from Polygon API from {start.date()} to {end.date()}")
        
        all_rows = []
        current_start = start
        
        # Polygon API giới hạn 50,000 records/request (~1.5 tháng)
        # Tăng chunk size lên 60 ngày để giảm số requests
        chunk_days = 60
        
        while current_start < end:
            # Tính chunk end (2 tháng hoặc đến end date)
            chunk_end = min(current_start + dt.timedelta(days=chunk_days), end)
            
            print(f"  📅 Fetching chunk: {current_start.date()} to {chunk_end.date()}")
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{current_start.date()}/{chunk_end.date()}"
            params = {
                "adjusted": "true",
                "sort": "asc",
                "limit": 50000,
                "apiKey": POLYGON_API_KEY
            }
            
            resp = requests.get(url, params=params, timeout=30)
            
            # Check if response is successful
            if resp.status_code != 200:
                if resp.status_code == 429:  # Rate limit
                    print(f"  ⏳ Rate limit hit (429), waiting 60 seconds...")
                    import time
                    time.sleep(60)
                    continue  # Retry same chunk
                else:
                    print(f"  ❌ Polygon API error for {ticker}: HTTP {resp.status_code}")
                    # Send SMS alert for Polygon API error
                    try:
                        from app.services.sms_service import SMSService
                        sms_service = SMSService()
                        sms_service.send_polygon_down_alert(ticker, f"HTTP {resp.status_code}")
                    except Exception as sms_error:
                        print(f"Failed to send polygon SMS alert: {sms_error}")
                    break
            
            # Check if response has content
            if not resp.text.strip():
                print(f"  ⚠️ Empty response from Polygon API for {ticker}")
                # Send SMS alert for empty response
                try:
                    from app.services.sms_service import SMSService
                    sms_service = SMSService()
                    sms_service.send_polygon_down_alert(ticker, "Empty response")
                except Exception as sms_error:
                    print(f"Failed to send polygon SMS alert: {sms_error}")
                break
            
            # Try to parse JSON
            try:
                data = resp.json()
            except ValueError as e:
                print(f"  ❌ JSON parsing error for {ticker}: {e}")
                # Send SMS alert for JSON parsing error
                try:
                    from app.services.sms_service import SMSService
                    sms_service = SMSService()
                    sms_service.send_polygon_down_alert(ticker, f"JSON parsing error: {e}")
                except Exception as sms_error:
                    print(f"Failed to send polygon SMS alert: {sms_error}")
                break
            
            # Check if data has results
            if 'results' not in data:
                print(f"  ⚠️ No results in Polygon API response for {ticker}")
                if 'message' in data:
                    print(f"  API message: {data['message']}")
                # Send SMS alert for no results
                try:
                    from app.services.sms_service import SMSService
                    sms_service = SMSService()
                    sms_service.send_polygon_no_data_alert(ticker, data.get('message', 'No results'))
                except Exception as sms_error:
                    print(f"Failed to send polygon SMS alert: {sms_error}")
                break
            
            # Process results
            chunk_rows = []
            for r in data['results']:
                ts = dt.datetime.fromtimestamp(r['t']/1000, tz=UTC)
                chunk_rows.append({
                    'ts': ts,
                    'open': r['o'],
                    'high': r['h'],
                    'low': r['l'],
                    'close': r['c'],
                    'volume': r['v']
                })
            
            all_rows.extend(chunk_rows)
            print(f"  ✅ Fetched {len(chunk_rows)} rows for chunk")
            
            # Move to next chunk
            current_start = chunk_end + dt.timedelta(days=1)
            
            # Rate limiting: sleep 1 second between requests để tăng tốc
            import time
            time.sleep(1)
        
        if not all_rows:
            print(f"❌ No data fetched for {ticker}")
            # Send SMS alert for no data
            try:
                from app.services.sms_service import SMSService
                sms_service = SMSService()
                sms_service.send_polygon_no_data_alert(ticker, "No data fetched")
            except Exception as sms_error:
                print(f"Failed to send polygon SMS alert: {sms_error}")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_rows).set_index('ts')
        # Remove duplicates and sort
        df = df[~df.index.duplicated(keep='first')].sort_index()
        
        print(f"✅ Successfully fetched {len(df)} rows for {ticker} from Polygon (across {len(all_rows)} total)")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching {ticker} from Polygon API: {e}")
        # Send SMS alert for general Polygon error
        try:
            from app.services.sms_service import SMSService
            sms_service = SMSService()
            sms_service.send_polygon_down_alert(ticker, str(e))
        except Exception as sms_error:
            print(f"Failed to send polygon SMS alert: {sms_error}")
        return pd.DataFrame()

# ---------------------------
# YFINANCE
# ---------------------------
def fetch_yf_1m(ticker:str, start:dt.datetime, end:dt.datetime) -> pd.DataFrame:
    """Lấy dữ liệu 1m từ Yahoo Finance"""
    try:
        # Validate and clean ticker symbol
        if not ticker or ticker.strip() == "":
            print(f"Invalid ticker symbol: '{ticker}'")
            return pd.DataFrame()
        
        ticker = ticker.strip().upper()
        
        # Check for template strings that weren't processed
    
        
        print(f"Fetching {ticker} from Yahoo Finance...")
        df = yf.download(ticker, start=start, end=end, interval="1m", progress=False)
        
        if df.empty:
            print(f"No data returned for {ticker}")
            # Send SMS alert for no data
            try:
                from app.services.sms_service import SMSService
                sms_service = SMSService()
                sms_service.send_yfinance_no_data_alert(ticker)
            except Exception as sms_error:
                print(f"Failed to send yfinance SMS alert: {sms_error}")
            return df
        
        # Handle MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        
        df = df.rename(columns={
            'Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'
        })
        
        # Handle timezone conversion more safely
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')
            
        print(f"Successfully fetched {len(df)} rows for {ticker}")
        return df[['open','high','low','close','volume']]
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error fetching {ticker} from Yahoo Finance: {error_msg}")
        
        # Handle specific yfinance errors
        if "YFPricesMissingError" in error_msg or "possibly delisted" in error_msg:
            print(f"⚠️  {ticker} may be delisted or temporarily unavailable")
            # Don't send SMS for delisted symbols
        else:
            # Send SMS alert for other Yahoo Finance errors
            try:
                from app.services.sms_service import SMSService
                sms_service = SMSService()
                sms_service.send_yfinance_down_alert(ticker, error_msg)
            except Exception as sms_error:
                print(f"Failed to send yfinance SMS alert: {sms_error}")
        
        return pd.DataFrame()

# Alias for backward compatibility
fetch_yfinance_1m = fetch_yf_1m

# ---------------------------
# Hàm tổng hợp
# ---------------------------
def backfill_1m_(symbol_id:int, ticker:str, exchange:str, source:str="auto", days:int=0):
    """Backfill 1m candles cho 1 mã"""
    print(f"Backfilling {ticker} ({exchange}) from {source} for {days} days")
    
    end = dt.datetime.now(tz=UTC)
    start = end - dt.timedelta(days=days)
    print(f"start -----: {start}, end: {end} {POLYGON_API_KEY} {VNSTOCK_ENABLED} {YF_ENABLED}")
    if source == "auto":
        if exchange in ("HOSE","HNX","UPCOM") and VNSTOCK_ENABLED:
            source = "vnstock"
        elif POLYGON_API_KEY and exchange not in ("HOSE","HNX","UPCOM"):
            source = "polygon"
        elif YF_ENABLED:
            source = "yfinance"
        else:
            raise RuntimeError("Không có nguồn dữ liệu phù hợp")

    print(f"Using data source: {source} for {ticker}")

    try:
        if source == "vnstock":
            print(f"Fetching {ticker} from vnstock...")
            df = fetch_vnstock_1m(ticker, start, end)
        elif source == "polygon":
            print(f"Fetching {ticker} from polygon...")
            df = fetch_polygon_1m(ticker, start, end)
        elif source == "yfinance":
            print(f"Fetching {ticker} from yfinance...")
            df = fetch_yf_1m(ticker, start, end)
        else:
            print(f"Unknown source {source}")
            raise ValueError(f"Unknown source {source}")

        if df.empty:
            print(f"No data returned for {ticker} from {source}")
            return 0

        print(f"Saving ====  {len(df)} rows for {ticker}")
        return save_candles_1m(symbol_id, df)
        
    except Exception as e:
        print(f"backfill_1m: Error backfilling {ticker} from {source}: {e}")
        return 0

# ---------------------------
# Realtime helper (no DB save)
# ---------------------------
def get_realtime_df_1m(ticker: str, exchange: str, minutes: int = 180) -> pd.DataFrame:
    """
    Fetch recent 1m candles directly from API for realtime processing without reading from DB.
    - US (NASDAQ/NYSE): yfinance
    - VN (HOSE/HNX/UPCOM): vnstock
    Returns empty DataFrame if source fails.
    """
    try:
        end = dt.datetime.now(tz=UTC)
        # Avoid too-close end for YF (data completeness)
        yf_end = end - dt.timedelta(minutes=5)
        start = end - dt.timedelta(minutes=minutes)

        if exchange in ("HOSE", "HNX", "UPCOM") and VNSTOCK_ENABLED:
            df = fetch_vnstock_1m(ticker, start, end)
            return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

        # Default to yfinance for US
        df = fetch_yf_1m(ticker, start, yf_end)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    except Exception as e:
        print(f"get_realtime_df_1m error for {ticker}: {e}")
        return pd.DataFrame()


def get_data_coverage_days(symbol_id:int):
    with SessionLocal() as s:
        min_ts, max_ts = s.execute(text("""
            SELECT MIN(ts), MAX(ts) FROM candles_1m WHERE symbol_id=:sid
        """), {'sid': symbol_id}).fetchone()
    if not min_ts or not max_ts:
        return 0, None, None
    coverage_days = (max_ts - min_ts).days
    return coverage_days, min_ts, max_ts

def backfill_1m_streaming(symbol_id:int, ticker:str, exchange:str, days:int=365):
    """Backfill streaming - vừa lấy vừa lưu để tăng tốc"""
    print(f"🚀 Streaming backfill {ticker} for {days} days")
    
    if exchange not in ("NASDAQ", "NYSE"):
        print(f"❌ Streaming backfill chỉ hỗ trợ mã US")
        return 0
    
    end = dt.datetime.now(tz=UTC)
    start = end - dt.timedelta(days=days)
    
    total_saved = 0
    
    try:
        # Chia thành chunks lớn hơn để giảm số requests
        current_start = start
        chunk_days = 180  # Chunk lớn hơn (6 tháng) để giảm requests
        
        while current_start < end:
            chunk_end = min(current_start + dt.timedelta(days=chunk_days), end)
            print(f"  📅 Processing chunk: {current_start.date()} to {chunk_end.date()}")
            
            # Lấy dữ liệu chunk
            df_chunk = fetch_polygon_chunk(ticker, current_start, chunk_end)
            
            if df_chunk is not None and not df_chunk.empty:
                # Lưu ngay chunk này
                saved_count = save_candles_1m(symbol_id, df_chunk)
                total_saved += saved_count
                print(f"  ✅ Saved {saved_count} rows (total: {total_saved})")
            else:
                print(f"  ⚠️ No data for chunk")
            
            # Chuyển sang chunk tiếp theo
            current_start = chunk_end + dt.timedelta(days=1)
            
            # Sleep để tránh rate limit
            import time
            time.sleep(5)  # Sleep 5s giữa các chunk để tránh rate limit
        
        print(f"✅ Streaming backfill completed: {total_saved} total rows")
        return total_saved
        
    except Exception as e:
        print(f"❌ Streaming backfill error for {ticker}: {e}")
        return total_saved

def fetch_polygon_chunk(ticker:str, start:dt.datetime, end:dt.datetime) -> pd.DataFrame:
    """Lấy một chunk dữ liệu từ Polygon API với pagination"""
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{start.date()}/{end.date()}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": POLYGON_API_KEY
        }
        
        all_results = []
        
        while True:
            resp = requests.get(url, params=params, timeout=30)
            
            if resp.status_code != 200:
                if resp.status_code == 429:
                    print(f"  ⏳ Rate limit hit (429), waiting 30 seconds...")
                    import time
                    time.sleep(30)
                    continue  # Retry same request
                else:
                    print(f"  ❌ Polygon API error: HTTP {resp.status_code}")
                    break
            
            if not resp.text.strip():
                print(f"  ⚠️ Empty response from Polygon API")
                break
            
            try:
                data = resp.json()
            except ValueError as e:
                print(f"  ❌ JSON parsing error: {e}")
                break
            
            if 'results' in data:
                all_results.extend(data['results'])
                print(f"  📊 Fetched {len(data['results'])} rows (total: {len(all_results)})")
            
            # Check for next_url pagination
            if 'next_url' not in data:
                break
            
            # Use next_url for pagination
            url = data['next_url'] + f"&apiKey={POLYGON_API_KEY}"
            params = {}  # Clear params since next_url contains everything
            
            # Small sleep between paginated requests
            import time
            time.sleep(0.3)
        
        if not all_results:
            print(f"  ⚠️ No data for chunk")
            return pd.DataFrame()
        
        # Convert to DataFrame
        rows = []
        for r in all_results:
            ts = dt.datetime.fromtimestamp(r['t']/1000, tz=UTC)
            rows.append({
                'ts': ts,
                'open': r['o'],
                'high': r['h'],
                'low': r['l'],
                'close': r['c'],
                'volume': r['v']
            })
        
        df = pd.DataFrame(rows).set_index('ts')
        df = df[~df.index.duplicated(keep='first')].sort_index()
        
        print(f"  ✅ Total fetched {len(df)} rows for chunk")
        return df
        
    except Exception as e:
        print(f"  ❌ Error fetching chunk: {e}")
        return pd.DataFrame()

def backfill_1m_fast(symbol_id:int, ticker:str, exchange:str, days:int=365):
    """Backfill nhanh với batch processing và tối ưu hóa"""
    print(f"🚀 Fast backfill {ticker} for {days} days")
    
    if exchange not in ("NASDAQ", "NYSE"):
        print(f"❌ Fast backfill chỉ hỗ trợ mã US")
        return 0
    
    end = dt.datetime.now(tz=UTC)
    start = end - dt.timedelta(days=days)
    
    try:
        # Lấy dữ liệu trực tiếp từ Polygon với chunk lớn
        df = fetch_polygon_1m(ticker, start, end)
        
        if df is None or df.empty:
            print(f"⚠️ No data returned for {ticker}")
            return 0
        
        # Lưu dữ liệu với batch size lớn hơn
        print(f"💾 Saving {len(df)} rows for {ticker}")
        return save_candles_1m(symbol_id, df)
        
    except Exception as e:
        print(f"❌ Fast backfill error for {ticker}: {e}")
        return 0

def backfill_1m(symbol_id:int, ticker:str, exchange:str, source:str="auto", days:int=365):
    """
    Lấy dữ liệu 1m cho 1 mã:
    - VN: luôn vnstock
    - US: lần đầu polygon 365 ngày, lần sau yfinance (trễ 20 phút)
    """
    coverage_days, min_ts, max_ts = get_data_coverage_days(symbol_id)
    end = dt.datetime.now(tz=UTC)
    
    # Kiểm tra xem có cần backfill không (chỉ khi source = "auto")
    if source == "auto" and max_ts:
        # Đảm bảo max_ts là UTC-aware
        max_ts_utc = ensure_utc(max_ts)
        time_since_last = (end - max_ts_utc).total_seconds()
        
        # Với thị trường VN, luôn lấy dữ liệu mới khi thị trường mở
        if exchange in ('HOSE', 'HNX', 'UPCOM'):
            print(f"🔍 [{ticker}] VN market detected, applying VN logic")
            # Với VN, dữ liệu được lưu dưới dạng Vietnam time (UTC+7)
            # Cần chuyển đổi để so sánh đúng
            if max_ts_utc.tzinfo is None:
                # Nếu là naive datetime, coi như Vietnam time
                max_ts_vn = max_ts_utc.replace(tzinfo=dt.timezone(dt.timedelta(hours=7)))
                max_ts_utc = max_ts_vn.astimezone(UTC)
                print(f"🔍 [{ticker}] Converted naive datetime to VN time: {max_ts_vn} -> {max_ts_utc}")
            
            time_since_last = (end - max_ts_utc).total_seconds()
            print(f"🔍 [{ticker}] Time since last: {time_since_last:.1f} seconds = {time_since_last/60:.1f} minutes")
            
            # Nếu thời gian là âm (dữ liệu "tương lai"), có nghĩa là logic chuyển đổi sai
            if time_since_last < 0:
                print(f"🔍 [{ticker}] Negative time detected, using original max_ts as UTC")
                # Thử lại với logic khác: coi như dữ liệu đã là UTC
                max_ts_utc = max_ts.replace(tzinfo=UTC)
                time_since_last = (end - max_ts_utc).total_seconds()
                print(f"🔍 [{ticker}] Recalculated time since last: {time_since_last:.1f} seconds = {time_since_last/60:.1f} minutes")
                
                # Nếu vẫn âm, có nghĩa là dữ liệu thực sự cũ
                if time_since_last < 0:
                    print(f"🔍 [{ticker}] Still negative, data is really old, forcing fetch")
                    time_since_last = abs(time_since_last)  # Lấy giá trị tuyệt đối
            
            # Chỉ skip nếu dữ liệu mới hơn 5 phút (để đảm bảo có dữ liệu real-time)
            if time_since_last < 300:  # 5 phút
                print(f"📊 [{ticker}] Data is up to date (last update: {time_since_last/60:.1f} minutes ago)")
                return 0
            else:
                print(f"📊 [{ticker}] Data is outdated (last update: {time_since_last/60:.1f} minutes ago), fetching new data")
                # Không return 0, tiếp tục lấy dữ liệu mới
        else:
            # Với thị trường US, giữ logic cũ
            if time_since_last < 3600 and coverage_days >= 365:
                print(f"📊 [{ticker}] Data is up to date (last update: {time_since_last/60:.1f} minutes ago)")
                return 0

    # Lấy timestamp mới nhất trong DB
    with SessionLocal() as s:
        last_ts = s.execute(text("""
            SELECT MAX(ts) FROM candles_1m WHERE symbol_id=:sid
        """), {'sid': symbol_id}).scalar()

    # --- VN STOCKS ---
    if exchange in ("HOSE", "HNX", "UPCOM"):
        source = "vnstock"
        if not last_ts:
            start = end - dt.timedelta(days=365)	
            print(f"📅 [{ticker}] No data in DB, backfilling 365 days from {start} to {end}")
        else:
            start = last_ts + dt.timedelta(minutes=1)
            print(f"📅 [{ticker}] Last candle: {last_ts}, fetching from {start} to {end}")

    # --- US STOCKS ---
    elif exchange in ("NASDAQ", "NYSE"):
        if source == "auto":
            if not last_ts:
                # Không có dữ liệu gì, backfill từ Polygon
                source = "polygon"
                start = end - dt.timedelta(days=days)
                print(f"📅 [{ticker}] No data in DB, backfilling {days} days from {start} to {end} via Polygon")
            else:
                # Có dữ liệu, kiểm tra độ cũ
                last_ts_utc = ensure_utc(last_ts)
                days_since_last = (end - last_ts_utc).days
                
                if days_since_last <= 15:
                    # Dữ liệu cũ ≤ 15 ngày, dùng Yahoo Finance
                    source = "yfinance"
                    start = last_ts_utc + dt.timedelta(minutes=1)
                    # Giới hạn end = now - 20 phút để tránh dữ liệu chưa hoàn thiện
                    end = end - dt.timedelta(minutes=20)
                    
                    # Yahoo Finance chỉ cho phép fetch tối đa 8 ngày dữ liệu 1m
                    max_end = start + dt.timedelta(days=7)  # 7 ngày để an toàn
                    if end > max_end:
                        end = max_end
                        print(f"📅 [{ticker}] YFinance limited to 7 days, adjusting end to {end}")
                    
                    print(f"📅 [{ticker}] Data is {days_since_last} days old (≤15), fetching from {start} to {end} via Yahoo Finance")
                    
                    # Kiểm tra xem có cần fetch không
                    if start >= end:
                        print(f"📊 [{ticker}] No new data to fetch (start >= end)")
                        return 0
                else:
                    # Dữ liệu cũ > 15 ngày, dùng Polygon
                    source = "polygon"
                    start = end - dt.timedelta(days=days)
                    print(f"📅 [{ticker}] Data is {days_since_last} days old (>15), backfilling {days} days from {start} to {end} via Polygon")
        else:
            # Source được chỉ định rõ ràng, sử dụng logic đơn giản
            if source == "polygon":
                start = end - dt.timedelta(days=days)
                print(f"📅 [{ticker}] Force backfilling {days} days from {start} to {end} via Polygon")
            elif source == "yfinance":
                if not last_ts:
                    print(f"❌ [{ticker}] No existing data for YFinance incremental update")
                    return 0
                last_ts_utc = ensure_utc(last_ts)
                start = last_ts_utc + dt.timedelta(minutes=1)
                end = end - dt.timedelta(minutes=20)
                print(f"📅 [{ticker}] Force fetching from {start} to {end} via Yahoo Finance")
            else:
                print(f"❌ [{ticker}] Unknown source: {source}")
                return 0

    else:
        raise RuntimeError(f"[{ticker}] Không xác định được sàn giao dịch")

    # --- Fetch dữ liệu ---
    try:
        if source == "vnstock":
            df = fetch_vnstock_1m(ticker, start, end)
        elif source == "polygon":
            df = fetch_polygon_1m(ticker, start, end)
        elif source == "yfinance":
            df = fetch_yf_1m(ticker, start, end)
        else:
            raise ValueError(f"Unknown source {source}")

        if df is None or df.empty:
            print(f"⚠️ [{ticker}] No data returned from {source}")
            return 0
        
        # Lọc bỏ dữ liệu trùng
        if last_ts:
            last_ts = ensure_utc(last_ts)
            df = ensure_index_utc(df)
            original_count = len(df)
            df = df[df.index > last_ts]
            filtered_count = len(df)
            print(f"🔍 [{ticker}] Filtered {original_count} -> {filtered_count} rows (removed {original_count - filtered_count} duplicates)")

        if df.empty:
            print(f"📊 [{ticker}] No new data to save after filtering")
            return 0

        print(f"💾 [{ticker}] Saving {len(df)} rows from {source}")
        return save_candles_1m(symbol_id, df)

    except Exception as e:
        print(f"❌ backfill_1m: Error for {ticker} from {source}: {e}")
        return 0


# ---------------------------
# Realtime polling
# ---------------------------
def fetch_latest_1m(symbol_id:int, ticker:str, exchange:str, source:str="auto"):
    """Lấy nến 1m mới nhất và lưu - luôn fetch dữ liệu mới cho real-time"""
    end = dt.datetime.now(tz=UTC)
    start = end - dt.timedelta(minutes=5)
    
    # For real-time fetching, always try to get new data regardless of coverage
    # Force fetch by using a specific source instead of "auto"
    if source == "auto":
        # Determine the best source for real-time data
        if exchange in ("HOSE","HNX","UPCOM"):
            source = "vnstock"
        elif exchange in ("NASDAQ", "NYSE"):
            source = "yfinance"  # Use yfinance for real-time US data
        else:
            source = "yfinance"
    
    count = backfill_1m(symbol_id, ticker, exchange, source=source)
    return count

