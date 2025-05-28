import os
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import video_routes, auth, users, health
from routes.profile import router as profile_router
from routes.padel_iq.dashboard import router as dashboard_router
from routes.onboarding import router as onboarding_router
from routes.matchmaking import router as matchmaking_router
from app.api.v1.endpoints.padel_iq import router as padel_iq_router
from app.core.middleware import error_handling_middleware
from app.core.config.firebase import initialize_firebase, get_firebase_clients
from dotenv import load_dotenv
from app.api.videos import router as videos_router
from app.services.pipeline_manager import PipelineManager
from app.services.firebase import get_firebase_client
from google.cloud import firestore

# Cargar variables de entorno según el entorno
env = os.getenv('ENV', 'development')
if env == 'development':
    load_dotenv('.env.development')
else:
    load_dotenv()

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
    initialize_firebase()
    clients = get_firebase_clients()
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

# Incluir routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(video_routes.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(profile_router, prefix="/api/v1/profile", tags=["profile"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(onboarding_router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(matchmaking_router, prefix="/api/v1/matchmaking", tags=["matchmaking"])
app.include_router(padel_iq_router, prefix="/api/v1/padel-iq", tags=["padel-iq"])
app.include_router(videos_router)

API_TASKS_KEY = os.getenv("API_TASKS_KEY")  # Opcional: clave para proteger el endpoint

@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación."""
    try:
        # Verificar conexión con Firebase
        from app.core.config.firebase import verify_firebase_connection
        if not verify_firebase_connection():
            logger.error("No se pudo establecer conexión con Firebase")
            raise Exception("Error de conexión con Firebase")
        logger.info("Conexión con Firebase verificada correctamente")
    except Exception as e:
        logger.error(f"Error en startup: {str(e)}")
        raise

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

@app.post("/tasks/analyze_video")
async def analyze_video_task(request: Request):
    data = await request.json()
    analysis_id = data.get("analysis_id")
    # Protección opcional por API key
    api_key = request.headers.get("x-api-key")
    if API_TASKS_KEY and api_key != API_TASKS_KEY:
        return {"error": "Unauthorized"}, status.HTTP_401_UNAUTHORIZED
    if not analysis_id:
        return {"error": "analysis_id requerido"}, status.HTTP_400_BAD_REQUEST
    try:
        db, _ = get_firebase_client()
        analysis_ref = db.collection('video_analyses').document(analysis_id)
        analysis_doc = analysis_ref.get()
        if not analysis_doc.exists:
            return {"error": "No se encontró el documento de análisis"}, status.HTTP_404_NOT_FOUND
        analysis_data = analysis_doc.to_dict()
        video_url = analysis_data.get('video_url')
        video_type = analysis_data.get('video_type', 'game')
        nivel = analysis_data.get('nivel', 'intermedio')
        user_id = analysis_data.get('user_id')
        pipeline = PipelineManager()
        resultado = pipeline.analyze(
            video_path=video_url,
            tipo=video_type,
            nivel=nivel,
            user_id=user_id
        )
        analysis_ref.update({
            'status': 'completed' if 'error' not in resultado else 'failed',
            'metrics': resultado.get('metrics'),
            'raw_analysis': resultado.get('raw_analysis'),
            'output_video': resultado.get('output_video'),
            'completed_at': firestore.SERVER_TIMESTAMP,
            'error_details': resultado.get('error')
        })
        return {"status": "ok"}
    except Exception as e:
        if 'analysis_ref' in locals():
            analysis_ref.update({
                'status': 'failed',
                'error_details': f"Error general: {str(e)}",
                'failed_at': firestore.SERVER_TIMESTAMP
            })
        return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)