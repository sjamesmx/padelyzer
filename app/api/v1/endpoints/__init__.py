from .auth import router as auth_router
from .users import router as users_router
from .friends import router as friends_router
from .padel_iq import router as padel_iq_router
from . import video_routes as video_analysis
from . import auth
from . import users
from . import padel_iq
from . import matchmaking
from . import notifications
from . import social_wall
from . import settings
from . import onboarding
from . import search
from . import gamification
from . import subscriptions

__all__ = [
    'auth_router',
    'users_router',
    'friends_router',
    'padel_iq_router'
] 