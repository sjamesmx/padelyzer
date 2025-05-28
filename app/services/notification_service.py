import logging

logger = logging.getLogger(__name__)

def send_notification(user_id, message):
    """Simula el envío de una notificación push al usuario."""
    # Aquí iría la integración con un servicio de notificaciones (por ejemplo, Firebase Cloud Messaging)
    logger.info(f"Notificación enviada a {user_id}: {message}")
    # Simulación: solo registramos la notificación
    return True