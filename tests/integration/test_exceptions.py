import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.api.v1.dependencies.exceptions import PadelException, AppException
from app.api.v1.dependencies.middleware import error_handling_middleware

# Create a test app
app = FastAPI()
app.middleware("http")(error_handling_middleware)

client = TestClient(app)

def test_padel_exception():
    """Test that PadelException is properly initialized and has correct attributes."""
    message = "Test error message"
    status_code = 400
    exception = PadelException(message=message, status_code=status_code)
    
    assert str(exception) == message
    assert exception.message == message
    assert exception.status_code == status_code

def test_app_exception():
    """Test that AppException is properly initialized and has correct attributes."""
    message = "Test app error"
    status_code = 500
    exception = AppException(message=message, status_code=status_code)
    
    assert str(exception) == message
    assert exception.message == message
    assert exception.status_code == status_code

@pytest.mark.integration
def test_middleware_handles_padel_exception():
    """Test that middleware properly handles PadelException."""
    @app.get("/test-padel-exception")
    async def test_endpoint():
        raise PadelException(message="Test error", status_code=400)
    
    response = client.get("/test-padel-exception")
    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": 400,
            "message": "Test error",
            "type": "PadelException"
        }
    }

@pytest.mark.integration
def test_middleware_handles_app_exception():
    """Test that middleware properly handles AppException."""
    @app.get("/test-app-exception")
    async def test_endpoint():
        raise AppException(message="Test app error", status_code=500)
    
    response = client.get("/test-app-exception")
    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": 500,
            "message": "Test app error",
            "type": "AppException"
        }
    } 