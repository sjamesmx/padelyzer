import requests
import os
import tempfile
from app.services.video_service import upload_video, get_video_blueprint
from app.services.firebase import get_firebase_client, initialize_firebase
import logging

logger = logging.getLogger(__name__)

def download_test_video():
    """Descarga el vídeo de prueba."""
    video_url = "https://firebasestorage.googleapis.com/v0/b/pdzr-458820.firebasestorage.app/o/lety.mp4?alt=media&token=4e7c5d33-423b-4d0d-8b6f-5699d6604296"
    
    try:
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            # Descargar el vídeo
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            # Guardar el vídeo
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            
            return temp_file.name
    except Exception as e:
        logger.error(f"Error al descargar el vídeo: {str(e)}")
        raise

def test_video_upload():
    """Prueba el proceso de subida de vídeo."""
    try:
        # Inicializar Firebase
        initialize_firebase()
        logger.info("Firebase inicializado correctamente")
        
        # Descargar el vídeo
        video_path = download_test_video()
        logger.info(f"Vídeo descargado en: {video_path}")
        
        # ID de usuario de prueba
        test_user_id = "test_user_123"
        
        # Subir el vídeo
        result = upload_video(
            file_path=video_path,
            user_id=test_user_id,
            original_filename="lety.mp4"
        )
        
        logger.info(f"Vídeo subido exitosamente: {result}")
        
        # Generar blueprint
        blueprint = get_video_blueprint(result['url'])
        logger.info(f"Blueprint generado: {blueprint}")
        
        # Limpiar archivo temporal
        os.unlink(video_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Error en la prueba: {str(e)}")
        raise

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar prueba
    result = test_video_upload()
    print("Resultado de la prueba:", result) 