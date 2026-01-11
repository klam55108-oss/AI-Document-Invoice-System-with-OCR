#!/bin/bash
# Start the API server in "Safe Mode" for batch processing
# 1. No --reload to prevent unwanted restarts
# 2. Kill any existing uvicorn processes on port 8000
# 3. Optimized workers

echo "🛑 Stopping existing uvicorn processes..."
pkill -f "uvicorn.*8000" || true
sleep 1

echo "🚀 Starting API server in Safe Mode (No reload, Port 8000)..."
# Using 1 worker for stability in low-memory environments
PORT=8000 venv/bin/uvicorn interface.api.main:app --host 0.0.0.0 --port 8000 --workers 1
