#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Función para imprimir resultados
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        echo "Error: $3"
    fi
}

# Esperar a que la API esté lista
echo "Esperando a que la API esté lista..."
until curl -s http://localhost:8000/health > /dev/null; do
    sleep 1
done
echo "API lista!"

# 1. Probar endpoint de salud
echo -e "\n1. Probando endpoint de salud..."
response=$(curl -s -w "\n%{http_code}" http://localhost:8000/health)
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
print_result $status_code "Health check" "$body"

# 2. Subir un video de prueba
echo -e "\n2. Probando subida de video..."
# Crear archivo temporal de video
temp_video=$(mktemp)
dd if=/dev/zero of=$temp_video bs=1M count=1 2>/dev/null

response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer test-token" \
    -F "file=@$temp_video" \
    -F "video_type=training" \
    -F "description=Test video" \
    http://localhost:8000/api/v1/video/upload)

status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
print_result $status_code "Video upload" "$body"

# Limpiar archivo temporal
rm $temp_video

# 3. Probar subida de archivo inválido
echo -e "\n3. Probando subida de archivo inválido..."
temp_txt=$(mktemp)
echo "not a video" > $temp_txt

response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer test-token" \
    -F "file=@$temp_txt" \
    -F "video_type=training" \
    http://localhost:8000/api/v1/video/upload)

status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
print_result $status_code "Invalid file upload" "$body"

# Limpiar archivo temporal
rm $temp_txt

# 4. Probar subida sin autenticación
echo -e "\n4. Probando subida sin autenticación..."
response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -F "file=@$temp_video" \
    -F "video_type=training" \
    http://localhost:8000/api/v1/video/upload)

status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
print_result $status_code "Unauthorized upload" "$body"

echo -e "\nPruebas completadas!" 