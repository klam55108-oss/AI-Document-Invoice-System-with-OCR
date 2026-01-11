#!/bin/bash
# Start the API server in "Safe Mode" for batch processing
# 1. No --reload to prevent unwanted restarts
# 2. Kill any existing uvicorn processes on port 8000
# 3. Optimized workers

# Default port
PORT=${API_PORT:-8000}

echo "🛑 Stopping existing uvicorn processes on port $PORT..."
pkill -f "uvicorn.*$PORT" || true
sleep 1

echo "🚀 Starting API server in Safe Mode (No reload, Port $PORT)..."
# Using 1 worker for stability in low-memory environments
venv/bin/uvicorn interface.api.main:app --host 0.0.0.0 --port $PORT --workers 1
