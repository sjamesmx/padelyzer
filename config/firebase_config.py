import os
from firebase_admin import credentials, initialize_app

def initialize_firebase():
    """Inicializa Firebase con las credenciales apropiadas."""
    try:
        # En producción, usar variables de entorno o archivo de credenciales
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": "padel-iq-test",
            "private_key_id": "test_key_id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----\n",
            "client_email": "test@padel-iq-test.iam.gserviceaccount.com",
            "client_id": "test_client_id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test@padel-iq-test.iam.gserviceaccount.com"
        })
        
        # Inicializar Firebase
        initialize_app(cred)
        print("Firebase inicializado exitosamente")
        
    except Exception as e:
        print(f"Error al inicializar Firebase: {str(e)}")
        raise e 