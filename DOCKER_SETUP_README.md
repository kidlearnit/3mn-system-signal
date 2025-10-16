# Docker Setup cho Market Signal Monitor

Hướng dẫn setup và chạy Market Signal Monitor với Docker để tự động monitor thị trường và gửi tín hiệu vào Telegram.

## 🚀 Quick Start

### 1. **Setup tự động (Khuyến nghị)**
```bash
./setup_docker_monitor.sh setup
```

### 2. **Setup thủ công**
```bash
# 1. Copy file cấu hình
cp env.market-monitor.example .env.market-monitor

# 2. Chỉnh sửa cấu hình
nano .env.market-monitor

# 3. Build và chạy
docker-compose -f docker-compose.market-monitor.yml up -d
```

## 📋 Yêu cầu hệ thống

### **Software Requirements:**
- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Python 3.9+ (cho testing)

### **Hardware Requirements:**
- RAM: Tối thiểu 512MB
- CPU: 1 core
- Disk: 1GB free space

## ⚙️ Cấu hình

### **1. Environment Variables**

Tạo file `.env.market-monitor` từ template:

```bash
cp env.market-monitor.example .env.market-monitor
```

**Cấu hình bắt buộc:**

```bash
# Telegram Bot Configuration
TG_TOKEN=your_telegram_bot_token_here
TG_CHAT_ID=your_telegram_chat_id_here

# Database Configuration
DATABASE_URL=mysql://user:password@localhost:3306/trading_signals

# Timezone
TZ=Asia/Ho_Chi_Minh
TIMEZONE=Asia/Ho_Chi_Minh
```

### **2. Telegram Bot Setup**

#### **Tạo Telegram Bot:**
1. Mở Telegram và tìm `@BotFather`
2. Gửi lệnh `/newbot`
3. Đặt tên cho bot
4. Lưu lại **Bot Token**

#### **Lấy Chat ID:**
1. Gửi tin nhắn cho bot
2. Truy cập: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Tìm `chat.id` trong response

### **3. Database Configuration**

#### **Option 1: External Database**
```bash
DATABASE_URL=mysql://username:password@host:port/database_name
```

#### **Option 2: Local MySQL (uncomment trong docker-compose)**
```bash
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=trading_signals
MYSQL_USER=trading_user
MYSQL_PASSWORD=trading_password
```

## 🐳 Docker Commands

### **Quản lý Container:**

```bash
# Start monitor
./setup_docker_monitor.sh start

# Stop monitor
./setup_docker_monitor.sh stop

# Restart monitor
./setup_docker_monitor.sh restart

# Check status
./setup_docker_monitor.sh status

# View logs
./setup_docker_monitor.sh logs
```

### **Docker Compose Commands:**

```bash
# Build image
docker-compose -f docker-compose.market-monitor.yml build

# Start services
docker-compose -f docker-compose.market-monitor.yml up -d

# Stop services
docker-compose -f docker-compose.market-monitor.yml down

# View logs
docker-compose -f docker-compose.market-monitor.yml logs -f

# Restart services
docker-compose -f docker-compose.market-monitor.yml restart
```

## 📊 Monitoring & Logs

### **Log Files:**
- **Container logs**: `docker logs market-signal-monitor`
- **Application logs**: Mounted to `./logs/` directory
- **Docker logs**: `docker-compose logs market-monitor`

### **Health Check:**
```bash
# Check container health
docker inspect market-signal-monitor --format='{{.State.Health.Status}}'

# Manual health check
docker exec market-signal-monitor python -c "from app.services.market_signal_monitor import market_signal_monitor; print('OK')"
```

### **Monitoring Commands:**
```bash
# Container status
docker ps -f name=market-signal-monitor

# Resource usage
docker stats market-signal-monitor

# Container info
docker inspect market-signal-monitor
```

## ⏰ Lịch Tự Động

### **Thị trường VN:**
- **Phiên sáng**: 9:05, 9:35, 10:05, 10:35, 11:05
- **Phiên chiều**: 13:05, 13:35, 14:05, 14:35
- **Timezone**: Asia/Ho_Chi_Minh

### **Thị trường US:**
- **Giờ mở cửa**: 9:35, 10:05, 10:35, 11:05, 11:35, 12:05, 12:35, 13:05, 13:35, 14:05, 14:35, 15:05
- **Timezone**: America/New_York

## 🧪 Testing

### **Test Telegram Connection:**
```bash
# Test trong container
docker exec market-signal-monitor python test_telegram_connection.py

# Test local
python test_telegram_connection.py
```

### **Test với Mock Signals:**
```bash
# Test trong container
docker exec market-signal-monitor python demo_with_mock_signals.py

# Test local
python demo_with_mock_signals.py
```

### **Test Market Status:**
```bash
# Test trong container
docker exec market-signal-monitor python -c "
from app.services.market_signal_monitor import market_signal_monitor
print('VN Market:', 'OPEN' if market_signal_monitor.is_market_open('VN') else 'CLOSED')
print('US Market:', 'OPEN' if market_signal_monitor.is_market_open('US') else 'CLOSED')
"
```

## 🔧 Troubleshooting

### **Common Issues:**

#### **1. Container không start:**
```bash
# Check logs
docker logs market-signal-monitor

# Check environment
docker exec market-signal-monitor env | grep TG_

# Restart container
docker-compose -f docker-compose.market-monitor.yml restart
```

#### **2. Telegram không gửi được:**
```bash
# Test Telegram connection
./setup_docker_monitor.sh test

# Check bot token
echo $TG_TOKEN

# Check chat ID
echo $TG_CHAT_ID
```

#### **3. Database connection error:**
```bash
# Check database URL
echo $DATABASE_URL

# Test database connection
docker exec market-signal-monitor python -c "
import os
print('Database URL:', os.getenv('DATABASE_URL'))
"
```

#### **4. Container bị restart liên tục:**
```bash
# Check health status
docker inspect market-signal-monitor --format='{{.State.Health.Status}}'

# Check resource usage
docker stats market-signal-monitor

# Check logs for errors
docker logs market-signal-monitor --tail 50
```

### **Debug Commands:**

```bash
# Enter container
docker exec -it market-signal-monitor bash

# Check Python environment
docker exec market-signal-monitor python --version

# Check installed packages
docker exec market-signal-monitor pip list

# Check file permissions
docker exec market-signal-monitor ls -la /app
```

## 📈 Performance Tuning

### **Resource Limits:**
```yaml
# Trong docker-compose.market-monitor.yml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

### **Log Rotation:**
```yaml
# Trong docker-compose.market-monitor.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔄 Updates & Maintenance

### **Update Application:**
```bash
# Pull latest changes
git pull

# Rebuild and restart
./setup_docker_monitor.sh restart
```

### **Update Dependencies:**
```bash
# Rebuild image
docker-compose -f docker-compose.market-monitor.yml build --no-cache

# Restart container
docker-compose -f docker-compose.market-monitor.yml restart
```

### **Backup Configuration:**
```bash
# Backup environment file
cp .env.market-monitor .env.market-monitor.backup

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

## 🚨 Security

### **Environment Variables:**
- Không commit file `.env.market-monitor` vào git
- Sử dụng strong passwords cho database
- Rotate Telegram bot token định kỳ

### **Network Security:**
- Chỉ expose ports cần thiết
- Sử dụng internal networks cho database
- Enable firewall rules

### **Container Security:**
- Sử dụng non-root user trong container
- Scan images for vulnerabilities
- Keep base images updated

## 📞 Support

### **Logs để debug:**
```bash
# Application logs
docker logs market-signal-monitor

# System logs
journalctl -u docker

# Container health
docker inspect market-signal-monitor
```

### **Common Solutions:**
1. **Container không start**: Check environment variables
2. **Telegram không gửi**: Verify bot token và chat ID
3. **Database error**: Check connection string
4. **Memory issues**: Increase resource limits

---

**Market Signal Monitor Docker Setup** - Hệ thống monitoring tự động cho thị trường chứng khoán 🇻🇳
