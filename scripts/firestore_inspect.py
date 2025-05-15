import os
import firebase_admin
from firebase_admin import credentials, firestore

# Cargar credenciales desde variable de entorno o ruta por defecto
cred_path = os.getenv("FIREBASE_CRED_PATH", "../firebase-service-account.json")
cred = credentials.Certificate(cred_path)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

collections = ["users", "friendships", "match_requests", "video_analisis"]

for collection_name in collections:
    print(f"--- {collection_name} ---")
    docs = db.collection(collection_name).limit(5).stream()
    for doc in docs:
        print(f"Doc ID: {doc.id}")
        print(doc.to_dict())
    print() 