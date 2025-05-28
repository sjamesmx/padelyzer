from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from google.cloud import firestore
from datetime import datetime

router = APIRouter()

# Firestore client
try:
    db = firestore.Client()
except Exception:
    db = None

# --- USUARIOS ---
@router.get("/users/{user_id}")
def get_user(user_id: str):
    """Obtener detalle de usuario, incluyendo Padel IQ y análisis realizados."""
    if db:
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user_data = user_doc.to_dict()
        # Ejemplo: obtener análisis del usuario
        analyses = [a.to_dict() for a in db.collection('video_analysis').where('user_id', '==', user_id).stream()]
        user_data['analyses'] = analyses
        return user_data
    # Mock
    return {
        "id": user_id,
        "email": "mock@email.com",
        "name": "Mock User",
        "role": "Usuario",
        "status": "Activo",
        "registrationDate": "2024-01-01",
        "lastActivity": "2024-01-10",
        "emailVerified": True,
        "padelIQ": {
            "score": 1200,
            "level": "Intermedio",
            "evolution": [{"date": "2024-01-01", "score": 1100}],
            "metrics": {"precision": 80, "power": 75, "strategy": 85, "consistency": 78}
        },
        "analyses": []
    }

@router.put("/users/{user_id}")
def update_user(user_id: str, data: Dict[str, Any] = Body(...)):
    """Editar usuario."""
    if db:
        user_ref = db.collection('users').document(user_id)
        user_ref.update(data)
        return {"detail": "Usuario actualizado"}
    return {"detail": "Usuario actualizado (mock)"}

@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: str):
    """Resetear contraseña de usuario (mock)."""
    # Aquí deberías integrar con el sistema real de autenticación
    return {"detail": "Contraseña reseteada (mock)"}

@router.post("/users/{user_id}/resend-verification")
def resend_verification(user_id: str):
    """Reenviar verificación de email (mock)."""
    return {"detail": "Verificación reenviada (mock)"}

# --- PIPELINES/ANÁLISIS ---
@router.get("/pipelines/")
def list_pipelines():
    """Listar todos los análisis/pipelines."""
    if db:
        pipelines = [p.to_dict() for p in db.collection('video_analysis').stream()]
        return pipelines
    return [{"id": "AN-001", "user_id": "1", "status": "Completado", "date": "2024-01-20"}]

@router.get("/pipelines/{pipeline_id}")
def get_pipeline(pipeline_id: str):
    """Obtener detalle de un pipeline/análisis."""
    if db:
        ref = db.collection('video_analysis').document(pipeline_id)
        doc = ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Pipeline no encontrado")
        return doc.to_dict()
    return {"id": pipeline_id, "status": "Completado", "steps": ["upload", "process", "done"]}

@router.post("/pipelines/{pipeline_id}/retry")
def retry_pipeline(pipeline_id: str):
    """Reintentar/desatorar pipeline (mock)."""
    return {"detail": f"Pipeline {pipeline_id} reintentado (mock)"}

@router.post("/pipelines/{pipeline_id}/cancel")
def cancel_pipeline(pipeline_id: str):
    """Cancelar pipeline (mock)."""
    return {"detail": f"Pipeline {pipeline_id} cancelado (mock)"}

# --- CONFIGURACIÓN ---
@router.get("/config/")
def get_config():
    """Obtener configuración global del sistema."""
    if db:
        config_ref = db.collection('config').document('global')
        doc = config_ref.get()
        if doc.exists:
            return doc.to_dict()
    return {"detection_threshold": 0.3, "storage_path": "/videos/", "hooks_enabled": True}

@router.put("/config/")
def update_config(data: Dict[str, Any] = Body(...)):
    """Actualizar configuración global."""
    if db:
        config_ref = db.collection('config').document('global')
        config_ref.set(data, merge=True)
        return {"detail": "Configuración actualizada"}
    return {"detail": "Configuración actualizada (mock)"}

@router.get("/config/history")
def config_history():
    """Historial de cambios de configuración (mock)."""
    return [
        {"date": "2024-01-01", "user": "admin", "changes": {"detection_threshold": 0.3}},
        {"date": "2024-01-10", "user": "admin", "changes": {"hooks_enabled": True}}
    ]

# --- AUTENTICACIÓN ---
@router.post("/auth/login")
def login(data: Dict[str, Any] = Body(...)):
    """Login de usuario (mock)."""
    # Aquí deberías integrar con Firebase Auth o tu sistema real
    return {"token": "mock-token", "user_id": "1"}

@router.post("/auth/register")
def register(data: Dict[str, Any] = Body(...)):
    """Registro de usuario (mock)."""
    return {"detail": "Usuario registrado (mock)"}

@router.post("/auth/verify-email")
def verify_email(data: Dict[str, Any] = Body(...)):
    """Verificación de email (mock)."""
    return {"detail": "Email verificado (mock)"}

@router.post("/auth/reset-password")
def auth_reset_password(data: Dict[str, Any] = Body(...)):
    """Reset de contraseña (mock)."""
    return {"detail": "Contraseña reseteada (mock)"} 