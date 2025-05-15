from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from firebase_admin import firestore
from typing import List, Optional
import logging
from datetime import datetime
from .auth import get_current_user
import uuid

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])

class Subscription(BaseModel):
    user_id: str
    plan_id: str
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    auto_renew: bool = True
    payment_method: Optional[str]
    price: float
    currency: str = "EUR"

class SubscriptionResponse(BaseModel):
    subscription_id: str
    user_id: str
    plan_id: str
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    auto_renew: bool
    payment_method: Optional[str]
    price: float
    currency: str
    features: List[str]

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.get("/{user_id}", response_model=List[SubscriptionResponse])
async def get_subscriptions(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_db)
):
    """
    Obtiene las suscripciones activas de un usuario.
    """
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para ver suscripciones de otro usuario")

    try:
        logger.info("Obteniendo información de suscripciones")
        subscriptions = db.collection("subscriptions")\
            .where("user_id", "==", user_id)\
            .where("status", "in", ["active", "trial"])\
            .get()

        return [s.to_dict() for s in subscriptions]
    except Exception as e:
        logger.error(f"Error al obtener suscripciones: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener suscripciones")

@router.post("/{user_id}/subscribe")
async def create_subscription(
    user_id: str,
    plan_id: str = Field(..., description="ID del plan de suscripción"),
    payment_method: str = Field(..., description="Método de pago"),
    auto_renew: bool = True,
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_db)
):
    """
    Crea una nueva suscripción para un usuario.
    """
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para crear suscripciones en nombre de otro usuario")

    try:
        # Verificar si el plan existe
        plan = db.collection("subscription_plans").document(plan_id).get()
        if not plan.exists:
            raise HTTPException(status_code=404, detail="Plan de suscripción no encontrado")

        plan_data = plan.to_dict()
        
        # Verificar si ya tiene una suscripción activa
        active_subscriptions = db.collection("subscriptions")\
            .where("user_id", "==", user_id)\
            .where("status", "==", "active")\
            .get()

        if active_subscriptions:
            raise HTTPException(status_code=400, detail="Usuario ya tiene una suscripción activa")

        # Crear la suscripción
        subscription_id = str(uuid.uuid4())
        subscription_data = {
            "subscription_id": subscription_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "status": "active",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": None if auto_renew else calculate_end_date(plan_data["duration"]),
            "auto_renew": auto_renew,
            "payment_method": payment_method,
            "price": plan_data["price"],
            "currency": plan_data["currency"],
            "features": plan_data["features"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        db.collection("subscriptions").document(subscription_id).set(subscription_data)
        
        # Registrar la transacción
        transaction_id = str(uuid.uuid4())
        db.collection("subscription_transactions").document(transaction_id).set({
            "subscription_id": subscription_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "amount": plan_data["price"],
            "currency": plan_data["currency"],
            "status": "completed",
            "payment_method": payment_method,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        logger.info(f"Suscripción creada: {subscription_id}")
        return subscription_data
    except Exception as e:
        logger.error(f"Error al crear suscripción: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear la suscripción")

@router.post("/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_db)
):
    """
    Cancela una suscripción activa.
    """
    try:
        subscription = db.collection("subscriptions").document(subscription_id).get()
        
        if not subscription.exists:
            raise HTTPException(status_code=404, detail="Suscripción no encontrada")

        subscription_data = subscription.to_dict()
        if subscription_data["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="No autorizado para cancelar esta suscripción")

        if subscription_data["status"] != "active":
            raise HTTPException(status_code=400, detail="La suscripción no está activa")

        # Actualizar la suscripción
        update_data = {
            "status": "cancelled",
            "auto_renew": False,
            "end_date": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        db.collection("subscriptions").document(subscription_id).update(update_data)
        
        logger.info(f"Suscripción cancelada: {subscription_id}")
        return {"status": "success", "message": "Suscripción cancelada correctamente"}
    except Exception as e:
        logger.error(f"Error al cancelar suscripción: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al cancelar la suscripción")

@router.get("/plans")
async def get_subscription_plans(db: firestore.Client = Depends(get_db)):
    """
    Obtiene los planes de suscripción disponibles.
    """
    try:
        plans = db.collection("subscription_plans").get()
        return [p.to_dict() for p in plans]
    except Exception as e:
        logger.error(f"Error al obtener planes de suscripción: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener planes de suscripción")

def calculate_end_date(duration_months: int) -> str:
    """Calcula la fecha de finalización de una suscripción."""
    from dateutil.relativedelta import relativedelta
    end_date = datetime.utcnow() + relativedelta(months=duration_months)
    return end_date.isoformat() 