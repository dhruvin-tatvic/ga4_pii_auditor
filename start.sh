#!/bin/sh

# Start Flask backend on port 5000 in the background
echo "Starting Flask backend on port 5000..."
gunicorn --bind 0.0.0.0:5000 app.main:app &

# Start Next.js frontend on port 8080 (or PORT env var) in the foreground
echo "Starting Next.js frontend on port ${PORT:-8080}..."
cd frontend
PORT=${PORT:-8080} npm start
