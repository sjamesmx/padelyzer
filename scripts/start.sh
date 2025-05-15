#!/bin/bash
set -e

# Activate virtual environment
source venv/bin/activate

# Export Firebase credentials path
export FIREBASE_CRED_PATH="$(pwd)/config/firebase-credentials.json"

# Unset any conflicting Google credentials
unset GOOGLE_APPLICATION_CREDENTIALS

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A app.worker worker --loglevel=info &

# Wait a moment for Celery to start
sleep 2

# Start FastAPI server
echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 