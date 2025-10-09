#!/bin/bash

# Cleanup Script for Trading Signals Project
echo "🧹 Cleaning up project..."
echo "========================="

# Remove Python cache files
echo "🗑️ Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove Icon files
echo "🗑️ Removing Icon files..."
find . -name "Icon" -type f -delete 2>/dev/null || true

# Remove temporary files
echo "🗑️ Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*.backup" -delete 2>/dev/null || true

# Remove log files
echo "🗑️ Removing log files..."
find . -name "*.log" -delete 2>/dev/null || true

# Clean up frontend
echo "🧹 Cleaning frontend..."
cd frontend
if [ -d "node_modules" ]; then
    echo "🗑️ Removing node_modules..."
    rm -rf node_modules
fi
if [ -d "dist" ]; then
    echo "🗑️ Removing dist folder..."
    rm -rf dist
fi
cd ..

# Clean up Docker
echo "🐳 Cleaning Docker..."
docker system prune -f 2>/dev/null || true

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📋 To restore dependencies:"
echo "  ./install-backend.sh"
echo "  ./install-frontend.sh"
