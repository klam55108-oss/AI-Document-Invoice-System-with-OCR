#!/bin/bash


echo ""
echo "Stopping existing uvicorn processes on port 8000..."
pkill -f 'uvicorn interface.api.main'
echo ""

echo "Starting API server in Safe Mode (No reload, Port 8000)..."
uvicorn interface.api.main:app --reload

echo ""
echo "API server started successfully!"