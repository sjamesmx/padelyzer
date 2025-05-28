#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para verificar si un comando existe
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 no está instalado${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 está instalado${NC}"
        return 0
    fi
}

# Función para verificar si un archivo existe
check_file() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}✗ $1 no encontrado${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 encontrado${NC}"
        return 0
    fi
}

# Función para verificar si una variable de entorno está definida
check_env_var() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}✗ $1 no está definida${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 está definida${NC}"
        return 0
    fi
}

echo -e "${YELLOW}Iniciando verificación del entorno...${NC}\n"

# 1. Verificar dependencias básicas
echo -e "${YELLOW}Verificando dependencias básicas...${NC}"
check_command "python3"
check_command "pip3"
check_command "redis-cli"
check_command "celery"

# 2. Verificar archivos de configuración
echo -e "\n${YELLOW}Verificando archivos de configuración...${NC}"
check_file ".env"
check_file "requirements.txt"
check_file "firebase-service-account.json"

# 3. Verificar variables de entorno críticas
echo -e "\n${YELLOW}Verificando variables de entorno críticas...${NC}"
if [ -f .env ]; then
    source .env
    REQUIRED_VARS=(
        "ENVIRONMENT"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "FIREBASE_PROJECT_ID"
        "FIREBASE_PRIVATE_KEY"
        "FIREBASE_CLIENT_EMAIL"
        "REDIS_HOST"
        "REDIS_PORT"
        "CELERY_BROKER_URL"
        "CELERY_RESULT_BACKEND"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        check_env_var "$var"
    done
fi

# 4. Verificar conexión a Redis
echo -e "\n${YELLOW}Verificando conexión a Redis...${NC}"
if redis-cli -h $REDIS_HOST -p $REDIS_PORT ping &> /dev/null; then
    echo -e "${GREEN}✓ Conexión a Redis exitosa${NC}"
else
    echo -e "${RED}✗ No se pudo conectar a Redis${NC}"
fi

# 5. Verificar entorno de Python
echo -e "\n${YELLOW}Verificando entorno de Python...${NC}"
if python3 -c "import pydantic" &> /dev/null; then
    echo -e "${GREEN}✓ Pydantic instalado${NC}"
else
    echo -e "${RED}✗ Pydantic no instalado${NC}"
fi

if python3 -c "import firebase_admin" &> /dev/null; then
    echo -e "${GREEN}✓ Firebase Admin instalado${NC}"
else
    echo -e "${RED}✗ Firebase Admin no instalado${NC}"
fi

# 6. Verificar permisos de archivos
echo -e "\n${YELLOW}Verificando permisos de archivos...${NC}"
if [ -w "uploads" ]; then
    echo -e "${GREEN}✓ Directorio uploads tiene permisos de escritura${NC}"
else
    echo -e "${RED}✗ Directorio uploads no tiene permisos de escritura${NC}"
fi

if [ -w "temp" ]; then
    echo -e "${GREEN}✓ Directorio temp tiene permisos de escritura${NC}"
else
    echo -e "${RED}✗ Directorio temp no tiene permisos de escritura${NC}"
fi

# 7. Verificar configuración de Firebase
echo -e "\n${YELLOW}Verificando configuración de Firebase...${NC}"
if [ -f "firebase-service-account.json" ]; then
    if python3 -c "import json; json.load(open('firebase-service-account.json'))" &> /dev/null; then
        echo -e "${GREEN}✓ Archivo de credenciales de Firebase es válido${NC}"
    else
        echo -e "${RED}✗ Archivo de credenciales de Firebase no es válido${NC}"
    fi
fi

# 8. Verificar versiones de dependencias
echo -e "\n${YELLOW}Verificando versiones de dependencias...${NC}"
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Versiones instaladas:${NC}"
    pip3 freeze | grep -E "fastapi|pydantic|firebase-admin|celery|redis"
fi

# 9. Verificar configuración de Celery
echo -e "\n${YELLOW}Verificando configuración de Celery...${NC}"
if celery -A app.worker status &> /dev/null; then
    echo -e "${GREEN}✓ Celery está funcionando${NC}"
else
    echo -e "${RED}✗ Celery no está funcionando${NC}"
fi

echo -e "\n${YELLOW}Verificación del entorno completada.${NC}" 