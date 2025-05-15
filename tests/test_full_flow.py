import requests
import json
import os
from pathlib import Path
import time

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
TEST_VIDEO_PATH = "tests/test_videos/test_match.mp4"  # Asegúrate de tener un video de prueba

def test_full_flow():
    # 1. Registro de usuario
    signup_data = {
        "email": "test_user@example.com",
        "name": "Test User",
        "nivel": "intermedio",
        "posicion_preferida": "derecha",
        "password": "Test123!"
    }
    
    print("1. Registrando usuario...")
    signup_response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    assert signup_response.status_code == 200, f"Error en registro: {signup_response.text}"
    print("✅ Usuario registrado exitosamente")
    
    # 2. Inicio de sesión
    login_data = {
        "username": signup_data["email"],
        "password": signup_data["password"]
    }
    
    print("\n2. Iniciando sesión...")
    login_response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    assert login_response.status_code == 200, f"Error en login: {login_response.text}"
    tokens = login_response.json()
    access_token = tokens["access_token"]
    print("✅ Sesión iniciada exitosamente")
    
    # 3. Subir video
    print("\n3. Subiendo video...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Verificar que el video de prueba existe
    if not os.path.exists(TEST_VIDEO_PATH):
        raise FileNotFoundError(f"No se encontró el video de prueba en {TEST_VIDEO_PATH}")
    
    with open(TEST_VIDEO_PATH, "rb") as video_file:
        files = {
            "file": ("test_match.mp4", video_file, "video/mp4")
        }
        data = {
            "tipo_video": "partido",
            "descripcion": "Video de prueba para flujo completo"
        }
        
        upload_response = requests.post(
            f"{BASE_URL}/videos/upload",
            headers=headers,
            files=files,
            data=data
        )
    
    assert upload_response.status_code == 200, f"Error al subir video: {upload_response.text}"
    upload_result = upload_response.json()
    analysis_id = upload_result["analysis_id"]
    print("✅ Video subido exitosamente")
    
    # 4. Obtener Padel IQ (esperar a que el análisis esté completo)
    print("\n4. Esperando resultado del análisis...")
    max_attempts = 30  # 5 minutos máximo de espera
    attempt = 0
    
    while attempt < max_attempts:
        analysis_response = requests.get(
            f"{BASE_URL}/videos/analysis/{analysis_id}",
            headers=headers
        )
        assert analysis_response.status_code == 200, f"Error al obtener análisis: {analysis_response.text}"
        
        analysis_result = analysis_response.json()
        if analysis_result["estado"] == "completed":
            print("✅ Análisis completado exitosamente")
            print("\nResultado del Padel IQ:")
            print(json.dumps(analysis_result, indent=2))
            break
        
        print(f"Estado actual: {analysis_result['estado']} - Esperando...")
        time.sleep(10)  # Esperar 10 segundos entre intentos
        attempt += 1
    
    if attempt >= max_attempts:
        print("❌ Tiempo de espera agotado para el análisis")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_full_flow()
        if success:
            print("\n✅ Flujo completo ejecutado exitosamente")
        else:
            print("\n❌ El flujo completo no se completó correctamente")
    except Exception as e:
        print(f"\n❌ Error durante la ejecución del flujo: {str(e)}") 