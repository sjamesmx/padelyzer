import pytest
import os
import cv2
import numpy as np
from app.core.video_optimizer import VideoOptimizer
from unittest.mock import Mock, patch
import tempfile

@pytest.fixture
def video_optimizer():
    return VideoOptimizer()

@pytest.fixture
def sample_video():
    # Crear un video de prueba
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_path = temp_file.name
    temp_file.close()

    # Crear un video simple con OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_path, fourcc, 30.0, (1280, 720))
    
    # Generar algunos frames
    for _ in range(30):  # 1 segundo de video
        frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    yield temp_path
    os.remove(temp_path)

@pytest.mark.asyncio
async def test_validate_video_quality(video_optimizer, sample_video):
    """Test de validación de calidad de video."""
    is_valid, error_msg = await video_optimizer.validate_video_quality(sample_video)
    assert is_valid
    assert error_msg == ""

@pytest.mark.asyncio
async def test_validate_video_quality_invalid_resolution(video_optimizer):
    """Test de validación con resolución inválida."""
    # Crear video con resolución baja
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_path = temp_file.name
    temp_file.close()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_path, fourcc, 30.0, (320, 240))
    
    for _ in range(30):
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()

    is_valid, error_msg = await video_optimizer.validate_video_quality(temp_path)
    assert not is_valid
    assert "Resolución insuficiente" in error_msg

    os.remove(temp_path)

@pytest.mark.asyncio
async def test_optimize_video(video_optimizer, sample_video):
    """Test de optimización de video."""
    target_resolution = (640, 480)
    optimized_path = await video_optimizer.optimize_video(sample_video, target_resolution)
    
    assert os.path.exists(optimized_path)
    
    # Verificar resolución del video optimizado
    cap = cv2.VideoCapture(optimized_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    assert (width, height) == target_resolution
    os.remove(optimized_path)

@pytest.mark.asyncio
async def test_analyze_video(video_optimizer, sample_video):
    """Test de análisis de video."""
    analysis = await video_optimizer.analyze_video(sample_video)
    
    assert "duration" in analysis
    assert "fps" in analysis
    assert "total_frames" in analysis
    assert "motion_ratio" in analysis
    assert "quality_score" in analysis
    assert "blur_score" in analysis
    assert "is_acceptable_quality" in analysis
    assert "analysis_timestamp" in analysis

@pytest.mark.asyncio
async def test_process_batch(video_optimizer):
    """Test de procesamiento por lotes."""
    # Mock de URLs de video
    video_urls = [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4"
    ]
    
    # Mock de resultados de análisis
    mock_results = {
        "https://example.com/video1.mp4": {"metrics": {"score": 85}},
        "https://example.com/video2.mp4": {"metrics": {"score": 90}}
    }
    
    with patch.object(video_optimizer, 'process_single_video') as mock_process:
        mock_process.side_effect = [
            mock_results["https://example.com/video1.mp4"],
            mock_results["https://example.com/video2.mp4"]
        ]
        
        results = await video_optimizer.process_batch(video_urls)
        
        assert len(results) == 2
        assert results == mock_results

@pytest.mark.asyncio
async def test_cache_operations(video_optimizer):
    """Test de operaciones de caché."""
    video_url = "https://example.com/test.mp4"
    video_hash = video_optimizer.get_video_hash(video_url)
    test_result = {"metrics": {"score": 85}}
    
    # Test guardar en caché
    await video_optimizer.cache_result(video_hash, test_result)
    
    # Test obtener de caché
    cached_result = await video_optimizer.get_cached_result(video_hash)
    assert cached_result == test_result

@pytest.mark.asyncio
async def test_download_video(video_optimizer):
    """Test de descarga de video."""
    # Mock de respuesta HTTP
    mock_response = Mock()
    mock_response.status = 200
    mock_response.content.iter_chunked.return_value = [b"test" * 1024 * 1024]  # 1MB de datos
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        temp_path = await video_optimizer.download_video("https://example.com/test.mp4")
        
        assert os.path.exists(temp_path)
        assert os.path.getsize(temp_path) > 0
        os.remove(temp_path)

def test_video_hash_generation(video_optimizer):
    """Test de generación de hash de video."""
    video_url = "https://example.com/test.mp4"
    hash1 = video_optimizer.get_video_hash(video_url)
    hash2 = video_optimizer.get_video_hash(video_url)
    
    # El hash debe ser consistente para la misma URL
    assert hash1 == hash2 