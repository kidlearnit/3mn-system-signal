#!/bin/bash

# Script để khởi động Market Signal Monitor
# Sử dụng Hybrid Signal Engine để monitor thị trường và gửi tín hiệu từng mã riêng lẻ

echo "🚀 Starting Market Signal Monitor"
echo "=================================="

# Kiểm tra Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python3."
    exit 1
fi

# Kiểm tra pyenv
if command -v pyenv &> /dev/null; then
    echo "🐍 Activating pyenv environment..."
    pyenv local py-yfinance-app
fi

# Tạo thư mục logs nếu chưa có
mkdir -p logs

# Kiểm tra file cấu hình
if [ ! -f "app/services/market_signal_monitor.py" ]; then
    echo "❌ Market Signal Monitor not found. Please check the file path."
    exit 1
fi

# Hiển thị menu
echo ""
echo "📋 Choose monitoring mode:"
echo "1. Single run (test mode)"
echo "2. Continuous monitoring (production mode)"
echo "3. Worker mode (scheduled monitoring)"
echo "4. Test mode (run tests)"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🔧 Running single monitoring..."
        python3 run_market_monitor.py --mode single --market VN
        ;;
    2)
        echo "🔄 Starting continuous monitoring..."
        echo "Press Ctrl+C to stop"
        python3 run_market_monitor.py --mode continuous --market VN --interval 5
        ;;
    3)
        echo "⏰ Starting worker mode..."
        echo "Press Ctrl+C to stop"
        python3 worker/market_monitor_worker.py
        ;;
    4)
        echo "🧪 Running tests..."
        python3 test_market_monitor.py
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "👋 Market Signal Monitor stopped"
