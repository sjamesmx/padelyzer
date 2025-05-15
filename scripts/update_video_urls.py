import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.firebase import update_video_urls

if __name__ == "__main__":
    try:
        logger.info("Iniciando actualización de URLs de videos...")
        update_video_urls()
        logger.info("Actualización completada exitosamente")
    except Exception as e:
        logger.error(f"Error durante la actualización: {str(e)}")
        sys.exit(1) 