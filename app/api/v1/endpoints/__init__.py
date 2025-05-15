from .auth import router as auth_router
from .users import router as users_router
from .video_analysis import router as video_analysis_router
from .friends import router as friends_router

__all__ = ["auth_router", "users_router", "video_analysis_router", "friends_router"] 