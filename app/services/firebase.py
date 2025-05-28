"""
Servicio para interactuar con Firebase/Firestore.

Este módulo proporciona funciones para interactuar con la base de datos
Firestore de Firebase, incluyendo operaciones CRUD básicas y manejo de
almacenamiento de archivos.
"""
import logging
import os
from typing import Dict, Any, List, Optional, Union, Tuple, BinaryIO
from datetime import datetime
import tempfile
import json

import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from app.config.firebase import initialize_firebase
from app.core.config.firebase import get_firebase_clients

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_firebase_client():
    """
    Obtiene una instancia del cliente de Firestore.

    Returns:
        Cliente de Firestore inicializado

    Raises:
        Exception: Si hay un error al inicializar Firebase
    """
    try:
        # Intentar obtener el cliente de Firestore
        clients = get_firebase_clients()
        return clients['db']
    except Exception as e:
        logger.error(f"Error al obtener cliente de Firebase: {str(e)}")
        raise

def get_storage_client():
    """
    Obtiene una instancia del cliente de Storage.

    Returns:
        Cliente de Storage inicializado
    """
    try:
        app = firebase_admin.get_app()
        bucket = storage.bucket(app=app, name=settings.FIREBASE_STORAGE_BUCKET)
        return bucket
    except Exception as e:
        logger.error(f"Error al obtener cliente de Storage: {str(e)}")
        raise

def create_document(collection: str, document_id: str, data: Dict[str, Any]) -> bool:
    """
    Crea un documento en Firestore.

    Args:
        collection: Nombre de la colección
        document_id: ID del documento
        data: Datos a guardar

    Returns:
        True si la operación fue exitosa
    """
    try:
        db = get_firebase_client()
        db.collection(collection).document(document_id).set(data)
        return True
    except Exception as e:
        logger.error(f"Error al crear documento {document_id} en {collection}: {str(e)}")
        return False

def get_document(collection: str, document_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un documento de Firestore.

    Args:
        collection: Nombre de la colección
        document_id: ID del documento

    Returns:
        Datos del documento o None si no existe
    """
    try:
        db = get_firebase_client()
        doc_ref = db.collection(collection).document(document_id).get()

        if doc_ref.exists:
            return doc_ref.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error al obtener documento {document_id} de {collection}: {str(e)}")
        return None

def update_document(collection: str, document_id: str, data: Dict[str, Any]) -> bool:
    """
    Actualiza un documento en Firestore.

    Args:
        collection: Nombre de la colección
        document_id: ID del documento
        data: Datos a actualizar

    Returns:
        True si la operación fue exitosa
    """
    try:
        db = get_firebase_client()
        db.collection(collection).document(document_id).update(data)
        return True
    except Exception as e:
        logger.error(f"Error al actualizar documento {document_id} en {collection}: {str(e)}")
        return False

def delete_document(collection: str, document_id: str) -> bool:
    """
    Elimina un documento de Firestore.

    Args:
        collection: Nombre de la colección
        document_id: ID del documento

    Returns:
        True si la operación fue exitosa
    """
    try:
        db = get_firebase_client()
        db.collection(collection).document(document_id).delete()
        return True
    except Exception as e:
        logger.error(f"Error al eliminar documento {document_id} de {collection}: {str(e)}")
        return False

def query_collection(
    collection: str,
    filters: Optional[List[tuple]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Consulta documentos en una colección con filtros opcionales.

    Args:
        collection: Nombre de la colección
        filters: Lista de tuplas (campo, operador, valor)
        order_by: Campo para ordenar los resultados
        limit: Número máximo de resultados

    Returns:
        Lista de documentos que coinciden con la consulta
    """
    try:
        db = get_firebase_client()
        query = db.collection(collection)

        # Aplicar filtros si existen
        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)

        # Aplicar orden si existe
        if order_by:
            query = query.order_by(order_by)

        # Aplicar límite si existe
        if limit:
            query = query.limit(limit)

        # Ejecutar consulta
        results = query.get()

        # Convertir resultados a diccionarios
        return [doc.to_dict() for doc in results]
    except Exception as e:
        logger.error(f"Error al consultar colección {collection}: {str(e)}")
        return []

def upload_file(
    file_path: str,
    destination_path: str,
    metadata: Optional[Dict[str, str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Sube un archivo a Firebase Storage.

    Args:
        file_path: Ruta local del archivo
        destination_path: Ruta de destino en Storage
        metadata: Metadatos del archivo (opcional)

    Returns:
        Tupla (éxito, url)
    """
    try:
        bucket = get_storage_client()
        blob = bucket.blob(destination_path)

        # Configurar metadatos si existen
        if metadata:
            blob.metadata = metadata

        # Subir archivo
        blob.upload_from_filename(file_path)

        # Generar URL
        url = blob.public_url

        return True, url
    except Exception as e:
        logger.error(f"Error al subir archivo {file_path} a {destination_path}: {str(e)}")
        return False, None

def upload_file_from_memory(
    file_data: BinaryIO,
    destination_path: str,
    content_type: str = "application/octet-stream",
    metadata: Optional[Dict[str, str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Sube datos binarios a Firebase Storage.

    Args:
        file_data: Datos del archivo en memoria
        destination_path: Ruta de destino en Storage
        content_type: Tipo de contenido MIME
        metadata: Metadatos del archivo (opcional)

    Returns:
        Tupla (éxito, url)
    """
    try:
        bucket = get_storage_client()
        blob = bucket.blob(destination_path)

        # Configurar metadatos si existen
        if metadata:
            blob.metadata = metadata

        # Subir datos
        blob.upload_from_file(
            file_data,
            content_type=content_type
        )

        # Generar URL
        url = blob.public_url

        return True, url
    except Exception as e:
        logger.error(f"Error al subir archivo a {destination_path}: {str(e)}")
        return False, None

def download_file(
    source_path: str,
    destination_path: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Descarga un archivo de Firebase Storage.

    Args:
        source_path: Ruta del archivo en Storage
        destination_path: Ruta local de destino (opcional)

    Returns:
        Tupla (éxito, ruta_local)
    """
    try:
        bucket = get_storage_client()
        blob = bucket.blob(source_path)

        # Si no se proporciona ruta de destino, crear un archivo temporal
        if not destination_path:
            _, extension = os.path.splitext(source_path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp:
                destination_path = temp.name

        # Descargar archivo
        blob.download_to_filename(destination_path)

        return True, destination_path
    except Exception as e:
        logger.error(f"Error al descargar archivo {source_path}: {str(e)}")
        return False, None

def delete_file(source_path: str) -> bool:
    """
    Elimina un archivo de Firebase Storage.

    Args:
        source_path: Ruta del archivo en Storage

    Returns:
        True si la operación fue exitosa
    """
    try:
        bucket = get_storage_client()
        blob = bucket.blob(source_path)
        blob.delete()

        return True
    except Exception as e:
        logger.error(f"Error al eliminar archivo {source_path}: {str(e)}")
        return False

def get_firebase_client() -> firestore.Client:
    """Obtiene una instancia del cliente de Firestore.

    Returns:
        Instancia de Firestore Client

    Raises:
        Exception: Si hay un error al obtener el cliente
    """
    try:
        # Asegurarse de que Firebase está inicializado
        if not firebase_admin._apps:
            initialize_firebase()

        # Retornar el cliente de Firestore
        return firestore.client()
    except Exception as e:
        logger.error(f"Error getting Firestore client: {str(e)}")
        raise

def get_auth_client() -> auth.Client:
    """Obtiene una instancia del cliente de Auth.

    Returns:
        Instancia de Auth Client

    Raises:
        Exception: Si hay un error al obtener el cliente
    """
    try:
        # Asegurarse de que Firebase está inicializado
        if not firebase_admin._apps:
            initialize_firebase()

        # Retornar el cliente de Auth
        return auth.Client(firebase_admin.get_app())
    except Exception as e:
        logger.error(f"Error getting Auth client: {str(e)}")
        raise

def get_storage_client():
    """Obtiene una instancia del cliente de Storage."""
    if not firebase_admin._apps:
        initialize_firebase()
    return storage.bucket()

def get_db():
    """Alias de get_firebase_client() para compatibilidad."""
    return get_firebase_client()

def create_user(user_data: dict) -> Optional[str]:
    """
    Crea un nuevo usuario en Firestore usando el email como ID del documento.
    """
    try:
        db, _ = get_firebase_client()
        users_ref = db.collection('users')

        # Verificar si el email ya existe
        existing_user = get_user_by_email(user_data['email'])
        if existing_user:
            raise ValueError("El email ya está registrado")

        # Crear documento de usuario usando el email como ID
        user_ref = users_ref.document(user_data['email'])

        # Preparar datos del usuario con valores por defecto
        user_data.update({
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True,
            'is_verified': False,
            'fecha_registro': datetime.utcnow(),
            'preferences': {
                'notifications': True,
                'email_notifications': True,
                'language': 'es',
                'timezone': 'UTC'
            },
            'stats': {
                'matches_played': 0,
                'matches_won': 0,
                'total_points': 0
            },
            'achievements': [],
            'blocked_users': [],
            'clubs': [],
            'availability': [],
            'onboarding_status': 'pending'
        })

        user_ref.set(user_data)
        return user_ref.id
    except Exception as e:
        logger.error(f"Error al crear usuario: {str(e)}")
        raise

def get_user_by_email(email: str) -> Optional[dict]:
    """
    Obtiene un usuario por su email.
    """
    try:
        db, _ = get_firebase_client()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        results = query.get()

        if not results:
            return None

        user_doc = results[0]
        user_data = user_doc.to_dict()
        user_data['id'] = user_doc.id
        return user_data
    except Exception as e:
        logger.error(f"Error al obtener usuario por email: {str(e)}")
        return None

def create_user_document(user_data: dict):
    """Crea un documento de usuario en Firestore."""
    db, _ = get_firebase_client()
    user_ref = db.collection('users').document()
    user_data.update({
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'is_active': True,
        'is_verified': False
    })
    user_ref.set(user_data)
    return user_ref.id

def update_user_document(user_id: str, update_data: dict):
    """Actualiza un documento de usuario en Firestore."""
    db, _ = get_firebase_client()
    user_ref = db.collection('users').document(user_id)
    update_data['updated_at'] = datetime.utcnow()
    user_ref.update(update_data)
