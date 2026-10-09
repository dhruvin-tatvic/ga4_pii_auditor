#!/bin/bash

# Force Python output to stream in real-time without buffering
export PYTHONUNBUFFERED=1

# Auto-activate Python virtual environment if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Clean up background processes on Ctrl+C, SIGTERM, or script exit
cleanup() {
    echo -e "\nStopping all servers..."
    kill $BACKEND_PID 2>/dev/null
    pkill -f "gunicorn.*app.main:app" 2>/dev/null
    pkill -f "next-dev" 2>/dev/null
    kill $(jobs -p) 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Clean previous build artifacts so Next.js runs cleanly from the dev server
echo "Clearing .next cache..."
rm -rf frontend/.next

# Start Flask backend with hot-reload on port 5000 in the background
echo "Starting Flask backend with hot-reload on port 5000..."
gunicorn --bind 0.0.0.0:5000 --reload --timeout 3600 --access-logfile - --error-logfile - --capture-output --log-level info app.main:app &
BACKEND_PID=$!

# Start Next.js frontend with hot-reload on port 8080 (or PORT env var) using webpack engine
PORT_NUM=${PORT:-8080}
echo "Starting Next.js frontend dev server with hot-reload on port ${PORT_NUM}..."
cd frontend
npx next dev --webpack -p "${PORT_NUM}"
