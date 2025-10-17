# 🔍 System Diagnostic Report & Fixes
**Date**: 2025-10-17  
**Status**: Most systems healthy, 4 minor issues identified

---

## ✅ VERIFIED HEALTHY SYSTEMS

| Component | Status | Details |
|-----------|--------|---------|
| **Database** | ✅ | 5.3M 1m candles, 347K candles_tf, 6,209 signals |
| **Redis** | ✅ | All queues operational, 0 jobs stuck |
| **Worker VN** | ✅ | Processing jobs, ~1 job/sec (CTG, BID, etc.) |
| **Worker US** | ✅ | Queue operational, data current |
| **Signal Engine** | ✅ | 10 signals in last 24h, VN30 working |
| **Telegram** | ✅ | Properly configured with token & chat ID |
| **Market Detection** | ✅ | Correctly identifies VN OPEN, US CLOSED |
| **Data Integrity** | ✅ | No duplicate candles found |
| **Candles_TF** | ✅ | Good coverage: 28K 2m, 12K 5m, 4.5K 15m, 2.5K 30m, 1.5K 1h |
| **VN30 Engine** | ✅ | Signal generation working (SELL signal) |

---

## ⚠️ ISSUES DETECTED

### Issue #1: US Market Symbols Outdated ❌ (NOT CRITICAL)
**Severity**: Low  
**Status**: Expected behavior

**Details**:
- Last update: 2025-10-16 19:59:00 (Market close)
- Affected symbols: AAPL, MSFT, AMZN, NFLX, AVGO
- Root cause: US market closed at 4 PM ET

**Why it's OK**:
- This is EXPECTED when US market is closed
- Data will resume when market opens next trading day
- No action needed

---

### Issue #2: VN Signal Distribution Imbalance ⚠️
**Severity**: Medium  
**Status**: Requires investigation

**Details**:
- Top signals are mostly US stocks (AAPL 197, MSFT 197, etc.)
- VN stocks are NOT in top 10 despite VN market being OPEN
- Expected: VN signals should be dominant during VN market hours

**Root Causes to Investigate**:
1. Scheduler may not be enqueueing VN jobs correctly
2. VN signal engine thresholds might be too strict
3. VN jobs may be processing but signals filtered out

**Action Required**:
```bash
# Check scheduler logs
docker-compose logs scheduler --tail=50

# Check if VN jobs are being enqueued
docker-compose logs worker_vn --tail=50 | grep "Processing VN"

# Check signal generation for specific VN stock
docker-compose exec mysql mysql -u trader -ptraderpass trading -e "
  SELECT ticker, COUNT(*) as signal_count 
  FROM signals s
  JOIN symbols sy ON s.symbol_id = sy.id
  WHERE sy.exchange = 'HOSE'
  AND s.ts > DATE_SUB(NOW(), INTERVAL 7 DAY)
  GROUP BY ticker
"
```

---

### Issue #3: Low MySQL Buffer Pool 🔴
**Severity**: Medium  
**Status**: Should be fixed soon

**Details**:
- Current: 0.12 GB (128 MB)
- Recommended: 1-2 GB for 5.3M+ candles
- Impact: Slow queries during peak loads, cache misses

**Fix**:
Edit `docker-compose.yml` MySQL section:
```yaml
services:
  mysql:
    environment:
      - MYSQL_INNODB_BUFFER_POOL_SIZE=1073741824  # 1 GB
```

Then restart:
```bash
docker-compose restart mysql
```

---

### Issue #4: Missing Environment Variable ⚠️
**Severity**: Low  
**Status**: Should be documented

**Details**:
- `RT_LOOKBACK_MINUTES` not set in environment
- Currently using hardcoded default: 525600 (1 year)
- This should be explicit for production

**Fix**:
Add to `docker-compose.yml`:
```yaml
environment:
  - RT_LOOKBACK_MINUTES=525600
```

Or set in `.env` file.

---

## 📊 Performance Metrics

```
Job Processing Rate:          ~1 job per second
Queue Depth:                  0 jobs (all being processed)
Signal Generation Rate:       10 signals / 24 hours
Avg Signal per Symbol:        ~100 signals per symbol (7 days)
Database Size:                ~200-300 MB
Database Connections:         151 available (OK)
Max Packet Size:              64 MB (OK)
```

---

## 🔧 Recommended Actions

### ✅ DONE (Already Fixed)
1. ✅ Increased lookback_minutes from 1440 to 525600
2. ✅ Fixed resample_ohlcv incomplete candle logic
3. ✅ Fixed VN30 hybrid signal engine
4. ✅ Verified candles_tf ratio is correct

### 📝 TODO - HIGH PRIORITY
1. [ ] Investigate VN signal distribution imbalance
   - Why are US stocks dominating signals?
   - Should VN stocks be generating more signals during market hours?

2. [ ] Monitor US market data when market opens
   - Verify data fetching resumes correctly

### 📝 TODO - MEDIUM PRIORITY  
1. [ ] Increase MySQL buffer pool to 1 GB
   - Current: 128 MB → Recommended: 1024 MB
   - Edit docker-compose.yml and restart

2. [ ] Set RT_LOOKBACK_MINUTES environment variable
   - Add to docker-compose.yml for clarity

### 📝 TODO - LOW PRIORITY (Nice to Have)
1. [ ] Add monitoring dashboard for queue depths
2. [ ] Implement alerting for anomalous signal rates
3. [ ] Add automatic worker health checks
4. [ ] Archive candles older than 1 year
5. [ ] Optimize database indices for faster queries

---

## 🚀 Verification Steps

Run this to verify system health:

```bash
# Check if workers are processing jobs
docker-compose logs worker_vn --tail=20 | grep -i "job ok"

# Check signal generation
docker-compose exec mysql mysql -u trader -ptraderpass trading -e "
  SELECT COUNT(*) as signals_24h 
  FROM signals 
  WHERE ts > DATE_SUB(NOW(), INTERVAL 24 HOUR)
"

# Check if VN market is open
docker-compose exec worker_vn python -c "
  from utils.market_time import is_market_open
  print('VN Market Open:', is_market_open('HOSE'))
"
```

---

## 📞 Support

If issues persist:
1. Check `/Users/hanhdx/3mn-trading-signals/logs/` for error details
2. Verify all services are running: `docker-compose ps`
3. Check Redis connection: `docker-compose exec redis redis-cli ping`
4. Check MySQL connection: `docker-compose exec mysql mysql -u trader -ptraderpass -e "SELECT 1"`

