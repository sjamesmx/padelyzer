import pytest
from fastapi.testclient import TestClient
from app.main import app
from fastapi import HTTPException
from app.api.v1.endpoints import video_analysis

client = TestClient(app)

def test_upload_video_invalid_type(mocker):
    mocker.patch("app.core.config.settings.ALLOWED_VIDEO_TYPES", ["video/mp4"])
    file_data = {
        "file": ("test.txt", b"contenido", "text/plain")
    }
    response = client.post("/api/v1/video/upload", files=file_data)
    assert response.status_code == 400
    assert "Tipo de archivo no permitido" in response.text

def test_upload_video_not_implemented(mocker):
    mocker.patch("app.core.config.settings.ALLOWED_VIDEO_TYPES", ["video/mp4"])
    file_data = {
        "file": ("test.mp4", b"contenido", "video/mp4")
    }
    response = client.post("/api/v1/video/upload", files=file_data)
    assert response.status_code == 501
    assert "Función no implementada" in response.text

def test_get_analysis_not_implemented():
    response = client.get("/api/v1/video/analysis/test_id")
    assert response.status_code == 501
    assert "Not Implemented" in response.text

def test_process_training_video_not_implemented():
    response = client.post("/api/v1/video/process_training_video")
    assert response.status_code == 501
    assert "Not Implemented" in response.text

def test_calculate_padel_iq_not_implemented():
    response = client.post("/api/v1/video/calculate_padel_iq")
    assert response.status_code == 501
    assert "Not Implemented" in response.text

def test_upload_video_unexpected_error(mocker):
    # Forzar excepción inesperada en HTTPException
    mocker.patch("app.api.v1.endpoints.video_analysis.validate_video", side_effect=Exception("Unexpected"))
    with pytest.raises(HTTPException) as exc_info:
        video_analysis.upload_video(None)
    assert exc_info.value.status_code == 500
    assert "Error al procesar video" in str(exc_info.value.detail)

def test_get_analysis_unexpected_error(mocker):
    mocker.patch("app.api.v1.endpoints.video_analysis.get_video_analysis", side_effect=Exception("Unexpected"))
    with pytest.raises(HTTPException) as exc_info:
        video_analysis.get_analysis("test_id")
    assert exc_info.value.status_code == 500
    assert "Error al obtener análisis" in str(exc_info.value.detail)

def test_process_training_video_unexpected_error(mocker):
    mocker.patch("app.api.v1.endpoints.video_analysis.process_video", side_effect=Exception("Unexpected"))
    with pytest.raises(HTTPException) as exc_info:
        video_analysis.process_training_video(None)
    assert exc_info.value.status_code == 500
    assert "Error al procesar video" in str(exc_info.value.detail)

def test_calculate_padel_iq_unexpected_error(mocker):
    mocker.patch("app.api.v1.endpoints.video_analysis.calculate_iq", side_effect=Exception("Unexpected"))
    with pytest.raises(HTTPException) as exc_info:
        video_analysis.calculate_padel_iq(None)
    assert exc_info.value.status_code == 500
    assert "Error al calcular Padel IQ" in str(exc_info.value.detail) 