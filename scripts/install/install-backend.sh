#!/bin/bash

# Install Backend Dependencies
echo "📦 Installing Backend Dependencies..."
echo "====================================="

# Navigate to backend directory
cd backend

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in backend directory!"
    exit 1
fi

# Install Python dependencies
echo "🔧 Installing Python packages..."
pip install -r requirements.txt

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ Backend dependencies installed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Create .env file in project root"
    echo "2. Run: ../start-backend.sh"
    echo "3. Or run: ../start-all.sh (backend + frontend)"
else
    echo "❌ Backend dependency installation failed!"
    echo "💡 Try: pip install --upgrade pip"
    exit 1
fi
