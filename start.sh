#!/usr/bin/env bash
# One-command launcher (macOS/Linux): sets everything up on first run, then serves API + UI on http://localhost:8000
set -e
cd "$(dirname "$0")"

if [ ! -x backend/.venv/bin/python ]; then
  echo "[1/3] Creating the Python environment..."
  python3 -m venv backend/.venv
  backend/.venv/bin/python -m pip install -r backend/requirements.txt
fi
if [ ! -d frontend/node_modules ]; then
  echo "[2/3] Installing frontend packages..."
  (cd frontend && npm install)
fi
if [ ! -f frontend/dist/index.html ]; then
  echo "[3/3] Building the web UI..."
  (cd frontend && npm run build)
fi

echo "Compiler Pipeline Visualizer -> http://localhost:8000  (Ctrl+C to stop)"
exec backend/.venv/bin/python -m uvicorn --app-dir backend app.main:app --port 8000
