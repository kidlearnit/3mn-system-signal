#!/bin/bash
# Setup VN30 Index Realtime Job

echo "Setting up VN30 Index Realtime Job..."

# Get current directory
PROJECT_DIR=$(pwd)

# Create systemd service file for VN30 Realtime Job
SERVICE_FILE="/etc/systemd/system/vn30-realtime.service"

echo "Creating systemd service file..."

sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=VN30 Index Realtime Job
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker-compose exec -T market_monitor python vn30_realtime_job.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "Reloading systemd and enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable vn30-realtime.service

echo "✅ VN30 Index Realtime Job setup completed!"
echo ""
echo "📊 VN30 Realtime Job Features:"
echo "   🎯 Single Symbol: VN30 Index (VN-Index)"
echo "   📊 SMA + MACD: Hybrid signal analysis"
echo "   ⏰ 3-Timeframe Analysis: 1m, 2m, 5m"
echo "   🔄 Realtime Processing: Only when new data arrives"
echo "   📅 VN Market Hours: 09:00 - 15:00 (UTC+7)"
echo "   ⏱️ Cycle Interval: 30 seconds"
echo ""
echo "🚀 Service Management Commands:"
echo "   Start:   sudo systemctl start vn30-realtime"
echo "   Stop:    sudo systemctl stop vn30-realtime"
echo "   Status:  sudo systemctl status vn30-realtime"
echo "   Logs:    sudo journalctl -u vn30-realtime -f"
echo ""
echo "📋 Manual Testing:"
echo "   docker-compose exec market_monitor python vn30_realtime_job.py"
echo ""
echo "📈 Realtime Features:"
echo "   🔄 Data-Driven: Only processes when new candles arrive"
echo "   ⚡ Efficient: No unnecessary calculations"
echo "   📊 Real-time: Immediate signal generation"
echo "   🎯 Market-Aware: Only runs during VN market hours"
