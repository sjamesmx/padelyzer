from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File, Form
from firebase_admin import firestore, storage
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import logging
from pydantic import BaseModel
from app.services.notifications import notification_service

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos de datos
class PostCreate(BaseModel):
    content: str
    media_urls: Optional[List[str]] = []
    visibility: str = "public"  # public, friends, private
    location: Optional[Dict] = None
    tags: Optional[List[str]] = []

class CommentCreate(BaseModel):
    content: str
    parent_comment_id: Optional[str] = None

class ReactionCreate(BaseModel):
    type: str  # like, love, laugh, wow, sad, angry

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

def get_storage():
    try:
        return storage.bucket()
    except ValueError as e:
        logger.error(f"Error inicializando Storage: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Storage")

@router.get("/", response_model=Dict, summary="Obtener muro social", tags=["social_wall"])
async def get_social_wall(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None, description="Categoría: all, friends, trending"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene el muro social con posts.
    - Paginación
    - Filtros por categoría
    - Posts de amigos y trending
    """
    try:
        db = get_db()
        offset = (page - 1) * limit
        
        # Construir query base
        posts_ref = db.collection("posts")
        
        if category == "friends":
            # Obtener IDs de amigos
            friendships = db.collection("friendships")\
                .where("user1_id", "==", current_user.id)\
                .get()
            friend_ids = [f.to_dict()["user2_id"] for f in friendships]
            
            friendships2 = db.collection("friendships")\
                .where("user2_id", "==", current_user.id)\
                .get()
            friend_ids.extend([f.to_dict()["user1_id"] for f in friendships2])
            friend_ids.append(current_user.id)
            
            # Filtrar posts de amigos
            query = posts_ref.where("user_id", "in", friend_ids)
        elif category == "trending":
            # Posts con más interacciones
            query = posts_ref.order_by("interaction_count", direction=firestore.Query.DESCENDING)
        else:
            # Todos los posts públicos
            query = posts_ref.where("visibility", "==", "public")
            
        # Aplicar paginación
        posts = query.order_by("created_at", direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .offset(offset)\
            .get()
            
        # Enriquecer posts con información adicional
        enriched_posts = []
        for post in posts:
            post_data = post.to_dict()
            post_id = post.id
            
            # Obtener información del autor
            author = db.collection("users").document(post_data["user_id"]).get()
            author_data = author.to_dict() if author.exists else {}
            
            # Obtener reacciones
            reactions = db.collection("post_reactions")\
                .where("post_id", "==", post_id)\
                .get()
            reaction_counts = {}
            for reaction in reactions:
                r_type = reaction.to_dict()["type"]
                reaction_counts[r_type] = reaction_counts.get(r_type, 0) + 1
                
            # Obtener comentarios recientes
            recent_comments = db.collection("comments")\
                .where("post_id", "==", post_id)\
                .order_by("created_at", direction=firestore.Query.DESCENDING)\
                .limit(3)\
                .get()
                
            # Verificar si el usuario actual ha reaccionado
            user_reaction = db.collection("post_reactions")\
                .where("post_id", "==", post_id)\
                .where("user_id", "==", current_user.id)\
                .get()
                
            enriched_post = {
                "post_id": post_id,
                "content": post_data["content"],
                "media_urls": post_data.get("media_urls", []),
                "created_at": post_data["created_at"],
                "author": {
                    "user_id": author_data.get("id"),
                    "username": author_data.get("username"),
                    "name": author_data.get("name"),
                    "profile_picture": author_data.get("profile_picture")
                },
                "reactions": reaction_counts,
                "user_reaction": user_reaction[0].to_dict()["type"] if user_reaction else None,
                "comment_count": post_data.get("comment_count", 0),
                "recent_comments": [c.to_dict() for c in recent_comments],
                "visibility": post_data.get("visibility", "public"),
                "location": post_data.get("location"),
                "tags": post_data.get("tags", [])
            }
            enriched_posts.append(enriched_post)
            
        # Obtener total de posts para paginación
        total = query.count().get()[0][0]
        
        return {
            "posts": enriched_posts,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (offset + limit) < total
        }
        
    except Exception as e:
        logger.error(f"Error al obtener muro social: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener muro social"
        )

@router.post("/", response_model=Dict, summary="Crear post", tags=["social_wall"])
async def create_post(
    content: str = Form(...),
    visibility: str = Form("public"),
    location: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    media_files: Optional[List[UploadFile]] = File(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Crea un nuevo post en el muro social.
    - Soporte para contenido multimedia
    - Control de visibilidad
    - Etiquetas y ubicación
    """
    try:
        db = get_db()
        bucket = get_storage()
        
        # Procesar archivos multimedia
        media_urls = []
        if media_files:
            for file in media_files:
                # Generar nombre único
                file_extension = file.filename.split(".")[-1]
                file_name = f"posts/{current_user.id}/{uuid.uuid4()}.{file_extension}"
                
                # Subir a Storage
                blob = bucket.blob(file_name)
                blob.upload_from_file(file.file)
                
                # Obtener URL pública
                blob.make_public()
                media_urls.append(blob.public_url)
                
        # Procesar ubicación
        location_data = None
        if location:
            try:
                location_data = eval(location)  # Convertir string a dict
            except:
                location_data = {"name": location}
                
        # Procesar etiquetas
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            
        # Crear post
        post_id = str(uuid.uuid4())
        post_data = {
            "post_id": post_id,
            "user_id": current_user.id,
            "content": content,
            "media_urls": media_urls,
            "visibility": visibility,
            "location": location_data,
            "tags": tag_list,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "interaction_count": 0,
            "comment_count": 0
        }
        
        db.collection("posts").document(post_id).set(post_data)
        
        # Notificar a amigos
        if visibility == "public":
            # Obtener amigos
            friendships = db.collection("friendships")\
                .where("user1_id", "==", current_user.id)\
                .get()
            friend_ids = [f.to_dict()["user2_id"] for f in friendships]
            
            friendships2 = db.collection("friendships")\
                .where("user2_id", "==", current_user.id)\
                .get()
            friend_ids.extend([f.to_dict()["user1_id"] for f in friendships2])
            
            # Enviar notificaciones
            for friend_id in friend_ids:
                notification_service.create_notification(
                    user_id=friend_id,
                    type="new_post",
                    title="Nuevo post de amigo",
                    message=f"{current_user.username} ha publicado algo nuevo",
                    data={
                        "post_id": post_id,
                        "author_id": current_user.id
                    }
                )
                
        return {
            "message": "Post creado exitosamente",
            "post_id": post_id,
            "post": post_data
        }
        
    except Exception as e:
        logger.error(f"Error al crear post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear post"
        )

@router.get("/{user_id}", response_model=Dict, summary="Obtener posts de usuario", tags=["social_wall"])
async def get_user_posts(
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene los posts de un usuario específico.
    - Paginación
    - Filtrado por visibilidad
    """
    try:
        db = get_db()
        offset = (page - 1) * limit
        
        # Verificar si el usuario actual es amigo
        is_friend = False
        if user_id != current_user.id:
            friendship = db.collection("friendships")\
                .where("user1_id", "in", [current_user.id, user_id])\
                .where("user2_id", "in", [current_user.id, user_id])\
                .get()
            is_friend = len(friendship) > 0
            
        # Construir query
        posts_ref = db.collection("posts").where("user_id", "==", user_id)
        
        # Filtrar por visibilidad
        if user_id == current_user.id:
            # Ver todos los posts propios
            query = posts_ref
        elif is_friend:
            # Ver posts públicos y de amigos
            query = posts_ref.where("visibility", "in", ["public", "friends"])
        else:
            # Ver solo posts públicos
            query = posts_ref.where("visibility", "==", "public")
            
        # Obtener posts
        posts = query.order_by("created_at", direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .offset(offset)\
            .get()
            
        # Enriquecer posts
        enriched_posts = []
        for post in posts:
            post_data = post.to_dict()
            post_id = post.id
            
            # Obtener reacciones
            reactions = db.collection("post_reactions")\
                .where("post_id", "==", post_id)\
                .get()
            reaction_counts = {}
            for reaction in reactions:
                r_type = reaction.to_dict()["type"]
                reaction_counts[r_type] = reaction_counts.get(r_type, 0) + 1
                
            # Verificar reacción del usuario actual
            user_reaction = db.collection("post_reactions")\
                .where("post_id", "==", post_id)\
                .where("user_id", "==", current_user.id)\
                .get()
                
            enriched_post = {
                "post_id": post_id,
                "content": post_data["content"],
                "media_urls": post_data.get("media_urls", []),
                "created_at": post_data["created_at"],
                "reactions": reaction_counts,
                "user_reaction": user_reaction[0].to_dict()["type"] if user_reaction else None,
                "comment_count": post_data.get("comment_count", 0),
                "visibility": post_data.get("visibility", "public"),
                "location": post_data.get("location"),
                "tags": post_data.get("tags", [])
            }
            enriched_posts.append(enriched_post)
            
        # Obtener total para paginación
        total = query.count().get()[0][0]
        
        return {
            "posts": enriched_posts,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (offset + limit) < total
        }
        
    except Exception as e:
        logger.error(f"Error al obtener posts de usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener posts de usuario"
        )

@router.post("/{post_id}/reaction", response_model=Dict, summary="Reaccionar a post", tags=["social_wall"])
async def react_to_post(
    post_id: str,
    reaction: ReactionCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Agrega o actualiza una reacción a un post.
    - Soporte para múltiples tipos de reacciones
    - Notificación al autor
    """
    try:
        db = get_db()
        
        # Verificar post
        post = db.collection("posts").document(post_id).get()
        if not post.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post no encontrado"
            )
            
        post_data = post.to_dict()
        
        # Verificar si ya existe una reacción
        existing_reaction = db.collection("post_reactions")\
            .where("post_id", "==", post_id)\
            .where("user_id", "==", current_user.id)\
            .get()
            
        reaction_id = f"{current_user.id}_{post_id}"
        
        if existing_reaction:
            # Actualizar reacción existente
            old_type = existing_reaction[0].to_dict()["type"]
            if old_type == reaction.type:
                # Quitar reacción
                db.collection("post_reactions").document(reaction_id).delete()
                # Actualizar contador
                db.collection("posts").document(post_id).update({
                    "interaction_count": firestore.Increment(-1)
                })
                return {"message": "Reacción eliminada"}
            else:
                # Cambiar tipo de reacción
                db.collection("post_reactions").document(reaction_id).update({
                    "type": reaction.type,
                    "updated_at": datetime.now()
                })
        else:
            # Crear nueva reacción
            db.collection("post_reactions").document(reaction_id).set({
                "reaction_id": reaction_id,
                "post_id": post_id,
                "user_id": current_user.id,
                "type": reaction.type,
                "created_at": datetime.now()
            })
            # Actualizar contador
            db.collection("posts").document(post_id).update({
                "interaction_count": firestore.Increment(1)
            })
            
        # Notificar al autor si no es el mismo usuario
        if post_data["user_id"] != current_user.id:
            notification_service.create_notification(
                user_id=post_data["user_id"],
                type="post_reaction",
                title="Nueva reacción en tu post",
                message=f"{current_user.username} reaccionó a tu post",
                data={
                    "post_id": post_id,
                    "reaction_type": reaction.type,
                    "user_id": current_user.id
                }
            )
            
        return {
            "message": "Reacción actualizada",
            "reaction_type": reaction.type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al reaccionar a post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al reaccionar a post"
        )

@router.post("/{post_id}/comment", response_model=Dict, summary="Comentar post", tags=["social_wall"])
async def comment_post(
    post_id: str,
    comment: CommentCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Agrega un comentario a un post.
    - Soporte para respuestas anidadas
    - Notificaciones
    """
    try:
        db = get_db()
        
        # Verificar post
        post = db.collection("posts").document(post_id).get()
        if not post.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post no encontrado"
            )
            
        post_data = post.to_dict()
        
        # Verificar comentario padre si existe
        if comment.parent_comment_id:
            parent_comment = db.collection("comments").document(comment.parent_comment_id).get()
            if not parent_comment.exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comentario padre no encontrado"
                )
                
        # Crear comentario
        comment_id = str(uuid.uuid4())
        comment_data = {
            "comment_id": comment_id,
            "post_id": post_id,
            "user_id": current_user.id,
            "content": comment.content,
            "parent_comment_id": comment.parent_comment_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "reaction_count": 0
        }
        
        db.collection("comments").document(comment_id).set(comment_data)
        
        # Actualizar contador de comentarios
        db.collection("posts").document(post_id).update({
            "comment_count": firestore.Increment(1)
        })
        
        # Notificar al autor del post
        if post_data["user_id"] != current_user.id:
            notification_service.create_notification(
                user_id=post_data["user_id"],
                type="post_comment",
                title="Nuevo comentario en tu post",
                message=f"{current_user.username} comentó en tu post",
                data={
                    "post_id": post_id,
                    "comment_id": comment_id,
                    "user_id": current_user.id
                }
            )
            
        # Notificar al autor del comentario padre si existe
        if comment.parent_comment_id:
            parent_data = parent_comment.to_dict()
            if parent_data["user_id"] != current_user.id:
                notification_service.create_notification(
                    user_id=parent_data["user_id"],
                    type="comment_reply",
                    title="Respuesta a tu comentario",
                    message=f"{current_user.username} respondió a tu comentario",
                    data={
                        "post_id": post_id,
                        "comment_id": comment_id,
                        "parent_comment_id": comment.parent_comment_id,
                        "user_id": current_user.id
                    }
                )
                
        return {
            "message": "Comentario publicado",
            "comment_id": comment_id,
            "comment": comment_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al comentar post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al comentar post"
        )

@router.get("/{post_id}/comments", response_model=Dict, summary="Obtener comentarios", tags=["social_wall"])
async def get_comments(
    post_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene los comentarios de un post.
    - Paginación
    - Comentarios anidados
    """
    try:
        db = get_db()
        offset = (page - 1) * limit
        
        # Verificar post
        post = db.collection("posts").document(post_id).get()
        if not post.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post no encontrado"
            )
            
        # Obtener comentarios principales
        comments = db.collection("comments")\
            .where("post_id", "==", post_id)\
            .where("parent_comment_id", "==", None)\
            .order_by("created_at", direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .offset(offset)\
            .get()
            
        # Enriquecer comentarios
        enriched_comments = []
        for comment in comments:
            comment_data = comment.to_dict()
            comment_id = comment.id
            
            # Obtener autor
            author = db.collection("users").document(comment_data["user_id"]).get()
            author_data = author.to_dict() if author.exists else {}
            
            # Obtener respuestas
            replies = db.collection("comments")\
                .where("parent_comment_id", "==", comment_id)\
                .order_by("created_at")\
                .limit(3)\
                .get()
                
            # Obtener reacciones
            reactions = db.collection("comment_reactions")\
                .where("comment_id", "==", comment_id)\
                .get()
            reaction_counts = {}
            for reaction in reactions:
                r_type = reaction.to_dict()["type"]
                reaction_counts[r_type] = reaction_counts.get(r_type, 0) + 1
                
            # Verificar reacción del usuario actual
            user_reaction = db.collection("comment_reactions")\
                .where("comment_id", "==", comment_id)\
                .where("user_id", "==", current_user.id)\
                .get()
                
            enriched_comment = {
                "comment_id": comment_id,
                "content": comment_data["content"],
                "created_at": comment_data["created_at"],
                "author": {
                    "user_id": author_data.get("id"),
                    "username": author_data.get("username"),
                    "name": author_data.get("name"),
                    "profile_picture": author_data.get("profile_picture")
                },
                "reactions": reaction_counts,
                "user_reaction": user_reaction[0].to_dict()["type"] if user_reaction else None,
                "reply_count": len(replies),
                "replies": [r.to_dict() for r in replies]
            }
            enriched_comments.append(enriched_comment)
            
        # Obtener total para paginación
        total = db.collection("comments")\
            .where("post_id", "==", post_id)\
            .where("parent_comment_id", "==", None)\
            .count()\
            .get()[0][0]
            
        return {
            "comments": enriched_comments,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (offset + limit) < total
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener comentarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener comentarios"
        )

@router.delete("/{post_id}", response_model=Dict, summary="Eliminar post", tags=["social_wall"])
async def delete_post(
    post_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Elimina un post y su contenido asociado.
    - Elimina archivos multimedia
    - Limpia reacciones y comentarios
    """
    try:
        db = get_db()
        bucket = get_storage()
        
        # Verificar post
        post = db.collection("posts").document(post_id).get()
        if not post.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post no encontrado"
            )
            
        post_data = post.to_dict()
        
        # Verificar permisos
        if post_data["user_id"] != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para eliminar este post"
            )
            
        # Eliminar archivos multimedia
        for media_url in post_data.get("media_urls", []):
            try:
                # Extraer nombre del archivo de la URL
                file_name = media_url.split("/")[-1]
                blob = bucket.blob(f"posts/{post_data['user_id']}/{file_name}")
                blob.delete()
            except Exception as e:
                logger.error(f"Error al eliminar archivo multimedia: {str(e)}")
                
        # Eliminar reacciones
        reactions = db.collection("post_reactions")\
            .where("post_id", "==", post_id)\
            .get()
        for reaction in reactions:
            reaction.reference.delete()
            
        # Eliminar comentarios y sus reacciones
        comments = db.collection("comments")\
            .where("post_id", "==", post_id)\
            .get()
        for comment in comments:
            comment_id = comment.id
            # Eliminar reacciones del comentario
            comment_reactions = db.collection("comment_reactions")\
                .where("comment_id", "==", comment_id)\
                .get()
            for reaction in comment_reactions:
                reaction.reference.delete()
            # Eliminar comentario
            comment.reference.delete()
            
        # Eliminar post
        db.collection("posts").document(post_id).delete()
        
        return {"message": "Post eliminado correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar post"
        )

@router.put("/{post_id}", response_model=Dict, summary="Editar post", tags=["social_wall"])
async def edit_post(
    post_id: str,
    content: str = Form(...),
    visibility: str = Form("public"),
    location: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    media_files: Optional[List[UploadFile]] = File(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Edita un post existente.
    - Actualiza contenido y metadatos
    - Maneja archivos multimedia
    """
    try:
        db = get_db()
        bucket = get_storage()
        
        # Verificar post
        post = db.collection("posts").document(post_id).get()
        if not post.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post no encontrado"
            )
            
        post_data = post.to_dict()
        
        # Verificar permisos
        if post_data["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para editar este post"
            )
            
        # Procesar archivos multimedia
        media_urls = post_data.get("media_urls", [])
        if media_files:
            # Eliminar archivos antiguos
            for old_url in media_urls:
                try:
                    file_name = old_url.split("/")[-1]
                    blob = bucket.blob(f"posts/{current_user.id}/{file_name}")
                    blob.delete()
                except Exception as e:
                    logger.error(f"Error al eliminar archivo antiguo: {str(e)}")
                    
            # Subir nuevos archivos
            media_urls = []
            for file in media_files:
                file_extension = file.filename.split(".")[-1]
                file_name = f"posts/{current_user.id}/{uuid.uuid4()}.{file_extension}"
                
                blob = bucket.blob(file_name)
                blob.upload_from_file(file.file)
                
                blob.make_public()
                media_urls.append(blob.public_url)
                
        # Procesar ubicación
        location_data = None
        if location:
            try:
                location_data = eval(location)
            except:
                location_data = {"name": location}
                
        # Procesar etiquetas
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            
        # Actualizar post
        update_data = {
            "content": content,
            "media_urls": media_urls,
            "visibility": visibility,
            "location": location_data,
            "tags": tag_list,
            "updated_at": datetime.now()
        }
        
        db.collection("posts").document(post_id).update(update_data)
        
        return {
            "message": "Post actualizado correctamente",
            "post_id": post_id,
            "updates": update_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al editar post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al editar post"
        )

@router.post("/{post_id}/report", response_model=Dict, summary="Reportar post", tags=["social_wall"])
async def report_post(
    post_id: str,
    reason: str = Form(...),
    details: Optional[str] = Form(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Reporta un post inapropiado.
    - Validación de reportes duplicados
    - Notificación a moderadores
    """
    try:
        db = get_db()
        
        # Verificar post
        post = db.collection("posts").document(post_id).get()
        if not post.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post no encontrado"
            )
            
        # Verificar reporte duplicado
        existing_report = db.collection("post_reports")\
            .where("post_id", "==", post_id)\
            .where("user_id", "==", current_user.id)\
            .get()
            
        if existing_report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya has reportado este post"
            )
            
        # Crear reporte
        report_id = str(uuid.uuid4())
        report_data = {
            "report_id": report_id,
            "post_id": post_id,
            "user_id": current_user.id,
            "reason": reason,
            "details": details,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        db.collection("post_reports").document(report_id).set(report_data)
        
        # Notificar a moderadores
        moderators = db.collection("users")\
            .where("is_admin", "==", True)\
            .get()
            
        for moderator in moderators:
            notification_service.create_notification(
                user_id=moderator.id,
                type="new_report",
                title="Nuevo reporte de post",
                message=f"Post reportado por {current_user.username}",
                data={
                    "report_id": report_id,
                    "post_id": post_id,
                    "user_id": current_user.id
                }
            )
            
        return {
            "message": "Reporte enviado correctamente",
            "report_id": report_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al reportar post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al reportar post"
        )

@router.post("/{post_id}/comments/{comment_id}/report", response_model=Dict, summary="Reportar comentario", tags=["social_wall"])
async def report_comment(
    post_id: str,
    comment_id: str,
    reason: str = Form(...),
    details: Optional[str] = Form(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Reporta un comentario inapropiado.
    - Validación de reportes duplicados
    - Notificación a moderadores
    """
    try:
        db = get_db()
        
        # Verificar comentario
        comment = db.collection("comments").document(comment_id).get()
        if not comment.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comentario no encontrado"
            )
            
        # Verificar reporte duplicado
        existing_report = db.collection("comment_reports")\
            .where("comment_id", "==", comment_id)\
            .where("user_id", "==", current_user.id)\
            .get()
            
        if existing_report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya has reportado este comentario"
            )
            
        # Crear reporte
        report_id = str(uuid.uuid4())
        report_data = {
            "report_id": report_id,
            "post_id": post_id,
            "comment_id": comment_id,
            "user_id": current_user.id,
            "reason": reason,
            "details": details,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        db.collection("comment_reports").document(report_id).set(report_data)
        
        # Notificar a moderadores
        moderators = db.collection("users")\
            .where("is_admin", "==", True)\
            .get()
            
        for moderator in moderators:
            notification_service.create_notification(
                user_id=moderator.id,
                type="new_comment_report",
                title="Nuevo reporte de comentario",
                message=f"Comentario reportado por {current_user.username}",
                data={
                    "report_id": report_id,
                    "post_id": post_id,
                    "comment_id": comment_id,
                    "user_id": current_user.id
                }
            )
            
        return {
            "message": "Reporte enviado correctamente",
            "report_id": report_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al reportar comentario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al reportar comentario"
        ) 