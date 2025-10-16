# AI Agent Quick Reference

## 🚀 Quick Start Rules

### **1. Code Location Rules**
```
NEW CODE → src/
LEGACY CODE → app/ (maintain until migrated)
SHARED UTILITIES → src/core/
API ENDPOINTS → src/api/routes/
BACKGROUND WORKERS → src/workers/
```

### **2. Before Making Changes**
```python
# Always check first:
1. Is similar code already in src/?
2. Is there a base class I can extend?
3. Can I reuse existing patterns?
4. Am I following the migration plan?
```

### **3. Migration Priority**
```
HIGH PRIORITY:
✅ src/core/services/ (Business logic)
✅ src/core/data/ (Data access)

MEDIUM PRIORITY:
📋 src/api/routes/ (API endpoints)
📋 src/workers/ (Background workers)

LOW PRIORITY:
📋 src/web/ (Web interface)
```

## 🔍 Code Discovery Commands

### **Find Similar Code**
```bash
# Search for similar functions
grep -r "def calculate_macd" .
grep -r "def fetch_.*_data" .
grep -r "class.*Strategy" .

# Search for patterns
grep -r "ewm.*span" .
grep -r "rolling.*window" .
grep -r "pd\.DataFrame" .
```

### **Check Dependencies**
```bash
# Find what imports what
grep -r "from app\." .
grep -r "import app\." .
grep -r "from src\." .
```

## 📋 Refactoring Checklist

### **Before Refactoring:**
- [ ] Read existing code
- [ ] Find code duplication
- [ ] Check for base classes
- [ ] Plan migration path

### **During Refactoring:**
- [ ] Create new file in src/
- [ ] Implement logic
- [ ] Create re-export in app/
- [ ] Test functionality

### **After Refactoring:**
- [ ] Update imports
- [ ] Test thoroughly
- [ ] Update documentation
- [ ] Clean up old code

## 🚫 Anti-Patterns to Avoid

```python
# ❌ DON'T: Duplicate code
def calculate_macd_us(data): ...
def calculate_macd_vn(data): ...  # Same logic!

# ✅ DO: Reusable function
def calculate_macd(data, fast=12, slow=26): ...

# ❌ DON'T: Mixed responsibilities
class SignalService:
    def calculate(self): ...      # Business logic
    def save_db(self): ...        # Data access
    def send_email(self): ...     # Notification

# ✅ DO: Separated concerns
class MACDCalculator: ...         # Business logic only
class SignalRepository: ...       # Data access only
class EmailNotifier: ...          # Notification only
```

## 🏗️ Common Patterns

### **Repository Pattern**
```python
# src/core/data/repositories/base_repository.py
class BaseRepository:
    def save(self, entity): ...
    def find_by_id(self, id): ...
    def find_all(self): ...
```

### **Service Pattern**
```python
# src/core/services/signal_service.py
class SignalService:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier
```

### **Strategy Pattern**
```python
# src/core/strategies/base_strategy.py
class BaseStrategy(ABC):
    @abstractmethod
    def execute(self, data): ...
```

## 📊 File Structure Template

```
src/
├── core/
│   ├── services/          # Business logic
│   ├── data/             # Data access
│   ├── strategies/       # Trading strategies
│   └── workflows/        # Workflow engine
├── api/
│   ├── routes/           # API endpoints
│   ├── middleware/       # Request/response
│   └── schemas/          # Data validation
└── workers/
    ├── observers/        # Event handling
    ├── processors/       # Data processing
    └── schedulers/       # Job scheduling
```

## 🔄 Migration Examples

### **Service Migration**
```python
# 1. Create new service in src/
# src/core/services/new_service.py
class NewService:
    def process(self, data):
        # Implementation
        pass

# 2. Create re-export in app/
# app/services/old_service.py
from src.core.services.new_service import NewService
__all__ = ["NewService"]
```

### **Model Migration**
```python
# 1. Create new model in src/
# src/core/data/models/new_model.py
class NewModel:
    def __init__(self):
        # Implementation
        pass

# 2. Create re-export in app/
# app/models.py
from src.core.data.models.new_model import NewModel
__all__ = ["NewModel"]
```

## 🎯 Success Criteria

### **Code Quality:**
- No code duplication
- Single responsibility per class
- Clear dependencies
- Consistent naming

### **Architecture:**
- New code in src/
- Legacy code in app/
- Clear separation of concerns
- Backward compatibility maintained

### **Testing:**
- All tests pass
- New functionality tested
- Backward compatibility verified
- Performance maintained

---

*Quick reference này giúp AI agent nhanh chóng hiểu quy tắc và thực hiện refactoring đúng chuẩn.*
