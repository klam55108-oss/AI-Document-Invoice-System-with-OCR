#!/bin/bash
# Script to restart the API server with updated code

echo "🔄 Restarting API server..."
echo ""
echo "1. Stop the current API server (Ctrl+C if running in terminal)"
echo "2. Start the API server:"
echo "   uvicorn interface.api.main:app --reload"
echo ""
echo "Or if using a process manager:"
echo "   pkill -f 'uvicorn interface.api.main'"
echo "   uvicorn interface.api.main:app --reload &"
echo ""
echo "✅ After restart, the new timeout (180 seconds) will be active"

