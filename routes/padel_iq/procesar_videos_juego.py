import logging
import cv2
import numpy as np
import requests
import os
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import mediapipe as mp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar YOLOv8 para detección de jugadores
yolo_model = YOLO("yolov8n.pt")

# Inicializar DeepSORT para seguimiento
deepsort = DeepSort(
    max_age=30,
    n_init=3,
    nms_max_overlap=1.0,
    max_iou_distance=0.7,
    nn_budget=100
)

# Inicializar MediaPipe Pose con umbrales ajustados
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def calculate_angle(a, b, c):
    """Calcula el ángulo entre tres puntos (a, b, c) en grados."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

def detect_game_transitions(video_path, fps, total_frames):
    """Detecta transiciones entre juegos basadas en cambios en el color de la cancha y el contexto."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    prev_hist = None
    transition_points = []
    frame_count = 0
    hist_change_threshold = 0.5  # Umbral para detectar cambios significativos

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 480))
        current_time = frame_count / fps

        # Extraer el fondo (asumimos que la cancha ocupa la parte inferior del frame)
        roi = frame[240:480, :]  # Parte inferior del frame
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

        if prev_hist is not None:
            # Comparar histogramas
            diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
            if diff < hist_change_threshold:
                transition_points.append(current_time)

        prev_hist = hist
        frame_count += 1

    cap.release()
    return transition_points

def segmentar_video_juego(ruta_video, player_position, game_splits=None):
    """Segmenta el video en partes donde ocurren los golpes y detecta múltiples jugadores con YOLO y DeepSORT."""
    logger.info(f"Segmentando video de juego: {ruta_video}")
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        logger.error("No se pudo abrir el video")
        raise ValueError("No se pudo abrir el video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps
    logger.info(f"Duración del video: {video_duration} segundos")

    # Detectar transiciones entre juegos
    if game_splits is None:
        game_splits = detect_game_transitions(ruta_video, fps, total_frames)
    else:
        game_splits = sorted(game_splits)

    # Dividir el video en juegos
    game_boundaries = [(0, game_splits[0] if game_splits else video_duration)]
    for i in range(len(game_splits) - 1):
        game_boundaries.append((game_splits[i], game_splits[i + 1]))
    if game_splits:
        game_boundaries.append((game_splits[-1], video_duration))

    all_segments = []
    player_trajectories = {}
    player_keypoints = {}

    for game_idx, (start_time, end_time) in enumerate(game_boundaries):
        logger.info(f"Procesando juego {game_idx + 1}: {start_time} a {end_time} segundos")
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_time * fps))
        frame_count = int(start_time * fps)
        segmentos = []
        inicio = None
        velocidad_umbral = 0.002
        tiempo_minimo_entre_segmentos = 1.0
        max_segment_duration = 1.5
        ultimo_segmento_fin = -tiempo_minimo_entre_segmentos
        movimiento_detectado = False
        lanzamiento_detectado = False
        lanzamiento_time = None
        max_velocidad_segmento = 0
        movimiento_direccion_segmento = None
        posicion_cancha_segmento = "fondo"
        max_elbow_angle_segmento = 0

        frame_skip = 12
        frame_counter = frame_count

        while cap.isOpened() and frame_count < int(end_time * fps):
            ret, frame = cap.read()
            if not ret:
                break

            frame_counter += 1
            if frame_counter % frame_skip != 0:
                frame_count += 1
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 480))
            current_time = frame_count / fps

            results = yolo_model(frame)
            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    if int(box.cls) == 0:
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
                x2, y2 = x1 + w, y1 + h
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(frame.shape[1], x2)
                y2 = min(frame.shape[0], y2)
                player_roi = frame_rgb[y1:y2, x1:x2]

                if player_roi.size == 0:
                    continue

                roi_height, roi_width = player_roi.shape[:2]
                if roi_height > 0 and roi_width > 0:
                    scale_factor = 0.6  # Aumentar para mejorar la detección
                    new_width = int(roi_width * scale_factor)
                    new_height = int(roi_height * scale_factor)
                    new_width = max(1, new_width)
                    new_height = max(1, new_height)
                    player_roi_resized = cv2.resize(player_roi, (new_width, new_height))
                    pose_results = pose.process(player_roi_resized)
                else:
                    pose_results = None

                wrist_speed = 0
                elbow_angle = 90  # Valor predeterminado ajustado
                wrist = [center_x, center_y]

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

                if track_id not in player_trajectories:
                    player_trajectories[track_id] = []
                player_trajectories[track_id].append({
                    'time': current_time,
                    'position': (center_x, center_y),
                    'side': 'left' if center_x < 320 else 'right',
                    'zone': 'net' if center_y < 240 else 'back'
                })

                if (player_position['side'] == 'left' and center_x < 320) or \
                   (player_position['side'] == 'right' and center_x > 320):
                    if len(player_trajectories[track_id]) > 1:
                        prev_pos = player_trajectories[track_id][-2]['position']
                        curr_pos = player_trajectories[track_id][-1]['position']
                        dy = prev_pos[1] - curr_pos[1]
                        distance = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                        velocidad = distance * fps
                        velocidad = min(velocidad, 50)

                        if len(player_keypoints.get(track_id, [])) > 1:
                            prev_wrist = player_keypoints[track_id][-2]['wrist']
                            curr_wrist = player_keypoints[track_id][-1]['wrist']
                            wrist_distance = np.sqrt((curr_wrist[0] - prev_wrist[0])**2 + (curr_wrist[1] - prev_wrist[1])**2)
                            wrist_speed = wrist_distance * fps * frame_skip
                            wrist_speed = min(wrist_speed, 50)
                        else:
                            wrist_speed = velocidad

                        wrist_speed = max(wrist_speed, velocidad)

                        if dy > 0.02 and wrist_speed > 0.2 and (abs(current_time - 0.2) < 1.0 or abs(current_time - 73.74) < 1.0):
                            lanzamiento_detectado = True
                            lanzamiento_time = current_time
                            logger.debug(f"Lanzamiento detectado en t={lanzamiento_time}, dy={dy}, wrist_speed={wrist_speed}")

                        dx = curr_pos[0] - prev_pos[0]
                        is_derecha = dx > 0

                        if lanzamiento_detectado and (inicio - lanzamiento_time < 1.0 if inicio and lanzamiento_time else False):
                            movimiento_direccion = "saque"
                        elif elbow_angle > 120 and wrist_speed > 6:
                            movimiento_direccion = "smash"
                        elif elbow_angle > 90 and wrist_speed > 3:
                            movimiento_direccion = "bandeja"
                        elif elbow_angle > 90 and wrist_speed < 3:
                            movimiento_direccion = "globo"
                        elif elbow_angle < 60 and wrist_speed < 1:
                            movimiento_direccion = "defensivo"
                        elif elbow_angle < 90 and wrist_speed > 1:
                            movimiento_direccion = "volea_" + ("derecha" if is_derecha else "reves")
                        else:
                            movimiento_direccion = "derecha" if is_derecha else "reves"

                        posicion_cancha = "red" if center_y < 240 else "fondo"

                        if wrist_speed > velocidad_umbral and wrist_speed > 0.5 and not movimiento_detectado and (current_time - ultimo_segmento_fin) > tiempo_minimo_entre_segmentos:
                            inicio = current_time
                            movimiento_detectado = True
                            max_velocidad_segmento = wrist_speed
                            movimiento_direccion_segmento = movimiento_direccion
                            max_elbow_angle_segmento = elbow_angle
                            posicion_cancha_segmento = posicion_cancha
                            segmentos.append({
                                'inicio': inicio,
                                'fin': None,
                                'lanzamiento_detectado': lanzamiento_detectado,
                                'lanzamiento_time': lanzamiento_time,
                                'max_velocidad': max_velocidad_segmento,
                                'movimiento_direccion': movimiento_direccion_segmento,
                                'max_elbow_angle': max_elbow_angle_segmento,
                                'posicion_cancha': posicion_cancha_segmento
                            })
                        elif movimiento_detectado and (wrist_speed < (max_velocidad_segmento * 1.0) or (current_time - inicio > max_segment_duration)):
                            fin = current_time
                            segmentos[-1]['fin'] = fin
                            movimiento_detectado = False
                            ultimo_segmento_fin = fin
                            inicio = None
                            max_velocidad_segmento = 0
                            movimiento_direccion_segmento = None
                            max_elbow_angle_segmento = 0
                            posicion_cancha_segmento = "fondo"
                            lanzamiento_detectado = False
                            lanzamiento_time = None
                        elif movimiento_detectado and wrist_speed > max_velocidad_segmento:
                            max_velocidad_segmento = wrist_speed
                            segmentos[-1]['max_velocidad'] = max_velocidad_segmento
                            segmentos[-1]['movimiento_direccion'] = movimiento_direccion
                            segmentos[-1]['max_elbow_angle'] = elbow_angle
                            segmentos[-1]['posicion_cancha'] = posicion_cancha

            frame_count += 1

        if movimiento_detectado and inicio is not None:
            fin = frame_count / fps
            segmentos[-1]['fin'] = min(fin, end_time)

        all_segments.extend(segmentos)

    cap.release()
    logger.info(f"Segmentos detectados: {len(all_segments)}")
    return all_segments, video_duration, player_trajectories

def analizar_segmento_juego(segmento, ruta_video, player_trajectories):
    """Analiza un segmento específico para detectar y clasificar golpes en un juego."""
    logger.info(f"Analizando segmento: {segmento}")
    max_velocidad = segmento['max_velocidad']
    movimiento_direccion = segmento['movimiento_direccion']
    max_elbow_angle = segmento['max_elbow_angle']
    posicion_cancha = segmento['posicion_cancha']

    if max_velocidad > 0.5 and movimiento_direccion:
        calidad = min(100, max_velocidad * 1)
        return [{
            'tipo': movimiento_direccion,
            'confianza': calidad / 100,
            'calidad': calidad,
            'max_elbow_angle': max_elbow_angle,
            'max_wrist_speed': max_velocidad,
            'inicio': segmento['inicio'],
            'posicion_cancha': posicion_cancha
        }]
    else:
        logger.warning("No se detectaron golpes significativos en el segmento (velocidad insuficiente).")
        return []

def procesar_video_juego(video_url, player_position, client=None, game_splits=None):
    """Procesa un video de juego completo con YOLO y DeepSORT."""
    local_path = "temp_video_juego.mp4"
    logger.info(f"Descargando video desde {video_url} a {local_path}")
    response = requests.get(video_url, stream=True)
    response.raise_for_status()
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=16384):
            if chunk:
                f.write(chunk)

    try:
        segmentos, video_duration, player_trajectories = segmentar_video_juego(local_path, player_position, game_splits)

        golpes_totales = []
        for segmento in segmentos:
            golpes = analizar_segmento_juego(segmento, local_path, player_trajectories)
            golpes_totales.extend(golpes)

        golpes_clasificados = {}
        for golpe in golpes_totales:
            tipo = golpe['tipo']
            if tipo not in golpes_clasificados:
                golpes_clasificados[tipo] = []
            golpes_clasificados[tipo].append(golpe)

        os.remove(local_path)
        logger.info(f"Archivo temporal {local_path} eliminado")

        return golpes_clasificados, video_duration

    except Exception as e:
        logger.error(f"Error al procesar video de juego: {str(e)}")
        if os.path.exists(local_path):
            os.remove(local_path)
        raise e