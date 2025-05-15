import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Cargar credenciales desde variable de entorno o ruta por defecto
cred_path = os.getenv("FIREBASE_CRED_PATH", "../firebase-service-account.json")
cred = credentials.Certificate(cred_path)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Poblar users
users = [
    {
        "user_id": "test_user_1",
        "email": "ana.padel@example.com",
        "name": "Ana Pádel",
        "level": "intermediate",
        "padel_iq": 72.5,
        "clubs": ["Padel Pro", "Club Central"],
        "availability": ["Lunes 18:00-20:00", "Miércoles 20:00-22:00"],
        "location": {"latitude": 40.4168, "longitude": -3.7038},
        "onboarding_status": "completed",
        "created_at": datetime.utcnow(),
        "ultimo_analisis": "analysis_1",
        "tipo_ultimo_analisis": "entrenamiento",
        "fecha_ultimo_analisis": datetime.utcnow()
    },
    {
        "user_id": "test_user_2",
        "email": "carlos.padel@example.com",
        "name": "Carlos Pádel",
        "level": "advanced",
        "padel_iq": 85.0,
        "clubs": ["Padel Pro"],
        "availability": ["Martes 19:00-21:00", "Jueves 18:00-20:00"],
        "location": {"latitude": 40.418, "longitude": -3.702},
        "onboarding_status": "completed",
        "created_at": datetime.utcnow(),
        "ultimo_analisis": "analysis_2",
        "tipo_ultimo_analisis": "juego",
        "fecha_ultimo_analisis": datetime.utcnow()
    }
]
for user in users:
    db.collection("users").document(user["user_id"]).set(user)

# Poblar friendships
friendship = {
    "friendship_id": "friendship_1",
    "user_id_1": "test_user_1",
    "user_id_2": "test_user_2",
    "status": "accepted",
    "timestamp": datetime.utcnow(),
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}
db.collection("friendships").document(friendship["friendship_id"]).set(friendship)

# Poblar match_requests
match_request = {
    "from_user_id": "test_user_1",
    "to_user_id": "test_user_2",
    "club": "Padel Pro",
    "schedule": "Viernes 19:00-21:00",
    "status": "pending",
    "timestamp": datetime.utcnow()
}
db.collection("match_requests").add(match_request)

# Poblar video_analisis
video_analysis = {
    "analysis_id": "analysis_1",
    "user_id": "test_user_1",
    "video_url": "https://firebasestorage.googleapis.com/v0/b/pdzr-458820.firebasestorage.app/o/lety.mp4?alt=media&token=4e7c5d33-423b-4d0d-8b6f-5699d6604296",
    "tipo_video": "entrenamiento",
    "fecha_analisis": datetime.utcnow(),
    "estado": "completado",
    "resultados": {
        "padel_iq": 72.5,
        "tecnica": 80,
        "ritmo": 75,
        "fuerza": 70,
        "court_coverage": 60.0
    }
}
db.collection("video_analisis").document(video_analysis["analysis_id"]).set(video_analysis)

video_analysis2 = {
    "analysis_id": "analysis_2",
    "user_id": "test_user_2",
    "video_url": "https://firebasestorage.googleapis.com/v0/b/pdzr-458820.firebasestorage.app/o/4.mp4?alt=media&token=460485d2-1e6c-4aca-a013-b5d2dd14bde4",
    "tipo_video": "juego",
    "fecha_analisis": datetime.utcnow(),
    "estado": "completado",
    "resultados": {
        "padel_iq": 85.0,
        "tecnica": 90,
        "ritmo": 80,
        "fuerza": 85,
        "court_coverage": 70.0
    }
}
db.collection("video_analisis").document(video_analysis2["analysis_id"]).set(video_analysis2)

print("Datos de ejemplo insertados correctamente en Firestore.") 