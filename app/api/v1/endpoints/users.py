from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.user import User, UserUpdate, PrivacyUpdateRequest, PreferencesUpdateRequest, DeleteAccountRequest, UserInDB
from app.services.firebase import get_firebase_client
from app.core.security import verify_password, get_password_hash
from app.core.deps import get_current_user
import logging
from fastapi import HTTPException as RealHTTPException
from google.cloud import firestore

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/me", response_model=User)
async def read_user_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Obtiene la información del usuario actual.
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(user_in: UserUpdate, current_user: UserInDB = Depends(get_current_user)):
    """
    Actualiza la información del usuario actual.
    """
    try:
        db = get_firebase_client()
        user_ref = db.collection('users').document(current_user.id)
        update_data = user_in.dict(exclude_unset=True)
        user_ref.update(update_data)
        user_doc = user_ref.get()
        user_data = user_doc.to_dict()
        user_data['id'] = user_ref.id
        return UserInDB(**user_data)
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al actualizar usuario")

@router.get("/{user_id}/profile")
async def read_user_profile(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user),
    level: str = Query(None, description="Nivel de detalle del perfil: basic, detailed, full")
):
    """
    Obtiene el perfil de un usuario específico.
    - Valida la configuración de privacidad del usuario
    - Permite diferentes niveles de detalle según la relación entre usuarios
    """
    try:
        db = get_firebase_client()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        user_data = user_doc.to_dict()
        
        # Verificar si el usuario está bloqueado
        blocked_ref = db.collection('blocked_users').where('blocker_id', '==', current_user.id).where('blocked_id', '==', user_id).get()
        if blocked_ref:
            raise HTTPException(status_code=403, detail="No puedes ver este perfil")
            
        # Verificar configuración de privacidad
        privacy = user_data.get('privacy', {})
        if not privacy.get('profile_visible', True):
            raise HTTPException(status_code=403, detail="Este perfil es privado")
            
        # Determinar nivel de detalle
        is_self = user_id == current_user.id
        is_friend = False
        
        if not is_self:
            # Verificar si son amigos
            friendship_ref = db.collection('friendships').where('user1_id', 'in', [current_user.id, user_id]).where('user2_id', 'in', [current_user.id, user_id]).get()
            is_friend = len(friendship_ref) > 0
            
        # Preparar respuesta según nivel de detalle
        response = {
            'id': user_id,
            'name': user_data.get('name'),
            'nivel': user_data.get('nivel'),
            'posicion_preferida': user_data.get('posicion_preferida'),
            'fecha_registro': user_data.get('fecha_registro')
        }
        
        # Añadir información adicional según nivel y relación
        if is_self or is_friend or level == 'detailed':
            response.update({
                'ultimo_analisis': user_data.get('ultimo_analisis'),
                'tipo_ultimo_analisis': user_data.get('tipo_ultimo_analisis'),
                'fecha_ultimo_analisis': user_data.get('fecha_ultimo_analisis'),
                'estadisticas': user_data.get('estadisticas', {})
            })
            
        if is_self or level == 'full':
            response.update({
                'email': user_data.get('email') if privacy.get('show_email', False) else None,
                'preferencias': user_data.get('preferencias', {}),
                'privacy': user_data.get('privacy', {})
            })
            
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener perfil de usuario: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener perfil de usuario")

@router.put("/{user_id}/profile")
async def update_user_profile(user_id: str, nivel: str = None, posicion_preferida: str = None, biografia: str = None):
    raise HTTPException(status_code=501, detail="Not Implemented")

@router.delete("/me")
async def delete_user_me(request: DeleteAccountRequest, current_user: UserInDB = Depends(get_current_user)):
    """Elimina la cuenta del usuario autenticado."""
    try:
        db = get_firebase_client()
        user_ref = db.collection('users').document(current_user.id)
        user_data = user_ref.get().to_dict()
        if not verify_password(request.password, user_data.get('hashed_password', '')):
            raise HTTPException(status_code=403, detail="Contraseña incorrecta")
        user_ref.delete()
        # Opcional: eliminar datos relacionados (amigos, análisis, etc.)
        return {"detail": "Cuenta eliminada correctamente"}
    except Exception as e:
        logger.error(f"Error al eliminar cuenta: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al eliminar cuenta")

@router.put("/me/privacy")
async def update_privacy_me(request: PrivacyUpdateRequest, current_user: UserInDB = Depends(get_current_user)):
    """Actualiza la configuración de privacidad del usuario."""
    try:
        db = get_firebase_client()
        user_ref = db.collection('users').document(current_user.id)
        user_ref.update({"privacy": request.privacy.dict()})
        return {"detail": "Privacidad actualizada"}
    except Exception as e:
        logger.error(f"Error al actualizar privacidad: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al actualizar privacidad")

@router.put("/me/preferences")
async def update_preferences_me(request: PreferencesUpdateRequest, current_user: UserInDB = Depends(get_current_user)):
    """Actualiza las preferencias del usuario."""
    try:
        db = get_firebase_client()
        user_ref = db.collection('users').document(current_user.id)
        user_ref.update({"preferences": request.preferences.dict()})
        return {"detail": "Preferencias actualizadas"}
    except Exception as e:
        logger.error(f"Error al actualizar preferencias: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al actualizar preferencias")

@router.get("/me/activity")
async def get_user_activity(
    current_user: UserInDB = Depends(get_current_user),
    activity_type: str = Query(None, description="Tipo de actividad: all, videos, matches, social"),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """
    Obtiene el historial de actividad del usuario.
    - Incluye análisis de videos, partidos jugados e interacciones sociales
    - Permite filtrar por tipo de actividad
    - Implementa paginación
    """
    try:
        db = get_firebase_client()
        activities = []
        
        # Obtener análisis de videos
        if activity_type in [None, 'all', 'videos']:
            video_analyses = db.collection('video_analysis')\
                .where('user_id', '==', current_user.id)\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .offset(offset)\
                .get()
                
            for analysis in video_analyses:
                analysis_data = analysis.to_dict()
                activities.append({
                    'type': 'video_analysis',
                    'id': analysis.id,
                    'created_at': analysis_data.get('created_at'),
                    'padel_iq': analysis_data.get('padel_iq'),
                    'tipo_video': analysis_data.get('tipo_video'),
                    'metrics': analysis_data.get('metrics', {})
                })
        
        # Obtener partidos jugados
        if activity_type in [None, 'all', 'matches']:
            matches = db.collection('matches')\
                .where('players', 'array_contains', current_user.id)\
                .order_by('date', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .offset(offset)\
                .get()
                
            for match in matches:
                match_data = match.to_dict()
                activities.append({
                    'type': 'match',
                    'id': match.id,
                    'date': match_data.get('date'),
                    'result': match_data.get('result'),
                    'opponents': match_data.get('opponents', []),
                    'score': match_data.get('score')
                })
        
        # Obtener interacciones sociales
        if activity_type in [None, 'all', 'social']:
            social_interactions = db.collection('social_interactions')\
                .where('user_id', '==', current_user.id)\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .offset(offset)\
                .get()
                
            for interaction in social_interactions:
                interaction_data = interaction.to_dict()
                activities.append({
                    'type': 'social',
                    'id': interaction.id,
                    'created_at': interaction_data.get('created_at'),
                    'interaction_type': interaction_data.get('type'),
                    'content': interaction_data.get('content'),
                    'related_user': interaction_data.get('related_user_id')
                })
        
        # Ordenar todas las actividades por fecha
        activities.sort(key=lambda x: x.get('created_at', x.get('date', 0)), reverse=True)
        
        # Aplicar límite y offset final
        paginated_activities = activities[offset:offset + limit]
        
        return {
            'activities': paginated_activities,
            'total': len(activities),
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error(f"Error al obtener historial de actividad: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener historial de actividad") 