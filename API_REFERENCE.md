# API Reference - Trading Signals System

## 🌐 API Endpoints Overview

### **Base URL**: `http://localhost:5000`

## 📊 Data Endpoints

### **Symbols Management**
```http
GET    /api/symbols                    # Get all symbols
GET    /api/symbols/{id}               # Get symbol by ID
POST   /api/symbols                    # Create new symbol
PUT    /api/symbols/{id}               # Update symbol
DELETE /api/symbols/{id}               # Delete symbol
GET    /api/symbols/active             # Get active symbols
```

### **Candle Data**
```http
GET    /api/candles/{symbol_id}        # Get candles for symbol
GET    /api/candles/{symbol_id}/{tf}   # Get candles by timeframe
POST   /api/candles/backfill           # Trigger data backfill
GET    /api/candles/latest/{symbol_id} # Get latest candle
```

### **Technical Indicators**
```http
GET    /api/indicators/macd/{symbol_id}     # Get MACD data
GET    /api/indicators/rsi/{symbol_id}      # Get RSI data
GET    /api/indicators/sma/{symbol_id}      # Get SMA data
GET    /api/indicators/bollinger/{symbol_id} # Get Bollinger Bands
POST   /api/indicators/calculate            # Calculate indicators
```

## 📈 Signal Endpoints

### **Trading Signals**
```http
GET    /api/signals                     # Get all signals
GET    /api/signals/{symbol_id}         # Get signals for symbol
GET    /api/signals/latest              # Get latest signals
POST   /api/signals/generate            # Generate new signals
GET    /api/signals/history             # Get signal history
```

### **Signal Analysis**
```http
GET    /api/signals/analysis/{symbol_id}    # Signal analysis
GET    /api/signals/strength/{symbol_id}    # Signal strength
GET    /api/signals/confidence/{symbol_id}  # Signal confidence
POST   /api/signals/validate                # Validate signals
```

## 🎯 Strategy Endpoints

### **Strategy Management**
```http
GET    /api/strategies                  # Get all strategies
GET    /api/strategies/{id}             # Get strategy by ID
POST   /api/strategies                  # Create new strategy
PUT    /api/strategies/{id}             # Update strategy
DELETE /api/strategies/{id}             # Delete strategy
GET    /api/strategies/active           # Get active strategies
```

### **Strategy Execution**
```http
POST   /api/strategies/{id}/execute     # Execute strategy
GET    /api/strategies/{id}/results     # Get strategy results
POST   /api/strategies/{id}/backtest    # Run backtest
GET    /api/strategies/{id}/performance # Get performance metrics
```

## 🔄 Workflow Endpoints

### **Workflow Management**
```http
GET    /api/workflow                    # Get all workflows
GET    /api/workflow/{id}               # Get workflow by ID
POST   /api/workflow                    # Create new workflow
PUT    /api/workflow/{id}               # Update workflow
DELETE /api/workflow/{id}               # Delete workflow
```

### **Workflow Execution**
```http
POST   /api/workflow/{id}/execute       # Execute workflow
GET    /api/workflow/{id}/runs          # Get workflow runs
GET    /api/workflow/{id}/runs/{run_id} # Get specific run
POST   /api/workflow/{id}/validate      # Validate workflow
```

## 📊 Dashboard Endpoints

### **Dashboard Data**
```http
GET    /api/dashboard/overview          # Dashboard overview
GET    /api/dashboard/signals           # Recent signals
GET    /api/dashboard/performance       # Performance metrics
GET    /api/dashboard/alerts            # System alerts
GET    /api/dashboard/status            # System status
```

### **Charts & Visualization**
```http
GET    /api/charts/{symbol_id}          # Get chart data
GET    /api/charts/{symbol_id}/{tf}     # Get chart by timeframe
POST   /api/charts/generate             # Generate chart
GET    /api/charts/indicators/{symbol_id} # Chart with indicators
```

## 🔧 System Endpoints

### **System Monitoring**
```http
GET    /api/system/health               # System health check
GET    /api/system/status               # System status
GET    /api/system/logs                 # System logs
GET    /api/system/metrics              # System metrics
POST   /api/system/restart              # Restart services
```

### **Configuration**
```http
GET    /api/config                      # Get system config
PUT    /api/config                      # Update system config
GET    /api/config/symbols              # Get symbol configs
PUT    /api/config/symbols              # Update symbol configs
GET    /api/config/strategies           # Get strategy configs
PUT    /api/config/strategies           # Update strategy configs
```

## 🔔 Notification Endpoints

### **Notification Management**
```http
GET    /api/notifications               # Get notifications
POST   /api/notifications/send          # Send notification
GET    /api/notifications/history       # Notification history
PUT    /api/notifications/{id}/read     # Mark as read
DELETE /api/notifications/{id}          # Delete notification
```

### **Notification Settings**
```http
GET    /api/notifications/settings      # Get notification settings
PUT    /api/notifications/settings      # Update settings
POST   /api/notifications/test          # Test notification
```

## 📡 WebSocket Events

### **Real-time Data**
```javascript
// Connect to WebSocket
const socket = io('http://localhost:5000');

// Listen for events
socket.on('price_update', (data) => {
    // Handle price updates
});

socket.on('signal_alert', (data) => {
    // Handle signal alerts
});

socket.on('system_status', (data) => {
    // Handle system status updates
});
```

### **WebSocket Events**
```javascript
// Client → Server
socket.emit('subscribe_symbol', {symbol_id: 1});
socket.emit('subscribe_signals', {strategy_id: 1});
socket.emit('unsubscribe_symbol', {symbol_id: 1});

// Server → Client
socket.on('price_update', (data) => {
    // {symbol_id, price, timestamp, change}
});

socket.on('signal_generated', (data) => {
    // {symbol_id, signal, strength, confidence, timestamp}
});

socket.on('system_alert', (data) => {
    // {type, message, severity, timestamp}
});
```

## 📝 Request/Response Examples

### **Get Symbols**
```http
GET /api/symbols
```

**Response:**
```json
{
    "symbols": [
        {
            "id": 1,
            "ticker": "AAPL",
            "exchange": "NASDAQ",
            "currency": "USD",
            "active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ],
    "total": 1,
    "page": 1,
    "per_page": 50
}
```

### **Get Signals**
```http
GET /api/signals?symbol_id=1&limit=10
```

**Response:**
```json
{
    "signals": [
        {
            "id": 1,
            "symbol_id": 1,
            "signal": "BUY",
            "strength": 0.85,
            "confidence": 0.92,
            "timestamp": "2024-01-01T12:00:00Z",
            "strategy": "MACD_Strategy",
            "details": {
                "macd": 0.15,
                "signal_line": 0.12,
                "histogram": 0.03
            }
        }
    ],
    "total": 1,
    "page": 1,
    "per_page": 10
}
```

### **Execute Strategy**
```http
POST /api/strategies/1/execute
Content-Type: application/json

{
    "symbol_ids": [1, 2, 3],
    "timeframes": ["1h", "4h", "1D"],
    "parameters": {
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9
    }
}
```

**Response:**
```json
{
    "execution_id": "exec_123456",
    "status": "started",
    "message": "Strategy execution started",
    "estimated_duration": "2-5 minutes",
    "created_at": "2024-01-01T12:00:00Z"
}
```

## 🔐 Authentication & Security

### **API Keys** (Future Implementation)
```http
GET /api/symbols
Authorization: Bearer your_api_key_here
```

### **Rate Limiting**
- **Standard endpoints**: 100 requests/minute
- **Data endpoints**: 50 requests/minute
- **WebSocket connections**: 10 concurrent connections

## 📊 Error Responses

### **Standard Error Format**
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid symbol_id provided",
        "details": {
            "field": "symbol_id",
            "value": "invalid",
            "expected": "integer"
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

### **Common Error Codes**
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `503` - Service Unavailable

## 🚀 Usage Examples

### **Python Client**
```python
import requests

# Get symbols
response = requests.get('http://localhost:5000/api/symbols')
symbols = response.json()

# Get signals for a symbol
response = requests.get('http://localhost:5000/api/signals/1')
signals = response.json()

# Execute strategy
payload = {
    "symbol_ids": [1, 2, 3],
    "timeframes": ["1h", "4h"]
}
response = requests.post(
    'http://localhost:5000/api/strategies/1/execute',
    json=payload
)
result = response.json()
```

### **JavaScript Client**
```javascript
// Fetch symbols
fetch('/api/symbols')
    .then(response => response.json())
    .then(data => console.log(data.symbols));

// WebSocket connection
const socket = io();
socket.on('signal_generated', (signal) => {
    console.log('New signal:', signal);
});
```

---

*Tài liệu này cung cấp tham chiếu đầy đủ về tất cả API endpoints trong hệ thống trading signals, bao gồm request/response formats, WebSocket events, và các ví dụ sử dụng.*
