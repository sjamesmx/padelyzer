"""
Pruebas del flujo completo de Padelyzer.
"""
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.init_test_data import (
    create_test_users,
    create_test_videos,
    clear_test_data,
    create_test_strokes,
    create_test_padel_iq_history,
    create_test_video_analisis,
    initialize_firestore
)
import requests
import time
import json
from datetime import datetime

client = TestClient(app)

BASE_URL = "http://localhost:8000/api/v1"
TEST_VIDEO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_video.mp4")

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Fixture para limpiar datos antes y después de cada prueba."""
    clear_test_data()
    yield
    clear_test_data()

@pytest.fixture
def plan_id():
    return "basic_plan"

@pytest.fixture
def create_test_video():
    return ("test.mp4", b"fake content", "video/mp4")

def test_upload_and_analyze_training_video():
    """Prueba el flujo completo de subida y análisis de video de entrenamiento."""
    # Crear usuario y video de prueba
    user_id = create_test_users(1)[0]
    videos = create_test_videos()
    training_video_path = videos['entrenamiento']

    # Subir video
    with open(training_video_path, 'rb') as video_file:
        response = client.post(
            '/api/v1/video/upload',
            files={'video': video_file},
            data={'user_id': user_id, 'tipo_video': 'entrenamiento'}
        )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_upload_and_analyze_match_video():
    """Prueba el flujo completo de subida y análisis de video de partido."""
    user_id = create_test_users(1)[0]
    videos = create_test_videos()
    match_video_path = videos['partido']

    # Subir video
    with open(match_video_path, 'rb') as video_file:
        response = client.post(
            '/api/v1/video/upload',
            files={'video': video_file},
            data={
                'user_id': user_id,
                'tipo_video': 'partido',
                'player_position_side': 'left',
                'player_position_zone': 'back'
            }
        )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_error_cases():
    """Prueba casos de error en el procesamiento de videos."""
    user_id = create_test_users(1)[0]

    # Caso 1: Resolución insuficiente
    low_res_video = create_test_video(
        filename='low_res.mp4',
        resolution=(640, 480)
    )
    with open(low_res_video, 'rb') as video_file:
        response = client.post(
            '/process_training_video',
            files={'video': video_file},
            data={'user_id': user_id, 'tipo_video': 'entrenamiento'}
        )
    assert response.status_code == 400
    assert 'resolución' in response.json().get('error', '').lower()

    # Caso 2: Video de partido como entrenamiento
    videos = create_test_videos()
    with open(videos['partido'], 'rb') as video_file:
        response = client.post(
            '/process_training_video',
            files={'video': video_file},
            data={'user_id': user_id, 'tipo_video': 'entrenamiento'}
        )
    assert response.status_code == 400
    assert 'múltiples jugadores' in response.json().get('error', '').lower()

    # Caso 3: Posición de jugador inválida
    with open(videos['partido'], 'rb') as video_file:
        response = client.post(
            '/process_training_video',
            files={'video': video_file},
            data={
                'user_id': user_id,
                'tipo_video': 'partido',
                'player_position': {'side': 'invalid', 'zone': 'invalid'}
            }
        )
    assert response.status_code == 400
    assert 'posición' in response.json().get('error', '').lower()

def test_firestore_integration():
    """Prueba la integración con Firestore."""
    user_id = create_test_users(1)[0]
    
    # Crear datos de prueba
    create_test_strokes(user_id)
    create_test_padel_iq_history(user_id)
    video_id = create_test_video_analisis(user_id)

    # Verificar datos en Firestore
    response = client.get(f'/api/get_profile?user_id={user_id}')
    assert response.status_code == 200
    profile = response.json()
    
    assert profile['ultimo_analisis'] == video_id
    assert profile['tipo_ultimo_analisis'] == 'entrenamiento'
    assert profile['fecha_ultimo_analisis'] is not None

def test_preview_generation():
    """Prueba la generación de previsualizaciones."""
    user_id = create_test_users(1)[0]
    video_id = create_test_video_analisis(user_id)

    # Verificar previsualizaciones
    response = client.get(f'/api/v1/video/analysis/{video_id}')
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_signup_and_login():
    """Prueba el flujo de registro y login."""
    # Registro exitoso
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@padelyzer.com",
            "password": "password123",
            "name": "Test User",
            "nivel": "principiante",
            "posicion_preferida": "drive"
        }
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Registro fallido (email duplicado)
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@padelyzer.com",
            "password": "password123",
            "name": "Test User"
        }
    )
    assert response.status_code == 400
    assert "email ya registrado" in response.json().get("detail").lower()

    # Login exitoso
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@padelyzer.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Login fallido
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@padelyzer.com", "password": "wrong"}
    )
    assert response.status_code == 401
    assert "credenciales inválidas" in response.json().get("detail").lower()

def test_subscriptions():
    """Prueba el flujo de suscripciones."""
    user_id = create_test_users(1)[0]
    
    # Crear suscripción (mock Stripe)
    response = client.post(
        "/api/v1/subscriptions/create",
        json={
            "user_id": user_id,
            "plan": "Social",
            "payment_method": "pm_test_123"
        },
        headers={"Authorization": f"Bearer mock_token"}
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Listar suscripciones
    response = client.get(
        f"/api/subscriptions?user_id={user_id}",
        headers={"Authorization": f"Bearer mock_token"}
    )
    assert response.status_code == 200
    subscriptions = response.json()
    assert len(subscriptions) > 0
    assert subscriptions[0]["plan"] == "Social"

    # Cancelar suscripción
    response = client.post(
        f"/api/subscriptions/{subscriptions[0]['subscription_id']}/cancel",
        headers={"Authorization": f"Bearer mock_token"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

def test_search_players():
    """Prueba la búsqueda de jugadores."""
    # Crear usuarios con diferentes Padel IQ y ubicaciones
    users = create_test_users(3)
    db = initialize_firestore()
    
    # Actualizar ubicaciones de usuarios
    locations = [
        {"city": "Puebla", "lat": 19.043, "lon": -98.198},
        {"city": "Puebla", "lat": 19.044, "lon": -98.199},
        {"city": "Puebla", "lat": 19.045, "lon": -98.200}
    ]
    
    for i, user_id in enumerate(users):
        db.collection("users").document(user_id).update({
            "location": locations[i],
            "padel_iq": 50 + i * 10
        })

    # Buscar jugadores
    response = client.post(
        "/api/v1/search/players",
        json={
            "location": {"lat": 19.043, "lon": -98.198},
            "max_distance_km": 10,
            "padel_iq_range": [40, 60]
        }
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_onboarding():
    """Prueba el flujo de onboarding."""
    user_id = create_test_users(1)[0]
    
    # Completar onboarding
    response = client.post(
        "/api/v1/onboarding",
        json={
            "user_id": user_id,
            "location": {
                "city": "Puebla",
                "lat": 19.043,
                "lon": -98.198
            },
            "preferences": {
                "force_level": "Quinta Fuerza",
                "availability": ["Lunes", "Miércoles", "Viernes"],
                "preferred_time": "18:00-20:00"
            }
        }
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_user_profile_updates():
    """Prueba actualizaciones del perfil de usuario."""
    user_id = create_test_users(1)[0]
    
    # Actualizar perfil
    response = client.put(
        f"/api/v1/users/{user_id}/profile",
        json={
            "nivel": "intermedio",
            "posicion_preferida": "revés",
            "biografia": "Jugador de pádel desde 2020"
        }
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"
    # Verificar actualización
    response = client.get(f"/api/v1/users/{user_id}/profile", params={"level": "intermediate"})
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_friends_flow():
    """Prueba el flujo completo de amistades."""
    user_ids = create_test_users(2)
    user1, user2 = user_ids

    # Enviar solicitud
    response = client.post(
        "/api/v1/friends/request",
        json={"friend_id": user2},
        headers={"Authorization": f"Bearer mock_token"}
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Aceptar solicitud
    response = client.post(
        "/api/v1/friends/accept",
        json={"proposer_id": user1, "receiver_id": user2},
        headers={"Authorization": f"Bearer mock_token"}
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Listar amistades
    response = client.get(f"/api/v1/friends/{user1}")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Eliminar amistad
    response = client.delete(f"/api/v1/friends/123")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_social_wall_flow():
    """Prueba el flujo completo del muro social."""
    user_id = create_test_users(1)[0]

    # Crear post
    response = client.get(
        "/api/v1/social_wall",
        params={"page": 1, "limit": 10},
        headers={"Authorization": f"Bearer mock_token"}
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_gamification_flow():
    """Prueba el flujo completo de gamificación."""
    user_id = create_test_users(1)[0]

    # Obtener estado inicial
    response = client.get(f"/api/v1/gamification/{user_id}")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Añadir puntos
    response = client.post(
        f"/api/v1/gamification/{user_id}/add_points",
        json={
            "points": 1500,
            "reason": "Test points"
        }
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Verificar logros
    response = client.get(f"/api/v1/gamification/{user_id}/achievements")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_subscriptions_flow(plan_id):
    """Prueba el flujo completo de suscripciones."""
    user_id = create_test_users(1)[0]

    # Obtener planes disponibles
    response = client.get("/api/v1/subscriptions/plans")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Crear suscripción
    response = client.post(
        f"/api/v1/subscriptions/{user_id}/subscribe",
        json={
            "plan_id": plan_id,
            "payment_method": "credit_card",
            "auto_renew": True
        }
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Obtener suscripciones activas
    response = client.get(f"/api/v1/subscriptions/{user_id}")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Cancelar suscripción
    response = client.post(f"/api/v1/subscriptions/123/cancel")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_get_analysis():
    """Prueba la obtención de análisis de video."""
    user_id = create_test_users(1)[0]
    video_id = create_test_video_analisis(user_id)

    response = client.get(f"/api/v1/video/analysis/{video_id}")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def test_matchmaking_flow():
    """Prueba el flujo completo de matchmaking."""
    user_id = create_test_users(1)[0]

    # Buscar partido
    response = client.post(
        "/api/v1/matchmaking/find_match",
        json={"level": "intermediate", "position": "left"}
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Obtener partidos disponibles
    response = client.get("/api/v1/matchmaking/matches")
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

    # Crear partido
    response = client.post(
        "/api/v1/matchmaking/create_match",
        json={
            "creator_id": user_id,
            "date": "2024-03-20T10:00:00Z",
            "location": "Test Court",
            "max_players": 4,
            "min_padel_iq": 40,
            "max_padel_iq": 60
        }
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not Implemented"

def generate_test_email():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"test{timestamp}@example.com"

def test_complete_flow():
    # Generate test email
    test_email = generate_test_email()
    test_password = "password123"
    test_name = f"Test User {datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 1. Register user
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": test_name
        }
    )
    assert register_response.status_code == 200
    register_data = register_response.json()
    assert "message" in register_data
    assert register_data["message"] == "User created successfully"
    
    # Get user ID from response
    user_id = register_data.get("user_id")
    assert user_id is not None
    
    # 2. Verify email (development mode)
    verify_response = requests.post(
        f"{BASE_URL}/auth/verify-email",
        json={"token": user_id}
    )
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["message"] == "Email verified successfully"
    
    # 3. Login and get JWT token
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    token = login_data["access_token"]
    
    # 4. Upload video
    with open(TEST_VIDEO_PATH, "rb") as video_file:
        upload_response = requests.post(
            f"{BASE_URL}/videos/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": video_file}
        )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert "video_url" in upload_data
    video_url = upload_data["video_url"]
    
    # 5. Start video analysis
    analysis_response = requests.post(
        f"{BASE_URL}/videos/training",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "url": video_url,
            "title": "Test Video",
            "description": "Video de prueba",
            "type": "training"
        }
    )
    assert analysis_response.status_code == 200
    analysis_data = analysis_response.json()
    assert "analysis_id" in analysis_data
    analysis_id = analysis_data["analysis_id"]
    
    # 6. Check analysis status until completed
    max_attempts = 30  # 5 minutes maximum (10 seconds * 30)
    attempt = 0
    while attempt < max_attempts:
        status_response = requests.get(
            f"{BASE_URL}/videos/analysis/{analysis_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        if status_data["status"] == "completed":
            assert "padel_iq" in status_data
            assert isinstance(status_data["padel_iq"], (int, float))
            break
            
        time.sleep(10)  # Wait 10 seconds between checks
        attempt += 1
    
    assert attempt < max_attempts, "Analysis did not complete within the expected time" 