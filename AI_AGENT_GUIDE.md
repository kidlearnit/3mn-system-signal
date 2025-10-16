# AI Agent Guide - Project Structure & Refactoring Standards

## 🎯 Mục Đích
Tài liệu này giúp AI agent hiểu rõ cấu trúc dự án, tránh lặp code và thực hiện refactoring đúng chuẩn.

## 📋 Nguyên Tắc Cơ Bản

### 1. **Single Responsibility Principle**
- Mỗi file/module chỉ có một trách nhiệm duy nhất
- Tách biệt rõ ràng giữa data access, business logic, và presentation

### 2. **DRY (Don't Repeat Yourself)**
- Không duplicate code
- Sử dụng inheritance và composition
- Tạo shared utilities và base classes

### 3. **Consistent Naming Convention**
- `snake_case` cho files và functions
- `PascalCase` cho classes
- `UPPER_CASE` cho constants

## 🏗️ Cấu Trúc Dự Án Chi Tiết

```
3mn-trading-signals/
├── 📁 app/                          # LEGACY - Flask Application (Monolithic)
│   ├── __init__.py                  # Flask app factory
│   ├── config.py                    # App configuration
│   ├── db.py                        # Database connection
│   ├── models.py                    # SQLAlchemy models
│   ├── routes/                      # API endpoints (LEGACY)
│   │   ├── admin.py                 # Admin panel
│   │   ├── candles.py               # Candle data API
│   │   ├── dashboard.py             # Dashboard API
│   │   ├── indicators.py            # Technical indicators
│   │   ├── signals.py               # Trading signals
│   │   ├── strategies.py            # Strategy management
│   │   ├── symbols.py               # Symbol management
│   │   ├── websocket_api.py         # Real-time WebSocket
│   │   └── workflow_api.py          # Workflow execution
│   ├── services/                    # Business logic (LEGACY)
│   │   ├── data_sources.py          # External data APIs
│   │   ├── signal_engine.py         # Signal generation
│   │   ├── indicators.py            # Technical analysis
│   │   ├── strategy_*.py            # Trading strategies
│   │   ├── notify.py                # Notifications
│   │   └── system_monitor.py        # System health
│   ├── static/                      # Web assets
│   └── templates/                   # HTML templates
│
├── 📁 src/                          # NEW - Modular Architecture
│   ├── __init__.py
│   ├── 📁 api/                      # API Layer
│   │   ├── __init__.py
│   │   ├── middleware/              # Request/response middleware
│   │   ├── routes/                  # API endpoints (NEW)
│   │   └── schemas/                 # Data validation schemas
│   ├── 📁 core/                     # Core Business Logic
│   │   ├── __init__.py
│   │   ├── 📁 data/                 # Data Access Layer
│   │   │   ├── base_repository.py   # Base repository pattern
│   │   │   ├── market_data_repository.py
│   │   │   ├── signal_repository.py
│   │   │   └── strategy_repository.py
│   │   ├── 📁 signals/              # Signal Processing
│   │   │   ├── data_fetch_step.py
│   │   │   ├── indicator_calculation_step.py
│   │   │   └── signal_evaluation_step.py
│   │   ├── 📁 strategies/           # Trading Strategies
│   │   │   ├── base_strategy.py
│   │   │   ├── macd_strategy.py
│   │   │   └── sma_strategy.py
│   │   └── 📁 workflows/            # Workflow Engine
│   │       ├── workflow_engine.py
│   │       └── workflow_steps.py
│   ├── 📁 web/                      # Web Interface
│   │   ├── templates/               # HTML templates
│   │   ├── static/                  # Web assets
│   │   └── components/              # UI components
│   └── 📁 workers/                  # Background Workers
│       ├── observers/               # Event observers
│       ├── processors/              # Data processors
│       └── schedulers/              # Job schedulers
│
├── 📁 worker/                       # LEGACY - Background Workers
│   ├── base_worker.py               # Base worker class
│   ├── run_worker.py                # Worker entry point
│   ├── scheduler_multi.py           # Multi-timeframe scheduler
│   ├── jobs.py                      # Job definitions
│   ├── observers/                   # Event handling
│   ├── pipeline/                    # Data processing pipeline
│   ├── repositories/                # Data access
│   └── strategies/                  # Trading strategies
│
├── 📁 config/                       # Configuration Files
│   ├── environments/                # Environment configs
│   ├── sma.yaml                     # SMA strategy config
│   ├── strategies/                  # Strategy configurations
│   └── symbols/                     # Symbol configurations
│
├── 📁 utils/                        # Shared Utilities
│   ├── __init__.py
│   ├── market_time.py               # Market time utilities
│   └── value.py                     # Value formatting utilities
│
├── 📁 scripts/                      # Deployment & Maintenance
│   ├── auto_setup_db.py
│   ├── deploy_*.sh
│   └── utils/
│
├── 📁 tests/                        # Test Suite
│   ├── e2e/                         # End-to-end tests
│   ├── integration/                 # Integration tests
│   └── unit/                        # Unit tests
│
├── 📁 logs/                         # Log Files
├── 📁 mysql-init/                   # Database initialization
├── docker-compose.yml               # Multi-service deployment
├── Dockerfile                       # Container definition
├── requirements.txt                 # Python dependencies
└── README.md                        # Project documentation
```

## 🔄 Migration Strategy

### **Phase 1: Core Services Migration** ✅ COMPLETED
```
app/services/ → src/core/services/
├── logger.py → src/core/services/logger.py
├── market_service.py → src/core/services/market_service.py
├── system_monitor.py → src/core/services/system_monitor.py
├── notify.py → src/core/services/notify.py
├── email_service.py → src/core/services/email_service.py
├── sms_service.py → src/core/services/sms_service.py
├── candle_utils.py → src/core/services/candle_utils.py
├── resample.py → src/core/services/resample.py
├── indicators.py → src/core/services/indicators.py
├── sma_indicators.py → src/core/services/sma_indicators.py
├── aggregation_engine.py → src/core/services/aggregation_engine.py
├── signal_engine.py → src/core/services/signal_engine.py
└── strategy_base.py → src/core/services/strategy_base.py
```

### **Phase 2: Data Layer Migration** 🔄 IN PROGRESS
```
app/models.py → src/core/data/models/
├── Symbol → src/core/data/models/symbol.py
├── Candle1m → src/core/data/models/candle.py
├── Signal → src/core/data/models/signal.py
└── Strategy → src/core/data/models/strategy.py

app/db.py → src/core/data/database.py
```

### **Phase 3: API Layer Migration** 📋 PLANNED
```
app/routes/ → src/api/routes/
├── admin.py → src/api/routes/admin.py
├── candles.py → src/api/routes/candles.py
├── signals.py → src/api/routes/signals.py
└── strategies.py → src/api/routes/strategies.py
```

### **Phase 4: Worker Migration** 📋 PLANNED
```
worker/ → src/workers/
├── base_worker.py → src/workers/base_worker.py
├── scheduler_multi.py → src/workers/schedulers/scheduler_multi.py
├── observers/ → src/workers/observers/
└── strategies/ → src/workers/strategies/
```

## 🚫 Anti-Patterns to Avoid

### 1. **Code Duplication**
```python
# ❌ BAD - Duplicate code
def calculate_macd_us(data):
    ema12 = data['close'].ewm(span=12).mean()
    ema26 = data['close'].ewm(span=26).mean()
    macd = ema12 - ema26
    return macd

def calculate_macd_vn(data):
    ema12 = data['close'].ewm(span=12).mean()  # Same code!
    ema26 = data['close'].ewm(span=26).mean()  # Same code!
    macd = ema12 - ema26                       # Same code!
    return macd

# ✅ GOOD - Reusable function
def calculate_macd(data, fast=12, slow=26):
    ema_fast = data['close'].ewm(span=fast).mean()
    ema_slow = data['close'].ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    return macd
```

### 2. **Mixed Responsibilities**
```python
# ❌ BAD - Mixed responsibilities
class SignalService:
    def generate_signal(self, data):
        # Business logic
        macd = self.calculate_macd(data)
        signal = self.evaluate_signal(macd)
        
        # Data access
        self.save_to_database(signal)
        
        # Notification
        self.send_email(signal)
        
        return signal

# ✅ GOOD - Separated concerns
class SignalService:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier
    
    def generate_signal(self, data):
        macd = self.calculate_macd(data)
        signal = self.evaluate_signal(macd)
        return signal

class SignalRepository:
    def save_signal(self, signal):
        # Database operations only
        pass

class SignalNotifier:
    def notify_signal(self, signal):
        # Notification logic only
        pass
```

### 3. **Hard-coded Dependencies**
```python
# ❌ BAD - Hard-coded dependencies
class MACDStrategy:
    def __init__(self):
        self.data_source = YahooFinanceAPI()  # Hard-coded!
        self.notifier = EmailNotifier()       # Hard-coded!

# ✅ GOOD - Dependency injection
class MACDStrategy:
    def __init__(self, data_source, notifier):
        self.data_source = data_source
        self.notifier = notifier
```

## ✅ Best Practices for AI Agent

### 1. **Before Making Changes**
```python
# Always check existing code first
def check_existing_implementation():
    """
    Before creating new code, check if similar functionality exists:
    1. Search for similar function names
    2. Check for existing patterns
    3. Look for base classes or utilities
    4. Verify if it's already in src/ or app/
    """
    pass
```

### 2. **Code Organization Rules**
```python
# Rule 1: New code goes to src/
# Rule 2: Legacy code stays in app/ until migrated
# Rule 3: Shared utilities go to src/core/
# Rule 4: API endpoints go to src/api/
# Rule 5: Workers go to src/workers/

# Example structure for new feature:
src/
├── core/
│   ├── services/          # Business logic
│   ├── data/             # Data access
│   └── models/           # Domain models
├── api/
│   └── routes/           # API endpoints
└── workers/
    └── processors/       # Background processing
```

### 3. **Refactoring Checklist**
```python
def refactoring_checklist():
    """
    Before refactoring, ensure:
    ✅ 1. Understand current functionality
    ✅ 2. Identify code duplication
    ✅ 3. Check for existing patterns
    ✅ 4. Plan migration path
    ✅ 5. Create backward compatibility
    ✅ 6. Update imports gradually
    ✅ 7. Test after each change
    ✅ 8. Update documentation
    """
    pass
```

### 4. **Import Management**
```python
# ✅ GOOD - Clear import structure
from src.core.services.logger import TradingLogger
from src.core.data.repositories import SignalRepository
from src.api.routes.base import BaseAPI

# ❌ BAD - Mixed import sources
from app.services.logger import TradingLogger
from src.core.data.repositories import SignalRepository
from app.routes.base import BaseAPI
```

## 🔍 Code Discovery Patterns

### 1. **Finding Similar Code**
```bash
# Search for similar functions
grep -r "def calculate_macd" .
grep -r "def generate_signal" .
grep -r "class.*Strategy" .

# Search for patterns
grep -r "ewm.*span" .
grep -r "rolling.*window" .
grep -r "pd\.DataFrame" .
```

### 2. **Understanding Dependencies**
```python
# Check what imports what
def analyze_dependencies():
    """
    1. Look at import statements
    2. Check for circular dependencies
    3. Identify shared utilities
    4. Find base classes
    """
    pass
```

### 3. **Migration Priority**
```python
# Migration order (from most to least critical):
MIGRATION_PRIORITY = [
    "src/core/services/",      # Business logic
    "src/core/data/",          # Data access
    "src/api/routes/",         # API endpoints
    "src/workers/",            # Background workers
    "src/web/",                # Web interface
]
```

## 📝 Documentation Standards

### 1. **Code Comments**
```python
class SignalGenerator:
    """
    Generates trading signals based on technical indicators.
    
    This class implements the signal generation logic for various
    trading strategies including MACD, RSI, and SMA-based signals.
    
    Attributes:
        repository: Data repository for accessing market data
        notifier: Notification service for signal alerts
        config: Strategy configuration parameters
    """
    
    def generate_signal(self, symbol_id: int, timeframe: str) -> Signal:
        """
        Generate trading signal for a specific symbol and timeframe.
        
        Args:
            symbol_id: Unique identifier for the trading symbol
            timeframe: Timeframe for analysis (1m, 5m, 1h, 1D)
            
        Returns:
            Signal object containing signal type, strength, and confidence
            
        Raises:
            DataNotFoundError: When market data is not available
            InvalidTimeframeError: When timeframe is not supported
        """
        pass
```

### 2. **Type Hints**
```python
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Signal:
    symbol_id: int
    signal_type: str
    strength: float
    confidence: float
    timestamp: datetime
    details: Dict[str, Union[str, float, int]]

def process_signals(signals: List[Signal]) -> Dict[str, List[Signal]]:
    """Process a list of signals and group them by type."""
    pass
```

## 🚀 Quick Reference for AI Agent

### **When to Create New Files:**
- ✅ New business logic → `src/core/services/`
- ✅ New data access → `src/core/data/`
- ✅ New API endpoint → `src/api/routes/`
- ✅ New worker → `src/workers/`
- ✅ New utility → `src/core/utils/`

### **When to Modify Existing Files:**
- ✅ Bug fixes in any location
- ✅ Performance improvements
- ✅ Adding new methods to existing classes
- ✅ Updating configuration

### **When to Refactor:**
- ✅ Code duplication detected
- ✅ Mixed responsibilities found
- ✅ Hard-coded dependencies
- ✅ Inconsistent patterns

### **Migration Rules:**
1. **Never delete** `app/` files until fully migrated
2. **Always create** backward compatibility bridges
3. **Test thoroughly** after each migration step
4. **Update imports** gradually, not all at once
5. **Document changes** in migration logs

---

*Tài liệu này cung cấp hướng dẫn chi tiết cho AI agent để hiểu cấu trúc dự án, tránh lặp code và thực hiện refactoring đúng chuẩn.*
