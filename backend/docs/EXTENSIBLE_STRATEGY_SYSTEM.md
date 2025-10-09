# Extensible Strategy System

## Tổng quan

Hệ thống Extensible Strategy được thiết kế để có thể dễ dàng mở rộng thêm các chiến lược trading mới mà không cần thay đổi code hiện tại. Hệ thống sử dụng các design patterns như Strategy Pattern, Registry Pattern và Factory Pattern.

## Kiến trúc

### 1. Base Classes

#### `BaseStrategy` (Abstract Base Class)
```python
class BaseStrategy(ABC):
    @abstractmethod
    def evaluate_signal(self, symbol_id, ticker, exchange, timeframe) -> SignalResult
    @abstractmethod
    def get_required_indicators(self) -> List[str]
    @abstractmethod
    def get_supported_timeframes(self) -> List[str]
```

#### `StrategyConfig` (Configuration)
```python
@dataclass
class StrategyConfig:
    name: str
    description: str
    version: str
    is_active: bool = True
    weight: float = 1.0
    min_confidence: float = 0.5
    parameters: Dict[str, Any] = None
```

#### `SignalResult` (Result)
```python
@dataclass
class SignalResult:
    strategy_name: str
    signal_type: str
    direction: SignalDirection
    strength: float
    confidence: float
    details: Dict[str, Any]
    timestamp: str
    timeframe: str
    symbol_id: int
    ticker: str
    exchange: str
```

### 2. Strategy Registry

#### `StrategyRegistry`
- Quản lý tất cả strategies
- Đăng ký/hủy đăng ký strategies
- Lấy thông tin strategies
- Filter strategies theo trạng thái

### 3. Aggregation Engine

#### `AggregationEngine`
- Tổng hợp tín hiệu từ nhiều strategies
- Hỗ trợ nhiều phương pháp aggregation:
  - **Weighted Average**: Tổng hợp theo trọng số
  - **Majority Vote**: Bỏ phiếu đa số
  - **Consensus**: Đồng thuận
  - **Confidence Weighted**: Theo độ tin cậy

#### `AggregationConfig`
```python
@dataclass
class AggregationConfig:
    method: AggregationMethod
    min_strategies: int = 2
    consensus_threshold: float = 0.6
    confidence_threshold: float = 0.5
    conflict_penalty: float = 0.3
    custom_weights: Dict[str, float] = None
```

### 4. Extensible Signal Engine

#### `ExtensibleSignalEngine`
- Engine chính để đánh giá tín hiệu
- Tự động khởi tạo strategies mặc định
- Hỗ trợ đánh giá single/multi-timeframe
- Quản lý aggregation

## Cách thêm Strategy mới

### Bước 1: Tạo Strategy Class

```python
from app.services.strategy_base import BaseStrategy, StrategyConfig, SignalResult, SignalDirection

class MyNewStrategy(BaseStrategy):
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="My New Strategy",
                description="Description of my strategy",
                version="1.0.0",
                weight=1.0,
                min_confidence=0.5,
                parameters={
                    'param1': 'value1',
                    'param2': 'value2'
                }
            )
        super().__init__(config)
    
    def evaluate_signal(self, symbol_id: int, ticker: str, exchange: str, 
                       timeframe: str) -> SignalResult:
        # Implementation logic here
        return SignalResult(
            strategy_name=self.config.name,
            signal_type="buy",  # or "sell", "neutral"
            direction=SignalDirection.BUY,
            strength=0.8,
            confidence=0.7,
            details={'key': 'value'},
            timestamp=datetime.now().isoformat(),
            timeframe=timeframe,
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange
        )
    
    def get_required_indicators(self) -> List[str]:
        return ['indicator1', 'indicator2']
    
    def get_supported_timeframes(self) -> List[str]:
        return ['5m', '15m', '30m', '1h', '4h']
```

### Bước 2: Đăng ký Strategy

```python
from app.services.extensible_signal_engine import extensible_signal_engine

# Tạo strategy instance
my_strategy = MyNewStrategy()

# Đăng ký strategy
success = extensible_signal_engine.add_strategy(my_strategy)
```

### Bước 3: Sử dụng Strategy

```python
# Đánh giá tín hiệu với strategy mới
result = extensible_signal_engine.evaluate_signal(
    symbol_id=1,
    ticker="AAPL",
    exchange="NASDAQ",
    timeframe="5m",
    strategy_names=["My New Strategy"]  # Hoặc None để dùng tất cả
)
```

## API Endpoints

### 1. Quản lý Strategies

#### Lấy danh sách strategies
```http
GET /api/extensible/strategies
```

#### Lấy chi tiết strategy
```http
GET /api/extensible/strategies/{strategy_name}
```

#### Thêm strategy mới
```http
POST /api/extensible/strategies/add
Content-Type: application/json

{
    "type": "rsi",
    "name": "Custom RSI Strategy",
    "description": "Custom RSI with different parameters",
    "weight": 0.9,
    "min_confidence": 0.7,
    "rsi_period": 21,
    "overbought_level": 75,
    "oversold_level": 25
}
```

#### Xóa strategy
```http
DELETE /api/extensible/strategies/{strategy_name}
```

### 2. Đánh giá tín hiệu

#### Đánh giá single timeframe
```http
POST /api/extensible/evaluate/{symbol_id}
Content-Type: application/json

{
    "timeframe": "5m",
    "strategies": ["SMA Strategy", "MACD Strategy"]
}
```

#### Đánh giá multi-timeframe
```http
POST /api/extensible/multi-timeframe/{symbol_id}
Content-Type: application/json

{
    "strategies": ["SMA Strategy", "MACD Strategy", "RSI Strategy"]
}
```

### 3. Cấu hình Aggregation

#### Lấy cấu hình aggregation
```http
GET /api/extensible/aggregation/config
```

#### Cập nhật cấu hình aggregation
```http
POST /api/extensible/aggregation/config
Content-Type: application/json

{
    "method": "consensus",
    "min_strategies": 2,
    "consensus_threshold": 0.7,
    "confidence_threshold": 0.6,
    "custom_weights": {
        "SMA Strategy": 1.2,
        "MACD Strategy": 1.0,
        "RSI Strategy": 0.8
    }
}
```

### 4. Test hệ thống

#### Test toàn bộ hệ thống
```http
POST /api/extensible/test
Content-Type: application/json

{
    "symbol_id": 1,
    "timeframe": "5m",
    "strategies": ["SMA Strategy", "MACD Strategy"]
}
```

## Ví dụ sử dụng

### 1. Thêm RSI Strategy

```python
from app.services.strategy_implementations import RSIStrategy
from app.services.strategy_base import StrategyConfig

# Tạo config cho RSI
config = StrategyConfig(
    name="Custom RSI Strategy",
    description="RSI with custom parameters",
    version="1.0.0",
    weight=0.8,
    min_confidence=0.6,
    parameters={
        'rsi_period': 14,
        'overbought_level': 70,
        'oversold_level': 30
    }
)

# Tạo và đăng ký strategy
rsi_strategy = RSIStrategy(config)
extensible_signal_engine.add_strategy(rsi_strategy)
```

### 2. Đánh giá tín hiệu với nhiều strategies

```python
# Đánh giá với tất cả strategies
result = extensible_signal_engine.evaluate_signal(
    symbol_id=1,
    ticker="AAPL",
    exchange="NASDAQ",
    timeframe="5m"
)

print(f"Final Signal: {result['final_signal']}")
print(f"Direction: {result['final_direction']}")
print(f"Strength: {result['final_strength']}")
print(f"Confidence: {result['final_confidence']}")
print(f"Participating Strategies: {result['participating_strategies']}")
```

### 3. Cấu hình aggregation

```python
from app.services.aggregation_engine import AggregationConfig, AggregationMethod

# Cấu hình consensus với threshold cao
config = AggregationConfig(
    method=AggregationMethod.CONSENSUS,
    min_strategies=3,
    consensus_threshold=0.8,
    confidence_threshold=0.7
)

extensible_signal_engine.update_aggregation_config(config)
```

## Lợi ích của thiết kế này

### 1. **Mở rộng dễ dàng**
- Chỉ cần implement `BaseStrategy`
- Không cần thay đổi code hiện tại
- Tự động tích hợp vào hệ thống

### 2. **Linh hoạt**
- Hỗ trợ nhiều phương pháp aggregation
- Có thể cấu hình trọng số cho từng strategy
- Hỗ trợ custom parameters

### 3. **Kiểm soát chất lượng**
- Validation config
- Confidence scoring
- Error handling

### 4. **Performance**
- Registry pattern cho lookup nhanh
- Caching strategies
- Parallel evaluation

### 5. **Maintainability**
- Code tách biệt rõ ràng
- Dễ test từng component
- Documentation đầy đủ

## Testing

### Chạy test hệ thống
```bash
cd backend
python scripts/test_extensible_system.py
```

### Test API
```bash
# Test available strategies
curl http://localhost:5010/api/extensible/strategies

# Test signal evaluation
curl -X POST http://localhost:5010/api/extensible/evaluate/1 \
  -H "Content-Type: application/json" \
  -d '{"timeframe": "5m", "strategies": ["SMA Strategy", "MACD Strategy"]}'

# Test system
curl -X POST http://localhost:5010/api/extensible/test \
  -H "Content-Type: application/json" \
  -d '{"symbol_id": 1, "timeframe": "5m"}'
```

## Kết luận

Hệ thống Extensible Strategy cho phép:
- ✅ Thêm strategies mới dễ dàng
- ✅ Tổng hợp tín hiệu từ nhiều strategies
- ✅ Cấu hình linh hoạt
- ✅ API đầy đủ
- ✅ Testing và monitoring
- ✅ Performance cao
- ✅ Maintainability tốt

Với thiết kế này, bạn có thể dễ dàng mở rộng hệ thống với bất kỳ strategy nào mà không cần thay đổi code hiện tại!
