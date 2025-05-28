from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import os
from logging.handlers import RotatingFileHandler

from app.core.config import settings
from app.api.v1.router import api_router
from app.api.auth import router as auth_router
from app.api.videos import router as videos_router
from app.core.config.firebase import initialize_firebase

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Formato para los logs
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Handler para archivo con rotación
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def create_application() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.
    """
    # Inicializar Firebase
    initialize_firebase()
    
    app = FastAPI(
        title="Padelyzer API",
        description="API para análisis biomecánico de pádel",
        version="1.0.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configurar CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Incluir rutas de la API
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(auth_router)  # Incluir router de autenticación
    app.include_router(videos_router)

    # Manejadores de excepciones
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail, "error_type": "HTTP_ERROR"}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "message": "Error de validación",
                "error_type": "VALIDATION_ERROR",
                "details": exc.errors()
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Error no manejado: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )

    @app.get("/")
    async def root():
        return {
            "message": "Bienvenido a la API de Padelyzer",
            "version": "1.0.0",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }

    return app

app = create_application() 