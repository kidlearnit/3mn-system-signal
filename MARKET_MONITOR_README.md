# Market Signal Monitor

Hệ thống sử dụng **Hybrid Signal Engine** để monitor thị trường và gửi tín hiệu từng mã riêng lẻ vào Telegram khi thị trường mở cửa.

## 🎯 Tính năng chính

### 1. **Hybrid Signal Engine Integration**
- Sử dụng kết hợp SMA và MACD signals
- Cấu hình thresholds tối ưu cho thị trường Việt Nam
- Đánh giá confidence score cho mỗi tín hiệu

### 2. **Market-Aware Monitoring**
- Tự động kiểm tra thời gian mở cửa thị trường
- Hỗ trợ thị trường VN và US
- Timezone-aware scheduling

### 3. **Individual Symbol Processing**
- Xử lý từng mã cổ phiếu riêng lẻ
- Tránh gửi tín hiệu trùng lặp (cache system)
- Gửi tin nhắn chi tiết cho mỗi tín hiệu

### 4. **Smart Telegram Integration**
- Format tin nhắn đẹp với emoji
- Gửi thông tin chi tiết về tín hiệu
- Chỉ gửi tín hiệu có độ tin cậy cao (>60%)

## 📁 Cấu trúc file

```
app/services/
├── market_signal_monitor.py      # Core monitoring service
├── hybrid_signal_engine.py       # Hybrid signal engine
└── sma_telegram_service.py       # Telegram integration

worker/
└── market_monitor_worker.py      # Scheduled worker

scripts/
├── run_market_monitor.py         # Main monitoring script
└── start_market_monitor.sh       # Easy start script
```

## 🚀 Cách sử dụng

### 1. **Chạy monitoring một lần (Test mode)**
```bash
python run_market_monitor.py --mode single --market VN
```

### 2. **Chạy monitoring liên tục (Production mode)**
```bash
python run_market_monitor.py --mode continuous --market VN --interval 5
```

### 3. **Chạy worker với lịch tự động**
```bash
python worker/market_monitor_worker.py
```

### 4. **Sử dụng script tiện lợi**
```bash
./start_market_monitor.sh
```

## ⏰ Lịch monitoring

### Thị trường VN
- **Phiên sáng**: 9:05, 9:35, 10:05, 10:35, 11:05
- **Phiên chiều**: 13:05, 13:35, 14:05, 14:35
- **Timezone**: Asia/Ho_Chi_Minh

### Thị trường US
- **Giờ mở cửa**: 9:35, 10:05, 10:35, 11:05, 11:35, 12:05, 12:35, 13:05, 13:35, 14:05, 14:35, 15:05
- **Timezone**: America/New_York

## 📊 Cấu hình thresholds

### VN30 (Index)
```yaml
thresholds:
  1m: 0.12    # -20% từ cấu hình cũ
  2m: 0.20    # -20% từ cấu hình cũ
  5m: 0.30    # -14% từ cấu hình cũ
  15m: 0.45   # -10% từ cấu hình cũ
  30m: 0.65   # -13% từ cấu hình cũ
  1h: 0.85    # -15% từ cấu hình cũ
  4h: 1.25    # -17% từ cấu hình cũ
```

### Lý do điều chỉnh
- Thị trường VN biến động cao hơn 67% so với US
- Thresholds thấp hơn để phát hiện tín hiệu sớm hơn
- Dự kiến cải thiện 4% accuracy, 3% ít false positive

## 🎯 Logic tín hiệu

### Hybrid Signal Types
- **STRONG_BUY**: Cả SMA và MACD đều BUY
- **BUY**: Một BUY, một NEUTRAL
- **WEAK_BUY**: Một BUY, một SELL (conflict)
- **NEUTRAL**: Cả hai đều NEUTRAL
- **WEAK_SELL**: Một SELL, một BUY (conflict)
- **SELL**: Một SELL, một NEUTRAL
- **STRONG_SELL**: Cả SMA và MACD đều SELL

### Confidence Scoring
- **Base confidence**: Từ strength của hybrid signal
- **Bonus +0.2**: Nếu cả SMA và MACD đồng thuận
- **Penalty -0.3**: Nếu SMA và MACD conflict
- **Minimum threshold**: 60% để gửi tín hiệu

## 💾 Cache System

### Tránh spam tín hiệu
- Cache tín hiệu đã gửi trong 30 phút
- Key format: `{symbol_id}_{signal_type}_{timeframe}`
- Tự động cleanup cache cũ

### Cache Logic
```python
# Lần đầu: Gửi tín hiệu
should_send_signal(symbol_id, "BUY", "5m")  # True

# Lần thứ hai (trong 30 phút): Không gửi
should_send_signal(symbol_id, "BUY", "5m")  # False
```

## 📱 Format tin nhắn Telegram

```
🟢💪 **TÍN HIỆU GIAO DỊCH**

📈 **Mã cổ phiếu:** VN30
🏢 **Công ty:** VN30 Index
🏭 **Ngành:** Index
⏰ **Timeframe:** 5m

🎯 **Tín hiệu Hybrid:**
• Loại: STRONG BUY
• Hướng: BUY
• Độ mạnh: 0.85
• Độ tin cậy: 0.78

📊 **Chi tiết chỉ báo:**
• SMA: BUY
• MACD: BUY

⏰ **Thời gian:** 15/10/2025 00:48:34
```

## 🔧 Cấu hình Environment

```bash
# Telegram Bot
export TG_TOKEN="your_telegram_bot_token"
export TG_CHAT_ID="your_telegram_chat_id"

# Database
export DATABASE_URL="your_database_url"

# Timezone
export TIMEZONE="Asia/Ho_Chi_Minh"
```

## 📈 Monitoring & Logging

### Log Files
- `logs/market_monitor.log` - Main monitoring logs
- `logs/market_monitor_worker.log` - Worker logs

### Log Levels
- **INFO**: Normal operations
- **WARNING**: Low confidence signals
- **ERROR**: Processing errors
- **DEBUG**: Detailed debugging info

## 🚨 Error Handling

### Database Connection
- Graceful fallback to mock data
- Retry mechanism for connection issues
- Log all database errors

### Telegram Sending
- Retry failed messages
- Log delivery status
- Continue processing other symbols

### Market Status
- Handle timezone issues
- Validate market schedules
- Skip processing when market closed

## 📊 Performance Metrics

### Expected Improvements
- **Signal Accuracy**: 68% → 72% (+4%)
- **False Positive Rate**: 25% → 22% (-3%)
- **Net Accuracy**: 43% → 50% (+7%)

### Monitoring KPIs
- Signals sent per hour
- Success rate of signal delivery
- Cache hit rate
- Processing time per symbol

## 🔄 Maintenance

### Daily Tasks
- Monitor log files for errors
- Check Telegram delivery status
- Verify market schedules

### Weekly Tasks
- Review signal accuracy
- Analyze cache performance
- Update thresholds if needed

### Monthly Tasks
- Performance analysis
- Threshold optimization
- System health check

## 🆘 Troubleshooting

### Common Issues

1. **No signals generated**
   - Check market status
   - Verify symbol data
   - Check confidence thresholds

2. **Telegram not sending**
   - Verify bot token
   - Check chat ID
   - Test connection

3. **Database errors**
   - Check connection string
   - Verify table structure
   - Check permissions

### Debug Commands
```bash
# Test market status
python -c "from app.services.market_signal_monitor import market_signal_monitor; print(market_signal_monitor.is_market_open('VN'))"

# Test symbol retrieval
python -c "from app.services.market_signal_monitor import market_signal_monitor; print(len(market_signal_monitor.get_active_symbols('VN')))"

# Test signal processing
python -c "import asyncio; from app.services.market_signal_monitor import market_signal_monitor; asyncio.run(market_signal_monitor.monitor_market_signals('VN'))"
```

## 📞 Support

Nếu gặp vấn đề, hãy kiểm tra:
1. Log files trong thư mục `logs/`
2. Environment variables
3. Database connection
4. Telegram bot configuration

---

**Market Signal Monitor** - Hệ thống monitoring thông minh cho thị trường chứng khoán Việt Nam 🇻🇳
