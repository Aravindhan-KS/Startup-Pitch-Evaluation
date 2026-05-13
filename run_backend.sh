#!/bin/bash
# Run the FastAPI backend with optional environment configuration

set -e

# Default values
BACKEND_DIR="backend"
PYTHON_CMD="${PYTHON_CMD:-python}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-true}"

# Load .env if present
if [ -f .env ]; then
    echo "Loading .env file..."
    export $(cat .env | xargs)
fi

# Check if running from repo root
if [ ! -d "$BACKEND_DIR" ]; then
    echo "Error: backend/ directory not found. Run from repo root."
    exit 1
fi

# Ensure venv is active or warn user
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: No virtual environment active. Consider activating one:"
    echo "  source .venv/bin/activate  # Linux/macOS"
    echo "  .venv\\Scripts\\Activate.ps1  # Windows PowerShell"
fi

# Install dependencies if needed
if ! $PYTHON_CMD -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r backend/requirements.txt
fi

# Display startup info
echo "Starting FastAPI backend..."
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Reload: $RELOAD"
echo "  Scoring Mode: $([ "$USE_HEURISTIC_PIPELINE" = "true" ] && echo "heuristic" || echo "neural-network")"
echo ""
echo "API Docs: http://$HOST:$PORT/docs"
echo "Health: http://$HOST:$PORT/health"
echo ""

# Start the app
cd "$BACKEND_DIR"
if [ "$RELOAD" = "true" ]; then
    $PYTHON_CMD -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
    $PYTHON_CMD -m uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
