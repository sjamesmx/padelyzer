#!/bin/bash
set -e
PORT=8000
cd "$(dirname "$0")/.."

# Verificar y exportar variables de entorno
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Validar entorno
./scripts/check_env.sh

# Verificar si el puerto está ocupado
if lsof -i :$PORT; then
    echo "[START_SERVER] Puerto $PORT ocupado, deteniendo proceso..."
    kill -9 $(lsof -t -i :$PORT)
fi

# Iniciar servidor
echo "[START_SERVER] Iniciando servidor FastAPI en puerto $PORT..."
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port $PORT --reload 