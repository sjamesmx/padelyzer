import requests
import os
import tempfile
import pytest
from fastapi import HTTPException
from app.services.video_service import upload_video, get_video_blueprint, validate_video_file, get_storage_client
from app.services.firebase import get_firebase_client, initialize_firebase
import logging
from app.core.config import settings

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
        
        # Verificar campos adicionales
        assert 'status' in result
        assert 'upload_date' in result
        assert result['status'] == 'pending'
        
        # Generar blueprint
        blueprint = get_video_blueprint(result['url'])
        logger.info(f"Blueprint generado: {blueprint}")
        
        # Limpiar archivo temporal
        os.unlink(video_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Error en la prueba: {str(e)}")
        raise

def test_validate_video_file():
    """Prueba la validación de archivos de vídeo."""
    # Crear un archivo de vídeo válido
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        temp_file.write(b'fake video content')
        valid_path = temp_file.name

    # Crear un archivo de texto inválido
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b'not a video')
        invalid_path = temp_file.name

    try:
        # Probar archivo válido
        is_valid, error = validate_video_file(valid_path)
        assert is_valid
        assert error == ""
        
        # Probar archivo inválido
        is_valid, error = validate_video_file(invalid_path)
        assert not is_valid
        assert "debe ser un video" in error.lower()
        
        # Probar archivo inexistente
        is_valid, error = validate_video_file('nonexistent.mp4')
        assert not is_valid
        assert "no existe" in error.lower()
        
        # Probar archivo demasiado grande
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'0' * (settings.MAX_VIDEO_SIZE_MB * 1024 * 1024 + 1))
            large_path = temp_file.name
            
        is_valid, error = validate_video_file(large_path)
        assert not is_valid
        assert "excede el tamaño máximo" in error.lower()
            
    finally:
        # Limpiar archivos temporales
        os.unlink(valid_path)
        os.unlink(invalid_path)
        if 'large_path' in locals():
            os.unlink(large_path)

def test_video_upload_integration():
    """Prueba la integración completa del proceso de carga de vídeo."""
    try:
        # Inicializar Firebase
        initialize_firebase()
        
        # Crear archivo de vídeo de prueba
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'fake video content')
            video_path = temp_file.name
            
        # ID de usuario de prueba
        test_user_id = "test_user_123"
        
        # Subir el vídeo
        result = upload_video(
            file_path=video_path,
            user_id=test_user_id,
            original_filename="test.mp4"
        )
        
        # Verificar resultado
        assert 'url' in result
        assert 'storage_path' in result
        assert 'status' in result
        assert 'upload_date' in result
        assert result['url'].startswith('https://firebasestorage.googleapis.com')
        assert result['storage_path'].startswith(f'videos/{test_user_id}/')
        assert result['status'] == 'pending'
        
        # Verificar que el vídeo existe en Firebase
        bucket = get_storage_client()
        blob = bucket.blob(result['storage_path'])
        assert blob.exists()
        
        # Verificar metadatos
        assert blob.metadata['uploaded_by'] == test_user_id
        assert blob.metadata['status'] == 'pending'
        assert 'file_size' in blob.metadata
        
        # Limpiar
        os.unlink(video_path)
        
    except Exception as e:
        logger.error(f"Error en la prueba de integración: {str(e)}")
        raise

def test_video_upload_error_handling():
    """Prueba el manejo de errores en la carga de vídeo."""
    # Probar con archivo inexistente
    with pytest.raises(HTTPException) as exc_info:
        upload_video(
            file_path='nonexistent.mp4',
            user_id='test_user_123',
            original_filename='test.mp4'
        )
    assert exc_info.value.status_code == 400
    assert "no existe" in str(exc_info.value.detail).lower()
    
    # Probar con archivo inválido
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b'not a video')
        invalid_path = temp_file.name
        
    try:
        with pytest.raises(HTTPException) as exc_info:
            upload_video(
                file_path=invalid_path,
                user_id='test_user_123',
                original_filename='test.txt'
            )
        assert exc_info.value.status_code == 400
        assert "debe ser un video" in str(exc_info.value.detail).lower()
    finally:
        os.unlink(invalid_path)

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar pruebas
    test_video_upload()
    test_validate_video_file()
    test_video_upload_integration()
    test_video_upload_error_handling() 