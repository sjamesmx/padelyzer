import cv2
import numpy as np
import mediapipe as mp
from collections import defaultdict
from app.pipeline.padel_pipeline import PadelAnalysisPipeline

# --- Configuración de entrada ---
VIDEO_PATH = '/Users/ja/padelyzer/videos/lety2.MOV'
OUTPUT_PATH = 'lety2_golpes_analizados.mp4'

# --- Inicialización de MediaPipe Pose ---
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# --- Funciones auxiliares ---
def calcular_angulo(p1, p2, p3):
    a = np.array(p1) - np.array(p2)
    b = np.array(p3) - np.array(p2)
    cos_angle = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-6)
    angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
    return np.degrees(angle)

def extraer_keypoints(results):
    if not results.pose_landmarks:
        return None
    puntos = {}
    for idx, lm in enumerate(results.pose_landmarks.landmark):
        puntos[idx] = (lm.x, lm.y)
    # Mapea nombres a índices de MediaPipe
    return {
        'hombro_izq': puntos.get(11),
        'hombro_der': puntos.get(12),
        'codo_izq': puntos.get(13),
        'codo_der': puntos.get(14),
        'muñeca_izq': puntos.get(15),
        'muñeca_der': puntos.get(16),
        'cadera_izq': puntos.get(23),
        'cadera_der': puntos.get(24),
        'rodilla_izq': puntos.get(25),
        'rodilla_der': puntos.get(26),
        'tobillo_izq': puntos.get(27),
        'tobillo_der': puntos.get(28),
    }

def clasificar_golpe(keypoints):
    if not keypoints:
        return "Desconocido"
    # Ejemplo simple: solo derecha y revés, puedes expandir
    # Asume jugador diestro (puedes mejorar esto)
    try:
        angulo_codo_der = calcular_angulo(keypoints['hombro_der'], keypoints['codo_der'], keypoints['muñeca_der'])
        angulo_codo_izq = calcular_angulo(keypoints['hombro_izq'], keypoints['codo_izq'], keypoints['muñeca_izq'])
        # Rotación torso: ángulo entre línea hombros y línea caderas
        hombros = np.array(keypoints['hombro_der']) - np.array(keypoints['hombro_izq'])
        caderas = np.array(keypoints['cadera_der']) - np.array(keypoints['cadera_izq'])
        torso_angle = calcular_angulo(keypoints['hombro_izq'], keypoints['hombro_der'], keypoints['cadera_der'])
        # Heurísticas básicas (puedes expandirlas)
        if 90 <= angulo_codo_der <= 150 and 30 <= torso_angle <= 60:
            return "Derecha"
        elif 30 <= angulo_codo_der <= 90 and 90 <= torso_angle <= 120:
            return "Revés"
        elif angulo_codo_der > 150 and keypoints['muñeca_izq'] and keypoints['muñeca_der'] and abs(keypoints['muñeca_izq'][1] - keypoints['muñeca_der'][1]) > 0.2:
            return "Saque"
        # Puedes agregar más reglas para volea, globo, bandeja, smash...
    except Exception:
        return "Desconocido"
    return "Desconocido"

# --- Inicialización de tus modelos (debes adaptar esto a tu código real) ---
# from app.detectors.yolo_detector import YOLODetector
# from app.trackers.deepsort_tracker import DeepSortTracker
# yolo = YOLODetector(...)
# deepsort = DeepSortTracker(...)
# mediapipe_pose = ...
# pipeline = PadelAnalysisPipeline(yolo, deepsort, mediapipe_pose)
#
# Para este script, usaremos solo MediaPipe para la pose y detección de jugadores con bounding boxes

# --- Procesamiento del vídeo ---
cap = cv2.VideoCapture(VIDEO_PATH)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS) or 25
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (width, height))

frame_count = 0
golpes_por_jugador = defaultdict(lambda: defaultdict(int))

print("Procesando vídeo para análisis de golpes...")
while True:
    ret, frame = cap.read()
    if not ret:
        break
    # --- Detección de jugadores (aquí deberías usar tu detector real, aquí solo un bbox grande de ejemplo) ---
    # Suponiendo que tienes una lista de detecciones: [{'bbox': (x1, y1, x2, y2), 'id': id_jugador}]
    # Aquí solo un jugador ficticio para demo:
    detecciones = [{'bbox': (int(width*0.3), int(height*0.2), int(width*0.7), int(height*0.9)), 'id': 1}]
    for det in detecciones:
        x1, y1, x2, y2 = det['bbox']
        jugador_id = det['id']
        jugador_frame = frame[y1:y2, x1:x2]
        # --- Estimación de pose ---
        jugador_rgb = cv2.cvtColor(jugador_frame, cv2.COLOR_BGR2RGB)
        results = pose.process(jugador_rgb)
        keypoints = extraer_keypoints(results)
        golpe = clasificar_golpe(keypoints)
        golpes_por_jugador[jugador_id][golpe] += 1
        # Dibuja bbox y etiqueta
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.putText(frame, f"Jugador {jugador_id}: {golpe}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
    out.write(frame)
    frame_count += 1
    if frame_count % 20 == 0:
        print(f"Frame {frame_count} procesado...")

cap.release()
out.release()

print("\n--- Estadísticas de golpes por jugador ---")
for jugador_id, golpes in golpes_por_jugador.items():
    print(f"Jugador {jugador_id}:")
    for tipo, cantidad in golpes.items():
        print(f"  {tipo}: {cantidad}")
print(f"\nVídeo de salida guardado en: {OUTPUT_PATH}") 