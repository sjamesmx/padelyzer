from fastapi import APIRouter
from .endpoints import auth, video, video_analysis

api_router = APIRouter()

# Incluir routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(video.router, prefix="/videos", tags=["videos"])
api_router.include_router(video_analysis.router, prefix="/video", tags=["video_analysis"]) 