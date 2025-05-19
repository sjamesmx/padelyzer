import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from app.core.middleware import error_handling_middleware
from app.core.exceptions import AppException, PadelException
from unittest.mock import patch

# Mock Firebase initialization
def mock_firebase():
    with patch('app.config.firebase.initialize_firebase') as mock:
        mock.return_value = None
        yield mock

@pytest.fixture(scope="module")
def test_app():
    app = FastAPI()
    app.middleware("http")(error_handling_middleware)

    # Handlers globales para asegurar formato consistente
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": exc.__class__.__name__
                }
            }
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": exc.__class__.__name__
                }
            }
        )

    @app.get("/test-http-error")
    async def test_http_error():
        raise HTTPException(status_code=404, detail="Not found")

    @app.get("/test-app-error")
    async def test_app_error():
        raise AppException(
            status_code=400,
            message="Bad request",
            error_code="INVALID_INPUT"
        )

    @app.get("/test-padel-error")
    async def test_padel_error():
        raise PadelException(
            status_code=422,
            detail="Invalid input data"
        )

    @app.get("/test-unexpected-error")
    async def test_unexpected_error():
        raise ValueError("Unexpected error")

    return app

@pytest.fixture(scope="module")
def client(test_app):
    return TestClient(test_app)

def test_http_exception_handling(client):
    response = client.get("/test-http-error")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == 404
    assert data["error"]["message"] == "Not found"
    assert data["error"]["type"] == "HTTPException"

def test_app_exception_handling(client):
    response = client.get("/test-app-error")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == 400
    assert data["error"]["message"] == "Bad request"
    assert data["error"]["type"] == "AppException"

def test_padel_exception_handling(client):
    response = client.get("/test-padel-error")
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == 422
    assert data["error"]["message"] == "Invalid input data"
    assert data["error"]["type"] == "PadelException"

def test_unexpected_error_handling(client):
    response = client.get("/test-unexpected-error")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == 500
    assert data["error"]["message"] == "Error interno del servidor"
    assert data["error"]["type"] == "InternalServerError" 