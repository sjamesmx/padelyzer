#!/bin/bash

# Script para ejecutar pruebas del proyecto Padelyzer

# Configurar entorno de pruebas
export ENVIRONMENT="test"
export TESTING="True"
export FIREBASE_PROJECT_ID="test-project"
export FIREBASE_PRIVATE_KEY_ID="test-key-id"
export FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n"
export FIREBASE_CLIENT_EMAIL="test@example.com"
export FIREBASE_CLIENT_ID="test-client-id"
export FIREBASE_CLIENT_CERT_URL="https://test.example.com/cert"

# Opcional: usar emulador de Firestore si está disponible
# export FIRESTORE_EMULATOR_HOST="localhost:8080"

echo "Ejecutando pruebas unitarias..."
python -m pytest tests/test_video_processor.py -v

echo "Ejecutando pruebas de error handling..."
python -m pytest tests/test_error_handling.py -v

echo "Ejecutando pruebas de servicios..."
python -m pytest tests/test_services.py -v

# Para ejecutar todas las pruebas, descomenta la siguiente línea
# python -m pytest

echo "Pruebas completadas"
