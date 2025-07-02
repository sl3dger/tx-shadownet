#!/bin/bash

# Production startup script for ShadowLedger

set -e

echo "🚀 Starting ShadowLedger in production mode..."

# Create necessary directories
mkdir -p logs data

# Set environment variables
export PYTHONUNBUFFERED=1
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# Start P2P node in background
echo "📡 Starting P2P node..."
python p2p.py &
P2P_PID=$!

# Wait a moment for P2P to start
sleep 2

# Start API server with gunicorn
echo "🌐 Starting API server..."
gunicorn api:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100

# Cleanup on exit
trap "echo '🛑 Shutting down...'; kill $P2P_PID 2>/dev/null || true; exit 0" SIGTERM SIGINT

wait
