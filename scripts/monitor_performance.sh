#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuración
API_URL="https://YOUR_CLOUD_RUN_URL"
LOG_FILE="performance_metrics.log"

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

# Función para medir tiempo de respuesta
measure_response_time() {
    local start_time=$(date +%s.%N)
    curl -s -o /dev/null -w "%{http_code}" -X POST "${API_URL}/api/calculate_padel_iq" \
        -H "Content-Type: application/json" \
        -d "$1"
    local end_time=$(date +%s.%N)
    local response_time=$(echo "$end_time - $start_time" | bc)
    echo "$response_time"
}

# Función para monitorear uso de recursos
monitor_resources() {
    gcloud run services describe padelyzer \
        --format="value(status.conditions[0].message)" \
        --region us-central1
}

# Función para verificar caché
check_cache() {
    local video_url=$1
    local first_response_time=$(measure_response_time "$2")
    local second_response_time=$(measure_response_time "$2")
    
    echo "First request: ${first_response_time}s"
    echo "Second request: ${second_response_time}s"
    
    if (( $(echo "$second_response_time < $first_response_time" | bc -l) )); then
        print_success "Cache hit detected!"
    else
        print_error "No cache hit detected"
    fi
}

# Función para probar procesamiento por lotes
test_batch_processing() {
    local start_time=$(date +%s.%N)
    local batch_size=5
    local success_count=0
    
    print_status "Testing batch processing with ${batch_size} videos..."
    
    for i in $(seq 1 $batch_size); do
        response=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/calculate_padel_iq" \
            -H "Content-Type: application/json" \
            -d "{
                \"user_id\": \"test_user_${i}\",
                \"video_url\": \"https://storage.googleapis.com/YOUR_BUCKET/test_${i}.mp4\",
                \"tipo_video\": \"entrenamiento\",
                \"player_position\": {\"side\": \"right\", \"zone\": \"forward\"}
            }")
        
        status_code=$(echo "$response" | tail -n1)
        if [ "$status_code" -eq 200 ]; then
            ((success_count++))
        fi
    done
    
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc)
    
    echo "Batch processing completed in ${total_time}s"
    echo "Success rate: ${success_count}/${batch_size}"
}

# Función para monitorear errores
monitor_errors() {
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=padelyzer AND severity>=ERROR" \
        --limit 10 \
        --format="value(textPayload)"
}

# Función principal
main() {
    print_status "Starting performance monitoring..."
    
    # Crear archivo de log
    echo "Performance Metrics - $(date)" > $LOG_FILE
    
    # Monitorear recursos
    print_status "Monitoring resource usage..."
    monitor_resources >> $LOG_FILE
    
    # Probar caché
    print_status "Testing cache performance..."
    check_cache "test_video.mp4" '{
        "user_id": "test_user",
        "video_url": "https://storage.googleapis.com/YOUR_BUCKET/test_video.mp4",
        "tipo_video": "entrenamiento",
        "player_position": {"side": "right", "zone": "forward"}
    }' >> $LOG_FILE
    
    # Probar procesamiento por lotes
    print_status "Testing batch processing performance..."
    test_batch_processing >> $LOG_FILE
    
    # Monitorear errores
    print_status "Monitoring errors..."
    monitor_errors >> $LOG_FILE
    
    print_status "Performance monitoring completed. Results saved to ${LOG_FILE}"
}

# Ejecutar script
main 