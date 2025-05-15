from fastapi import APIRouter, HTTPException, Depends, status
from firebase_admin import firestore
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from typing import List, Dict, Optional
import uuid
import logging
from datetime import datetime
from app.services.notifications import notification_service

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ONBOARDING_STEPS = [
    {
        "step_id": "profile",
        "name": "Completar perfil",
        "description": "Agrega tu información básica.",
        "required": True,
        "order": 1
    },
    {
        "step_id": "preferences",
        "name": "Preferencias",
        "description": "Selecciona tus preferencias de juego.",
        "required": True,
        "order": 2
    },
    {
        "step_id": "tutorial",
        "name": "Tutorial",
        "description": "Aprende a usar la plataforma.",
        "required": False,
        "order": 3
    }
]

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.post("/", response_model=dict, summary="Completar onboarding", tags=["onboarding"])
async def complete_onboarding(current_user: UserInDB = Depends(get_current_user)):
    """
    Completa el proceso de onboarding.
    - Verifica que todos los pasos requeridos estén completos.
    - Actualiza el estado del usuario.
    - Envía notificación de bienvenida.
    """
    try:
        db = get_db()
        
        # Verificar progreso actual
        doc = db.collection("onboarding").document(current_user.id).get()
        if doc.exists:
            data = doc.to_dict()
            if data.get("completed", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El onboarding ya está completado"
                )
        
        # Verificar pasos requeridos
        required_steps = [step["step_id"] for step in ONBOARDING_STEPS if step["required"]]
        steps = data.get("steps", {}) if doc.exists else {}
        
        missing_steps = [step for step in required_steps if not steps.get(step, False)]
        if missing_steps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Faltan pasos requeridos: {', '.join(missing_steps)}"
            )
        
        # Actualizar estado
        onboarding_data = {
            "user_id": current_user.id,
            "completed": True,
            "steps": steps,
            "completed_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        db.collection("onboarding").document(current_user.id).set(onboarding_data)
        
        # Actualizar estado del usuario
        db.collection("users").document(current_user.id).update({
            "onboarding_completed": True,
            "onboarding_completed_at": datetime.now()
        })
        
        # Enviar notificación de bienvenida
        notification_service.create_notification(
            user_id=current_user.id,
            type="onboarding_completed",
            title="¡Bienvenido a Padelyzer!",
            message="Has completado el onboarding. ¡Comienza a disfrutar de todas las funcionalidades!",
            data={"onboarding_completed": True}
        )
        
        return {
            "message": "Onboarding completado exitosamente",
            "completed_at": onboarding_data["completed_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al completar onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al completar onboarding"
        )

# Estado de onboarding
@router.get("/status/{user_id}", response_model=dict, summary="Obtener estado de onboarding", tags=["onboarding"])
async def get_onboarding_status(user_id: str):
    """
    Obtiene el estado detallado del onboarding de un usuario.
    - Incluye información de cada paso.
    - Muestra progreso general.
    """
    try:
        db = get_db()
        
        # Obtener datos de onboarding
        doc = db.collection("onboarding").document(user_id).get()
        if not doc.exists:
            return {
                "user_id": user_id,
                "completed": False,
                "steps": {step["step_id"]: False for step in ONBOARDING_STEPS},
                "progress_percent": 0,
                "started_at": None,
                "completed_at": None,
                "last_updated": None
            }
            
        data = doc.to_dict()
        steps = data.get("steps", {step["step_id"]: False for step in ONBOARDING_STEPS})
        
        # Calcular progreso
        total_steps = len(ONBOARDING_STEPS)
        completed_steps = sum(1 for v in steps.values() if v)
        progress = int((completed_steps / total_steps) * 100) if total_steps else 0
        
        # Enriquecer información de pasos
        enriched_steps = []
        for step in ONBOARDING_STEPS:
            step_data = {
                **step,
                "completed": steps.get(step["step_id"], False),
                "completed_at": data.get(f"{step['step_id']}_completed_at")
            }
            enriched_steps.append(step_data)
            
        # Ordenar pasos
        enriched_steps.sort(key=lambda x: x["order"])
        
        return {
            "user_id": user_id,
            "completed": data.get("completed", False),
            "steps": enriched_steps,
            "progress_percent": progress,
            "started_at": data.get("started_at"),
            "completed_at": data.get("completed_at"),
            "last_updated": data.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estado de onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estado de onboarding"
        )

# Listar pasos del onboarding
@router.get("/steps")
async def get_onboarding_steps():
    return ONBOARDING_STEPS

# Actualizar un paso específico
@router.put("/step/{step_id}", response_model=dict, summary="Actualizar paso de onboarding", tags=["onboarding"])
async def update_onboarding_step(
    step_id: str,
    completed: bool,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Actualiza el estado de un paso específico del onboarding.
    - Valida el paso y su orden.
    - Actualiza el progreso.
    - Envía notificaciones de progreso.
    """
    try:
        db = get_db()
        
        # Validar paso
        step_info = next((step for step in ONBOARDING_STEPS if step["step_id"] == step_id), None)
        if not step_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paso no válido"
            )
            
        # Obtener progreso actual
        doc_ref = db.collection("onboarding").document(current_user.id)
        doc = doc_ref.get()
        
        if not doc.exists:
            # Inicializar progreso
            steps = {step["step_id"]: False for step in ONBOARDING_STEPS}
            started_at = datetime.now()
        else:
            data = doc.to_dict()
            steps = data.get("steps", {step["step_id"]: False for step in ONBOARDING_STEPS})
            started_at = data.get("started_at", datetime.now())
            
        # Validar orden de pasos
        if completed:
            previous_steps = [step for step in ONBOARDING_STEPS if step["order"] < step_info["order"]]
            for prev_step in previous_steps:
                if not steps.get(prev_step["step_id"], False):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Debes completar el paso '{prev_step['name']}' primero"
                    )
                    
        # Actualizar paso
        steps[step_id] = completed
        update_data = {
            "steps": steps,
            "updated_at": datetime.now()
        }
        
        if completed:
            update_data[f"{step_id}_completed_at"] = datetime.now()
            
        # Verificar si todos los pasos requeridos están completos
        required_steps = [step["step_id"] for step in ONBOARDING_STEPS if step["required"]]
        all_required_completed = all(steps.get(step, False) for step in required_steps)
        
        if all_required_completed:
            update_data["completed"] = True
            update_data["completed_at"] = datetime.now()
            
            # Actualizar estado del usuario
            db.collection("users").document(current_user.id).update({
                "onboarding_completed": True,
                "onboarding_completed_at": datetime.now()
            })
            
            # Notificar completado
            notification_service.create_notification(
                user_id=current_user.id,
                type="onboarding_completed",
                title="¡Onboarding completado!",
                message="Has completado todos los pasos requeridos del onboarding.",
                data={"onboarding_completed": True}
            )
        else:
            # Notificar progreso
            completed_steps = sum(1 for v in steps.values() if v)
            total_steps = len(ONBOARDING_STEPS)
            progress = int((completed_steps / total_steps) * 100)
            
            if progress % 25 == 0:  # Notificar cada 25% de progreso
                notification_service.create_notification(
                    user_id=current_user.id,
                    type="onboarding_progress",
                    title="Progreso en el onboarding",
                    message=f"Has completado el {progress}% del onboarding.",
                    data={"progress": progress}
                )
                
        # Guardar actualización
        doc_ref.set(update_data, merge=True)
        
        return {
            "message": f"Paso '{step_info['name']}' actualizado",
            "completed": all_required_completed,
            "progress_percent": int((sum(1 for v in steps.values() if v) / len(ONBOARDING_STEPS)) * 100)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar paso de onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar paso de onboarding"
        )

# Progreso detallado
@router.get("/progress/{user_id}")
async def get_onboarding_progress(user_id: str):
    db = get_db()
    doc = db.collection("onboarding").document(user_id).get()
    if not doc.exists:
        steps = {step["step_id"]: False for step in ONBOARDING_STEPS}
        completed = False
    else:
        data = doc.to_dict()
        steps = data.get("steps", {step["step_id"]: False for step in ONBOARDING_STEPS})
        completed = data.get("completed", False)
    total = len(ONBOARDING_STEPS)
    done = sum(1 for v in steps.values() if v)
    progress = int((done / total) * 100) if total else 0
    return {
        "user_id": user_id,
        "steps": steps,
        "completed": completed,
        "progress_percent": progress
    }

@router.post("/skip", response_model=dict, summary="Saltar onboarding", tags=["onboarding"])
async def skip_onboarding(current_user: UserInDB = Depends(get_current_user)):
    """
    Salta el proceso de onboarding.
    - Marca todos los pasos como completados.
    - Actualiza el estado del usuario.
    - Envía notificación.
    """
    try:
        db = get_db()
        
        # Verificar si ya está completado
        doc = db.collection("onboarding").document(current_user.id).get()
        if doc.exists:
            data = doc.to_dict()
            if data.get("completed", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El onboarding ya está completado"
                )
                
        # Marcar todos los pasos como completados
        steps = {step["step_id"]: True for step in ONBOARDING_STEPS}
        now = datetime.now()
        
        onboarding_data = {
            "user_id": current_user.id,
            "completed": True,
            "steps": steps,
            "skipped": True,
            "skipped_at": now,
            "completed_at": now,
            "updated_at": now
        }
        
        # Guardar en Firestore
        db.collection("onboarding").document(current_user.id).set(onboarding_data)
        
        # Actualizar estado del usuario
        db.collection("users").document(current_user.id).update({
            "onboarding_completed": True,
            "onboarding_completed_at": now,
            "onboarding_skipped": True
        })
        
        # Notificar
        notification_service.create_notification(
            user_id=current_user.id,
            type="onboarding_skipped",
            title="Onboarding saltado",
            message="Has saltado el proceso de onboarding. Puedes completarlo más tarde desde tu perfil.",
            data={"onboarding_skipped": True}
        )
        
        return {
            "message": "Onboarding saltado exitosamente",
            "skipped_at": now
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al saltar onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al saltar onboarding"
        ) 