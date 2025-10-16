# Refactoring Guide for AI Agent

## 🎯 Mục Đích
Hướng dẫn chi tiết cho AI agent thực hiện refactoring code đúng chuẩn, tránh lặp code và duy trì tính nhất quán.

## 📋 Quy Trình Refactoring

### **Bước 1: Phân Tích Code Hiện Tại**
```python
def analyze_code_before_refactoring():
    """
    1. Đọc và hiểu chức năng hiện tại
    2. Xác định code duplication
    3. Tìm patterns có thể tái sử dụng
    4. Kiểm tra dependencies
    5. Đánh giá complexity
    """
    pass
```

### **Bước 2: Lập Kế Hoạch Migration**
```python
def plan_migration():
    """
    1. Xác định target location (src/)
    2. Tạo base classes nếu cần
    3. Thiết kế interface
    4. Lập timeline migration
    5. Tạo backward compatibility
    """
    pass
```

### **Bước 3: Thực Hiện Migration**
```python
def execute_migration():
    """
    1. Tạo file mới trong src/
    2. Implement logic
    3. Tạo re-export trong app/
    4. Test functionality
    5. Update imports
    """
    pass
```

## 🔍 Code Analysis Patterns

### **1. Tìm Code Duplication**
```python
# Pattern: Tìm functions tương tự
def find_duplicate_functions():
    """
    Tìm kiếm patterns:
    - calculate_macd_*
    - fetch_*_data
    - save_*_to_db
    - send_*_notification
    """
    pass

# Example: Tìm tất cả MACD calculations
grep_patterns = [
    "def.*macd.*",
    "def.*MACD.*", 
    "ema.*span.*12",
    "ema.*span.*26"
]
```

### **2. Xác Định Responsibilities**
```python
# Pattern: Phân tích class responsibilities
def analyze_class_responsibilities():
    """
    Mỗi class chỉ nên có 1 responsibility:
    - Data access only
    - Business logic only  
    - API handling only
    - Notification only
    """
    pass

# Example: Tách SignalService
class SignalService:  # ❌ Too many responsibilities
    def calculate_macd(self):      # Business logic
    def save_to_db(self):          # Data access
    def send_email(self):          # Notification
    def validate_data(self):       # Validation

# ✅ Separated concerns
class MACDCalculator:     # Business logic only
class SignalRepository:   # Data access only
class EmailNotifier:      # Notification only
class DataValidator:      # Validation only
```

### **3. Dependency Analysis**
```python
# Pattern: Phân tích dependencies
def analyze_dependencies():
    """
    Kiểm tra:
    - Hard-coded dependencies
    - Circular imports
    - Missing abstractions
    - Tight coupling
    """
    pass

# Example: Dependency injection
class MACDStrategy:
    def __init__(self):
        self.data_source = YahooFinanceAPI()  # ❌ Hard-coded
        self.notifier = EmailNotifier()       # ❌ Hard-coded

# ✅ Dependency injection
class MACDStrategy:
    def __init__(self, data_source, notifier):
        self.data_source = data_source  # ✅ Injected
        self.notifier = notifier        # ✅ Injected
```

## 🏗️ Refactoring Patterns

### **1. Extract Method Pattern**
```python
# ❌ Before: Long method with multiple responsibilities
def process_signal_data(symbol_id, timeframe):
    # Fetch data
    data = fetch_data_from_api(symbol_id, timeframe)
    
    # Calculate indicators
    ema12 = data['close'].ewm(span=12).mean()
    ema26 = data['close'].ewm(span=26).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9).mean()
    histogram = macd - signal_line
    
    # Generate signal
    if macd.iloc[-1] > signal_line.iloc[-1]:
        signal = "BUY"
    else:
        signal = "SELL"
    
    # Save to database
    save_signal_to_db(symbol_id, signal, macd.iloc[-1])
    
    # Send notification
    send_notification(signal, symbol_id)
    
    return signal

# ✅ After: Extracted methods
def process_signal_data(symbol_id, timeframe):
    data = self.fetch_market_data(symbol_id, timeframe)
    macd_data = self.calculate_macd_indicators(data)
    signal = self.generate_signal(macd_data)
    self.save_signal(symbol_id, signal, macd_data)
    self.notify_signal(signal, symbol_id)
    return signal

def calculate_macd_indicators(self, data):
    ema12 = data['close'].ewm(span=12).mean()
    ema26 = data['close'].ewm(span=26).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9).mean()
    histogram = macd - signal_line
    return {'macd': macd, 'signal': signal_line, 'histogram': histogram}

def generate_signal(self, macd_data):
    if macd_data['macd'].iloc[-1] > macd_data['signal'].iloc[-1]:
        return "BUY"
    return "SELL"
```

### **2. Repository Pattern**
```python
# ❌ Before: Direct database access
class SignalService:
    def save_signal(self, signal):
        with SessionLocal() as session:
            signal_record = Signal(
                symbol_id=signal.symbol_id,
                signal_type=signal.type,
                timestamp=datetime.now()
            )
            session.add(signal_record)
            session.commit()

# ✅ After: Repository pattern
class SignalRepository:
    def save(self, signal):
        with SessionLocal() as session:
            signal_record = Signal(
                symbol_id=signal.symbol_id,
                signal_type=signal.type,
                timestamp=datetime.now()
            )
            session.add(signal_record)
            session.commit()
    
    def find_by_symbol(self, symbol_id):
        with SessionLocal() as session:
            return session.query(Signal).filter(
                Signal.symbol_id == symbol_id
            ).all()

class SignalService:
    def __init__(self, repository):
        self.repository = repository
    
    def save_signal(self, signal):
        self.repository.save(signal)
```

### **3. Strategy Pattern**
```python
# ❌ Before: If-else logic
def calculate_indicator(data, indicator_type):
    if indicator_type == "MACD":
        return calculate_macd(data)
    elif indicator_type == "RSI":
        return calculate_rsi(data)
    elif indicator_type == "SMA":
        return calculate_sma(data)
    else:
        raise ValueError("Unknown indicator")

# ✅ After: Strategy pattern
class IndicatorStrategy(ABC):
    @abstractmethod
    def calculate(self, data):
        pass

class MACDStrategy(IndicatorStrategy):
    def calculate(self, data):
        ema12 = data['close'].ewm(span=12).mean()
        ema26 = data['close'].ewm(span=26).mean()
        return ema12 - ema26

class RSIStrategy(IndicatorStrategy):
    def calculate(self, data):
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

class IndicatorCalculator:
    def __init__(self):
        self.strategies = {
            "MACD": MACDStrategy(),
            "RSI": RSIStrategy(),
            "SMA": SMAStrategy()
        }
    
    def calculate(self, data, indicator_type):
        strategy = self.strategies.get(indicator_type)
        if not strategy:
            raise ValueError("Unknown indicator")
        return strategy.calculate(data)
```

### **4. Observer Pattern**
```python
# ❌ Before: Direct notification calls
class SignalService:
    def generate_signal(self, data):
        signal = self.calculate_signal(data)
        self.save_to_database(signal)
        self.send_email(signal)
        self.send_telegram(signal)
        self.send_websocket(signal)
        return signal

# ✅ After: Observer pattern
class SignalEvent:
    def __init__(self, signal, timestamp):
        self.signal = signal
        self.timestamp = timestamp

class SignalObserver(ABC):
    @abstractmethod
    def notify(self, event):
        pass

class DatabaseObserver(SignalObserver):
    def notify(self, event):
        self.save_signal(event.signal)

class EmailObserver(SignalObserver):
    def notify(self, event):
        self.send_email(event.signal)

class TelegramObserver(SignalObserver):
    def notify(self, event):
        self.send_telegram(event.signal)

class SignalNotifier:
    def __init__(self):
        self.observers = []
    
    def add_observer(self, observer):
        self.observers.append(observer)
    
    def notify_all(self, event):
        for observer in self.observers:
            observer.notify(event)

class SignalService:
    def __init__(self, notifier):
        self.notifier = notifier
    
    def generate_signal(self, data):
        signal = self.calculate_signal(data)
        event = SignalEvent(signal, datetime.now())
        self.notifier.notify_all(event)
        return signal
```

## 🔄 Migration Process

### **Step 1: Create New Structure**
```python
# 1. Tạo file mới trong src/
# src/core/services/new_service.py

class NewService:
    def __init__(self, dependencies):
        self.dependencies = dependencies
    
    def process(self, data):
        # New implementation
        pass
```

### **Step 2: Create Backward Compatibility**
```python
# 2. Tạo re-export trong app/
# app/services/old_service.py

from src.core.services.new_service import NewService

# Re-export for backward compatibility
__all__ = ["NewService"]
```

### **Step 3: Update Imports Gradually**
```python
# 3. Cập nhật imports từng file một
# Old import
from app.services.old_service import OldService

# New import  
from src.core.services.new_service import NewService
```

### **Step 4: Test and Validate**
```python
# 4. Test functionality
def test_migration():
    # Test old import still works
    from app.services.old_service import OldService
    
    # Test new import works
    from src.core.services.new_service import NewService
    
    # Test functionality is identical
    assert OldService().process(data) == NewService().process(data)
```

## 🚫 Common Refactoring Mistakes

### **1. Breaking Existing Functionality**
```python
# ❌ BAD: Thay đổi interface mà không backward compatibility
class OldService:
    def process(self, data, config):  # 2 parameters
        pass

class NewService:
    def process(self, data):  # 1 parameter - BREAKS!
        pass

# ✅ GOOD: Maintain backward compatibility
class NewService:
    def process(self, data, config=None):  # Optional parameter
        if config is None:
            config = self.default_config
        # Implementation
```

### **2. Circular Dependencies**
```python
# ❌ BAD: Circular import
# service_a.py
from service_b import ServiceB

# service_b.py  
from service_a import ServiceA  # Circular!

# ✅ GOOD: Dependency injection
class ServiceA:
    def __init__(self, service_b=None):
        self.service_b = service_b or ServiceB()

class ServiceB:
    def __init__(self, service_a=None):
        self.service_a = service_a or ServiceA()
```

### **3. Over-Engineering**
```python
# ❌ BAD: Over-engineering simple functions
class SimpleCalculator:
    def __init__(self, strategy_factory, dependency_injector):
        self.strategy_factory = strategy_factory
        self.dependency_injector = dependency_injector
    
    def add(self, a, b):
        strategy = self.strategy_factory.create("addition")
        return strategy.execute(a, b)

# ✅ GOOD: Keep it simple
def add(a, b):
    return a + b
```

## ✅ Refactoring Checklist

### **Before Refactoring:**
- [ ] Hiểu rõ chức năng hiện tại
- [ ] Xác định code duplication
- [ ] Kiểm tra dependencies
- [ ] Lập kế hoạch migration
- [ ] Tạo test cases

### **During Refactoring:**
- [ ] Tạo file mới trong src/
- [ ] Implement logic mới
- [ ] Tạo backward compatibility
- [ ] Test functionality
- [ ] Update documentation

### **After Refactoring:**
- [ ] Verify all tests pass
- [ ] Check performance
- [ ] Update imports
- [ ] Clean up old code
- [ ] Update documentation

## 🎯 Success Metrics

### **Code Quality Metrics:**
- **Cyclomatic Complexity**: < 10 per function
- **Code Duplication**: < 5%
- **Test Coverage**: > 80%
- **Dependencies**: Minimal and clear

### **Architecture Metrics:**
- **Separation of Concerns**: Clear boundaries
- **Single Responsibility**: One purpose per class
- **Dependency Inversion**: Depend on abstractions
- **Open/Closed Principle**: Open for extension, closed for modification

---

*Hướng dẫn này cung cấp quy trình chi tiết cho AI agent thực hiện refactoring code đúng chuẩn, tránh lặp code và duy trì tính nhất quán trong dự án.*
