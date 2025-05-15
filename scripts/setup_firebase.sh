#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Configurando Firebase para Padelyzer...${NC}\n"

# 1. Verificar que Firebase CLI está instalado
if ! command -v firebase &> /dev/null; then
    echo -e "${YELLOW}Instalando Firebase CLI...${NC}"
    npm install -g firebase-tools
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error al instalar Firebase CLI${NC}"
        exit 1
    fi
fi

# 2. Verificar que estamos en el directorio correcto
if [ ! -f "firebase.json" ]; then
    echo -e "${RED}Error: No se encuentra firebase.json${NC}"
    exit 1
fi

# 3. Obtener el ID del proyecto
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No hay proyecto configurado${NC}"
    exit 1
fi
echo -e "${GREEN}Proyecto: $PROJECT_ID${NC}"

# 4. Iniciar sesión en Firebase
echo -e "${YELLOW}Iniciando sesión en Firebase...${NC}"
firebase login
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al iniciar sesión en Firebase${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Sesión iniciada${NC}"

# 5. Inicializar Firebase en el proyecto
echo -e "${YELLOW}Inicializando Firebase...${NC}"
firebase use $PROJECT_ID
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al seleccionar el proyecto${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Proyecto seleccionado${NC}"

# 6. Desplegar reglas de Firestore
echo -e "${YELLOW}Desplegando reglas de Firestore...${NC}"
firebase deploy --only firestore:rules
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al desplegar reglas de Firestore${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Reglas de Firestore desplegadas${NC}"

# 7. Desplegar reglas de Storage
echo -e "${YELLOW}Desplegando reglas de Storage...${NC}"
firebase deploy --only storage
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al desplegar reglas de Storage${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Reglas de Storage desplegadas${NC}"

# 8. Crear bucket de Storage si no existe
echo -e "${YELLOW}Verificando bucket de Storage...${NC}"
if ! gsutil ls gs://$PROJECT_ID.appspot.com &> /dev/null; then
    echo -e "${YELLOW}Creando bucket de Storage...${NC}"
    gsutil mb -l us-central1 gs://$PROJECT_ID.appspot.com
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error al crear bucket de Storage${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Bucket creado${NC}"
else
    echo -e "${GREEN}✓ Bucket ya existe${NC}"
fi

# 9. Configurar CORS para el bucket
echo -e "${YELLOW}Configurando CORS para el bucket...${NC}"
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "POST", "PUT", "DELETE"],
    "responseHeader": ["Content-Type", "Access-Control-Allow-Origin"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://$PROJECT_ID.appspot.com
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al configurar CORS${NC}"
    exit 1
fi
echo -e "${GREEN}✓ CORS configurado${NC}"

# 10. Limpiar archivo temporal
rm cors.json

echo -e "\n${YELLOW}Resumen de la configuración de Firebase:${NC}"
echo -e "1. Proyecto: ${GREEN}$PROJECT_ID${NC}"
echo -e "2. Firestore: ${GREEN}Configurado${NC}"
echo -e "3. Storage: ${GREEN}Configurado${NC}"
echo -e "4. Bucket: ${GREEN}gs://$PROJECT_ID.appspot.com${NC}"
echo -e "5. CORS: ${GREEN}Configurado${NC}" 