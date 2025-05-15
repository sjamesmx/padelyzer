import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa el cliente de Gmail API."""
        try:
            # Modo mock para desarrollo
            self.client = None
            logger.info("Email service initialized (mock mode)")
        except Exception as e:
            logger.error(f"Error initializing email service: {str(e)}")
            self.client = None

    def send_verification_email(self, email: str, token: str) -> bool:
        """
        Envía un email de verificación.
        Retorna True si el envío fue exitoso, False en caso contrario.
        """
        try:
            if not self.client:
                logger.warning("Email service not initialized, logging token instead")
                logger.info(f"Verification token for {email}: {token}")
                return True

            # TODO: Implementar envío real de email usando Gmail API
            # Por ahora solo simulamos el envío
            logger.info(f"Would send verification email to {email} with token {token}")
            return True

        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False

    def send_password_reset_email(self, email: str, token: str) -> bool:
        """
        Envía un email de recuperación de contraseña.
        Retorna True si el envío fue exitoso, False en caso contrario.
        """
        try:
            if not self.client:
                logger.warning("Email service not initialized, logging token instead")
                logger.info(f"Password reset token for {email}: {token}")
                return True

            # TODO: Implementar envío real de email usando Gmail API
            # Por ahora solo simulamos el envío
            logger.info(f"Would send password reset email to {email} with token {token}")
            return True

        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False

# Singleton instance
email_service = EmailService() 