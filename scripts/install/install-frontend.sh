#!/bin/bash

# Install Frontend Dependencies
echo "📦 Installing Frontend Dependencies..."

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "🔧 Installing npm packages..."
npm install

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ Frontend dependencies installed successfully!"
    echo "🚀 You can now run: ./start-frontend.sh"
else
    echo "❌ Frontend dependency installation failed!"
    exit 1
fi
