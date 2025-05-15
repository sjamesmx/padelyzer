#!/bin/bash
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "[CHECK_ENV] Verificando configuración del entorno..."
if [ "$ENVIRONMENT" == "production" ]; then
    if [ -z "$FIREBASE_CRED_PATH" ] || [ ! -f "$FIREBASE_CRED_PATH" ]; then
        echo "[CHECK_ENV] Error: Archivo de credenciales Firebase no encontrado en $FIREBASE_CRED_PATH"
        exit 1
    fi
    echo "[CHECK_ENV] Entorno de producción: credenciales encontradas."
else
    echo "[CHECK_ENV] Entorno de desarrollo: usando emulador de Firestore."
fi

echo "[CHECK_ENV] Entorno configurado correctamente." 