#!/bin/bash

# Script para configurar las variables de entorno de Firebase
# Uso: source scripts/set_firebase_env.sh

# Leer el archivo de credenciales
CRED_FILE="/Users/dev4/pdzr/backend/config/firebase-credentials.json"

if [ ! -f "$CRED_FILE" ]; then
    echo "Error: No se encuentra el archivo de credenciales en $CRED_FILE"
    exit 1
fi

# Extraer valores del archivo JSON
export FIREBASE_PRIVATE_KEY_ID=$(grep -o '"private_key_id": *"[^"]*"' "$CRED_FILE" | cut -d'"' -f4)
export FIREBASE_PRIVATE_KEY=$(grep -o '"private_key": *"[^"]*"' "$CRED_FILE" | cut -d'"' -f4)
export FIREBASE_CLIENT_EMAIL=$(grep -o '"client_email": *"[^"]*"' "$CRED_FILE" | cut -d'"' -f4)
export FIREBASE_CLIENT_ID=$(grep -o '"client_id": *"[^"]*"' "$CRED_FILE" | cut -d'"' -f4)
export FIREBASE_CLIENT_CERT_URL=$(grep -o '"client_x509_cert_url": *"[^"]*"' "$CRED_FILE" | cut -d'"' -f4)

# Verificar que todas las variables se hayan configurado
if [ -z "$FIREBASE_PRIVATE_KEY_ID" ] || [ -z "$FIREBASE_PRIVATE_KEY" ] || [ -z "$FIREBASE_CLIENT_EMAIL" ] || [ -z "$FIREBASE_CLIENT_ID" ] || [ -z "$FIREBASE_CLIENT_CERT_URL" ]; then
    echo "Error: Algunas variables de entorno no se pudieron configurar"
    exit 1
else
    echo "Variables de entorno de Firebase configuradas correctamente"
fi 