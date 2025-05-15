#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Iniciando despliegue completo de Padelyzer...${NC}\n"

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: No se encuentra el Dockerfile${NC}"
    exit 1
fi

# 2. Verificar que gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud no está instalado${NC}"
    echo -e "${YELLOW}Por favor, instala Google Cloud SDK:${NC}"
    echo -e "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 3. Verificar que estamos autenticados
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}Iniciando sesión en Google Cloud...${NC}"
    gcloud auth login
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error al iniciar sesión en Google Cloud${NC}"
        exit 1
    fi
fi

# 4. Verificar que tenemos un proyecto seleccionado
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No hay proyecto seleccionado${NC}"
    echo -e "${YELLOW}Por favor, selecciona un proyecto:${NC}"
    gcloud projects list
    echo -e "\nEjecuta: gcloud config set project [PROJECT_ID]"
    exit 1
fi
echo -e "${GREEN}Proyecto: $PROJECT_ID${NC}"

# 5. Habilitar APIs necesarias
echo -e "${YELLOW}Habilitando APIs necesarias...${NC}"
APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "firestore.googleapis.com"
    "storage.googleapis.com"
    "redis.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo -e "${YELLOW}Habilitando $api...${NC}"
    gcloud services enable $api
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error al habilitar $api${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ APIs habilitadas${NC}"

# 6. Crear instancia de Redis
echo -e "${YELLOW}Verificando instancia de Redis...${NC}"
if ! gcloud redis instances describe padelyzer-redis --region=us-central1 &> /dev/null; then
    echo -e "${YELLOW}Creando instancia de Redis...${NC}"
    gcloud redis instances create padelyzer-redis \
        --size=1 \
        --region=us-central1 \
        --redis-version=redis_6_x
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error al crear instancia de Redis${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Instancia de Redis creada${NC}"
else
    echo -e "${GREEN}✓ Instancia de Redis ya existe${NC}"
fi

# 7. Configurar Firebase
echo -e "${YELLOW}Configurando Firebase...${NC}"
./scripts/setup_firebase.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al configurar Firebase${NC}"
    exit 1
fi

# 8. Desplegar en Cloud Run
echo -e "${YELLOW}Desplegando en Cloud Run...${NC}"
./scripts/deploy_cloud_run.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al desplegar en Cloud Run${NC}"
    exit 1
fi

# 9. Verificar el despliegue
echo -e "${YELLOW}Verificando el despliegue...${NC}"
./scripts/verify_cloud_setup.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al verificar el despliegue${NC}"
    exit 1
fi

echo -e "\n${GREEN}¡Despliegue completado con éxito!${NC}"
echo -e "\n${YELLOW}Resumen del despliegue:${NC}"
echo -e "1. Proyecto: ${GREEN}$PROJECT_ID${NC}"
echo -e "2. APIs: ${GREEN}Habilitadas${NC}"
echo -e "3. Redis: ${GREEN}Configurado${NC}"
echo -e "4. Firebase: ${GREEN}Configurado${NC}"
echo -e "5. Cloud Run: ${GREEN}Desplegado${NC}"
echo -e "\n${YELLOW}Próximos pasos:${NC}"
echo -e "1. Verifica que puedes acceder a la aplicación en la URL proporcionada"
echo -e "2. Configura el dominio personalizado si es necesario"
echo -e "3. Configura las alertas de monitoreo"
echo -e "4. Realiza pruebas de carga" 