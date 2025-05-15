import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import video_analysis, auth, users
from routes.profile import router as profile_router
from routes.padel_iq.dashboard import router as dashboard_router
from routes.onboarding import router as onboarding_router
from routes.matchmaking import router as matchmaking_router
from app.config.firebase import initialize_firebase
from app.config.logging import setup_logging
from routes.padel_iq import router as padel_iq_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suprimir logs de TensorFlow
logging.getLogger('mediapipe').setLevel(logging.ERROR)  # Suprimir logs de MediaPipe

app = FastAPI(
    title="Padelyzer API",
    description="API para análisis de videos de pádel",
    version="1.0.0"
)

logger = setup_logging()
db = None

@app.on_event("startup")
async def startup_event():
    global db
    db = initialize_firebase()
    logger.info("Firebase inicializado correctamente")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Servidor FastAPI detenido")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(video_analysis.router, prefix="/api/v1/video", tags=["video_analysis"])
app.include_router(profile_router, prefix="/api", tags=["profile"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(onboarding_router, prefix="/api", tags=["onboarding"])
app.include_router(matchmaking_router, prefix="/api", tags=["matchmaking"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(
    padel_iq_router,
    prefix="/api/v1/padel-iq",
    tags=["Padel IQ"]
)

@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "message": "Bienvenido a la API de Padelyzer",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )