#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Verificando configuración de Padelyzer...${NC}\n"

# 1. Verificar proyecto de Google Cloud
echo -e "${YELLOW}Verificando proyecto de Google Cloud...${NC}"
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No hay proyecto configurado${NC}"
    exit 1
fi
echo -e "${GREEN}Proyecto: $PROJECT_ID${NC}"

# 2. Verificar APIs habilitadas
echo -e "${YELLOW}Verificando APIs habilitadas...${NC}"
APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "firestore.googleapis.com"
    "storage.googleapis.com"
    "redis.googleapis.com"
)

for api in "${APIS[@]}"; do
    if gcloud services list --enabled | grep -q "$api"; then
        echo -e "${GREEN}✓ $api está habilitada${NC}"
    else
        echo -e "${RED}✗ $api no está habilitada${NC}"
    fi
done

# 3. Verificar Redis
echo -e "${YELLOW}Verificando instancia de Redis...${NC}"
if gcloud redis instances describe padelyzer-redis --region=us-central1 &> /dev/null; then
    echo -e "${GREEN}✓ Instancia de Redis creada${NC}"
    REDIS_HOST=$(gcloud redis instances describe padelyzer-redis --region=us-central1 --format='value(host)')
    echo -e "${GREEN}  Host: $REDIS_HOST${NC}"
else
    echo -e "${RED}✗ Instancia de Redis no encontrada${NC}"
fi

# 4. Verificar Cloud Run
echo -e "${YELLOW}Verificando servicio de Cloud Run...${NC}"
if gcloud run services describe padelyzer-backend --region=us-central1 &> /dev/null; then
    echo -e "${GREEN}✓ Servicio de Cloud Run desplegado${NC}"
    URL=$(gcloud run services describe padelyzer-backend --region=us-central1 --format='value(status.url)')
    echo -e "${GREEN}  URL: $URL${NC}"
else
    echo -e "${RED}✗ Servicio de Cloud Run no encontrado${NC}"
fi

# 5. Verificar Firebase
echo -e "${YELLOW}Verificando configuración de Firebase...${NC}"
if firebase projects:list | grep -q "$PROJECT_ID"; then
    echo -e "${GREEN}✓ Proyecto de Firebase configurado${NC}"
else
    echo -e "${RED}✗ Proyecto de Firebase no encontrado${NC}"
fi

# 6. Verificar variables de entorno
echo -e "${YELLOW}Verificando variables de entorno...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}✓ Archivo .env encontrado${NC}"
    REQUIRED_VARS=(
        "GOOGLE_CLOUD_PROJECT"
        "REDIS_URL"
        "CELERY_BROKER_URL"
        "STORAGE_BUCKET"
        "JWT_SECRET_KEY"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^$var=" .env; then
            echo -e "${GREEN}  ✓ $var está configurada${NC}"
        else
            echo -e "${RED}  ✗ $var no está configurada${NC}"
        fi
    done
else
    echo -e "${RED}✗ Archivo .env no encontrado${NC}"
fi

# 7. Verificar credenciales
echo -e "${YELLOW}Verificando credenciales...${NC}"
if [ -f "firebase-credentials.json" ]; then
    echo -e "${GREEN}✓ Credenciales de Firebase encontradas${NC}"
else
    echo -e "${RED}✗ Credenciales de Firebase no encontradas${NC}"
fi

echo -e "\n${YELLOW}Resumen de la configuración:${NC}"
echo -e "1. Proyecto de Google Cloud: ${GREEN}$PROJECT_ID${NC}"
echo -e "2. Redis: ${GREEN}$REDIS_HOST${NC}"
echo -e "3. Cloud Run URL: ${GREEN}$URL${NC}"
echo -e "4. Firebase: ${GREEN}Configurado${NC}"
echo -e "5. Variables de entorno: ${GREEN}Configuradas${NC}" 