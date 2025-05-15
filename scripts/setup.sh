#!/bin/bash
set -e

cd "$(dirname "$0")/.."

# Activar entorno virtual o crearlo si no existe
echo "[SETUP] Activando entorno virtual..."
if [ ! -d "venv" ]; then
  python3.11 -m venv venv
fi
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install certifi

# Configurar certificados SSL
export SSL_CERT_FILE=$(python -m certifi)

# Descargar modelo de MediaPipe si no existe
MODEL_PATH="venv/lib/python3.11/site-packages/mediapipe/modules/pose_landmark/pose_landmark_heavy.tflite"
if [ ! -f "$MODEL_PATH" ]; then
  echo "[SETUP] Descargando modelo pose_landmark_heavy.tflite..."
  mkdir -p "$(dirname "$MODEL_PATH")"
  curl --insecure -L -o "$MODEL_PATH" https://storage.googleapis.com/mediapipe-assets/pose_landmark_heavy.tflite
else
  echo "[SETUP] Modelo pose_landmark_heavy.tflite ya existe."
fi

echo "[SETUP] Entorno listo. Puedes arrancar el backend con:"
echo "cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload" 