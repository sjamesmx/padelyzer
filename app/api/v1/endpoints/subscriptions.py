from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import firestore
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from typing import Optional
import uuid
import logging

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

# Listar planes disponibles
@router.get("/plans")
async def get_plans():
    # Simulación de planes
    plans = [
        {"plan_id": "free", "name": "Gratis", "price": 0, "features": ["Básico"]},
        {"plan_id": "pro", "name": "Pro", "price": 9.99, "features": ["Análisis avanzado", "Sin anuncios"]},
        {"plan_id": "elite", "name": "Elite", "price": 19.99, "features": ["Todo Pro", "Soporte prioritario"]}
    ]
    return plans

# Crear suscripción
@router.post("/create")
async def create_subscription(plan_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    subscription_id = str(uuid.uuid4())
    subscription_data = {
        "subscription_id": subscription_id,
        "user_id": current_user.id,
        "plan_id": plan_id,
        "status": "active",
        "created_at": firestore.SERVER_TIMESTAMP
    }
    db.collection("subscriptions").document(subscription_id).set(subscription_data)
    # Notificación automática
    notif_id = str(uuid.uuid4())
    db.collection("notifications").document(notif_id).set({
        "notification_id": notif_id,
        "user_id": current_user.id,
        "type": "subscription_created",
        "subscription_id": subscription_id,
        "plan_id": plan_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "read": False
    })
    return {"message": "Suscripción creada", "subscription_id": subscription_id}

# Cancelar suscripción
@router.delete("/{subscription_id}")
async def cancel_subscription(subscription_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    sub = db.collection("subscriptions").document(subscription_id).get()
    if not sub.exists:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    sub_data = sub.to_dict()
    if sub_data["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para cancelar esta suscripción")
    db.collection("subscriptions").document(subscription_id).update({"status": "cancelled"})
    # Notificación automática
    notif_id = str(uuid.uuid4())
    db.collection("notifications").document(notif_id).set({
        "notification_id": notif_id,
        "user_id": current_user.id,
        "type": "subscription_cancelled",
        "subscription_id": subscription_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "read": False
    })
    return {"message": "Suscripción cancelada"}

# Actualizar suscripción
@router.put("/{subscription_id}")
async def update_subscription(subscription_id: str, plan_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    sub = db.collection("subscriptions").document(subscription_id).get()
    if not sub.exists:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    sub_data = sub.to_dict()
    if sub_data["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para actualizar esta suscripción")
    db.collection("subscriptions").document(subscription_id).update({"plan_id": plan_id, "updated_at": firestore.SERVER_TIMESTAMP})
    # Notificación automática
    notif_id = str(uuid.uuid4())
    db.collection("notifications").document(notif_id).set({
        "notification_id": notif_id,
        "user_id": current_user.id,
        "type": "subscription_updated",
        "subscription_id": subscription_id,
        "plan_id": plan_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "read": False
    })
    return {"message": "Suscripción actualizada"}

# Consultar estado de suscripción
@router.get("/{subscription_id}")
async def get_subscription(subscription_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    sub = db.collection("subscriptions").document(subscription_id).get()
    if not sub.exists:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    sub_data = sub.to_dict()
    if sub_data["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta suscripción")
    return sub_data

# Simular pago de suscripción (preparado para Stripe)
@router.post("/pay")
async def pay_subscription(subscription_id: str, stripe_payment_intent_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    sub = db.collection("subscriptions").document(subscription_id).get()
    if not sub.exists:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    sub_data = sub.to_dict()
    if sub_data["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para pagar esta suscripción")
    # Aquí iría la integración real con Stripe:
    # 1. Consultar el estado del PaymentIntent con la API de Stripe
    # 2. Verificar que el pago fue exitoso
    # 3. Actualizar la suscripción y registrar el pago
    # Por ahora, solo simula el pago exitoso
    db.collection("subscriptions").document(subscription_id).update({
        "last_payment_intent_id": stripe_payment_intent_id,
        "last_payment_at": firestore.SERVER_TIMESTAMP
    })
    # Notificación automática
    notif_id = str(uuid.uuid4())
    db.collection("notifications").document(notif_id).set({
        "notification_id": notif_id,
        "user_id": current_user.id,
        "type": "subscription_paid",
        "subscription_id": subscription_id,
        "payment_intent_id": stripe_payment_intent_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "read": False
    })
    return {"message": "Pago procesado (Stripe simulado)", "payment_intent_id": stripe_payment_intent_id}

@router.get("/{user_id}")
async def get_user_subscriptions(user_id: str):
    raise HTTPException(status_code=501, detail="Not Implemented")

@router.post("/{user_id}/subscribe")
async def subscribe_user(user_id: str):
    raise HTTPException(status_code=501, detail="Not Implemented") 