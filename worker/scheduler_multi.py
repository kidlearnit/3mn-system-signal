import os
import time
import redis
from rq import Queue
from sqlalchemy import text

from worker.jobs import job_backfill_symbol, job_realtime_pipeline
# from worker.jobs_refactored import job_realtime_pipeline
from worker.worker_us_macd import job_realtime_pipeline_with_macd as job_realtime_pipeline_us_macd
from worker.worker_vn_macd import job_realtime_pipeline_with_macd as job_realtime_pipeline_vn_macd
from worker.sma_jobs import job_sma_backfill
from utils.market_time import is_market_open
from app.db import  init_db
# 🔹 Khởi tạo DB
init_db(os.getenv("DATABASE_URL"))

from app.db import SessionLocal

# 🔹 Kết nối Redis
r = redis.from_url(os.getenv('REDIS_URL'))

# 🔹 Tạo hàng đợi theo thị trường + backfill
q_vn = Queue('vn', connection=r)
q_us = Queue('us', connection=r)
q_backfill = Queue('backfill', connection=r)

# 🔹 Nhóm sàn theo thị trường
VN_EXCHANGES = {"HOSE", "HNX", "UPCOM"}
US_EXCHANGES = {"NASDAQ", "NYSE"}

# Stagger enqueue seconds between symbols to avoid spikes
try:
    STAGGER_SECS = float(os.getenv('STAGGER_SECS', '2'))
except Exception:
    STAGGER_SECS = 2.0

# Optional: limit scheduler to a subset of tickers (comma-separated)
ONLY_SYMBOLS_ENV = os.getenv('ONLY_SYMBOLS', '').strip()
ONLY_SYMBOLS = set([s.strip().upper() for s in ONLY_SYMBOLS_ENV.split(',') if s.strip()]) if ONLY_SYMBOLS_ENV else None

# 🔹 Track symbols đã được backfill
processed_symbols = set()

# --- Feature flags / guards ---
MULTI_INDICATOR_SCHEDULER_ENABLED = False  # hard-disable

def _check_macd_multi_active():
    """Check if MACD Multi-TF workflows are active"""
    try:
        with SessionLocal() as s:
            # Check for active workflows with MACD Multi-TF nodes
            result = s.execute(text("""
                SELECT COUNT(*) as count
                FROM workflows w
                WHERE w.status = 'active'
                AND JSON_SEARCH(w.nodes, 'one', 'macd-multi') IS NOT NULL
            """)).fetchone()
            
            return result[0] > 0 if result else False
    except Exception as e:
        print(f"Error checking MACD Multi-TF active status: {e}")
        return False

def _check_multi_indicator_active():
    """Check if Multi-Indicator workflows are active"""
    try:
        with SessionLocal() as s:
            # Check for active workflows with aggregation nodes (multi-indicator)
            result = s.execute(text("""
                SELECT COUNT(*) as count
                FROM workflows w
                WHERE w.status = 'active'
                AND JSON_SEARCH(w.nodes, 'one', 'aggregation') IS NOT NULL
            """)).fetchone()
            
            return result[0] > 0 if result else False
    except Exception as e:
        print(f"Error checking Multi-Indicator active status: {e}")
        return False

def _get_prioritized_macd_workflow_config():
    """Fetch MACD Multi-TF workflow config, prioritizing workflow named '25symbols'.

    Returns a single node config dict that contains 'symbolThresholds' if found,
    otherwise returns None.
    """
    try:
        with SessionLocal() as s:
            # 1) Try prioritized workflow by exact name
            prioritized = s.execute(text("""
                SELECT nodes, properties
                FROM workflows
                WHERE status = 'active'
                  AND name = :name
                  AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
                LIMIT 1
            """), { 'name': '25symbols' }).fetchone()

            candidates = []
            if prioritized:
                candidates.append(prioritized)

            # 2) Fallback to any active workflow containing macd-multi
            if not candidates:
                rows = s.execute(text("""
                    SELECT nodes, properties
                    FROM workflows
                    WHERE status = 'active'
                      AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
                """))
                candidates.extend(rows.fetchall())

        # Extract first macd-multi node config that has symbolThresholds
        for nodes_json, properties_json in candidates:
            try:
                import json
                nodes = json.loads(nodes_json)
                properties = json.loads(properties_json)
                macd_nodes = [n for n in nodes if isinstance(n, dict) and n.get('type') == 'macd-multi']
                for node in macd_nodes:
                    node_id = node.get('id')
                    if not node_id:
                        continue
                    node_cfg = properties.get(node_id, {}) if isinstance(properties, dict) else {}
                    if isinstance(node_cfg, dict) and node_cfg.get('symbolThresholds'):
                        return node_cfg
            except Exception:
                # Skip malformed entries
                continue

        return None
    except Exception as e:
        print(f"Error loading MACD workflow config: {e}")
        return None

def _ensure_workflow_exchanges(default_exchange: str = 'NASDAQ') -> int:
    """Ensure each symbolThreshold in prioritized MACD workflow has an 'exchange'.

    Returns number of entries updated. Non-destructive: only fills missing exchange.
    """
    try:
        updated = 0
        with SessionLocal() as s:
            row = s.execute(text("""
                SELECT id, nodes, properties
                FROM workflows
                WHERE status = 'active'
                  AND name = :name
                  AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
                LIMIT 1
            """), { 'name': '25symbols' }).fetchone()

            if not row:
                return 0

            wf_id, nodes_json, properties_json = row
            import json
            nodes = json.loads(nodes_json)
            properties = json.loads(properties_json) if properties_json else {}
            changed = False

            macd_nodes = [n for n in nodes if isinstance(n, dict) and n.get('type') == 'macd-multi']
            for node in macd_nodes:
                node_id = node.get('id')
                if not node_id:
                    continue
                node_cfg = properties.get(node_id, {}) if isinstance(properties, dict) else {}
                if not isinstance(node_cfg, dict):
                    continue
                thresholds = node_cfg.get('symbolThresholds') or []
                if isinstance(thresholds, list):
                    for item in thresholds:
                        if isinstance(item, dict) and item.get('symbol'):
                            symbol_raw = str(item.get('symbol')).upper()
                            sector_raw = str(item.get('sector', '')).upper()
                            # Heuristic: symbols ending with .VN are VN market -> default HOSE
                            if symbol_raw.endswith('.VN'):
                                if not item.get('exchange'):
                                    item['exchange'] = 'HOSE'
                                    updated += 1
                                    changed = True
                                # normalize symbol: strip .VN suffix for DB ticker storage
                                base_symbol = symbol_raw[:-3]
                                if item.get('symbol') != base_symbol:
                                    item['symbol'] = base_symbol
                                    changed = True
                            # If sector explicitly marks VN, infer HOSE when exchange missing
                            elif sector_raw == 'VN':
                                if not item.get('exchange'):
                                    item['exchange'] = 'HOSE'
                                    updated += 1
                                    changed = True
                            else:
                                if not item.get('exchange'):
                                    item['exchange'] = default_exchange
                                    updated += 1
                                    changed = True

            if changed:
                new_properties_json = json.dumps(properties)
                s.execute(text("""
                    UPDATE workflows
                    SET properties = :props
                    WHERE id = :id
                """), { 'props': new_properties_json, 'id': wf_id })
                s.commit()

        return updated
    except Exception as e:
        print(f"Error ensuring workflow exchanges: {e}")
        return 0

def _ensure_macd_symbols_exist(workflow_config: dict) -> int:
    """Ensure MACD Multi-TF symbols exist in database respecting the 'active' flag.

    - If item.active is True (default if missing): upsert symbol as active
    - If item.active is False: set symbol inactive if exists
    Returns number of symbols changed (added/activated/deactivated)
    """
    try:
        symbol_thresholds = workflow_config.get('symbolThresholds', [])
        if not symbol_thresholds:
            return 0
        
        symbols_changed = 0
        
        with SessionLocal() as s:
            for symbol_config in symbol_thresholds:
                symbol = symbol_config.get('symbol', '').upper()
                if not symbol:
                    continue
                
                # Determine target exchange and normalize symbol
                sector_raw = str(symbol_config.get('sector','')).upper()
                target_exchange = (symbol_config.get('exchange') or ('HOSE' if sector_raw == 'VN' else 'NASDAQ')).upper()
                if symbol.endswith('.VN'):
                    symbol = symbol[:-3]
                    target_exchange = 'HOSE'

                # Read desired active flag (default True)
                desired_active = symbol_config.get('active')
                if desired_active is None:
                    desired_active = True

                # Check if symbol exists
                result = s.execute(text("""
                    SELECT id, active FROM symbols 
                    WHERE ticker = :ticker AND exchange = :exchange
                """), {'ticker': symbol, 'exchange': target_exchange}).fetchone()
                
                if not result:
                    # Insert if desired_active True, otherwise skip insert but may log
                    if desired_active:
                        try:
                            s.execute(text("""
                                INSERT INTO symbols (ticker, exchange, active)
                                VALUES (:ticker, :exchange, 1)
                            """), {'ticker': symbol, 'exchange': target_exchange})
                            symbols_changed += 1
                            print(f"🔄 [Scheduler] Added new symbol: {symbol} ({target_exchange})")
                        except Exception as e:
                            if "Duplicate entry" in str(e):
                                print(f"🔄 [Scheduler] Symbol {symbol} already exists with different exchange")
                            else:
                                raise e
                    else:
                        # desired inactive and not in DB -> nothing to do
                        pass
                else:
                    current_active = bool(result[1])
                    if desired_active and not current_active:
                        s.execute(text("""
                            UPDATE symbols SET active = 1
                            WHERE ticker = :ticker AND exchange = :exchange
                        """), {'ticker': symbol, 'exchange': target_exchange})
                        symbols_changed += 1
                        print(f"🔄 [Scheduler] Activated symbol: {symbol} ({target_exchange})")
                    elif (not desired_active) and current_active:
                        s.execute(text("""
                            UPDATE symbols SET active = 0
                            WHERE ticker = :ticker AND exchange = :exchange
                        """), {'ticker': symbol, 'exchange': target_exchange})
                        symbols_changed += 1
                        print(f"🔄 [Scheduler] Deactivated symbol: {symbol} ({target_exchange})")
            
            s.commit()
        
        return symbols_changed
        
    except Exception as e:
        from app.services.logger import log_scheduler_error
        log_scheduler_error("Error ensuring MACD symbols exist", e)
        return 0

def _enqueue_macd_multi_jobs():
    """Deprecated: MACD Multi-TF enqueuing is handled inline by market workers."""
    return 0

def _enqueue_multi_indicator_jobs():
    """Deprecated: Multi-Indicator scheduling disabled."""
    return 0

def check_and_backfill_new_symbols():
    """Kiểm tra và backfill các symbol mới được kích hoạt"""
    global processed_symbols
    
    try:
        from app.services.logger import log_scheduler_info, log_scheduler_error
        
        with SessionLocal() as s:
            # Lấy tất cả symbols active
            rows = s.execute(text("""
                SELECT id, ticker, exchange
                FROM symbols
                WHERE active = 1
            """)).fetchall()
        
        current_symbols = set()
        new_symbols = []
        
        for sid, tck, exch in rows:
            current_symbols.add(sid)
            # Check if symbol has data in candles_1m table
            has_data = s.execute(text("""
                SELECT COUNT(*) FROM candles_1m WHERE symbol_id = :symbol_id LIMIT 1
            """), {'symbol_id': sid}).scalar()
            
            if sid not in processed_symbols and has_data == 0:
                new_symbols.append((sid, tck, exch))
            elif has_data > 0:
                # Symbol has data, add to processed_symbols immediately
                processed_symbols.add(sid)
        
        # Backfill các symbol mới
        for sid, tck, exch in new_symbols:
            log_scheduler_info(f"New symbol detected: {tck} ({exch}) - Starting backfill", {
                'symbol_id': sid,
                'ticker': tck,
                'exchange': exch
            })
            
            try:
                # Enqueue backfill job
                q_backfill.enqueue(
                    job_backfill_symbol, 
                    sid, tck, exch, 
                    days=365, 
                    source="auto",
                    job_timeout=1800  # 30 phút
                )
                
                # Enqueue SMA backfill job
                q_backfill.enqueue(
                    job_sma_backfill,
                    sid, tck, exch,
                    days=365,
                    job_timeout=1800
                )
                
                log_scheduler_info(f"Backfill jobs enqueued for {tck}", {
                    'symbol_id': sid,
                    'ticker': tck,
                    'exchange': exch
                })
                
            except Exception as e:
                log_scheduler_error(f"Failed to enqueue backfill jobs for {tck}", e, {
                    'symbol_id': sid,
                    'ticker': tck,
                    'exchange': exch
                })
        
        # Cập nhật processed_symbols
        processed_symbols = current_symbols
        
        return len(new_symbols)
        
    except Exception as e:
        from app.services.logger import log_scheduler_error
        log_scheduler_error("Error in check_and_backfill_new_symbols", e)
        return 0

def loop():
    while True:
        try:
            # Bổ sung exchange mặc định cho entries thiếu trong workflow 25symbols
            wf_updated = _ensure_workflow_exchanges(default_exchange='NASDAQ')
            if wf_updated:
                print(f"🔄 [Scheduler] Filled missing exchange for {wf_updated} workflow entries")

            # Đồng bộ symbols từ workflow MACD (ưu tiên '25symbols') -> upsert vào DB và active
            wf_cfg = _get_prioritized_macd_workflow_config()
            if wf_cfg:
                added = _ensure_macd_symbols_exist(wf_cfg)
                if added:
                    print(f"🔄 [Scheduler] Synced {added} symbols from workflow into DB")

            # Backfill batch removed: handled by external tooling or manual ops

            # Kiểm tra và backfill symbol mới
            new_count = check_and_backfill_new_symbols()
            if new_count > 0:
                print(f"🔄 [Scheduler] {new_count} new symbols detected and backfill started")
            
            # Lấy symbols active để xử lý realtime
            with SessionLocal() as s:
                rows = s.execute(text("""
                    SELECT id, ticker, exchange
                    FROM symbols
                    WHERE active = 1
                """)).fetchall()

            # Filter by ONLY_SYMBOLS if provided
            if ONLY_SYMBOLS:
                rows = [(sid, tck, exch) for (sid, tck, exch) in rows if tck.upper() in ONLY_SYMBOLS]

            # Check if MACD Multi-TF workflows are active
            macd_multi_active = _check_macd_multi_active()
            
            # Multi-Indicator disabled
            multi_indicator_active = False
            
            # MACD Multi-TF workflow executor disabled (removed module). Workers do inline MACD via regular pipeline.
            
            # Multi-Indicator scheduling disabled
            
            for sid, tck, exch in rows:
                # Chỉ xử lý realtime nếu đã được backfill
                if sid in processed_symbols:
                    # Use refactored pipeline for both VN and US markets
                    if exch in VN_EXCHANGES:
                        if is_market_open(exch):
                            job_id = f"rt:{sid}:{tck}:vn"
                            # Use hybrid signal engine for VN30, regular pipeline for others
                            if tck.upper() == 'VN30':
                                q_vn.enqueue(job_realtime_pipeline_vn_macd, sid, tck, exch, 1, job_timeout=300, job_id=job_id, failure_ttl=60)
                            else:
                                q_vn.enqueue(job_realtime_pipeline, sid, tck, exch, 1, job_timeout=300, job_id=job_id, failure_ttl=60)
                            # Stagger to spread load
                            if STAGGER_SECS > 0:
                                import time as _t
                                _t.sleep(STAGGER_SECS)
                    elif exch in US_EXCHANGES:
                        job_id = f"rt:{sid}:{tck}:us"
                        q_us.enqueue(job_realtime_pipeline, sid, tck, exch, 1, job_timeout=300, job_id=job_id, failure_ttl=60)
                        if STAGGER_SECS > 0:
                            import time as _t
                            _t.sleep(STAGGER_SECS)
                    # Khác (nếu có)
                    else:
                        # Có thể enqueue vào queue chung hoặc bỏ qua
                        pass

        except Exception as e:
            from app.services.logger import log_scheduler_error
            log_scheduler_error("Error in main loop", e)
            print(f"❌ [Scheduler] Error in main loop: {e}")
        
        # MT5 scheduling disabled

        # Log MACD Multi-TF status
        if macd_multi_active:
            print("🔄 MACD Multi-TF workflows active - logic integrated into worker_us/worker_vn")

        # Email digest execution removed: handled by dedicated emailer service

        time.sleep(60)

if __name__ == "__main__":
    loop()
