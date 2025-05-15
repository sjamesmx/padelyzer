import pytest
import json
import os
from pathlib import Path
from google.cloud import storage
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
import requests
import time
from typing import Dict, Any, List
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
TEST_VIDEOS_BUCKET = "padelyzer-videos"
TEST_VIDEOS_PREFIX = "test/"
API_BASE_URL = "http://localhost:8000"
TEST_DATA_PATH = "tests/data/test_videos.json"

@pytest.fixture(scope="session")
def firebase_app():
    """Inicializa Firebase una sola vez para todos los tests."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate("firebase-credentials.json")
        return firebase_admin.initialize_app(cred)

@pytest.fixture(scope="session")
def storage_client():
    """Cliente de Google Cloud Storage."""
    return storage.Client()

@pytest.fixture(scope="session")
def firestore_client(firebase_app):
    """Cliente de Firestore."""
    return firestore.client()

@pytest.fixture(scope="session")
def test_videos_data():
    """Carga los datos de prueba de los videos."""
    with open(TEST_DATA_PATH) as f:
        return json.load(f)

def test_video_analysis(firebase_app, storage_client, firestore_client, test_videos_data):
    """Test de análisis de videos reales."""
    results = []
    
    for video_data in test_videos_data['videos']:
        video_name = video_data['name']
        video_url = f"gs://{TEST_VIDEOS_BUCKET}/{TEST_VIDEOS_PREFIX}{video_name}"
        
        # 1. Enviar video para análisis
        response = requests.post(
            f"{API_BASE_URL}/api/calculate_padel_iq",
            json={
                "video_url": video_url,
                "player_position": video_data['player_position'],
                "video_type": video_data['type']
            }
        )
        assert response.status_code == 200
        task_id = response.json()['task_id']
        
        # 2. Esperar y verificar estado
        max_retries = 30  # 5 minutos máximo
        for _ in range(max_retries):
            status_response = requests.get(f"{API_BASE_URL}/api/analysis_status/{task_id}")
            if status_response.status_code == 200:
                status = status_response.json()
                if status['status'] == 'completed':
                    break
            time.sleep(10)
        else:
            pytest.fail(f"Análisis no completado para {video_name}")
        
        # 3. Verificar resultados
        result = status_response.json()
        
        # Validar golpes detectados
        detected_strokes = len(result['strokes'])
        expected_strokes = video_data['expected_strokes']
        assert abs(detected_strokes - expected_strokes) <= 1, \
            f"Video {video_name}: Diferencia en golpes detectados ({detected_strokes}) vs esperados ({expected_strokes})"
        
        # Validar tipos de golpes
        detected_types = {}
        for stroke in result['strokes']:
            detected_types[stroke['type']] = detected_types.get(stroke['type'], 0) + 1
        
        for stroke_type, count in video_data['expected_stroke_types'].items():
            detected_count = detected_types.get(stroke_type, 0)
            assert abs(detected_count - count) <= 1, \
                f"Video {video_name}: Diferencia en tipo {stroke_type} ({detected_count} vs {count})"
        
        # Validar métricas
        padel_iq = result['padel_iq']
        for metric in ['tecnica', 'fuerza', 'ritmo', 'repeticion']:
            assert 0 <= padel_iq[metric] <= 100, \
                f"Video {video_name}: Métrica {metric} fuera de rango ({padel_iq[metric]})"
        
        # Validar Padel IQ total
        assert 0 <= padel_iq['padel_iq'] <= 100, \
            f"Video {video_name}: Padel IQ total fuera de rango ({padel_iq['padel_iq']})"
        
        # 4. Verificar Firestore
        doc_ref = firestore_client.collection('analysis_results').document(task_id)
        doc = doc_ref.get()
        assert doc.exists, f"No se encontró resultado en Firestore para {video_name}"
        
        # 5. Verificar notificaciones
        notifications_ref = firestore_client.collection('notifications').where('task_id', '==', task_id)
        notifications = list(notifications_ref.get())
        assert len(notifications) > 0, f"No se encontraron notificaciones para {video_name}"
        
        # Guardar resultados para el reporte
        results.append({
            'video_name': video_name,
            'detected_strokes': detected_strokes,
            'expected_strokes': expected_strokes,
            'padel_iq': padel_iq,
            'latency': status['processing_time'],
            'status': 'success'
        })
    
    # Generar reporte
    generate_report(results, test_videos_data)

def test_no_strokes_video(firebase_app, storage_client, firestore_client):
    """Test para video sin golpes."""
    video_url = f"gs://{TEST_VIDEOS_BUCKET}/{TEST_VIDEOS_PREFIX}no_strokes.mp4"
    
    response = requests.post(
        f"{API_BASE_URL}/api/calculate_padel_iq",
        json={
            "video_url": video_url,
            "player_position": {"x": 0, "y": 0, "width": 100, "height": 200},
            "video_type": "training"
        }
    )
    assert response.status_code == 200
    task_id = response.json()['task_id']
    
    # Esperar y verificar estado
    max_retries = 30
    for _ in range(max_retries):
        status_response = requests.get(f"{API_BASE_URL}/api/analysis_status/{task_id}")
        if status_response.status_code == 200:
            status = status_response.json()
            if status['status'] == 'completed':
                break
        time.sleep(10)
    else:
        pytest.fail("Análisis no completado para video sin golpes")
    
    result = status_response.json()
    
    # Validar métricas por defecto
    assert len(result['strokes']) == 0
    assert result['padel_iq']['padel_iq'] == 0
    assert result['padel_iq']['tecnica'] == 0
    assert result['padel_iq']['fuerza'] == 0
    assert result['padel_iq']['ritmo'] == 0
    assert result['padel_iq']['repeticion'] == 0

def generate_report(results: List[Dict[str, Any]], test_videos_data: Dict[str, Any]):
    """Genera reporte de pruebas en Markdown."""
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_videos': len(results),
        'successful_analyses': sum(1 for r in results if r['status'] == 'success'),
        'average_latency': sum(r['latency'] for r in results) / len(results),
        'results': results
    }
    
    # Guardar en Firestore
    firestore_client.collection('test_reports').document(report['timestamp']).set(report)
    
    # Generar archivo Markdown
    with open('test_report.md', 'w') as f:
        f.write(f"# Reporte de Pruebas - {report['timestamp']}\n\n")
        f.write(f"## Resumen\n")
        f.write(f"- Total de videos: {report['total_videos']}\n")
        f.write(f"- Análisis exitosos: {report['successful_analyses']}\n")
        f.write(f"- Latencia promedio: {report['average_latency']:.2f} segundos\n\n")
        
        f.write("## Resultados Detallados\n")
        for result in results:
            f.write(f"\n### {result['video_name']}\n")
            f.write(f"- Golpes detectados: {result['detected_strokes']} (esperados: {result['expected_strokes']})\n")
            f.write(f"- Padel IQ: {result['padel_iq']['padel_iq']}\n")
            f.write(f"- Latencia: {result['latency']:.2f} segundos\n")
            f.write(f"- Estado: {result['status']}\n") 