import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import video_routes, auth, users
from routes.profile import router as profile_router
from routes.padel_iq.dashboard import router as dashboard_router
from routes.onboarding import router as onboarding_router
from routes.matchmaking import router as matchmaking_router
from routes.padel_iq import router as padel_iq_router
from app.api.v1.dependencies.middleware import error_handling_middleware

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logging.getLogger('mediapipe').setLevel(logging.ERROR)

logger.debug("Starting application initialization")

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="Padelyzer API",
    description="API para análisis de videos de pádel",
    version="1.0.0"
)

# Inicialización de Firebase
try:
    logger.debug("Checking FIREBASE_CREDENTIALS_PATH")
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    logger.debug(f"FIREBASE_CREDENTIALS_PATH={cred_path}")
    if not cred_path:
        logger.error("Variable FIREBASE_CREDENTIALS_PATH no configurada")
        raise ValueError("Variable FIREBASE_CREDENTIALS_PATH no configurada")
    if not os.path.exists(cred_path):
        logger.error(f"El archivo de credenciales no existe: {cred_path}")
        raise FileNotFoundError(f"El archivo de credenciales no existe: {cred_path}")
    logger.debug(f"Loading credentials from {cred_path}")
    with open(cred_path, 'r') as f:
        logger.debug(f"Reading {cred_path}: {f.read()[:100]}")
    cred = credentials.Certificate(cred_path)
    logger.debug("Initializing Firebase app")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase inicializado correctamente")
except Exception as e:
    logger.error(f"Error al inicializar Firebase: {str(e)}", exc_info=True)
    raise

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de manejo de errores
app.middleware("http")(error_handling_middleware)

# Inclusión de routers
app.include_router(video_routes.router, prefix="/api/v1/video", tags=["video_analysis"])
app.include_router(profile_router, prefix="/api", tags=["profile"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(onboarding_router, prefix="/api", tags=["onboarding"])
app.include_router(matchmaking_router, prefix="/api", tags=["matchmaking"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(padel_iq_router, prefix="/api/v1/padel-iq", tags=["Padel IQ"])

@app.get("/")
async def root():
    logger.debug("Root endpoint called")
    return {
        "message": "Bienvenido a la API de Padelyzer",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    logger.debug("Health check endpoint called")
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "firebase": "healthy",
            "ml_models": "healthy"
        }
    }
    try:
        db.collection("health_check").document("ping").get()
    except Exception as e:
        logger.error(f"Health check de Firebase falló: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["components"]["firebase"] = f"unhealthy: {str(e)}"
    return health_status

@app.get("/test-error")
async def test_error():
    logger.debug("Test error endpoint called")
    raise HTTPException(status_code=400, detail="Error de prueba")