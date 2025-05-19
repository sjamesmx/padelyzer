from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v1.endpoints import (
    friends,
    social_wall,
    matchmaking,
    subscriptions,
    search,
    onboarding,
    gamification,
    video_analysis,
    auth,
    users,
    videos,
    notifications
)
from app.config.firebase import initialize_firebase
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.
    """
    # Inicializar Firebase al inicio
    try:
        initialize_firebase()
        logger.info("Firebase inicializado correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {str(e)}")
        # No lanzamos la excepción para permitir que la aplicación continúe
        logger.warning("La aplicación continuará sin Firebase inicializado")

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Incluir routers con prefijos correctos
    app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
    app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
    app.include_router(videos.router, prefix=f"{settings.API_V1_STR}/videos", tags=["videos"])
    app.include_router(matchmaking.router, prefix=f"{settings.API_V1_STR}/matchmaking", tags=["matchmaking"])
    app.include_router(friends.router, prefix=f"{settings.API_V1_STR}/friends", tags=["friends"])
    app.include_router(social_wall.router, prefix=f"{settings.API_V1_STR}/social_wall", tags=["social_wall"])
    app.include_router(subscriptions.router, prefix=f"{settings.API_V1_STR}/subscriptions", tags=["subscriptions"])
    app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"])
    app.include_router(onboarding.router, prefix=f"{settings.API_V1_STR}/onboarding", tags=["onboarding"])
    app.include_router(gamification.router, prefix=f"{settings.API_V1_STR}/gamification", tags=["gamification"])
    app.include_router(video_analysis.router, prefix=f"{settings.API_V1_STR}/video", tags=["video"])
    app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

app = create_application() 