# Module Dependencies & Relationships

## 📦 Core Dependencies

### **External Libraries**
```python
# Web Framework
Flask==2.3.3
Flask-CORS==4.0.0
Flask-SocketIO==5.3.6

# Database
SQLAlchemy==2.0.21
PyMySQL==1.1.0
redis==4.6.0

# Data Processing
pandas==2.0.3
numpy==1.24.3
yfinance==0.2.18

# Background Jobs
rq==1.15.1
python-dotenv==1.0.0

# Notifications
requests==2.31.0
python-telegram-bot==20.5

# Technical Analysis
mplfinance==0.12.9b0
```

## 🔗 Module Relationships

### **1. Data Layer Dependencies**
```
app/models.py
├── SQLAlchemy (ORM)
├── datetime (timestamps)
└── typing (type hints)

app/db.py
├── SQLAlchemy (engine, session)
├── app/models (imports all models)
└── os (environment variables)

app/services/data_sources.py
├── pandas (data processing)
├── yfinance (US market data)
├── vnstock (VN market data)
├── requests (API calls)
├── app.db (database access)
└── app.services.sms_service (alerts)
```

### **2. Business Logic Dependencies**
```
app/services/signal_engine.py
├── app.services.strategy_config
├── app.services.symbol_thresholds
└── pandas (data analysis)

app/services/indicators.py
├── pandas (data processing)
├── numpy (mathematical operations)
├── app.services.strategy_config
└── typing (type hints)

app/services/strategy_*.py
├── app.services.indicators
├── app.services.signal_engine
├── app.services.data_sources
└── app.models (database models)
```

### **3. API Layer Dependencies**
```
app/routes/*.py
├── Flask (blueprint, request, jsonify)
├── app.models (database models)
├── app.services.* (business logic)
├── app.db (database sessions)
└── sqlalchemy (queries)

app/routes/websocket_api.py
├── Flask-SocketIO (real-time communication)
├── app.services.websocket_service
├── app.services.system_monitor
└── threading (background tasks)
```

### **4. Worker System Dependencies**
```
worker/base_worker.py
├── rq (job queue)
├── redis (connection)
├── app.services.logger
└── abc (abstract base classes)

worker/observers/*.py
├── app.models (database models)
├── app.db (database access)
├── app.services.notify
└── app.services.telegram_*

worker/pipeline/*.py
├── app.services.data_sources
├── app.services.indicators
├── app.services.signal_engine
└── app.services.data_validation
```

## 🏗️ Architecture Patterns

### **1. Layered Architecture**
```
┌─────────────────────────────────────┐
│           Presentation Layer        │
│  (Flask Routes, WebSocket, HTML)   │
├─────────────────────────────────────┤
│           Business Layer            │
│  (Services, Signal Engine, Logic)  │
├─────────────────────────────────────┤
│           Data Access Layer         │
│  (Models, Repositories, DB)        │
├─────────────────────────────────────┤
│           External Layer            │
│  (APIs, File System, Cache)        │
└─────────────────────────────────────┘
```

### **2. Observer Pattern**
```
SignalEvent
├── DatabaseObserver
│   ├── app.models.Signal
│   └── app.db.SessionLocal
├── TelegramObserver
│   ├── app.services.telegram_*
│   └── requests (HTTP calls)
└── WebSocketObserver
    ├── Flask-SocketIO
    └── app.services.websocket_service
```

### **3. Strategy Pattern**
```
BaseStrategy (Abstract)
├── MACDStrategy
│   ├── app.services.indicators.compute_macd
│   └── app.services.signal_engine.make_signal
├── SMAStrategy
│   ├── app.services.sma_indicators
│   └── app.services.sma_signal_engine
└── VNMultiTimeframeStrategy
    ├── app.services.vn_multi_timeframe_strategy
    └── app.services.data_sources.fetch_vnstock_1m
```

### **4. Factory Pattern**
```
WorkerFactory
├── create_us_worker()
│   ├── worker.worker_us_macd
│   └── worker.enhanced_sma_jobs
├── create_vn_worker()
│   ├── worker.worker_vn_macd
│   └── worker.enhanced_sma_jobs
└── create_scheduler()
    ├── worker.scheduler_multi
    └── worker.jobs
```

## 🔄 Data Flow Dependencies

### **1. Data Collection Flow**
```
External APIs
    ↓
data_sources.py
    ├── fetch_yf_1m() → yfinance
    ├── fetch_polygon_1m() → requests
    └── fetch_vnstock_1m() → vnstock
    ↓
save_candles_1m()
    ├── app.db.SessionLocal
    └── app.models.Candle1m
    ↓
Database (MySQL)
```

### **2. Signal Processing Flow**
```
Database (Candles)
    ↓
indicators.py
    ├── compute_macd() → pandas, numpy
    ├── compute_rsi() → pandas
    └── compute_bollinger_bands() → pandas
    ↓
signal_engine.py
    ├── match_zone_with_thresholds()
    └── make_signal()
    ↓
Database (Signals)
    ↓
Observers
    ├── DatabaseObserver → app.models.Signal
    ├── TelegramObserver → app.services.telegram_*
    └── WebSocketObserver → Flask-SocketIO
```

### **3. Real-time Updates Flow**
```
Market Data
    ↓
WebSocket Events
    ├── Flask-SocketIO
    └── app.services.websocket_service
    ↓
Frontend Dashboard
    ├── JavaScript (Charts)
    ├── HTML Templates
    └── CSS Styling
```

## 📊 Configuration Dependencies

### **Environment Variables**
```python
# Database
DATABASE_URL=mysql+pymysql://user:pass@host:port/db
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=trader
MYSQL_PASSWORD=traderpass
MYSQL_DB=trading

# Redis
REDIS_URL=redis://localhost:6379/0

# External APIs
POLYGON_API_KEY=your_polygon_key
VNSTOCK_ENABLED=true
YF_ENABLED=true

# Notifications
TG_TOKEN=your_telegram_bot_token
TG_CHAT_ID=your_chat_id
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email
EMAIL_PASS=your_password

# System
FLASK_ENV=production
SECRET_KEY=your_secret_key
TIMEZONE=Asia/Ho_Chi_Minh
```

### **Configuration Files**
```
config/
├── sma.yaml (SMA strategy config)
├── strategies/
│   ├── sma.yaml
│   ├── strategies/
│   └── symbols/ (26 symbol configs)
└── symbols/ (26 individual symbol configs)
```

## 🚀 Deployment Dependencies

### **Docker Services**
```yaml
services:
  web:          # Flask application
    depends_on: [mysql, redis]
    
  worker:       # Background job processor
    depends_on: [mysql, redis]
    
  scheduler:    # Cron job scheduler
    depends_on: [mysql, redis]
    
  mysql:        # Database
    volumes: [mysql_data, mysql-init]
    
  redis:        # Job queue & cache
    ports: ["6379:6379"]
```

### **Service Dependencies**
```
Web Service
├── MySQL (database)
├── Redis (sessions, cache)
└── External APIs (data sources)

Worker Services
├── MySQL (data access)
├── Redis (job queue)
└── External APIs (data fetching)

Scheduler Service
├── MySQL (job tracking)
├── Redis (job queue)
└── Worker Services (job execution)
```

## 🔧 Development Dependencies

### **Testing**
```python
pytest==7.4.0
pytest-flask==1.2.0
pytest-cov==4.1.0
```

### **Code Quality**
```python
black==23.7.0
flake8==6.0.0
mypy==1.5.1
```

### **Documentation**
```python
sphinx==7.1.2
sphinx-rtd-theme==1.3.0
```

---

*Tài liệu này mô tả chi tiết các dependencies và mối quan hệ giữa các modules trong hệ thống, giúp developers hiểu rõ cách các components tương tác và phụ thuộc lẫn nhau.*
