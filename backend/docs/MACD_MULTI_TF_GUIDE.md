# MACD Multi-Timeframe US Node Guide

## Overview

The MACD Multi-TF node is a specialized workflow node that performs **BuBeFSM** analysis across multiple timeframes (2m, 5m, 15m, 30m, 1h) for US stock trading signals.

**BuBeFSM** = **Bull, Bear, FastMACD, SignalMACD, M** (timeframe)

This node processes 25 US stocks with symbol-specific thresholds for each timeframe.

## Features

- **Multi-Timeframe Analysis**: Analyzes MACD across 5 different timeframes
- **Symbol-Specific Configuration**: Each symbol can have its own BuBeFSM thresholds
- **BuBeFSM Logic**: BULL/BEAR signals based on FastMACD and SignalMACD crossover
- **Confidence Scoring**: Calculates confidence based on consensus across timeframes
- **Database Integration**: Stores signals in the database for further processing

## Node Configuration

### MACD Parameters
- **Fast Period**: Default 7
- **Slow Period**: Default 113  
- **Signal Period**: Default 144

### Symbol Thresholds Table
Each symbol can have custom BuBeFSM values for each timeframe:

| Column | Description | Example |
|--------|-------------|---------|
| Symbol | Stock ticker | NVDA, MSFT, AAPL |
| BuBeFSM2 | Bull/Bear threshold for 2m | 0.47 (Bull: >0.47, Bear: <-0.47) |
| BuBeFSM5 | Bull/Bear threshold for 5m | 0.47 (Bull: >0.47, Bear: <-0.47) |
| BuBeFSM15 | Bull/Bear threshold for 15m | 0.47 (Bull: >0.47, Bear: <-0.47) |
| BuBeFSM30 | Bull/Bear threshold for 30m | 0.47 (Bull: >0.47, Bear: <-0.47) |
| BuBeFS_1H | Bull/Bear threshold for 1H | 1.74 (Bull: >1.74, Bear: <-1.74) |

### BuBeFSM Logic
- **Bull Signal**: (FastMACD >= threshold OR SignalMACD >= threshold) AND both positive
- **Bear Signal**: (FastMACD <= -threshold OR SignalMACD <= -threshold) AND both negative
- **Neutral**: Otherwise

## How It Works

### 1. Data Processing
- **Fetches latest 1m data** from US exchanges (NASDAQ, NYSE, AMEX)
- **Resamples to 5 timeframes**: 2m, 5m, 15m, 30m, 1h
- **Calculates MACD** with parameters (7, 113, 144) for each timeframe

### 2. BuBeFSM Signal Generation
For each timeframe and symbol:
- **FastMACD & SignalMACD vs Threshold**: Compare both indicators with threshold value
- **Bull Signal**: (FastMACD >= threshold OR SignalMACD >= threshold) AND both positive
- **Bear Signal**: (FastMACD <= -threshold OR SignalMACD <= -threshold) AND both negative
- **Neutral**: Otherwise

### 3. Overall Signal Calculation
- **Counts Bull vs Bear** signals across 5 timeframes
- **Calculates confidence** based on consensus ratio (70%) + strength ratio (30%)
- **Determines final signal**: BULL/BEAR/NEUTRAL

### 4. Signal Storage
- **Stores in database** with strategy_id=998 (MACD_MULTI_TF_US)
- **Includes detailed results** for all timeframes
- **Sets confidence threshold** > 0.5 for signal activation

## Usage in Workflow Builder

### 1. Add Node
- Drag "MACD Multi-TF" from Actions dropdown
- Place on canvas

### 2. Configure Node
- Click ⚙️ to open configuration
- Set MACD parameters (7, 113, 144)
- Click "Load 25 Symbols" to load default data
- Modify symbol thresholds as needed

### 3. Execute Workflow

#### Backfill Mode (First Time)
```json
POST /api/workflow/execute/{workflow_id}
{
  "mode": "backfill"
}
```
- **Backfills 1 year** of historical data for each symbol
- **Processing time**: ~30 minutes for 25 symbols
- **Required before realtime** mode

#### Realtime Mode (Ongoing)
```json
POST /api/workflow/execute/{workflow_id}
{
  "mode": "realtime"
}
```
- **Fetches latest 1m data** and processes signals
- **Processing time**: ~10 minutes for 25 symbols
- **Runs every minute** when workflow is active

### 4. Worker Conflict Prevention
- **Regular US worker stops** when MACD Multi-TF is active
- **No duplicate processing** of US symbols
- **Automatic conflict detection** in scheduler

## API Endpoints

### Test MACD Multi-TF
```bash
# Test backfill mode
POST /api/workflow/test-macd-multi
Content-Type: application/json

{
  "symbol": "NVDA",
  "mode": "backfill"
}

# Test realtime mode
POST /api/workflow/test-macd-multi
Content-Type: application/json

{
  "symbol": "NVDA",
  "mode": "realtime"
}
```

### Execute Workflow
```bash
POST /api/workflow/execute/{workflow_id}
```

## Worker Integration

### Job Processing
- MACD Multi-TF workflows are processed by background workers
- Uses Redis Queue for job management
- Processes all active symbols in database

### Scheduler Integration
- Automatically enqueues MACD Multi-TF jobs
- Runs every minute when workflows are active
- Integrates with existing scheduler system

## Database Schema

### Signals Table
```sql
CREATE TABLE signals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol_id INT,
    timeframe VARCHAR(10),
    strategy_id INT,
    signal_type VARCHAR(10),
    confidence FLOAT,
    details JSON,
    status VARCHAR(20),
    created_at TIMESTAMP
);
```

### Signal Details Structure
```json
{
  "strategy": "MACD_MULTI_TF",
  "fast_period": 7,
  "slow_period": 113,
  "signal_period": 144,
  "overall_signal": {
    "signal_type": "BULL",
    "confidence": 0.75,
    "bull_count": 3,
    "bear_count": 2
  },
  "timeframe_results": {
    "2m": {
      "macd_line": 0.12,
      "signal_line": 0.08,
      "histogram": 0.04,
      "signal_type": "BULL",
      "strength": 0.04
    }
  }
}
```

## Testing

### Manual Test
```bash
# Test backfill mode
cd backend
python scripts/test_macd_multi_backfill.py

# Test realtime mode
python scripts/test_macd_multi_us.py
```

### API Test
```bash
curl -X POST http://localhost:5000/api/workflow/test-macd-multi \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NVDA"}'
```

## Troubleshooting

### Common Issues

1. **No Data**: Ensure symbols have 1-minute candle data
2. **No Configuration**: Check symbol thresholds are set
3. **Worker Not Running**: Verify Redis and worker processes
4. **Database Errors**: Check database connection and schema

### Debug Logs
- Check `logs/system.log` for execution details
- Use debug_helper for step-by-step logging
- Monitor Redis queue for job status

## Performance Considerations

- **Memory Usage**: Processes multiple timeframes simultaneously
- **Database Load**: Queries 1m data and resamples
- **Processing Time**: ~2-5 seconds per symbol
- **Concurrency**: Uses Redis Queue for parallel processing

## Future Enhancements

- Real-time signal updates
- Custom timeframe support
- Advanced confidence algorithms
- Integration with MT5 trading
- WebSocket notifications
