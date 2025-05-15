#!/bin/bash
set -e
PORT=8000
cd "$(dirname "$0")/.."

if lsof -i :$PORT; then
    echo "[STOP_SERVER] Deteniendo servidor FastAPI en puerto $PORT..."
    kill -9 $(lsof -t -i :$PORT)
else
    echo "[STOP_SERVER] No hay servidor ejecutándose en el puerto $PORT."
fi 