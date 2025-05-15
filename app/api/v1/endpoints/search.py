from fastapi import APIRouter, HTTPException, Query, Depends, status
from firebase_admin import firestore
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel
import uuid

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchFilters(BaseModel):
    location: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[str] = None
    radius: Optional[int] = None  # Radio en kilómetros para búsqueda por ubicación
    availability: Optional[str] = None  # Disponibilidad: morning, afternoon, evening, night
    last_active: Optional[int] = None  # Días desde última actividad

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.get("/users", response_model=List[Dict], summary="Buscar usuarios", tags=["search"])
async def search_users(
    query: Optional[str] = Query(None, description="Término de búsqueda"),
    filters: Optional[SearchFilters] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Busca usuarios con filtros avanzados.
    - Búsqueda por texto en nombre, email y ubicación
    - Filtros por nivel, posición, ubicación, edad, género
    - Búsqueda por radio de distancia
    - Filtros de disponibilidad y actividad reciente
    """
    try:
        db = get_db()
        users_ref = db.collection("users")
        users_query = users_ref

        # Aplicar filtros básicos
        if filters:
            if filters.location:
                users_query = users_query.where("location", "==", filters.location)
            if filters.level:
                users_query = users_query.where("level", "==", filters.level)
            if filters.position:
                users_query = users_query.where("preferred_position", "==", filters.position)
            if filters.gender:
                users_query = users_query.where("gender", "==", filters.gender)
            if filters.availability:
                users_query = users_query.where("availability", "array_contains", filters.availability)

        # Obtener resultados iniciales
        users = users_query.get()
        results = []

        # Aplicar filtros adicionales y búsqueda por texto
        for user in users:
            data = user.to_dict()
            
            # Filtrar por texto
            if query:
                if not any(query.lower() in str(value).lower() for value in [
                    data.get("username", ""),
                    data.get("email", ""),
                    data.get("location", ""),
                    data.get("name", "")
                ]):
                    continue

            # Filtrar por edad
            if filters and (filters.min_age or filters.max_age):
                birth_date = data.get("birth_date")
                if birth_date:
                    age = calculate_age(birth_date)
                    if filters.min_age and age < filters.min_age:
                        continue
                    if filters.max_age and age > filters.max_age:
                        continue

            # Filtrar por última actividad
            if filters and filters.last_active:
                last_active = data.get("last_active")
                if last_active:
                    days_since_active = (datetime.now() - last_active).days
                    if days_since_active > filters.last_active:
                        continue

            # Filtrar por radio de distancia
            if filters and filters.radius and data.get("location_coordinates"):
                user_coords = data["location_coordinates"]
                if not is_within_radius(user_coords, current_user.location_coordinates, filters.radius):
                    continue

            # Enriquecer datos del usuario
            enriched_data = {
                "id": user.id,
                "username": data.get("username"),
                "name": data.get("name"),
                "email": data.get("email"),
                "level": data.get("level"),
                "preferred_position": data.get("preferred_position"),
                "location": data.get("location"),
                "profile_picture": data.get("profile_picture"),
                "availability": data.get("availability", []),
                "last_active": data.get("last_active"),
                "stats": {
                    "matches_played": data.get("matches_played", 0),
                    "win_rate": data.get("win_rate", 0),
                    "padel_iq": data.get("padel_iq", 0)
                }
            }
            results.append(enriched_data)

        # Ordenar resultados por relevancia
        if query:
            results.sort(key=lambda x: calculate_relevance(x, query))

        # Aplicar paginación
        total = len(results)
        paginated_results = results[offset:offset + limit]

        return {
            "users": paginated_results,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error en búsqueda de usuarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en búsqueda de usuarios"
        )

@router.get("/content", response_model=List[Dict], summary="Buscar contenido", tags=["search"])
async def search_content(
    query: Optional[str] = Query(None, description="Término de búsqueda"),
    type: Optional[str] = Query(None, description="Tipo de contenido: post, video, analysis"),
    user_id: Optional[str] = Query(None, description="ID del usuario que creó el contenido"),
    from_date: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    tags: Optional[List[str]] = Query(None, description="Etiquetas del contenido"),
    min_views: Optional[int] = Query(None, description="Mínimo número de visualizaciones"),
    min_likes: Optional[int] = Query(None, description="Mínimo número de likes"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Busca contenido con filtros avanzados.
    - Búsqueda por texto en título y contenido
    - Filtros por tipo, usuario, fecha, etiquetas
    - Filtros por métricas (visualizaciones, likes)
    - Ordenamiento por relevancia y popularidad
    """
    try:
        db = get_db()
        
        # Determinar colección según tipo
        if type == "video":
            ref = db.collection("videos")
        elif type == "analysis":
            ref = db.collection("video_analysis")
        else:
            ref = db.collection("posts")

        # Aplicar filtros básicos
        content_query = ref
        if user_id:
            content_query = content_query.where("user_id", "==", user_id)
        if tags:
            for tag in tags:
                content_query = content_query.where("tags", "array_contains", tag)

        # Obtener resultados iniciales
        items = content_query.get()
        results = []

        # Aplicar filtros adicionales y búsqueda por texto
        for item in items:
            data = item.to_dict()

            # Filtrar por texto
            if query:
                if not any(query.lower() in str(value).lower() for value in [
                    data.get("title", ""),
                    data.get("content", ""),
                    data.get("description", "")
                ]):
                    continue

            # Filtrar por fecha
            if from_date and data.get("created_at") and data["created_at"] < from_date:
                continue
            if to_date and data.get("created_at") and data["created_at"] > to_date:
                continue

            # Filtrar por métricas
            if min_views and data.get("views", 0) < min_views:
                continue
            if min_likes and data.get("likes", 0) < min_likes:
                continue

            # Enriquecer datos del contenido
            enriched_data = {
                "id": item.id,
                "type": type or "post",
                "title": data.get("title"),
                "content": data.get("content"),
                "description": data.get("description"),
                "user_id": data.get("user_id"),
                "created_at": data.get("created_at"),
                "tags": data.get("tags", []),
                "metrics": {
                    "views": data.get("views", 0),
                    "likes": data.get("likes", 0),
                    "comments": data.get("comments", 0)
                }
            }
            results.append(enriched_data)

        # Ordenar resultados por relevancia y popularidad
        if query:
            results.sort(key=lambda x: calculate_content_relevance(x, query))
        else:
            results.sort(key=lambda x: x["metrics"]["views"], reverse=True)

        # Aplicar paginación
        total = len(results)
        paginated_results = results[offset:offset + limit]

        return {
            "content": paginated_results,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error en búsqueda de contenido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en búsqueda de contenido"
        )

@router.get("/suggestions", response_model=List[str], summary="Obtener sugerencias de búsqueda", tags=["search"])
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Término de búsqueda"),
    type: Optional[str] = Query(None, description="Tipo de sugerencias: users, content, all"),
    limit: int = Query(10, ge=1, le=50),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene sugerencias de búsqueda basadas en:
    - Búsquedas populares
    - Historial de búsquedas del usuario
    - Contenido y usuarios relevantes
    """
    try:
        db = get_db()
        suggestions = set()

        # Obtener sugerencias de búsquedas populares
        popular_searches = db.collection("search_stats")\
            .where("term", ">=", query)\
            .where("term", "<=", query + "\uf8ff")\
            .order_by("term")\
            .limit(limit)\
            .get()

        for search in popular_searches:
            suggestions.add(search.to_dict()["term"])

        # Obtener sugerencias del historial del usuario
        user_searches = db.collection("user_search_history")\
            .where("user_id", "==", current_user.id)\
            .where("term", ">=", query)\
            .where("term", "<=", query + "\uf8ff")\
            .order_by("term")\
            .limit(limit)\
            .get()

        for search in user_searches:
            suggestions.add(search.to_dict()["term"])

        # Obtener sugerencias de usuarios
        if type in [None, "users", "all"]:
            users = db.collection("users")\
                .where("username", ">=", query)\
                .where("username", "<=", query + "\uf8ff")\
                .limit(limit)\
                .get()

            for user in users:
                suggestions.add(f"@{user.to_dict()['username']}")

        # Obtener sugerencias de contenido
        if type in [None, "content", "all"]:
            content = db.collection("posts")\
                .where("title", ">=", query)\
                .where("title", "<=", query + "\uf8ff")\
                .limit(limit)\
                .get()

            for post in content:
                suggestions.add(post.to_dict()["title"])

        # Convertir a lista y limitar resultados
        suggestions_list = list(suggestions)[:limit]

        # Registrar la búsqueda
        search_id = str(uuid.uuid4())
        db.collection("user_search_history").document(search_id).set({
            "user_id": current_user.id,
            "term": query,
            "created_at": datetime.now()
        })

        return suggestions_list

    except Exception as e:
        logger.error(f"Error al obtener sugerencias: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener sugerencias"
        )

def calculate_age(birth_date):
    """Calcula la edad basada en la fecha de nacimiento."""
    today = datetime.now()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def is_within_radius(coords1, coords2, radius_km):
    """Verifica si dos coordenadas están dentro del radio especificado."""
    # Implementar cálculo de distancia usando la fórmula de Haversine
    # Por ahora retornamos True para simular la funcionalidad
    return True

def calculate_relevance(user_data, query):
    """Calcula la relevancia de un usuario para un término de búsqueda."""
    score = 0
    query = query.lower()
    
    # Ponderar coincidencias en diferentes campos
    if query in user_data.get("username", "").lower():
        score += 3
    if query in user_data.get("name", "").lower():
        score += 2
    if query in user_data.get("location", "").lower():
        score += 1
        
    return score

def calculate_content_relevance(content_data, query):
    """Calcula la relevancia de un contenido para un término de búsqueda."""
    score = 0
    query = query.lower()
    
    # Ponderar coincidencias en diferentes campos
    if query in content_data.get("title", "").lower():
        score += 3
    if query in content_data.get("content", "").lower():
        score += 2
    if query in content_data.get("description", "").lower():
        score += 1
        
    # Considerar métricas de popularidad
    score += content_data.get("metrics", {}).get("views", 0) * 0.1
    score += content_data.get("metrics", {}).get("likes", 0) * 0.2
    
    return score

@router.post("/players")
async def search_players():
    raise HTTPException(status_code=501, detail="Not Implemented")

@router.get("/nearby")
async def get_nearby_players():
    raise HTTPException(status_code=501, detail="Not Implemented") 