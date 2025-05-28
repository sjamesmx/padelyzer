from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
from google.cloud import firestore
import os

app = FastAPI()

# Configura logging para ver los eventos en consola y archivo
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("pipeline_hooks")

# Permitir CORS para desarrollo y producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuración de base de datos SQLite ---
DATABASE_URL = "sqlite:///pipeline_events.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class EventLog(Base):
    __tablename__ = "event_logs"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    analysis_id = Column(String, index=True, nullable=True)
    frame = Column(Integer, nullable=True)
    tracks = Column(Text, nullable=True)
    total_frames = Column(Integer, nullable=True)
    payload = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- Configuración de Firestore ---
# Asegúrate de tener GOOGLE_APPLICATION_CREDENTIALS apuntando al JSON de servicio de Firebase
firestore_client = None
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    try:
        firestore_client = firestore.Client()
        logger.info("Firestore inicializado correctamente.")
    except Exception as e:
        logger.error(f"No se pudo inicializar Firestore: {e}")
else:
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS no está configurado. Firestore deshabilitado.")

# --- Función para guardar eventos ---
def save_event(event_type, data):
    # Guardar en SQLite
    db = SessionLocal()
    try:
        analysis_id = data.get("analysis_id")
        frame = data.get("frame")
        tracks = json.dumps(data.get("tracks")) if "tracks" in data else None
        total_frames = data.get("total_frames")
        payload = json.dumps(data)
        event = EventLog(
            event_type=event_type,
            analysis_id=analysis_id,
            frame=frame,
            tracks=tracks,
            total_frames=total_frames,
            payload=payload,
            timestamp=datetime.utcnow()
        )
        db.add(event)
        db.commit()
    except Exception as e:
        logger.error(f"Error guardando evento en DB: {e}")
    finally:
        db.close()
    # Guardar en Firestore
    if firestore_client:
        try:
            doc = {
                "event_type": event_type,
                "analysis_id": data.get("analysis_id"),
                "frame": data.get("frame"),
                "tracks": data.get("tracks"),
                "total_frames": data.get("total_frames"),
                "payload": data,
                "timestamp": datetime.utcnow()
            }
            firestore_client.collection("pipeline_events").add(doc)
        except Exception as e:
            logger.error(f"Error guardando evento en Firestore: {e}")

@app.post("/hook/before_frame")
async def before_frame_hook(request: Request):
    data = await request.json()
    logger.info(f"[HOOK before_frame] {data}")
    save_event("before_frame", data)
    return JSONResponse(content={"status": "ok"})

@app.post("/hook/after_frame")
async def after_frame_hook(request: Request):
    data = await request.json()
    logger.info(f"[HOOK after_frame] {data}")
    save_event("after_frame", data)
    return JSONResponse(content={"status": "ok"})

@app.post("/hook/on_finish")
async def on_finish_hook(request: Request):
    data = await request.json()
    logger.info(f"[HOOK on_finish] {data}")
    save_event("on_finish", data)
    return JSONResponse(content={"status": "ok"})

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    uvicorn.run("pipeline_hooks_api:app", host="0.0.0.0", port=8000, reload=True)

# ---
# Para usar Firestore, instala google-cloud-firestore y configura GOOGLE_APPLICATION_CREDENTIALS con la ruta al JSON de servicio.
# pip install google-cloud-firestore
# export GOOGLE_APPLICATION_CREDENTIALS=/ruta/credenciales.json

# ---
# Para migrar a otra base de datos (PostgreSQL, MySQL, etc.), cambia DATABASE_URL y los argumentos de create_engine.
# Ejemplo PostgreSQL: 'postgresql://usuario:password@localhost/dbname' 