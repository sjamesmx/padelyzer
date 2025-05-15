#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Desplegando Padelyzer en Cloud Run...${NC}\n"

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: No se encuentra el Dockerfile${NC}"
    exit 1
fi

# 2. Obtener el ID del proyecto
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No hay proyecto configurado${NC}"
    exit 1
fi
echo -e "${GREEN}Proyecto: $PROJECT_ID${NC}"

# 3. Construir y subir la imagen
echo -e "${YELLOW}Construyendo y subiendo imagen...${NC}"
IMAGE_NAME="gcr.io/$PROJECT_ID/padelyzer-backend"
gcloud builds submit --tag $IMAGE_NAME

if [ $? -ne 0 ]; then
    echo -e "${RED}Error al construir y subir la imagen${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Imagen construida y subida${NC}"

# 4. Desplegar en Cloud Run
echo -e "${YELLOW}Desplegando en Cloud Run...${NC}"
gcloud run deploy padelyzer-backend \
    --image $IMAGE_NAME \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --set-env-vars="REDIS_URL=redis://padelyzer-redis:6379" \
    --set-env-vars="CELERY_BROKER_URL=redis://padelyzer-redis:6379/0" \
    --set-env-vars="STORAGE_BUCKET=$PROJECT_ID.appspot.com"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error al desplegar en Cloud Run${NC}"
    exit 1
fi

# 5. Obtener la URL del servicio
URL=$(gcloud run services describe padelyzer-backend --region=us-central1 --format='value(status.url)')
echo -e "${GREEN}✓ Servicio desplegado en: $URL${NC}"

# 6. Verificar el despliegue
echo -e "${YELLOW}Verificando el despliegue...${NC}"
curl -s $URL/health > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Servicio respondiendo correctamente${NC}"
else
    echo -e "${RED}✗ El servicio no está respondiendo${NC}"
fi

echo -e "\n${YELLOW}Resumen del despliegue:${NC}"
echo -e "1. Proyecto: ${GREEN}$PROJECT_ID${NC}"
echo -e "2. Imagen: ${GREEN}$IMAGE_NAME${NC}"
echo -e "3. URL: ${GREEN}$URL${NC}"
echo -e "4. Estado: ${GREEN}Desplegado${NC}" 