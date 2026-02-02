#!/bin/bash
# One-command demo: start DB, API, dashboard, and open browser for presentation.

set -e
cd "$(dirname "$0")/.."

API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-8501}"
API_PID=""

cleanup() {
  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
    echo ""
    echo "Stopping API (PID $API_PID)..."
    kill "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if [[ -d venv ]]; then
  source venv/bin/activate
fi

echo "=== E-Invoice Demo ==="
echo ""

echo "1. Starting database..."
docker-compose up -d

echo ""
echo "2. Running migrations..."
alembic upgrade head

echo ""
echo "3. Starting API on port $API_PORT..."
python -m uvicorn interface.api.main:app --host 0.0.0.0 --port "$API_PORT" &
API_PID=$!
echo "   API PID: $API_PID"

echo ""
echo "4. Waiting for API to be ready..."
for i in {1..12}; do
  if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$API_PORT/api/v1/health" 2>/dev/null | grep -q 200; then
    echo "   API ready."
    break
  fi
  sleep 1
  [[ $i -eq 12 ]] && echo "   (API may still be starting...)"
done

echo ""
echo "5. Opening dashboard at http://127.0.0.1:$UI_PORT"
if command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:$UI_PORT"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:$UI_PORT"
else
  python -m webbrowser -n "http://127.0.0.1:$UI_PORT" 2>/dev/null || true
fi

echo ""
echo "6. Starting Streamlit dashboard (Ctrl+C to stop demo)..."
echo "   Dashboard: http://127.0.0.1:$UI_PORT"
echo "   API Docs:  http://127.0.0.1:$API_PORT/docs"
echo ""
streamlit run interface/dashboard/app.py --server.port "$UI_PORT" --server.headless true
