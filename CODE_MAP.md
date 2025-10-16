# Bản Đồ Code - Hệ Thống Trading Signals

## 📋 Tổng Quan Kiến Trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING SIGNALS SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Web UI)  │  Backend (Flask)  │  Workers (RQ)        │
│  ┌───────────────┐  │  ┌─────────────┐  │  ┌─────────────────┐ │
│  │   Dashboard   │  │  │   Flask     │  │  │   Data Fetch    │ │
│  │   Charts      │  │  │   API       │  │  │   Indicators    │ │
│  │   Signals     │  │  │   Routes    │  │  │   Signals       │ │
│  └───────────────┘  │  └─────────────┘  │  └─────────────────┘ │
│                     │                   │                     │
│  ┌───────────────┐  │  ┌─────────────┐  │  ┌─────────────────┐ │
│  │   WebSocket   │  │  │   Services  │  │  │   Scheduler     │ │
│  │   Real-time   │  │  │   Business  │  │  │   Notifications │ │
│  │   Updates     │  │  │   Logic     │  │  │   Email/Telegram│ │
│  └───────────────┘  │  └─────────────┘  │  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
│
├── Database (MySQL) ──── Redis (Queue) ──── External APIs
│   ┌─────────────┐      ┌─────────────┐     ┌─────────────┐
│   │   Symbols   │      │   Job Queue │     │   Yahoo     │
│   │   Candles   │      │   Results   │     │   Finance   │
│   │   Signals   │      │   Cache     │     │   Polygon   │
│   │   Strategies│      │   Sessions  │     │   VNStock   │
│   └─────────────┘      └─────────────┘     └─────────────┘
```

## 🏗️ Cấu Trúc Thư Mục Chi Tiết

### 1. **Frontend Layer** (`app/`)
```
app/
├── __init__.py              # Flask app factory
├── config.py               # App configuration
├── db.py                   # Database connection
├── models.py               # SQLAlchemy models
├── routes/                 # API endpoints
│   ├── admin.py           # Admin panel
│   ├── candles.py         # Candle data API
│   ├── dashboard.py       # Dashboard API
│   ├── indicators.py      # Technical indicators
│   ├── signals.py         # Trading signals
│   ├── strategies.py      # Strategy management
│   ├── symbols.py         # Symbol management
│   ├── websocket_api.py   # Real-time WebSocket
│   └── workflow_api.py    # Workflow execution
├── services/              # Business logic
│   ├── data_sources.py    # External data APIs
│   ├── signal_engine.py   # Signal generation
│   ├── indicators.py      # Technical analysis
│   ├── strategy_*.py      # Trading strategies
│   ├── notify.py          # Notifications
│   └── system_monitor.py  # System health
├── static/                # Web assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript
│   └── config/           # Frontend config
└── templates/             # HTML templates
    ├── pages/            # Main pages
    ├── components/       # Reusable components
    └── layouts/          # Page layouts
```

### 2. **Core Business Logic** (`src/`)
```
src/
├── api/                   # API layer
│   ├── routes/           # API endpoints (duplicate of app/routes)
│   ├── middleware/       # Request/response middleware
│   └── schemas/          # Data validation schemas
├── core/                 # Core business logic
│   ├── data/            # Data access layer
│   ├── signals/         # Signal processing
│   ├── strategies/      # Trading strategies
│   └── workflows/       # Workflow engine
├── web/                 # Web interface
│   ├── templates/       # HTML templates
│   ├── static/         # Web assets
│   └── components/     # UI components
└── workers/             # Background workers
    ├── observers/       # Event observers
    ├── processors/      # Data processors
    └── schedulers/      # Job schedulers
```

### 3. **Worker System** (`worker/`)
```
worker/
├── base_worker.py           # Base worker class
├── run_worker.py           # Worker entry point
├── scheduler_multi.py      # Multi-timeframe scheduler
├── jobs.py                 # Job definitions
├── observers/              # Event handling
│   ├── base_observer.py   # Base observer
│   ├── database_observer.py # DB notifications
│   ├── telegram_observer.py # Telegram alerts
│   └── websocket_observer.py # WebSocket events
├── pipeline/               # Data processing pipeline
│   ├── data_fetch_step.py # Data collection
│   ├── indicator_calculation_step.py # Technical analysis
│   └── signal_evaluation_step.py # Signal generation
├── repositories/           # Data access
│   ├── market_data_repository.py
│   ├── signal_repository.py
│   └── strategy_repository.py
└── strategies/             # Trading strategies
    ├── macd_strategy.py
    ├── sma_strategy.py
    └── vn_multi_timeframe_strategy.py
```

## 🔄 Luồng Dữ Liệu (Data Flow)

### 1. **Data Collection Pipeline**
```
External APIs → Data Sources → Database → Workers → Signals
     ↓              ↓            ↓         ↓         ↓
[Yahoo Finance] → [data_sources.py] → [MySQL] → [RQ Jobs] → [Signal Engine]
[Polygon.io]    → [fetch_*_1m()]   → [candles_1m] → [indicators] → [signals]
[VNStock]       → [backfill_1m()]  → [candles_tf] → [MACD/SMA] → [alerts]
```

### 2. **Signal Generation Process**
```
Raw Data → Technical Indicators → Signal Logic → Notifications
    ↓              ↓                    ↓              ↓
[Candles] → [MACD/RSI/SMA] → [Buy/Sell/Hold] → [Email/Telegram/WebSocket]
[OHLCV]   → [Bollinger Bands] → [Confidence Score] → [Dashboard Updates]
[Volume]  → [Moving Averages] → [Risk Assessment] → [Portfolio Alerts]
```

### 3. **Real-time Processing**
```
Market Data → WebSocket → Frontend → User Actions
     ↓           ↓          ↓           ↓
[Live Prices] → [socketio] → [Charts] → [Trading Decisions]
[Signal Alerts] → [Events] → [Dashboard] → [Portfolio Management]
[System Status] → [Updates] → [Monitoring] → [Configuration]
```

## 🎯 Các Module Chính

### **1. Data Layer**
- **`app/models.py`**: SQLAlchemy models cho database
- **`app/db.py`**: Database connection và session management
- **`app/services/data_sources.py`**: External API integrations
- **`worker/repositories/`**: Data access objects

### **2. Business Logic**
- **`app/services/signal_engine.py`**: Core signal generation
- **`app/services/indicators.py`**: Technical analysis calculations
- **`app/services/strategy_*.py`**: Trading strategy implementations
- **`src/core/strategies/`**: Strategy framework

### **3. API Layer**
- **`app/routes/`**: REST API endpoints
- **`app/routes/websocket_api.py`**: Real-time communication
- **`src/api/routes/`**: Additional API endpoints

### **4. Worker System**
- **`worker/scheduler_multi.py`**: Job scheduling
- **`worker/pipeline/`**: Data processing steps
- **`worker/observers/`**: Event handling
- **`worker/jobs.py`**: Background job definitions

### **5. Notification System**
- **`app/services/notify.py`**: Notification dispatcher
- **`app/services/email_service.py`**: Email notifications
- **`app/services/sms_service.py`**: SMS alerts
- **`worker/telegram_digest_vietnamese.py`**: Telegram bot

## 🔧 Configuration & Deployment

### **Configuration Files**
- **`config/`**: Strategy và symbol configurations
- **`docker-compose.yml`**: Multi-service deployment
- **`env.example`**: Environment variables template
- **`requirements.txt`**: Python dependencies

### **Deployment Scripts**
- **`scripts/deploy_*.sh`**: Deployment automation
- **`scripts/start/`**: Service startup scripts
- **`scripts/maintenance/`**: System maintenance tools

## 📊 Database Schema

### **Core Tables**
- **`symbols`**: Trading symbols (stocks, crypto)
- **`candles_1m`**: 1-minute OHLCV data
- **`candles_tf`**: Multi-timeframe candle data
- **`indicators_macd`**: MACD indicator values
- **`signals`**: Generated trading signals
- **`signal_history`**: Signal execution history

### **Configuration Tables**
- **`trade_strategies`**: Strategy definitions
- **`timeframes`**: Supported timeframes
- **`indicators`**: Technical indicator configs
- **`zones`**: Signal strength zones
- **`threshold_values`**: Strategy thresholds

## 🚀 Key Features

### **1. Multi-Market Support**
- US Markets (NASDAQ, NYSE)
- Vietnamese Markets (HOSE, HNX, UPCOM)
- Multiple data sources (Yahoo Finance, Polygon, VNStock)

### **2. Real-time Processing**
- WebSocket connections for live updates
- Background job processing with RQ
- Multi-timeframe analysis

### **3. Advanced Analytics**
- Technical indicators (MACD, RSI, SMA, Bollinger Bands)
- Multi-strategy signal aggregation
- Risk assessment and confidence scoring

### **4. Notification System**
- Email alerts
- SMS notifications
- Telegram bot integration
- WebSocket real-time updates

### **5. Scalable Architecture**
- Microservices with Docker
- Redis for job queuing
- MySQL for data persistence
- Horizontal scaling support

## 🔍 Monitoring & Debugging

### **Logging**
- **`logs/`**: Structured logging by component
- **`app/services/logger.py`**: Centralized logging service
- **`app/services/debug.py`**: Debug utilities

### **System Monitoring**
- **`app/services/system_monitor.py`**: Health checks
- **Database monitoring**: Connection status
- **Redis monitoring**: Queue health
- **External API monitoring**: Data source status

---

*Bản đồ này cung cấp cái nhìn tổng quan về kiến trúc hệ thống trading signals, giúp developers hiểu rõ luồng dữ liệu và mối quan hệ giữa các components.*
