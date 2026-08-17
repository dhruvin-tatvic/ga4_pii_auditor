#!/bin/bash

# Function to handle script termination and kill only background jobs
cleanup() {
    echo -e "\nStopping development servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo "Starting Flask backend with hot-reload on port 5000..."
export FLASK_APP=app.main:app
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=5000 &

echo "Starting Next.js frontend with hot-reload..."
cd frontend
npm run dev &

# Wait for background processes to finish
wait
