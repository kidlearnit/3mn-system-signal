# 3MN Trading Signals System

A comprehensive trading signals system with SMA (Simple Moving Average) analysis, multi-timeframe support, and automated email notifications.

## 🚀 Features

- **SMA Strategy**: 18, 36, 48, 144 periods
- **Multi-timeframe Analysis**: 1m, 2m, 5m, 15m, 30m, 1h, 4h
- **Email Digest**: Automated HTML email reports for 25 US stocks
- **Docker Support**: Complete containerized setup
- **Database**: MySQL with pre-configured symbols (US + VN stocks)
- **Real-time Processing**: Redis Queue for background jobs
- **Web Interface**: FastAPI backend with HTML frontend

## 📋 Prerequisites

- Docker & Docker Compose
- Git

## 🛠️ Setup

### 1. Clone Repository
```bash
git clone https://github.com/kidlearnit/3mn-system-signal.git
cd 3mn-system-signal
```

### 2. Environment Configuration
```bash
# Copy template and configure your settings
cp .env.template .env

# Edit .env with your actual credentials
nano .env
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

## 🔐 Security Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MYSQL_PASSWORD` | MySQL user password | `your_secure_password` |
| `MYSQL_ROOT_PASSWORD` | MySQL root password | `your_root_password` |
| `EMAIL_PASSWORD` | Gmail app password | `your_app_password` |
| `TG_TOKEN` | Telegram bot token | `123456789:ABC...` |
| `TG_CHAT_ID` | Telegram chat ID | `-1001234567890` |
| `POLYGON_API_KEY` | Polygon.io API key | `your_api_key` |

### Email Setup (Gmail)
1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password in `EMAIL_PASSWORD`

### Telegram Setup
1. Create bot with @BotFather
2. Get bot token
3. Add bot to group and get chat ID

## 📊 Database Schema

### Symbols Table
- **US Stocks**: 25 major stocks (NASDAQ, NYSE)
- **VN Stocks**: 30 VN30 stocks (HOSE)
- **Fields**: ticker, company_name, weight, sector, exchange

### SMA Indicators
- **Periods**: 18, 36, 48, 144
- **Timeframes**: 1m, 2m, 5m, 15m, 30m, 1h, 4h
- **Signals**: local_bullish, local_bearish, confirmed, triple

## 🔄 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│   SMA Engine    │───▶│  Email Digest   │
│  (Yahoo, VNStock)│    │  (Multi-TF)     │    │   (HTML Table)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     MySQL       │    │     Redis       │    │   SMTP Server   │
│   (Database)    │    │   (Queue)       │    │   (Gmail)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📧 Email Digest

- **Frequency**: Every 10 minutes (configurable)
- **Market Hours**: Only when market is open
- **Format**: HTML table with color-coded signals
- **Symbols**: 25 US stocks (configurable via `EMAIL_DIGEST_SYMBOLS`)

## 🐳 Docker Services

| Service | Description | Port |
|---------|-------------|------|
| `mysql` | MySQL Database | 3309 |
| `redis` | Redis Queue | 6379 |
| `web` | FastAPI Backend | 8000 |
| `worker` | Background Jobs | - |
| `scheduler` | Job Scheduler | - |
| `emailer` | Email Digest | - |

## 🔧 Configuration

### Email Digest Settings
```bash
EMAIL_DIGEST_SYMBOLS=NVDA,MSFT,AAPL,AMZN,AVGO,META,NFLX,TSLA,GOOGL,GOOG,COST,PLTR,CSCO,TMUS,AMD,LIN,INTU,PEP,SHOP,BKNG,ISRG,TXN,QCOM,AMGN,ADBE
EMAIL_DIGEST_LIMIT=25
EMAIL_DIGEST_TIMEFRAMES=1m,2m,5m,15m
EMAIL_DIGEST_INTERVAL_SECONDS=600
EMAIL_DIGEST_SUBJECT=SMA Digest 25
```

### Database Connection
```bash
# External (outside Docker)
DB_CONNECTION_MODE=external
DATABASE_URL_EXTERNAL=mysql+pymysql://trader:password@localhost:3309/trading

# Internal (inside Docker)
DB_CONNECTION_MODE=internal
DATABASE_URL_INTERNAL=mysql+pymysql://trader:password@mysql:3306/trading
```

## 🚨 Security Best Practices

### ⚠️ NEVER Commit Sensitive Data
- ✅ Use `.env.template` for sharing
- ❌ Never commit `.env` files
- ✅ Use placeholder values in templates
- ❌ Never hardcode credentials

### 🔒 Environment Variables Protection
```bash
# .gitignore protects these files:
.env
.env.*
*.env
.env.backup
```

### 🛡️ Credential Management
1. **Rotate passwords regularly**
2. **Use App Passwords for Gmail**
3. **Limit API key permissions**
4. **Monitor access logs**

## 📝 API Endpoints

- `GET /` - Web dashboard
- `GET /api/signals` - Latest signals
- `GET /api/symbols` - Symbol list
- `GET /api/status` - System status

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Check `DATABASE_URL` in `.env`
2. **Email Not Sending**: Verify Gmail App Password
3. **No Signals**: Check market hours and data sources
4. **Docker Issues**: Run `docker-compose logs [service]`

### Logs
```bash
# View all logs
docker-compose logs

# View specific service
docker-compose logs worker
docker-compose logs emailer
```

## 📄 License

This project is for educational and research purposes.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. **Never commit sensitive data**
4. Submit pull request

---

**⚠️ Security Notice**: Always use `.env.template` for sharing configurations. Never commit actual credentials to version control.
