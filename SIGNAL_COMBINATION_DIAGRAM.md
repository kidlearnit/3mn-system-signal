# Signal Combination Diagram

## 🎯 Cách kết hợp SMA và MACD trong Hybrid Signal Engine

### 📊 Vai trò của từng chỉ báo

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID SIGNAL ENGINE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │   SMA SIGNAL    │              │   MACD SIGNAL   │      │
│  │                 │              │                 │      │
│  │ 🎯 TREND        │              │ ⚡ TIMING       │      │
│  │ CONFIRMER       │              │ PROVIDER        │      │
│  │                 │              │                 │      │
│  │ • M1 (MA18)     │              │ • FMACD (7,113) │      │
│  │ • M2 (MA36)     │              │ • SMACD (144)   │      │
│  │ • M3 (MA48)     │              │ • Bars (Hist)   │      │
│  │ • MA144         │              │                 │      │
│  │                 │              │                 │      │
│  │ Logic:          │              │ Logic:          │      │
│  │ CP > M1 > M2 > M3│              │ Zones: bull/    │      │
│  │ avg > MA144     │              │ neutral/bear    │      │
│  └─────────────────┘              └─────────────────┘      │
│           │                                │                │
│           │ SMA Direction                  │ MACD Direction │
│           │ (BUY/SELL/NEUTRAL)            │ (BUY/SELL/NEUTRAL)│
│           │                                │                │
│           └──────────────┬─────────────────┘                │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              SIGNAL COMBINATION LOGIC                   │ │
│  │                                                         │ │
│  │ SMA + MACD = Hybrid Signal                              │ │
│  │                                                         │ │
│  │ ┌─────────┬─────────┬─────────────────────────────────┐ │ │
│  │ │   SMA   │  MACD   │           RESULT                │ │ │
│  │ ├─────────┼─────────┼─────────────────────────────────┤ │ │
│  │ │  BUY    │  BUY    │ STRONG_BUY (strength: sum)     │ │ │
│  │ │  SELL   │  SELL   │ STRONG_SELL (strength: sum)    │ │ │
│  │ │  BUY    │NEUTRAL  │ BUY (strength: sma * 0.7)      │ │ │
│  │ │NEUTRAL  │  BUY    │ BUY (strength: macd * 0.7)     │ │ │
│  │ │  SELL   │NEUTRAL  │ SELL (strength: sma * 0.7)     │ │ │
│  │ │NEUTRAL  │  SELL   │ SELL (strength: macd * 0.7)    │ │ │
│  │ │  BUY    │  SELL   │ WEAK_BUY (strength: diff * 0.3)│ │ │
│  │ │  SELL   │  BUY    │ WEAK_SELL (strength: diff * 0.3)│ │ │
│  │ │NEUTRAL  │NEUTRAL  │ NEUTRAL (strength: 0.0)        │ │ │
│  │ └─────────┴─────────┴─────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🔄 Quy trình xử lý

```
1. LẤY DỮ LIỆU SMA
   ┌─────────────────────────────────────────────────────────┐
   │ Database: indicators_sma                                │
   │ SELECT ts, close, m1, m2, m3, ma144, avg_m1_m2_m3     │
   │ WHERE symbol_id = ? AND timeframe = ?                  │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │ MA Structure:                                           │
   │ {                                                       │
   │   'cp': close_price,                                    │
   │   'm1': ma18,                                          │
   │   'm2': ma36,                                          │
   │   'm3': ma48,                                          │
   │   'ma144': ma144,                                      │
   │   'avg_m1_m2_m3': (m1+m2+m3)/3                        │
   │ }                                                       │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │ SMA Evaluation:                                         │
   │ • Local Bullish: CP > M1 > M2 > M3 AND avg > MA144    │
   │ • Local Bearish: CP < M1 < M2 < M3 AND avg < MA144    │
   │ • Confirmed: Local + higher timeframe local            │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │ SMA Signal: {direction, strength, signal_type}         │
   └─────────────────────────────────────────────────────────┘

2. LẤY DỮ LIỆU MACD
   ┌─────────────────────────────────────────────────────────┐
   │ Database: indicators_macd                               │
   │ SELECT ts, macd, macd_signal, hist                     │
   │ WHERE symbol_id = ? AND timeframe = ?                  │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │ MACD Zones:                                             │
   │ • f_zone = match_zone_with_thresholds(macd, 'fmacd')   │
   │ • s_zone = match_zone_with_thresholds(signal, 'smacd') │
   │ • bars_zone = match_zone_with_thresholds(hist, 'bars') │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │ MACD Signal: {direction, strength, signal_type}        │
   └─────────────────────────────────────────────────────────┘

3. KẾT HỢP TÍN HIỆU
   ┌─────────────────────────────────────────────────────────┐
   │ SMA Signal + MACD Signal = Hybrid Signal                │
   │                                                         │
   │ if sma_direction == 'BUY' and macd_direction == 'BUY': │
   │     result = 'STRONG_BUY'                              │
   │     strength = min(sma_strength + macd_strength, 1.0)  │
   │ elif sma_direction == 'BUY' and macd_direction == 'NEUTRAL':│
   │     result = 'BUY'                                     │
   │     strength = sma_strength * 0.7                      │
   │ # ... các trường hợp khác                              │
   └─────────────────────────────────────────────────────────┘
```

### 📊 Ma trận kết hợp chi tiết

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SIGNAL COMBINATION MATRIX                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  SMA Direction  │  MACD Direction  │  Hybrid Result  │  Strength Formula      │
├─────────────────┼──────────────────┼─────────────────┼─────────────────────────┤
│      BUY        │      BUY         │  STRONG_BUY     │  sma + macd (max 1.0)  │
│      SELL       │      SELL        │  STRONG_SELL    │  sma + macd (max 1.0)  │
│      BUY        │    NEUTRAL       │      BUY        │  sma * 0.7             │
│    NEUTRAL      │      BUY         │      BUY        │  macd * 0.7            │
│      SELL       │    NEUTRAL       │      SELL       │  sma * 0.7             │
│    NEUTRAL      │      SELL        │      SELL       │  macd * 0.7            │
│      BUY        │      SELL        │    WEAK_BUY     │  |sma-macd| * 0.3      │
│      SELL       │      BUY         │    WEAK_SELL    │  |sma-macd| * 0.3      │
│    NEUTRAL      │    NEUTRAL       │    NEUTRAL      │  0.0                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 🎯 Ví dụ cụ thể

```
VÍ DỤ 1: STRONG_BUY
┌─────────────────────────────────────────────────────────┐
│ SMA Signal:                                             │
│ • Direction: BUY                                        │
│ • Strength: 0.8                                         │
│ • Details: CP > M1 > M2 > M3, avg > MA144              │
│                                                         │
│ MACD Signal:                                            │
│ • Direction: BUY                                        │
│ • Strength: 0.7                                         │
│ • Details: FMACD > threshold, SMACD > threshold         │
│                                                         │
│ Hybrid Result:                                          │
│ • Type: STRONG_BUY                                      │
│ • Strength: 1.0 (0.8 + 0.7, capped at 1.0)            │
│ • Confidence: 0.9 (high agreement)                     │
└─────────────────────────────────────────────────────────┘

VÍ DỤ 2: BUY (SMA Confirm)
┌─────────────────────────────────────────────────────────┐
│ SMA Signal:                                             │
│ • Direction: BUY                                        │
│ • Strength: 0.8                                         │
│ • Details: CP > M1 > M2 > M3, avg > MA144              │
│                                                         │
│ MACD Signal:                                            │
│ • Direction: NEUTRAL                                    │
│ • Strength: 0.3                                         │
│ • Details: FMACD neutral, SMACD neutral                 │
│                                                         │
│ Hybrid Result:                                          │
│ • Type: BUY                                             │
│ • Strength: 0.56 (0.8 * 0.7)                           │
│ • Confidence: 0.7 (SMA confirm, MACD neutral)          │
└─────────────────────────────────────────────────────────┘

VÍ DỤ 3: WEAK_BUY (Conflict)
┌─────────────────────────────────────────────────────────┐
│ SMA Signal:                                             │
│ • Direction: BUY                                        │
│ • Strength: 0.8                                         │
│ • Details: CP > M1 > M2 > M3, avg > MA144              │
│                                                         │
│ MACD Signal:                                            │
│ • Direction: SELL                                       │
│ • Strength: 0.6                                         │
│ • Details: FMACD < threshold, SMACD < threshold         │
│                                                         │
│ Hybrid Result:                                          │
│ • Type: WEAK_BUY                                        │
│ • Strength: 0.06 (|0.8-0.6| * 0.3)                     │
│ • Confidence: 0.4 (conflict between signals)           │
└─────────────────────────────────────────────────────────┘
```

### 🔧 Technical Implementation

```python
def _combine_signals(self, sma_signal: Dict, macd_signal: Dict, timeframe: str) -> Dict[str, Any]:
    """Kết hợp tín hiệu SMA và MACD"""
    
    sma_direction = sma_signal.get('direction', 'NEUTRAL')
    macd_direction = macd_signal.get('direction', 'NEUTRAL')
    sma_strength = sma_signal.get('strength', 0.0)
    macd_strength = macd_signal.get('strength', 0.0)
    
    # Logic kết hợp
    if sma_direction == 'BUY' and macd_direction == 'BUY':
        signal_type = HybridSignalType.STRONG_BUY
        direction = 'BUY'
        strength = min(sma_strength + macd_strength, 1.0)
        logic = "Both SMA and MACD bullish"
        
    elif sma_direction == 'SELL' and macd_direction == 'SELL':
        signal_type = HybridSignalType.STRONG_SELL
        direction = 'SELL'
        strength = min(sma_strength + macd_strength, 1.0)
        logic = "Both SMA and MACD bearish"
        
    elif sma_direction == 'BUY' and macd_direction == 'NEUTRAL':
        signal_type = HybridSignalType.BUY
        direction = 'BUY'
        strength = sma_strength * 0.7  # Giảm strength vì chỉ có SMA
        logic = "SMA bullish, MACD neutral"
        
    # ... các trường hợp khác
    
    return {
        'signal_type': signal_type,
        'direction': direction,
        'strength': strength,
        'logic': logic
    }
```

### ✅ Lợi ích của cách kết hợp

1. **🎯 SMA (Trend Confirmer)**:
   - Xác định xu hướng chính (bull/bear)
   - Cung cấp foundation ổn định
   - Giảm noise và false signals

2. **⚡ MACD (Timing Provider)**:
   - Cung cấp thời điểm vào/ra lệnh
   - Sử dụng FMACD để tính toán momentum
   - Tăng độ nhạy của hệ thống

3. **🔄 Hybrid System**:
   - Vừa ổn định (SMA) vừa nhạy (MACD)
   - 7 loại tín hiệu với strength khác nhau
   - Confidence scoring thông minh
   - Phù hợp với đặc điểm thị trường VN
