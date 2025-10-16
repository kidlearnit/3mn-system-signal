# QUY TRÌNH RA TÍN HIỆU TRONG HỆ THỐNG

## 📊 TỔNG QUAN QUY TRÌNH

Hệ thống sử dụng **Hybrid Signal Engine** để kết hợp 2 chỉ báo chính:
- **SMA (Simple Moving Average)**: Xác nhận xu hướng (trend confirmation)
- **MACD (Moving Average Convergence Divergence)**: Tính toán momentum

## 🔄 QUY TRÌNH CHI TIẾT

### 1. **KHỞI TẠO (Initialization)**
```
HybridSignalEngine.__init__()
├── sma_engine = sma_signal_engine
├── confidence_threshold = 0.6 (60%)
└── strong_signal_threshold = 0.8 (80%)
```

### 2. **ĐÁNH GIÁ TÍN HIỆU HYBRID (evaluate_hybrid_signal)**
```
Input: symbol_id, ticker, exchange, timeframe
│
├── 1. Lấy tín hiệu SMA (_get_sma_signal)
├── 2. Lấy tín hiệu MACD (_get_macd_signal)
├── 3. Kết hợp tín hiệu (_combine_signals)
├── 4. Tính confidence score (_calculate_confidence)
└── 5. Tạo kết quả cuối cùng
```

### 3. **LẤY TÍN HIỆU SMA (_get_sma_signal)**

#### 3.1. Truy vấn dữ liệu SMA
```sql
SELECT ts, close, m1, m2, m3, ma144, avg_m1_m2_m3
FROM indicators_sma
WHERE symbol_id = :symbol_id AND timeframe = :timeframe
ORDER BY ts DESC LIMIT 1
```

#### 3.2. Cấu trúc MA
```python
ma_structure = {
    'cp': close_price,      # Giá đóng cửa hiện tại
    'm1': ma_18,           # MA 18 periods
    'm2': ma_36,           # MA 36 periods  
    'm3': ma_48,           # MA 48 periods
    'ma144': ma_144,       # MA 144 periods
    'avg_m1_m2_m3': (m1 + m2 + m3) / 3
}
```

#### 3.3. Đánh giá tín hiệu SMA
```python
signal_type = sma_engine.evaluate_single_timeframe(ma_structure)
direction = sma_engine.get_signal_direction(signal_type)
strength = sma_engine.get_signal_strength(signal_type)
```

### 4. **LẤY TÍN HIỆU MACD (_get_macd_signal)**

#### 4.1. Truy vấn dữ liệu MACD
```sql
SELECT ts, macd, macd_signal, hist
FROM indicators_macd
WHERE symbol_id = :symbol_id AND timeframe = :timeframe
ORDER BY ts DESC LIMIT 1
```

#### 4.2. Đánh giá zones
```python
f_zone = match_zone_with_thresholds(macd, symbol_id, timeframe, 'fmacd')
s_zone = match_zone_with_thresholds(macd_signal, symbol_id, timeframe, 'smacd')
bars_zone = match_zone_with_thresholds(abs(histogram), symbol_id, timeframe, 'bars')
```

#### 4.3. Tạo tín hiệu MACD
```python
macd_signal = make_signal(f_zone, s_zone, bars_zone)
strength = calculate_macd_strength(f_zone, s_zone, bars_zone)
```

### 5. **KẾT HỢP TÍN HIỆU (_combine_signals)**

#### 5.1. Ma trận kết hợp SMA + MACD
```
                    MACD
SMA         BUY    NEUTRAL    SELL
BUY      STRONG_BUY   BUY    WEAK_BUY
NEUTRAL     BUY    NEUTRAL     SELL
SELL      WEAK_SELL   SELL   STRONG_SELL
```

#### 5.2. Logic kết hợp chi tiết
```python
if sma_direction == 'BUY' and macd_direction == 'BUY':
    signal_type = STRONG_BUY
    strength = min(sma_strength + macd_strength, 1.0)
    logic = "Both SMA and MACD bullish"

elif sma_direction == 'SELL' and macd_direction == 'SELL':
    signal_type = STRONG_SELL
    strength = min(sma_strength + macd_strength, 1.0)
    logic = "Both SMA and MACD bearish"

elif sma_direction == 'BUY' and macd_direction == 'NEUTRAL':
    signal_type = BUY
    strength = sma_strength * 0.7  # Giảm vì chỉ có SMA
    logic = "SMA bullish, MACD neutral"

elif sma_direction == 'BUY' and macd_direction == 'SELL':
    signal_type = WEAK_BUY
    strength = abs(sma_strength - macd_strength) * 0.3  # Rất yếu vì conflict
    logic = "SMA bullish, MACD bearish (conflict)"

# ... các trường hợp khác
```

### 6. **TÍNH CONFIDENCE SCORE (_calculate_confidence)**

#### 6.1. Công thức tính confidence
```python
confidence = (sma_confidence + macd_confidence) / 2

# Trong đó:
sma_confidence = sma_signal.get('strength', 0.0)
macd_confidence = macd_signal.get('strength', 0.0)
```

#### 6.2. Phân loại confidence
- **High Confidence**: > 0.8 (80%)
- **Medium Confidence**: 0.6 - 0.8 (60-80%)
- **Low Confidence**: < 0.6 (60%)

### 7. **KẾT QUẢ CUỐI CÙNG**

#### 7.1. Cấu trúc kết quả
```python
result = {
    'symbol_id': symbol_id,
    'ticker': ticker,
    'exchange': exchange,
    'timeframe': timeframe,
    'timestamp': datetime.now().isoformat(),
    'hybrid_signal': hybrid_result['signal_type'],
    'hybrid_direction': hybrid_result['direction'],
    'hybrid_strength': hybrid_result['strength'],
    'confidence': confidence,
    'sma_signal': sma_signal,
    'macd_signal': macd_signal,
    'details': {
        'sma_details': sma_signal.get('details', {}),
        'macd_details': macd_signal.get('details', {}),
        'combination_logic': hybrid_result['logic']
    }
}
```

## 📊 CÁC LOẠI TÍN HIỆU

### 1. **STRONG_BUY** (Mua mạnh)
- **Điều kiện**: SMA = BUY + MACD = BUY
- **Strength**: Cao (sma_strength + macd_strength)
- **Confidence**: > 0.8
- **Logic**: "Both SMA and MACD bullish"

### 2. **BUY** (Mua)
- **Điều kiện**: (SMA = BUY + MACD = NEUTRAL) hoặc (SMA = NEUTRAL + MACD = BUY)
- **Strength**: Trung bình (strength * 0.7)
- **Confidence**: 0.6 - 0.8
- **Logic**: "SMA bullish, MACD neutral" hoặc "MACD bullish, SMA neutral"

### 3. **WEAK_BUY** (Mua yếu)
- **Điều kiện**: SMA = BUY + MACD = SELL (conflict)
- **Strength**: Thấp (abs(sma_strength - macd_strength) * 0.3)
- **Confidence**: < 0.6
- **Logic**: "SMA bullish, MACD bearish (conflict)"

### 4. **NEUTRAL** (Trung tính)
- **Điều kiện**: SMA = NEUTRAL + MACD = NEUTRAL
- **Strength**: 0.0
- **Confidence**: 0.0
- **Logic**: "Both SMA and MACD neutral"

### 5. **WEAK_SELL** (Bán yếu)
- **Điều kiện**: SMA = SELL + MACD = BUY (conflict)
- **Strength**: Thấp (abs(sma_strength - macd_strength) * 0.3)
- **Confidence**: < 0.6
- **Logic**: "SMA bearish, MACD bullish (conflict)"

### 6. **SELL** (Bán)
- **Điều kiện**: (SMA = SELL + MACD = NEUTRAL) hoặc (SMA = NEUTRAL + MACD = SELL)
- **Strength**: Trung bình (strength * 0.7)
- **Confidence**: 0.6 - 0.8
- **Logic**: "SMA bearish, MACD neutral" hoặc "MACD bearish, SMA neutral"

### 7. **STRONG_SELL** (Bán mạnh)
- **Điều kiện**: SMA = SELL + MACD = SELL
- **Strength**: Cao (sma_strength + macd_strength)
- **Confidence**: > 0.8
- **Logic**: "Both SMA and MACD bearish"

## 🎯 THRESHOLD SYSTEM

### 1. **Market Thresholds**
- **US Market**: Conservative thresholds (lower volatility)
- **VN Market**: Aggressive thresholds (higher volatility - 1.67x US)
- **GLOBAL Market**: Balanced thresholds (middle ground)

### 2. **Threshold Zones**
- **📈 Bullish**: `igr`, `greed`, `bull`, `pos`
- **📊 Neutral**: `neutral`
- **📉 Bearish**: `neg`, `bear`, `fear`, `panic`

### 3. **Indicators**
- **MACD**: `fmacd`, `smacd`, `bars`
- **SMA**: `m1`, `m2`, `m3`, `ma144`

## ⚡ REALTIME PROCESSING

### 1. **VN30 Realtime Job**
- **Market Hours**: 09:00 - 15:00 (UTC+7)
- **Timeframes**: 1m, 2m, 5m
- **Cycle Interval**: 30 seconds
- **Data-Driven**: Chỉ tính khi có dữ liệu mới

### 2. **Processing Flow**
```
1. Check Market Hours → 2. Check New Data → 3. Process Timeframes → 4. Aggregate Signals → 5. Log Results → 6. Wait & Repeat
```

### 3. **Signal Aggregation**
- **Overall Confidence**: Trung bình từ 3 timeframes
- **Overall Direction**: Majority vote từ 3 timeframes
- **Overall Signal**: Dựa trên direction và confidence

## 📈 VÍ DỤ THỰC TẾ

### Input Data:
```python
symbol_id = 1
ticker = "VN30"
exchange = "HOSE"
timeframe = "5m"
```

### SMA Signal:
```python
sma_signal = {
    'signal_type': 'bull',
    'direction': 'BUY',
    'strength': 0.7,
    'details': {
        'cp': 181.877594,
        'm1': 182.03459933,
        'm2': 182.68434483,
        'm3': 182.54627325,
        'ma144': 185.36357211,
        'avg_m1_m2_m3': 182.42173914
    }
}
```

### MACD Signal:
```python
macd_signal = {
    'signal_type': 'NEUTRAL',
    'direction': 'NEUTRAL',
    'strength': 0.16,
    'details': {
        'macd': -0.983951,
        'macd_signal': -1.073611,
        'histogram': 0.08966,
        'f_zone': 'neg',
        's_zone': 'neutral',
        'bars_zone': 'neutral'
    }
}
```

### Hybrid Result:
```python
result = {
    'hybrid_signal': 'BUY',
    'hybrid_direction': 'BUY',
    'hybrid_strength': 0.49,  # 0.7 * 0.7
    'confidence': 0.43,       # (0.7 + 0.16) / 2
    'combination_logic': 'SMA bullish, MACD neutral'
}
```

## 🚀 KẾT LUẬN

Quy trình ra tín hiệu trong hệ thống được thiết kế để:
1. **Kết hợp 2 chỉ báo**: SMA (trend) + MACD (momentum)
2. **Tăng độ chính xác**: Thông qua logic kết hợp thông minh
3. **Xử lý conflict**: Khi 2 chỉ báo mâu thuẫn
4. **Tính confidence**: Đánh giá độ tin cậy của tín hiệu
5. **Realtime processing**: Chỉ tính khi có dữ liệu mới
6. **Market-aware**: Chỉ chạy khi thị trường mở cửa
