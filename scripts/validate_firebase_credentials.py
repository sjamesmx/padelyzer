#!/usr/bin/env python3
import json
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseCredentialValidator:
    def __init__(self, cred_path: str):
        self.cred_path = cred_path
        self.required_fields = {
            "type": "service_account",
            "project_id": "pdzr-458820",
            "private_key_id": str,
            "private_key": str,
            "client_email": str,
            "client_id": str,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": str
        }

    def validate_file_exists(self) -> bool:
        """Verifica que el archivo exista y sea accesible."""
        if not os.path.exists(self.cred_path):
            logger.error(f"❌ El archivo no existe en: {self.cred_path}")
            return False
        if not os.access(self.cred_path, os.R_OK):
            logger.error(f"❌ No hay permisos de lectura para: {self.cred_path}")
            return False
        logger.info(f"✅ Archivo encontrado en: {self.cred_path}")
        return True

    def validate_json_format(self) -> bool:
        """Verifica que el archivo sea un JSON válido."""
        try:
            with open(self.cred_path, 'r') as f:
                json.load(f)
            logger.info("✅ Archivo JSON válido")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error en formato JSON: {str(e)}")
            return False

    def validate_required_fields(self, data: Dict[str, Any]) -> bool:
        """Verifica que todos los campos requeridos estén presentes y sean del tipo correcto."""
        missing_fields = []
        invalid_fields = []

        for field, expected_type in self.required_fields.items():
            if field not in data:
                missing_fields.append(field)
                continue

            if isinstance(expected_type, type):
                if not isinstance(data[field], expected_type):
                    invalid_fields.append(f"{field} (tipo incorrecto)")
            elif data[field] != expected_type:
                invalid_fields.append(f"{field} (valor incorrecto)")

        if missing_fields:
            logger.error(f"❌ Campos faltantes: {', '.join(missing_fields)}")
            return False
        if invalid_fields:
            logger.error(f"❌ Campos inválidos: {', '.join(invalid_fields)}")
            return False

        logger.info("✅ Todos los campos requeridos están presentes y son válidos")
        return True

    def validate_private_key_format(self, data: Dict[str, Any]) -> bool:
        """Verifica el formato de la clave privada."""
        private_key = data.get('private_key', '')
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----\\n'):
            logger.error("❌ Formato incorrecto de private_key: debe comenzar con '-----BEGIN PRIVATE KEY-----\\n'")
            return False
        if not private_key.endswith('\\n-----END PRIVATE KEY-----\\n'):
            logger.error("❌ Formato incorrecto de private_key: debe terminar con '\\n-----END PRIVATE KEY-----\\n'")
            return False
        logger.info("✅ Formato de private_key válido")
        return True

    def test_firebase_connection(self) -> bool:
        """Prueba la conexión con Firebase."""
        try:
            # Limpiar cualquier instancia existente
            for app in firebase_admin._apps.values():
                try:
                    firebase_admin.delete_app(app)
                except Exception:
                    pass

            cred = credentials.Certificate(self.cred_path)
            app = firebase_admin.initialize_app(cred)
            db = firestore.client()
            collections = list(db.collections())
            logger.info(f"✅ Conexión exitosa con Firebase. Colecciones encontradas: {len(collections)}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al conectar con Firebase: {str(e)}")
            return False

    def validate(self) -> bool:
        """Ejecuta todas las validaciones."""
        logger.info("🔍 Iniciando validación de credenciales de Firebase...")
        
        if not self.validate_file_exists():
            return False

        try:
            with open(self.cred_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"❌ Error al leer el archivo: {str(e)}")
            return False

        validations = [
            self.validate_json_format(),
            self.validate_required_fields(data),
            self.validate_private_key_format(data),
            self.test_firebase_connection()
        ]

        success = all(validations)
        if success:
            logger.info("✅ Todas las validaciones completadas exitosamente")
        else:
            logger.error("❌ Algunas validaciones fallaron")
        
        return success

def main():
    cred_path = "/Users/dev4/pdzr/backend/config/firebase-credentials.json"
    validator = FirebaseCredentialValidator(cred_path)
    
    if not validator.validate():
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main() 