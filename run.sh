#!/bin/bash
# SupportIQ Single-Command Startup Script

set -e

# Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting SupportIQ AI System..."

# Function to stop background processes on exit
cleanup() {
    echo "Stopping SupportIQ services..."
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT

# Start FastAPI Backend in background
echo "Starting FastAPI Backend on port ${API_PORT:-8000}..."
uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} &

# Wait briefly for FastAPI to initialize
sleep 2

# Start Streamlit Frontend
echo "Starting Streamlit UI..."
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
