#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Configurando Padelyzer en Google Cloud Run...${NC}\n"

# 1. Verificar que gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud no está instalado. Por favor instala Google Cloud SDK.${NC}"
    exit 1
fi

# 2. Inicializar proyecto
echo -e "${YELLOW}Inicializando proyecto de Google Cloud...${NC}"
gcloud init

# 3. Habilitar APIs necesarias
echo -e "${YELLOW}Habilitando APIs necesarias...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    firestore.googleapis.com \
    storage.googleapis.com \
    redis.googleapis.com

# 4. Crear Redis instance
echo -e "${YELLOW}Creando instancia de Redis...${NC}"
gcloud redis instances create padelyzer-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x

# 5. Obtener Redis host y puerto
REDIS_HOST=$(gcloud redis instances describe padelyzer-redis --region=us-central1 --format='value(host)')
REDIS_PORT=$(gcloud redis instances describe padelyzer-redis --region=us-central1 --format='value(port)')

# 6. Configurar variables de entorno
echo -e "${YELLOW}Configurando variables de entorno...${NC}"
cat > .env << EOL
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
GOOGLE_APPLICATION_CREDENTIALS=firebase-credentials.json

# Redis Configuration
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}
REDIS_PASSWORD=

# Celery Configuration
CELERY_BROKER_URL=redis://${REDIS_HOST}:${REDIS_PORT}
CELERY_RESULT_BACKEND=redis://${REDIS_HOST}:${REDIS_PORT}
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
API_WORKERS=4
API_RELOAD=false

# Storage Configuration
STORAGE_BUCKET=padelyzer-videos
STORAGE_PREFIX=test/

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp
ENABLE_METRICS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOL

# 7. Configurar Cloud Run
echo -e "${YELLOW}Configurando Cloud Run...${NC}"
gcloud run deploy padelyzer-backend \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars-file .env

# 8. Configurar Firebase
echo -e "${YELLOW}Configurando Firebase...${NC}"
if ! command -v firebase &> /dev/null; then
    echo -e "${YELLOW}Instalando Firebase CLI...${NC}"
    npm install -g firebase-tools
fi

firebase login
firebase init

# 9. Desplegar reglas de Firebase
echo -e "${YELLOW}Desplegando reglas de Firebase...${NC}"
firebase deploy --only firestore:rules,storage:rules

echo -e "${GREEN}¡Configuración completada!${NC}"
echo -e "URL de la aplicación: $(gcloud run services describe padelyzer-backend --region us-central1 --format='value(status.url)')" 