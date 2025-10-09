#!/bin/bash

# Build Svelte Frontend for Production
echo "🔨 Building Svelte Frontend for Production..."

# Navigate to frontend directory
cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build the application
echo "🏗️ Building application..."
npm run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Frontend build completed successfully!"
    echo "📁 Built files are in: backend/app/static/dist/"
else
    echo "❌ Frontend build failed!"
    exit 1
fi
