#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path

# Añadir el directorio raíz al path para poder importar los módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from app.config.firebase import initialize_firebase, validate_credentials
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_credentials_file():
    """Prueba la validación del archivo de credenciales."""
    cred_path = "/Users/dev4/pdzr/backend/config/firebase-credentials.json"
    
    if not os.path.exists(cred_path):
        logger.error(f"❌ El archivo de credenciales no existe en: {cred_path}")
        return False
        
    try:
        with open(cred_path, 'r') as f:
            cred_dict = json.load(f)
            
        if validate_credentials(cred_dict):
            logger.info("✅ Archivo de credenciales válido")
            return True
        else:
            logger.error("❌ Archivo de credenciales inválido")
            return False
    except Exception as e:
        logger.error(f"❌ Error al validar archivo de credenciales: {str(e)}")
        return False

def test_firebase_initialization():
    """Prueba la inicialización de Firebase."""
    try:
        app = initialize_firebase(max_retries=3, retry_delay=2)
        if app:
            logger.info("✅ Firebase inicializado correctamente")
            return True
        else:
            logger.error("❌ Firebase no se pudo inicializar")
            return False
    except Exception as e:
        logger.error(f"❌ Error al inicializar Firebase: {str(e)}")
        return False

def main():
    """Función principal que ejecuta todas las pruebas."""
    logger.info("🔍 Iniciando pruebas de Firebase...")
    
    # Probar archivo de credenciales
    if not test_credentials_file():
        logger.error("❌ Prueba de archivo de credenciales falló")
        sys.exit(1)
        
    # Probar inicialización de Firebase
    if not test_firebase_initialization():
        logger.error("❌ Prueba de inicialización de Firebase falló")
        sys.exit(1)
        
    logger.info("✅ Todas las pruebas completadas exitosamente")
    sys.exit(0)

if __name__ == "__main__":
    main() 