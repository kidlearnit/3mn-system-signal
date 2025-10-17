# Python Virtual Environment Setup

## ✅ Installation Complete

A Python 3.13 virtual environment has been created for the 3mn-trading-signals project.

### 📍 Location
```
/Users/hanhdx/3mn-trading-signals/venv
```

### 🚀 Quick Start

#### 1. Activate Environment
```bash
cd /Users/hanhdx/3mn-trading-signals
source venv/bin/activate
```

#### 2. Verify Setup
```bash
python --version
# Output: Python 3.13.x

# Test imports
python -c "from app.services.vn_signal_engine import vn_signal_engine; print('✅ Ready')"
```

#### 3. Run Trading System
```bash
# Option A: Use Docker (recommended)
docker-compose up -d
docker-compose logs worker_vn -f

# Option B: Run locally with venv
source venv/bin/activate
python worker/worker_vn_macd.py
```

---

## 📦 Installed Packages

### Core Libraries
- **NumPy** 2.3.4 - Numerical computing
- **Pandas** 2.3.3 - Data manipulation
- **Matplotlib** 3.10.7 - Plotting & charting
- **Seaborn** 0.13.2 - Statistical visualization

### Database & Cache
- **SQLAlchemy** 2.0.44 - ORM
- **PyMySQL** 1.1.2 - MySQL connector
- **Redis** 6.4.0 - Cache/message queue

### Web Framework
- **Flask** 3.1.2 - Web server
- **Flask-CORS** 6.0.1 - Cross-origin support
- **Flask-SocketIO** 5.5.1 - WebSocket support

### Job Scheduling
- **RQ** 2.6.0 - Job queue
- **APScheduler** 3.11.0 - Scheduler
- **croniter** 6.0.0 - Cron expressions

### Trading & Market Data
- **vnstock** 3.2.6 - Vietnamese stock data
- **yfinance** 0.2.66 - Yahoo Finance data
- **ta** 0.11.0 - Technical Analysis

### Configuration & Utilities
- **PyYAML** 6.0.3 - YAML config
- **python-dotenv** 1.1.1 - Environment variables
- **pytz** 2025.2 - Timezone handling
- **python-dateutil** 2.9.0 - Date utilities

---

## 🛠️ Common Tasks

### Install Additional Package
```bash
source venv/bin/activate
pip install package_name
```

### Deactivate Environment
```bash
deactivate
```

### Update All Packages
```bash
source venv/bin/activate
pip install --upgrade pip
pip list --outdated
pip install -U package_name  # Update specific package
```

### Export Requirements
```bash
source venv/bin/activate
pip freeze > requirements_lock.txt
```

---

## 🐳 Docker vs Local Development

### Use Docker for:
- ✅ Production deployment
- ✅ Consistent environment across machines
- ✅ Isolated services (MySQL, Redis, workers)
- ✅ Scheduled background jobs

### Use Local Venv for:
- ✅ Development & debugging
- ✅ Quick testing
- ✅ Interactive Python shell
- ✅ IDE integration

---

## 🔗 Related Documentation

- **Main System**: See `VN30_INTEGRATION_SUMMARY.md`
- **Quick Start**: See `VN30_QUICK_START.md`
- **Docker Setup**: See `docker-compose.yml`

---

## ⚠️ Troubleshooting

### Module Not Found Error
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall package
pip install --force-reinstall package_name
```

### Database Connection Issues
```bash
# Ensure MySQL is running (Docker)
docker-compose exec mysql mysql -u trader -p'traderpass' trading -e "SELECT 1;"

# Or start MySQL
docker-compose up -d mysql
```

### Permission Denied
```bash
# Give venv execution permission
chmod +x venv/bin/activate
chmod +x venv/bin/python
```

---

## 📝 Notes

- Virtual environment uses Python 3.13.5
- All dependencies are pinned to compatible versions
- No external system dependencies required (except Python 3.10+)
- Safe to delete entire `venv/` folder and recreate with `python3 -m venv venv`

---

**Last Updated**: 2025-10-16  
**Status**: ✅ Production Ready
