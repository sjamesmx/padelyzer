from fastapi import APIRouter
from app.api.v1.endpoints import auth_router, users_router, video_analysis_router, friends_router

api_router = APIRouter()

# Auth routes
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])

# User routes
api_router.include_router(users_router, prefix="/users", tags=["users"])

# Video analysis routes
api_router.include_router(video_analysis_router, prefix="/video", tags=["video analysis"])

# Friends routes
api_router.include_router(friends_router, prefix="/friends", tags=["friends"]) 