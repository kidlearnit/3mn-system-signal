# Sơ Đồ Kiến Trúc Hệ Thống Trading Signals

## 🏛️ Kiến Trúc Tổng Thể

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TRADING SIGNALS SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   FRONTEND      │    │    BACKEND      │    │    WORKERS      │            │
│  │                 │    │                 │    │                 │            │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │            │
│  │ │  Dashboard  │ │    │ │   Flask     │    │ │ │ Data Fetch  │ │            │
│  │ │  Web UI     │ │◄──►│ │   API       │◄──►│ │ │ Workers     │ │            │
│  │ │  Charts     │ │    │ │   Server    │    │ │ │             │ │            │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │            │
│  │                 │    │                 │    │                 │            │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │            │
│  │ │ WebSocket   │ │◄──►│ │  Services   │ │    │ │ Scheduler   │ │            │
│  │ │ Real-time   │ │    │ │  Business   │ │    │ │ Multi-TF    │ │            │
│  │ │ Updates     │ │    │ │  Logic      │ │    │ │ Jobs        │ │            │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │    DATABASE     │    │      REDIS      │    │  EXTERNAL APIs  │            │
│  │                 │    │                 │    │                 │            │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │            │
│  │ │   MySQL     │ │    │ │ Job Queue   │ │    │ │ Yahoo       │ │            │
│  │ │ - Symbols   │ │    │ │ - Priority  │ │    │ │ Finance     │ │            │
│  │ │ - Candles   │ │    │ │ - Default   │ │    │ │ - US Stocks │ │            │
│  │ │ - Signals   │ │    │ │ - Results   │ │    │ │ - Real-time │ │            │
│  │ │ - Strategies│ │    │ │ - Cache     │ │    │ └─────────────┘ │            │
│  │ └─────────────┘ │    │ └─────────────┘ │    │                 │            │
│  └─────────────────┘    └─────────────────┘    │ ┌─────────────┐ │            │
│                                                 │ │ Polygon.io  │ │            │
│                                                 │ │ - US Data   │ │            │
│                                                 │ │ - Historical│ │            │
│                                                 │ │ - Real-time │ │            │
│                                                 │ └─────────────┘ │            │
│                                                 │                 │            │
│                                                 │ ┌─────────────┐ │            │
│                                                 │ │ VNStock     │ │            │
│                                                 │ │ - VN Stocks │ │            │
│                                                 │ │ - HOSE/HNX  │ │            │
│                                                 │ │ - UPCOM     │ │            │
│                                                 │ └─────────────┘ │            │
│                                                 └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Luồng Dữ Liệu Chi Tiết

### 1. **Data Collection Flow**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ External    │    │ Data        │    │ Database    │    │ Workers     │
│ APIs        │───►│ Sources     │───►│ Storage     │───►│ Processing  │
│             │    │             │    │             │    │             │
│ • Yahoo     │    │ • fetch_*   │    │ • candles_1m│    │ • Indicators│
│ • Polygon   │    │ • backfill  │    │ • candles_tf│    │ • Signals   │
│ • VNStock   │    │ • realtime  │    │ • symbols   │    │ • Alerts    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 2. **Signal Generation Pipeline**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Raw Data    │    │ Technical   │    │ Signal      │    │ Notifications│
│             │───►│ Indicators  │───►│ Engine      │───►│             │
│ • OHLCV     │    │             │    │             │    │             │
│ • Volume    │    │ • MACD      │    │ • Buy/Sell  │    │ • Email     │
│ • Timeframe │    │ • RSI       │    │ • Confidence│    │ • SMS       │
│             │    │ • SMA       │    │ • Risk      │    │ • Telegram  │
│             │    │ • Bollinger │    │ • Strength  │    │ • WebSocket │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 3. **Real-time Processing**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Market      │    │ WebSocket   │    │ Frontend    │    │ User        │
│ Data        │───►│ Events      │───►│ Dashboard   │───►│ Actions     │
│             │    │             │    │             │    │             │
│ • Live      │    │ • Price     │    │ • Charts    │    │ • Trading   │
│   Prices    │    │   Updates   │    │ • Signals   │    │   Decisions │
│ • Signals   │    │ • Alerts    │    │ • Portfolio │    │ • Portfolio │
│ • Alerts    │    │ • Status    │    │ • Monitoring│    │   Management│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🏗️ Component Architecture

### **Frontend Layer**
```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Static    │  │  Templates  │  │ JavaScript  │        │
│  │   Assets    │  │             │  │             │        │
│  │             │  │ • Dashboard │  │ • Charts    │        │
│  │ • CSS       │  │ • Charts    │  │ • Real-time │        │
│  │ • Images    │  │ • Signals   │  │ • WebSocket │        │
│  │ • Config    │  │ • Admin     │  │ • API Calls │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Backend API Layer**
```
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Routes    │  │  Services   │  │   Models    │        │
│  │             │  │             │  │             │        │
│  │ • REST API  │  │ • Business  │  │ • Database  │        │
│  │ • WebSocket │  │   Logic     │  │   Models    │        │
│  │ • Admin     │  │ • Data      │  │ • Relations │        │
│  │ • Dashboard │  │   Processing│  │ • Validation│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Worker System**
```
┌─────────────────────────────────────────────────────────────┐
│                    WORKER SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Scheduler   │  │ Processors  │  │ Observers   │        │
│  │             │  │             │  │             │        │
│  │ • Multi-TF  │  │ • Data      │  │ • Database  │        │
│  │ • Cron Jobs │  │   Fetch     │  │ • Telegram  │        │
│  │ • Priority  │  │ • Indicators│  │ • WebSocket │        │
│  │ • Retry     │  │ • Signals   │  │ • Email     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Database Schema

### **Core Data Tables**
```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE SCHEMA                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Symbols   │  │   Candles   │  │  Indicators │        │
│  │             │  │             │  │             │        │
│  │ • id        │  │ • symbol_id │  │ • symbol_id │        │
│  │ • ticker    │  │ • timestamp │  │ • timeframe │        │
│  │ • exchange  │  │ • OHLCV     │  │ • macd      │        │
│  │ • currency  │  │ • volume    │  │ • signal    │        │
│  │ • active    │  │ • timeframe │  │ • histogram │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Signals   │  │ Strategies  │  │ Thresholds  │        │
│  │             │  │             │  │             │        │
│  │ • id        │  │ • id        │  │ • symbol_id │        │
│  │ • symbol_id │  │ • name      │  │ • indicator │        │
│  │ • signal    │  │ • config    │  │ • zone      │        │
│  │ • strength  │  │ • active    │  │ • min_value │        │
│  │ • timestamp │  │ • weight    │  │ • max_value │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration & Deployment

### **Docker Services**
```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER SERVICES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Web      │  │   Worker    │  │  Scheduler  │        │
│  │             │  │             │  │             │        │
│  │ • Flask     │  │ • RQ Worker │  │ • Cron Jobs │        │
│  │ • Port 5000 │  │ • US/VN     │  │ • Multi-TF  │        │
│  │ • WebSocket │  │ • MACD/SMA  │  │ • Priority  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   MySQL     │  │   Redis     │  │  Emailer    │        │
│  │             │  │             │  │             │        │
│  │ • Port 3309 │  │ • Port 6379 │  │ • Digest    │        │
│  │ • Trading   │  │ • Job Queue │  │ • Alerts    │        │
│  │   Database  │  │ • Cache     │  │ • Reports   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Key Features & Capabilities

### **Multi-Market Support**
- **US Markets**: NASDAQ, NYSE (Yahoo Finance, Polygon.io)
- **Vietnamese Markets**: HOSE, HNX, UPCOM (VNStock)
- **Real-time Data**: Live price feeds and updates
- **Historical Data**: Backfill capabilities for analysis

### **Advanced Analytics**
- **Technical Indicators**: MACD, RSI, SMA, Bollinger Bands
- **Multi-timeframe Analysis**: 1m, 5m, 15m, 1h, 4h, 1D
- **Signal Aggregation**: Multiple strategy consensus
- **Risk Assessment**: Confidence scoring and validation

### **Real-time Processing**
- **WebSocket Communication**: Live dashboard updates
- **Background Jobs**: Asynchronous data processing
- **Event-driven Architecture**: Observer pattern for notifications
- **Scalable Workers**: Horizontal scaling support

### **Notification System**
- **Multi-channel Alerts**: Email, SMS, Telegram, WebSocket
- **Customizable Templates**: Personalized notification formats
- **Priority Queuing**: Critical alerts get priority
- **Delivery Tracking**: Notification status monitoring

---

*Sơ đồ này cung cấp cái nhìn chi tiết về kiến trúc hệ thống, giúp hiểu rõ cách các components tương tác và luồng dữ liệu trong toàn bộ hệ thống trading signals.*
