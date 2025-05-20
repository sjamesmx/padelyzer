#!/bin/bash
set -ex
echo "DEBUG: Starting start.sh at $(date)" | tee -a /tmp/start.log
echo "DEBUG: PORT=$PORT" | tee -a /tmp/start.log
echo "DEBUG: FIREBASE_CREDENTIALS_PATH=${FIREBASE_CREDENTIALS_PATH:0:100}" | tee -a /tmp/start.log

# Check if PORT is set
if [ -z "$PORT" ]; then
    echo "ERROR: PORT is not set" | tee -a /tmp/start.log
    exit 1
fi

# Check if FIREBASE_CREDENTIALS_PATH is set
if [ -z "$FIREBASE_CREDENTIALS_PATH" ]; then
    echo "ERROR: FIREBASE_CREDENTIALS_PATH is empty" | tee -a /tmp/start.log
    exit 1
fi

echo "DEBUG: Writing to /tmp/firebase-credentials.json" | tee -a /tmp/start.log
echo "$FIREBASE_CREDENTIALS_PATH" > /tmp/firebase-credentials.json 2>> /tmp/start.log
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to write /tmp/firebase-credentials.json" | tee -a /tmp/start.log
    exit 1
fi

echo "DEBUG: Contents of /tmp/firebase-credentials.json:" | tee -a /tmp/start.log
head -n 10 /tmp/firebase-credentials.json >> /tmp/start.log 2>> /tmp/start.log

# Verify JSON format
if ! jq . /tmp/firebase-credentials.json >/dev/null 2>&1; then
    echo "ERROR: Invalid JSON in firebase-credentials.json" | tee -a /tmp/start.log
    exit 1
fi

export FIREBASE_CREDENTIALS_PATH=/tmp/firebase-credentials.json

# Check Python and pip versions
echo "DEBUG: Python version:" | tee -a /tmp/start.log
python3 --version 2>&1 | tee -a /tmp/start.log
echo "DEBUG: Pip version:" | tee -a /tmp/start.log
pip3 --version 2>&1 | tee -a /tmp/start.log

echo "DEBUG: Starting Uvicorn" | tee -a /tmp/start.log
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --log-level debug 2>&1 | tee -a /tmp/start.log