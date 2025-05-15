from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from firebase_admin import firestore
from typing import List, Optional
import uuid
import logging
from datetime import datetime
from .auth import get_current_user

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social_wall", tags=["Social Wall"])

class Post(BaseModel):
    user_id: str = Field(..., description="ID del usuario que crea el post")
    content: str = Field(..., min_length=1, max_length=1000, description="Contenido del post")
    media_url: Optional[str] = Field(None, description="URL opcional de contenido multimedia")
    post_type: str = Field("text", description="Tipo de post (text, video, image)")

class PostResponse(BaseModel):
    post_id: str
    user_id: str
    content: str
    media_url: Optional[str]
    post_type: str
    timestamp: datetime
    likes: int
    comments: int

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.post("/", response_model=PostResponse)
async def create_post(
    post: Post,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un nuevo post en el muro social.
    """
    if post.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para crear posts en nombre de otro usuario")

    if not post.content:
        raise HTTPException(status_code=400, detail="El contenido del post es requerido")

    db = get_db()
    post_id = str(uuid.uuid4())
    post_data = {
        "post_id": post_id,
        "user_id": post.user_id,
        "content": post.content,
        "media_url": post.media_url,
        "post_type": post.post_type,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "likes": 0,
        "comments": 0
    }

    try:
        db.collection("posts").document(post_id).set(post_data)
        logger.info(f"Post creado: {post_id}")
        return post_data
    except Exception as e:
        logger.error(f"Error al crear post: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear el post")

@router.get("/{user_id}", response_model=List[PostResponse])
async def get_posts(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """
    Obtiene los posts de un usuario específico.
    """
    db = get_db()
    try:
        posts = db.collection("posts")\
            .where("user_id", "==", user_id)\
            .order_by("timestamp", direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .offset(offset)\
            .get()

        return [p.to_dict() for p in posts]
    except Exception as e:
        logger.error(f"Error al obtener posts: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener los posts")

@router.post("/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Da like a un post.
    """
    db = get_db()
    try:
        post_ref = db.collection("posts").document(post_id)
        post = post_ref.get()
        
        if not post.exists:
            raise HTTPException(status_code=404, detail="Post no encontrado")

        # Verificar si el usuario ya dio like
        like_ref = db.collection("likes").document(f"{post_id}_{current_user['user_id']}")
        if like_ref.get().exists:
            raise HTTPException(status_code=400, detail="Ya has dado like a este post")

        # Crear el like
        like_ref.set({
            "post_id": post_id,
            "user_id": current_user["user_id"],
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        # Incrementar contador de likes
        post_ref.update({"likes": firestore.Increment(1)})
        
        logger.info(f"Like añadido al post {post_id}")
        return {"status": "success", "message": "Like añadido correctamente"}
    except Exception as e:
        logger.error(f"Error al dar like: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al dar like al post")

@router.post("/{post_id}/comment")
async def add_comment(
    post_id: str,
    content: str = Field(..., min_length=1, max_length=500),
    current_user: dict = Depends(get_current_user)
):
    """
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from firebase_admin import firestore
from typing import List, Optional
import uuid
import logging
from datetime import datetime
from .auth import get_current_user

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social_wall", tags=["Social Wall"])

class Post(BaseModel):
    user_id: str = Field(..., description="ID del usuario que crea el post")
    content: str = Field(..., min_length=1, max_length=1000, description="Contenido del post")
    media_url: Optional[str] = Field(None, description="URL opcional de contenido multimedia")
    post_type: str = Field("text", description="Tipo de post (text, video, image)")

class PostResponse(BaseModel):
    post_id: str
    user_id: str
    content: str
    media_url: Optional[str]
    post_type: str
    timestamp: datetime
    likes: int
    comments: int

@router.post("/", response_model=PostResponse)
async def create_post(
    post: Post,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un nuevo post en el muro social.
    """
    if post.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para crear posts en nombre de otro usuario")

    if not post.content:
        raise HTTPException(status_code=400, detail="El contenido del post es requerido")

    db = firestore.client()
    post_id = str(uuid.uuid4())
    post_data = {
        "post_id": post_id,
        "user_id": post.user_id,
        "content": post.content,
        "media_url": post.media_url,
        "post_type": post.post_type,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "likes": 0,
        "comments": 0
    }

    try:
        db.collection("posts").document(post_id).set(post_data)
        logger.info(f"Post creado: {post_id}")
        return post_data
    except Exception as e:
        logger.error(f"Error al crear post: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear el post")

@router.get("/{user_id}", response_model=List[PostResponse])
async def get_posts(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """
    Obtiene los posts de un usuario específico.
    """
    db = firestore.client()
    try:
        posts = db.collection("posts")\
            .where("user_id", "==", user_id)\
            .order_by("timestamp", direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .offset(offset)\
            .get()

        return [p.to_dict() for p in posts]
    except Exception as e:
        logger.error(f"Error al obtener posts: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener los posts")

@router.post("/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Da like a un post.
    """
    db = firestore.client()
    try:
        post_ref = db.collection("posts").document(post_id)
        post = post_ref.get()
        
        if not post.exists:
            raise HTTPException(status_code=404, detail="Post no encontrado")

        # Verificar si el usuario ya dio like
        like_ref = db.collection("likes").document(f"{post_id}_{current_user['user_id']}")
        if like_ref.get().exists:
            raise HTTPException(status_code=400, detail="Ya has dado like a este post")

        # Crear el like
        like_ref.set({
            "post_id": post_id,
            "user_id": current_user["user_id"],
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        # Incrementar contador de likes
        post_ref.update({"likes": firestore.Increment(1)})
        
        logger.info(f"Like añadido al post {post_id}")
        return {"status": "success", "message": "Like añadido correctamente"}
    except Exception as e:
        logger.error(f"Error al dar like: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al dar like al post")

@router.post("/{post_id}/comment")
async def add_comment(
    post_id: str,
    content: str = Field(..., min_length=1, max_length=500),
    current_user: dict = Depends(get_current_user)
):
    """
    Añade un comentario a un post.
    """
    db = firestore.client()
    try:
        post_ref = db.collection("posts").document(post_id)
        post = post_ref.get()
        
        if not post.exists:
            raise HTTPException(status_code=404, detail="Post no encontrado")

        comment_id = str(uuid.uuid4())
        comment_data = {
            "comment_id": comment_id,
            "post_id": post_id,
            "user_id": current_user["user_id"],
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "created_at": datetime.utcnow().isoformat()
        }

        # Crear el comentario
        db.collection("comments").document(comment_id).set(comment_data)

        # Incrementar contador de comentarios
        post_ref.update({"comments": firestore.Increment(1)})
        
        logger.info(f"Comentario añadido al post {post_id}")
        return {"status": "success", "message": "Comentario añadido correctamente", "comment_id": comment_id}
    except Exception as e:
        logger.error(f"Error al añadir comentario: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al añadir el comentario")

@router.get("/{post_id}/comments")
async def get_comments(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """
    Obtiene los comentarios de un post.
    """
    db = firestore.client()
    try:
        comments = db.collection("comments")\
            .where("post_id", "==", post_id)\
            .order_by("timestamp", direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .offset(offset)\
            .get()

        return [c.to_dict() for c in comments]
    except Exception as e:
        logger.error(f"Error al obtener comentarios: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener los comentarios") 