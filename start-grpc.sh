#!/bin/bash

echo "🚀 Starting gRPC Trading Signals System..."

# Generate Go gRPC code
echo "📋 Generating gRPC code..."
cd go-trading-service
./scripts/generate_grpc.sh
cd ..

# Copy nginx config
cp nginx.grpc.conf nginx.conf

# Start services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.grpc.yml up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 30

# Check health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.grpc.yml ps

echo "✅ gRPC Trading Signals System is ready!"
echo "📊 API: http://localhost:8080"
echo "🔗 gRPC: localhost:50051"
echo "📈 Health: http://localhost/health"
