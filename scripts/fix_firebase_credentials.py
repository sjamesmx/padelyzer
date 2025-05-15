#!/usr/bin/env python3
import json
import os
import sys
import base64
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_private_key_format(private_key: str) -> str:
    """
    Formatea la clave privada para asegurar que tenga el formato correcto.
    
    Args:
        private_key: La clave privada en formato string
        
    Returns:
        str: La clave privada formateada correctamente
    """
    # Eliminar espacios en blanco y saltos de línea
    private_key = private_key.strip()
    
    # Reemplazar \n por saltos de línea reales
    private_key = private_key.replace('\\n', '\n')
    
    # Si la clave no tiene el formato correcto, intentar formatearla
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
        # Si es una clave RSA, convertirla a formato PKCS#8
        if private_key.startswith('-----BEGIN RSA PRIVATE KEY-----'):
            try:
                # Extraer el contenido base64
                key_lines = private_key.split('\n')
                key_content = ''.join(line for line in key_lines if line and not line.startswith('-----'))
                
                # Decodificar y recodificar en formato PKCS#8
                key_bytes = base64.b64decode(key_content)
                private_key = f"-----BEGIN PRIVATE KEY-----\n{base64.b64encode(key_bytes).decode()}\n-----END PRIVATE KEY-----"
            except Exception as e:
                logger.error(f"Error al convertir clave RSA: {str(e)}")
                return private_key
    
    return private_key

def fix_credentials_file(file_path: str) -> bool:
    """
    Verifica y corrige el formato del archivo de credenciales de Firebase.
    
    Args:
        file_path: Ruta al archivo de credenciales
        
    Returns:
        bool: True si el archivo se corrigió exitosamente, False en caso contrario
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            logger.error(f"❌ El archivo no existe: {file_path}")
            return False
            
        # Leer el archivo
        with open(file_path, 'r') as f:
            cred_dict = json.load(f)
            
        # Verificar campos requeridos
        required_fields = {
            "type": "service_account",
            "project_id": str,
            "private_key_id": str,
            "private_key": str,
            "client_email": str,
            "client_id": str,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": str
        }
        
        # Verificar y corregir cada campo
        for field, expected_type in required_fields.items():
            if field not in cred_dict:
                logger.error(f"❌ Campo requerido faltante: {field}")
                return False
                
            if isinstance(expected_type, type):
                if not isinstance(cred_dict[field], expected_type):
                    logger.error(f"❌ Tipo incorrecto para {field}: esperado {expected_type}, recibido {type(cred_dict[field])}")
                    return False
            elif cred_dict[field] != expected_type:
                logger.error(f"❌ Valor incorrecto para {field}: esperado {expected_type}, recibido {cred_dict[field]}")
                return False
                
        # Corregir formato de la clave privada
        if 'private_key' in cred_dict:
            cred_dict['private_key'] = fix_private_key_format(cred_dict['private_key'])
            
        # Crear backup del archivo original
        backup_path = f"{file_path}.bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(file_path, backup_path)
        
        # Guardar el archivo corregido
        with open(file_path, 'w') as f:
            json.dump(cred_dict, f, indent=2)
            
        logger.info(f"✅ Archivo corregido y guardado. Backup creado en: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al procesar el archivo: {str(e)}")
        return False

def main():
    """Función principal."""
    cred_path = "/Users/dev4/pdzr/backend/config/firebase-credentials.json"
    
    logger.info("🔍 Iniciando verificación y corrección del archivo de credenciales...")
    
    if fix_credentials_file(cred_path):
        logger.info("✅ Proceso completado exitosamente")
        sys.exit(0)
    else:
        logger.error("❌ El proceso falló")
        sys.exit(1)

if __name__ == "__main__":
    main() 