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

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar YOLOv8 para detección de jugadores
yolo_model = YOLO("yolov8n.pt")

# Inicializar DeepSORT para seguimiento con parámetros ajustados
deepsort = DeepSort(
    max_age=50,
    n_init=2,
    nms_max_overlap=1.0,
    max_iou_distance=0.9,
    nn_budget=100
)

# Inicializar MediaPipe Pose con umbrales bajos
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.01, min_tracking_confidence=0.01)

def enhance_image(image):
    """Mejora el contraste y la nitidez de la imagen para mejorar la detección de MediaPipe."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    enhanced = cv2.equalizeHist(gray)
    enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
    return enhanced_rgb

def detect_game_transitions(video_path, fps, total_frames):
    """Detecta transiciones entre juegos basadas en cambios en el color de la cancha y el contexto."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("No se pudo abrir el video para detectar transiciones")
        return []

    prev_hist = None
    transition_points = []
    frame_count = 0
    hist_change_threshold = 0.5

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 480))
        current_time = frame_count / fps

        roi = frame[240:480, :]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

        if prev_hist is not None:
            diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
            if diff < hist_change_threshold:
                transition_points.append(current_time)

        prev_hist = hist
        frame_count += 1

    cap.release()
    return transition_points

def segmentar_video_entrenamiento(ruta_video, custom_params=None):
    """Segmenta un video de entrenamiento en partes donde ocurren los golpes."""
    if custom_params is None:
        custom_params = {
            'velocidad_umbral': 0.00005,  # Reducir aún más
            'max_segment_duration': 1.5,
            'frame_skip': 12,
            'scale_factor': 0.8
        }

    velocidad_umbral = custom_params['velocidad_umbral']
    max_segment_duration = custom_params['max_segment_duration']
    frame_skip = custom_params['frame_skip']
    scale_factor = custom_params['scale_factor']

    logger.info(f"Segmentando video de entrenamiento: {ruta_video}")
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

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (640, 480))
        current_time = frame_counter / fps

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
                new_width = int(roi_width * scale_factor)
                new_height = int(roi_height * scale_factor)
                new_width = max(1, new_width)
                new_height = max(1, new_height)
                player_roi_resized = cv2.resize(player_roi, (new_width, new_height))
                player_roi_enhanced = enhance_image(player_roi_resized)
                pose_results = pose.process(player_roi_enhanced)
            else:
                pose_results = None

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

                # Detectar cambio rápido en la dirección del movimiento de la muñeca
                dx1 = prev_keypoint['wrist'][0] - prev_prev_keypoint['wrist'][0]
                dx2 = curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0]
                if dx1 * dx2 < 0:  # Cambio de dirección
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

            if elbow_angle > 120 and wrist_speed > 5:  # Ajustar umbrales para smashes
                movimiento_direccion = "smash"
            elif 100 < elbow_angle <= 120 and wrist_speed > 3:
                movimiento_direccion = "bandeja"
            elif 90 < elbow_angle <= 120 and wrist_speed <= 3:
                movimiento_direccion = "globo"
            elif elbow_angle <= 60 and wrist_speed < 2:
                movimiento_direccion = "defensivo"
            elif 60 < elbow_angle <= 90 and wrist_speed > 1:  # Ajustar para voleas
                movimiento_direccion = "volea_" + ("derecha" if is_derecha else "reves")
            else:
                movimiento_direccion = "derecha" if is_derecha else "reves"

            posicion_cancha = "red" if center_y < 240 else "fondo"

            if (wrist_speed > velocidad_umbral and wrist_speed > 0.03) or (elbow_angle_speed > 30) or (wrist_direction_change > 5):  # Reducir umbrales
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
                elif movimiento_detectado and (wrist_speed < (max_velocidad_segmento * 1.0) or (current_time - inicio > max_segment_duration)):
                    fin = max(current_time, inicio + 0.1)  # Asegurar duración mínima de 0.1 segundos
                    segmentos[-1]['fin'] = fin
                    movimiento_detectado = False
                    ultimo_segmento_fin = fin
                    inicio = None
                    max_velocidad_segmento = 0
                    movimiento_direccion_segmento = None
                    max_elbow_angle_segmento = 0
                    posicion_cancha_segmento = "fondo"
                elif movimiento_detectado and wrist_speed > max_velocidad_segmento:
                    max_velocidad_segmento = wrist_speed
                    segmentos[-1]['max_velocidad'] = max_velocidad_segmento
                    segmentos[-1]['movimiento_direccion'] = movimiento_direccion
                    segmentos[-1]['max_elbow_angle'] = elbow_angle
                    segmentos[-1]['posicion_cancha'] = posicion_cancha

    cap.release()
    logger.info(f"Segmentos detectados: {len(segmentos)}")
    return segmentos, video_duration

def validate_video_resolution(video_path):
    """Valida que el video tenga al menos resolución 720p."""
    cap = cv2.VideoCapture(video_path)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    cap.release()
    if height < 720:
        raise ValueError("La resolución del video debe ser al menos 720p")
    return True

def store_metrics_in_firestore(db, user_id, metrics_data):
    """Almacena las métricas en Firestore."""
    try:
        # Almacenar golpes del jugador
        strokes_ref = db.collection('player_strokes').document()
        strokes_ref.set({
            'user_id': user_id,
            'timestamp': datetime.now(),
            'strokes': metrics_data['golpes_clasificados']
        })

        # Almacenar historial de Padel IQ
        history_ref = db.collection('padel_iq_history').document()
        history_ref.set({
            'user_id': user_id,
            'timestamp': datetime.now(),
            'padel_iq': metrics_data['padel_iq'],
            'tecnica': metrics_data['tecnica'],
            'ritmo': metrics_data['ritmo'],
            'fuerza': metrics_data['fuerza']
        })

        return True
    except Exception as e:
        logger.error(f"Error storing metrics in Firestore: {str(e)}")
        return False

def generate_preview_with_metrics(frame, metrics, track_id=None):
    """Genera una previsualización con métricas superpuestas."""
    preview = frame.copy()
    
    # Dibujar métricas básicas
    cv2.putText(preview, f"Padel IQ: {metrics.get('padel_iq', 0):.1f}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(preview, f"Técnica: {metrics.get('tecnica', 0):.1f}", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(preview, f"Ritmo: {metrics.get('ritmo', 0):.1f}", 
                (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Si hay un track_id específico, mostrar métricas del jugador
    if track_id is not None:
        cv2.putText(preview, f"Jugador ID: {track_id}", 
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
    return preview

def procesar_video_entrenamiento(video_url, client=None):
    """Procesa un video de entrenamiento."""
    try:
        # Validar resolución
        validate_video_resolution(video_url)
        
        cap = cv2.VideoCapture(video_url)
        preview_frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Procesar frame y obtener métricas
            # ... existing code ...
            
            # Generar previsualización cada 30 frames
            if len(preview_frames) < 5:  # Guardar solo 5 previsualizaciones
                preview = generate_preview_with_metrics(frame, metrics)
                preview_frames.append(preview)
                
        cap.release()
        
        # Almacenar métricas si hay cliente de Firestore
        if client and metrics:
            store_metrics_in_firestore(client, metrics['user_id'], metrics)
            
        # Agregar previsualizaciones a las métricas
        metrics['preview_frames'] = preview_frames
        return metrics
        
    except Exception as e:
        logger.error(f"Error en procesar_video_entrenamiento: {str(e)}")
        raise

def segmentar_video_juego(ruta_video, player_position, game_splits=None, custom_params=None):
    """Segmenta el video en partes donde ocurren los golpes y detecta múltiples jugadores con YOLO y DeepSORT."""
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

    if game_splits is None:
        game_splits = detect_game_transitions(ruta_video, fps, total_frames)
    else:
        game_splits = sorted(game_splits)

    game_boundaries = [(0, game_splits[0] if game_splits else video_duration)]
    for i in range(len(game_splits) - 1):
        game_boundaries.append((game_splits[i], game_splits[i + 1]))
    if game_splits:
        game_boundaries.append((game_splits[-1], video_duration))

    all_segments = []
    player_trajectories = {}
    player_keypoints = {}
    global_player_positions = {}
    last_strike_player = None  # Para seguimiento de intercambios

    for game_idx, (start_time, end_time) in enumerate(game_boundaries):
        logger.info(f"Procesando juego {game_idx + 1}: {start_time} a {end_time} segundos")
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_time * fps))
        frame_count = int(start_time * fps)
        segmentos = []
        inicio = None
        tiempo_minimo_entre_segmentos = 0.5
        ultimo_segmento_fin = -tiempo_minimo_entre_segmentos
        movimiento_detectado = False
        lanzamiento_detectado = False
        lanzamiento_time = None
        max_velocidad_segmento = 0
        movimiento_direccion_segmento = None
        posicion_cancha_segmento = "fondo"
        max_elbow_angle_segmento = 0

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

            global_player_positions = assign_player_positions(tracks, existing_positions=global_player_positions)

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
                    new_width = int(roi_width * scale_factor * 1.5)
                    new_height = int(roi_height * scale_factor * 1.5)
                    new_width = max(1, new_width)
                    new_height = max(1, new_height)
                    player_roi_resized = cv2.resize(player_roi, (new_width, new_height))
                    player_roi_enhanced = enhance_image(player_roi_resized)
                    pose_results = pose.process(player_roi_enhanced)
                else:
                    pose_results = None

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
                    logger.info(f"Ángulo del codo detectado: {elbow_angle} en t={current_time}")
                else:
                    elbow_angle = interpolate_elbow_angle(player_keypoints, track_id, current_time)
                    logger.warning(f"No se detectaron puntos clave en t={current_time}, ángulo interpolado: {elbow_angle}")

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
                    'zone': 'net' if center_y < 240 else 'back',
                    'player_position': global_player_positions.get(track_id, 0)
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

                        if len(player_keypoints.get(track_id, [])) > 2:
                            prev_keypoint = player_keypoints[track_id][-2]
                            prev_prev_keypoint = player_keypoints[track_id][-3]
                            curr_keypoint = player_keypoints[track_id][-1]
                            wrist_distance = np.sqrt((curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0])**2 + 
                                                     (curr_keypoint['wrist'][1] - prev_keypoint['wrist'][1])**2)
                            wrist_speed = wrist_distance * fps * frame_skip
                            wrist_speed = min(wrist_speed, 50)

                            # Detectar cambio rápido en la dirección del movimiento de la muñeca
                            dx1 = prev_keypoint['wrist'][0] - prev_prev_keypoint['wrist'][0]
                            dx2 = curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0]
                            if dx1 * dx2 < 0:  # Cambio de dirección
                                wrist_direction_change = abs(dx2 - dx1) * fps * frame_skip

                            elbow_angle_change = abs(curr_keypoint['elbow_angle'] - prev_keypoint['elbow_angle'])
                            time_diff = curr_keypoint['time'] - prev_keypoint['time']
                            elbow_angle_speed = elbow_angle_change / time_diff if time_diff > 0 else 0
                        else:
                            wrist_speed = velocidad
                            elbow_angle_speed = 0
                            wrist_direction_change = 0

                        wrist_speed = max(wrist_speed, velocidad)

                        if dy > 0.02 and wrist_speed > 0.2 and (abs(current_time - 0.2) < 1.0 or abs(current_time - 73.74) < 1.0):
                            lanzamiento_detectado = True
                            lanzamiento_time = current_time
                            logger.debug(f"Lanzamiento detectado en t={lanzamiento_time}, dy={dy}, wrist_speed={wrist_speed}")

                        dx = curr_pos[0] - prev_pos[0]
                        is_derecha = dx > 0

                        if lanzamiento_detectado and (inicio - lanzamiento_time < 1.0 if inicio and lanzamiento_time else False):
                            movimiento_direccion = "saque"
                        elif elbow_angle > 120 and wrist_speed > 5:  # Ajustar umbrales para smashes
                            movimiento_direccion = "smash"
                        elif 100 < elbow_angle <= 120 and wrist_speed > 3:
                            movimiento_direccion = "bandeja"
                        elif 90 < elbow_angle <= 120 and wrist_speed <= 3:
                            movimiento_direccion = "globo"
                        elif elbow_angle <= 60 and wrist_speed < 2:
                            movimiento_direccion = "defensivo"
                        elif 60 < elbow_angle <= 90 and wrist_speed > 1:  # Ajustar para voleas
                            movimiento_direccion = "volea_" + ("derecha" if is_derecha else "reves")
                        else:
                            movimiento_direccion = "derecha" if is_derecha else "reves"

                        posicion_cancha = "red" if center_y < 240 else "fondo"
                        current_player = global_player_positions.get(track_id, 0)

                        # Filtro de contexto más relajado: permitir golpes iniciales o si el tiempo desde el último golpe es grande
                        is_valid_stroke = True
                        if last_strike_player is not None and current_player != 0:
                            team_a = (1, 2)
                            team_b = (3, 4)
                            if (last_strike_player in team_a and current_player in team_a) or \
                               (last_strike_player in team_b and current_player in team_b):
                                # Permitir si es el primer golpe del juego o si el tiempo desde el último golpe es mayor a 0.5 segundos
                                if (current_time - ultimo_segmento_fin) > 0.5 or len(segmentos) == 0:
                                    is_valid_stroke = True
                                else:
                                    is_valid_stroke = False
                                    logger.info(f"Descartando golpe en t={current_time}: no es parte de un intercambio válido.")

                        if ((wrist_speed > velocidad_umbral and wrist_speed > 0.03) or (elbow_angle_speed > 30) or (wrist_direction_change > 5)) and is_valid_stroke:
                            if not movimiento_detectado and (current_time - ultimo_segmento_fin) > tiempo_minimo_entre_segmentos:
                                inicio = current_time
                                movimiento_detectado = True
                                max_velocidad_segmento = wrist_speed
                                movimiento_direccion_segmento = movimiento_direccion
                                max_elbow_angle_segmento = elbow_angle
                                posicion_cancha_segmento = posicion_cancha
                                player_pos = current_player
                                segmentos.append({
                                    'inicio': inicio,
                                    'fin': None,
                                    'lanzamiento_detectado': lanzamiento_detectado,
                                    'lanzamiento_time': lanzamiento_time,
                                    'max_velocidad': max_velocidad_segmento,
                                    'movimiento_direccion': movimiento_direccion_segmento,
                                    'max_elbow_angle': max_elbow_angle_segmento,
                                    'posicion_cancha': posicion_cancha_segmento,
                                    'player_position': player_pos
                                })
                                last_strike_player = current_player
                            elif movimiento_detectado and (wrist_speed < (max_velocidad_segmento * 1.0) or (current_time - inicio > max_segment_duration)):
                                fin = max(current_time, inicio + 0.1)  # Asegurar duración mínima de 0.1 segundos
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
                                segmentos[-1]['player_position'] = current_player
                                last_strike_player = current_player

            frame_count += 1

        if movimiento_detectado and inicio is not None:
            fin = max(frame_count / fps, inicio + 0.1)  # Asegurar duración mínima
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
    player_pos = segmento['player_position']
    start_time = segmento['inicio']
    end_time = segmento.get('fin', start_time + 0.5)

    if max_velocidad > 0.03 and movimiento_direccion:
        calidad = min(100, max_velocidad * 1)
        golpe = {
            'tipo': movimiento_direccion,
            'confianza': calidad / 100,
            'calidad': calidad,
            'max_elbow_angle': max_elbow_angle,
            'max_wrist_speed': max_velocidad,
            'inicio': start_time,
            'fin': end_time,
            'posicion_cancha': posicion_cancha,
            'player_position': player_pos
        }

        non_striking_metrics = calculate_metrics_for_non_striking_players(player_pos, start_time, end_time, player_trajectories, (0, 0))
        golpe['non_striking_metrics'] = non_striking_metrics

        return [golpe]
    else:
        logger.warning("No se detectaron golpes significativos en el segmento (velocidad insuficiente).")
        return []

def procesar_video_juego(video_url, player_position, client=None, game_splits=None, custom_params=None):
    """Procesa un video de juego."""
    try:
        # Validar resolución
        validate_video_resolution(video_url)
        
        # Resto del código existente de procesamiento
        # ... existing code ...
        
        # Almacenar métricas si hay cliente de Firestore
        if client and metrics:
            store_metrics_in_firestore(client, metrics['user_id'], metrics)
            
        return metrics
        
    except Exception as e:
        logger.error(f"Error en procesar_video_juego: {str(e)}")
        raise

def procesar_video_partido(video_url):
    """Simula el procesamiento de un video de partido."""
    logger.info(f"Procesando video de partido: {video_url}")
    
    # Simular resultados del análisis
    return {
        'jugadores': {
            'equipo1': [
                {'id': 'jugador1', 'posicion': 'drive'},
                {'id': 'jugador2', 'posicion': 'reves'}
            ],
            'equipo2': [
                {'id': 'jugador3', 'posicion': 'drive'},
                {'id': 'jugador4', 'posicion': 'reves'}
            ]
        },
        'puntos': [
            {
                'equipo_ganador': 'equipo1',
                'tipo_punto': 'winner',
                'jugador_ganador': 'jugador1',
                'duracion': 15.5,
                'golpes': 8
            }
        ],
        'estadisticas': {
            'duracion_total': 120,
            'puntos_totales': 25,
            'winners': {'equipo1': 12, 'equipo2': 8},
            'errores': {'equipo1': 5, 'equipo2': 7}
        },
        'fecha_analisis': datetime.now().isoformat()
    }