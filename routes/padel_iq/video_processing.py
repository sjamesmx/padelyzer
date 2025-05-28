import logging
import cv2
import numpy as np
import requests
import os
import mediapipe as mp
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from .utils import calculate_angle
from .player_metrics import assign_player_positions, calculate_metrics_for_non_striking_players, interpolate_elbow_angle
from .procesar_videos_entrenamiento import analizar_segmento
from datetime import datetime
import torch

# Configurar logging con formato detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Permitir los globals necesarios para YOLO
from ultralytics.nn.tasks import DetectionModel
import torch
import torch.nn as nn
import ultralytics
import torch.serialization
torch.serialization.add_safe_globals([DetectionModel, nn.Sequential])

# Inicializar MediaPipe Pose con umbrales ajustados
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def enhance_image(image):
    """Mejora el contraste y la nitidez de la imagen para mejorar la detección de MediaPipe."""
    try:
        if image is None or image.size == 0:
            logger.warning("Imagen vacía o inválida recibida en enhance_image")
            return None
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        enhanced = cv2.equalizeHist(gray)
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        return enhanced_rgb
    except Exception as e:
        logger.error(f"Error en enhance_image: {str(e)}")
        return None

def detect_game_transitions(video_path, fps, total_frames):
    """Detecta transiciones entre juegos basadas en cambios en el color de la cancha y el contexto."""
    if not os.path.exists(video_path):
        logger.error(f"El archivo de video no existe: {video_path}")
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"No se pudo abrir el video para detectar transiciones: {video_path}")
        return []

    prev_hist = None
    transition_points = []
    frame_count = 0
    hist_change_threshold = 0.5

    logger.info(f"Procesando video para transiciones: {video_path}, total frames: {total_frames}")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        try:
            frame = cv2.resize(frame, (640, 480))
            current_time = frame_count / fps

            roi = frame[240:480, :]
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

            if prev_hist is not None:
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                if diff < hist_change_threshold:
                    logger.debug(f"Transición detectada en tiempo: {current_time:.2f}s, diff: {diff:.2f}")
                    transition_points.append(current_time)

            prev_hist = hist
            frame_count += 1
        except Exception as e:
            logger.error(f"Error procesando fotograma {frame_count}: {str(e)}")
            continue

    cap.release()
    logger.info(f"Transiciones detectadas: {len(transition_points)} puntos")
    return transition_points

def segmentar_video_entrenamiento(ruta_video, custom_params=None):
    """Segmenta un video de entrenamiento en partes donde ocurren los golpes."""
    if custom_params is None:
        custom_params = {
            'velocidad_umbral': 0.00005,
            'max_segment_duration': 1.5,
            'frame_skip': 12,
            'scale_factor': 0.8
        }

    velocidad_umbral = custom_params['velocidad_umbral']
    max_segment_duration = custom_params['max_segment_duration']
    frame_skip = custom_params['frame_skip']
    scale_factor = custom_params['scale_factor']

    if not os.path.exists(ruta_video):
        logger.error(f"El archivo de video no existe: {ruta_video}")
        raise ValueError(f"El archivo de video no existe: {ruta_video}")

    logger.info(f"Segmentando video de entrenamiento: {ruta_video}")
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        logger.error(f"No se pudo abrir el video: {ruta_video}")
        raise ValueError(f"No se pudo abrir el video: {ruta_video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        logger.warning("FPS no válido, usando valor por defecto: 30")
        fps = 30

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps
    logger.info(f"Duración del video: {video_duration:.2f} segundos, FPS: {fps}, Total frames: {total_frames}")

    segmentos = []
    inicio = None
    tiempo_minimo_entre_segmentos = 0.5
    ultimo_segmento_fin = -tiempo_minimo_entre_segmentos
    movimiento_detectado = False
    max_velocidad_segmento = 0
    movimiento_direccion_segmento = None
    posicion_cancha_segmento = "fondo"
    max_elbow_angle_segmento = 0

    frame_counter = 0
    player_keypoints = {}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_counter += 1
        if frame_counter % frame_skip != 0:
            continue

        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 480))
            current_time = frame_counter / fps

            # Inferencia de YOLO con no_grad para optimizar
            with torch.no_grad():
                results = yolo_model(frame)

            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    if int(box.cls) == 0:  # Clase 'persona'
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf.cpu().numpy()
                        if conf > 0.5:
                            detections.append(([x1, y1, x2 - x1, y2 - y1], conf, 0))

            tracks = deepsort.update_tracks(detections, frame=frame)

            for track in tracks:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                x1, y1, w, h = track.to_tlwh()
                x2, y1 + h
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(frame.shape[1], x2)
                y2 = min(frame.shape[0], y2)
                player_roi = frame_rgb[y1:y2, x1:x2]

                if player_roi.size == 0:
                    logger.debug(f"ROI vacío para track_id {track_id} en tiempo {current_time:.2f}s")
                    continue

                roi_height, roi_width = player_roi.shape[:2]
                if roi_height <= 0 or roi_width <= 0:
                    logger.debug(f"ROI inválido para track_id {track_id} en tiempo {current_time:.2f}s")
                    continue

                new_width = int(roi_width * scale_factor)
                new_height = int(roi_height * scale_factor)
                new_width = max(1, new_width)
                new_height = max(1, new_height)
                player_roi_resized = cv2.resize(player_roi, (new_width, new_height))
                player_roi_enhanced = enhance_image(player_roi_resized)
                if player_roi_enhanced is None:
                    logger.debug(f"No se pudo mejorar ROI para track_id {track_id} en tiempo {current_time:.2f}s")
                    continue

                pose_results = pose.process(player_roi_enhanced)

                wrist_speed = 0
                elbow_angle = 90
                wrist = [center_x, center_y]
                wrist_direction_change = 0

                if pose_results and pose_results.pose_landmarks:
                    landmarks = pose_results.pose_landmarks.landmark
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * roi_width * scale_factor + x1,
                               landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * roi_height * scale_factor + y1]
                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x * roi_width * scale_factor + x1,
                             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y * roi_height * scale_factor + y1]
                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x * roi_width * scale_factor + x1,
                             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y * roi_height * scale_factor + y1]

                    elbow_angle = calculate_angle(shoulder, elbow, wrist)

                if track_id not in player_keypoints:
                    player_keypoints[track_id] = []
                player_keypoints[track_id].append({
                    'time': current_time,
                    'wrist': wrist,
                    'elbow_angle': elbow_angle
                })

                curr_keypoint = player_keypoints[track_id][-1]
                prev_keypoint = player_keypoints[track_id][-2] if len(player_keypoints[track_id]) > 1 else curr_keypoint
                if len(player_keypoints[track_id]) > 2:
                    prev_prev_keypoint = player_keypoints[track_id][-3]
                    wrist_distance = np.sqrt((curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0])**2 +
                                             (curr_keypoint['wrist'][1] - prev_keypoint['wrist'][1])**2)
                    wrist_speed = wrist_distance * fps * frame_skip
                    wrist_speed = min(wrist_speed, 50)

                    dx1 = prev_keypoint['wrist'][0] - prev_prev_keypoint['wrist'][0]
                    dx2 = curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0]
                    if dx1 * dx2 < 0:
                        wrist_direction_change = abs(dx2 - dx1) * fps * frame_skip

                    elbow_angle_change = abs(curr_keypoint['elbow_angle'] - prev_keypoint['elbow_angle'])
                    time_diff = curr_keypoint['time'] - prev_keypoint['time']
                    elbow_angle_speed = elbow_angle_change / time_diff if time_diff > 0 else 0
                else:
                    wrist_speed = 0
                    elbow_angle_speed = 0
                    wrist_direction_change = 0

                dx = curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0] if len(player_keypoints[track_id]) > 1 else 0
                is_derecha = dx > 0

                if elbow_angle > 120 and wrist_speed > 5:
                    movimiento_direccion = "smash"
                elif 100 < elbow_angle <= 120 and wrist_speed > 3:
                    movimiento_direccion = "bandeja"
                elif 90 < elbow_angle <= 120 and wrist_speed <= 3:
                    movimiento_direccion = "globo"
                elif elbow_angle <= 60 and wrist_speed < 2:
                    movimiento_direccion = "defensivo"
                elif 60 < elbow_angle <= 90 and wrist_speed > 1:
                    movimiento_direccion = "volea_" + ("derecha" if is_derecha else "reves")
                else:
                    movimiento_direccion = "derecha" if is_derecha else "reves"

                posicion_cancha = "red" if center_y < 240 else "fondo"

                if (wrist_speed > velocidad_umbral and wrist_speed > 0.03) or (elbow_angle_speed > 30) or (wrist_direction_change > 5):
                    if not movimiento_detectado and (current_time - ultimo_segmento_fin) > tiempo_minimo_entre_segmentos:
                        inicio = current_time
                        movimiento_detectado = True
                        max_velocidad_segmento = wrist_speed
                        movimiento_direccion_segmento = movimiento_direccion
                        max_elbow_angle_segmento = elbow_angle
                        posicion_cancha_segmento = posicion_cancha
                        segmentos.append({
                            'inicio': inicio,
                            'fin': None,
                            'max_velocidad': max_velocidad_segmento,
                            'movimiento_direccion': movimiento_direccion_segmento,
                            'max_elbow_angle': max_elbow_angle_segmento,
                            'posicion_cancha': posicion_cancha_segmento
                        })
                        logger.debug(f"Segmento iniciado en tiempo: {inicio:.2f}s, tipo: {movimiento_direccion}")
                    elif movimiento_detectado and (wrist_speed < (max_velocidad_segmento * 1.0) or (current_time - inicio > max_segment_duration)):
                        fin = max(current_time, inicio + 0.1)
                        segmentos[-1]['fin'] = fin
                        movimiento_detectado = False
                        ultimo_segmento_fin = fin
                        inicio = None
                        max_velocidad_segmento = 0
                        movimiento_direccion_segmento = None
                        max_elbow_angle_segmento = 0
                        posicion_cancha_segmento = "fondo"
                        logger.debug(f"Segmento finalizado en tiempo: {fin:.2f}s")
                    elif movimiento_detectado and wrist_speed > max_velocidad_segmento:
                        max_velocidad_segmento = wrist_speed
                        segmentos[-1]['max_velocidad'] = max_velocidad_segmento
                        segmentos[-1]['movimiento_direccion'] = movimiento_direccion
                        segmentos[-1]['max_elbow_angle'] = elbow_angle
                        segmentos[-1]['posicion_cancha'] = posicion_cancha
                        logger.debug(f"Segmento actualizado, velocidad: {max_velocidad_segmento:.2f}, tipo: {movimiento_direccion}")

        except Exception as e:
            logger.error(f"Error procesando fotograma {frame_counter} en tiempo {current_time:.2f}s: {str(e)}")
            continue

    cap.release()
    logger.info(f"Segmentación completada: {len(segmentos)} segmentos detectados")
    return segmentos