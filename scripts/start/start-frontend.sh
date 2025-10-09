#!/bin/bash

# Start Svelte Frontend Development Server
echo "🚀 Starting Svelte Frontend Development Server..."

# Navigate to frontend directory
cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo "🌐 Starting development server on http://localhost:3000"
npm run dev
