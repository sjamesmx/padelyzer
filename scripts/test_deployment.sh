#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuración
API_URL="https://YOUR_CLOUD_RUN_URL"
TEST_USER_ID="test_user_123"
BUCKET_URL="https://storage.googleapis.com/YOUR_BUCKET"

# Función para imprimir mensajes
print_status() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para hacer requests a la API
make_request() {
    local endpoint=$1
    local data=$2
    local expected_status=$3

    response=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}${endpoint}" \
        -H "Content-Type: application/json" \
        -d "${data}")

    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" -eq "$expected_status" ]; then
        print_success "Request to ${endpoint} successful"
        echo "$body" | jq '.'
        return 0
    else
        print_error "Request to ${endpoint} failed with status ${status_code}"
        echo "$body" | jq '.'
        return 1
    fi
}

# Test 1: Video válido
print_status "Testing valid video upload..."
valid_video_data='{
    "user_id": "'${TEST_USER_ID}'",
    "video_url": "'${BUCKET_URL}'/test_valid.mp4",
    "tipo_video": "entrenamiento",
    "player_position": {"side": "right", "zone": "forward"}
}'
make_request "/api/calculate_padel_iq" "$valid_video_data" 200

# Test 2: Video con resolución baja
print_status "Testing low resolution video..."
low_res_data='{
    "user_id": "'${TEST_USER_ID}'",
    "video_url": "'${BUCKET_URL}'/test_low_res.mp4",
    "tipo_video": "entrenamiento",
    "player_position": {"side": "right", "zone": "forward"}
}'
make_request "/api/calculate_padel_iq" "$low_res_data" 400

# Test 3: Video con formato no soportado
print_status "Testing unsupported format..."
unsupported_format_data='{
    "user_id": "'${TEST_USER_ID}'",
    "video_url": "'${BUCKET_URL}'/test.avi",
    "tipo_video": "entrenamiento",
    "player_position": {"side": "right", "zone": "forward"}
}'
make_request "/api/calculate_padel_iq" "$unsupported_format_data" 400

# Test 4: Video borroso
print_status "Testing blurry video..."
blurry_video_data='{
    "user_id": "'${TEST_USER_ID}'",
    "video_url": "'${BUCKET_URL}'/test_blurry.mp4",
    "tipo_video": "entrenamiento",
    "player_position": {"side": "right", "zone": "forward"}
}'
make_request "/api/calculate_padel_iq" "$blurry_video_data" 200

# Test 5: Procesamiento por lotes
print_status "Testing batch processing..."
for i in {1..5}; do
    batch_data='{
        "user_id": "'${TEST_USER_ID}'",
        "video_url": "'${BUCKET_URL}'/test_batch_'${i}'.mp4",
        "tipo_video": "entrenamiento",
        "player_position": {"side": "right", "zone": "forward"}
    }'
    make_request "/api/calculate_padel_iq" "$batch_data" 200 &
done
wait

# Test 6: Caché
print_status "Testing cache..."
make_request "/api/calculate_padel_iq" "$valid_video_data" 200
print_status "Testing cache hit..."
make_request "/api/calculate_padel_iq" "$valid_video_data" 200

# Verificar logs
print_status "Checking Cloud Run logs..."
gcloud run services logs tail padelyzer --limit=50

print_status "All tests completed!" 