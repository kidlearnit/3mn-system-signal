#!/bin/bash

# Start both Backend and Frontend
echo "🚀 Starting 3MN Trading Signals System (Backend + Frontend)"
echo "============================================================"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    # Kill background processes
    jobs -p | xargs -r kill
    # Stop Docker services
    docker-compose down
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend services
echo "🔧 Starting backend services..."
./start-backend.sh &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 10

# Check if backend is running
if curl -s http://localhost:5010 > /dev/null; then
    echo "✅ Backend is ready at http://localhost:5010"
else
    echo "❌ Backend is not responding, but continuing..."
fi

# Start frontend
echo "🎨 Starting frontend development server..."
./start-frontend.sh &
FRONTEND_PID=$!

echo ""
echo "🎉 All services started!"
echo "========================"
echo "📊 Backend API: http://localhost:5010"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait
