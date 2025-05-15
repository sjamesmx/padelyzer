import logging
import cv2
import numpy as np
import json
from datetime import datetime
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import mediapipe as mp
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar YOLOv8 para detección de jugadores
try:
    yolo_model = YOLO("yolov8n.pt")
except Exception as e:
    logger.error(f"Error al inicializar YOLO: {str(e)}")
    exit(1)

# Inicializar DeepSORT para seguimiento
try:
    deepsort = DeepSort(
        max_age=50,
        n_init=2,
        nms_max_overlap=1.0,
        max_iou_distance=0.9,
        nn_budget=100
    )
except Exception as e:
    logger.error(f"Error al inicializar DeepSORT: {str(e)}")
    exit(1)

# Inicializar MediaPipe Pose con umbrales bajos
try:
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.005, min_tracking_confidence=0.005)
except Exception as e:
    logger.error(f"Error al inicializar MediaPipe: {str(e)}")
    exit(1)

# Variable global para almacenar el track_id del jugador seleccionado
global selected_track_id
selected_track_id = None

def mouse_callback(event, x, y, flags, param):
    """Función para manejar clics del mouse y seleccionar un jugador."""
    global selected_track_id
    if event == cv2.EVENT_LBUTTONDOWN:  # Clic izquierdo
        tracks = param  # Los tracks son pasados como parámetro
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            x1, y1, w, h = track.to_tlwh()
            x2, y2 = x1 + w, y1 + h
            if x1 <= x <= x2 and y1 <= y <= y2:
                selected_track_id = track_id
                logger.info(f"Jugador seleccionado: track_id {selected_track_id}")
                break

def calculate_angle(point1, point2, point3):
    """Calcula el ángulo entre tres puntos."""
    try:
        a = np.array(point1)
        b = np.array(point2)
        c = np.array(point3)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(cosine_angle)
        return np.degrees(angle)
    except Exception as e:
        logger.warning(f"Error al calcular ángulo: {str(e)}")
        return 90

def enhance_image(image):
    """Mejora el contraste y la nitidez de la imagen para MediaPipe."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        enhanced = cv2.equalizeHist(gray)
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        return enhanced_rgb
    except Exception as e:
        logger.warning(f"Error al mejorar imagen: {str(e)}")
        return image

def draw_camera_guidelines(frame, net_line_y, court_left_x, court_right_x):
    """Dibuja líneas guía para ajustar la cámara y mensajes de alineación."""
    try:
        height, width = frame.shape[:2]

        ideal_net_y = height // 2
        cv2.line(frame, (0, ideal_net_y), (width, ideal_net_y), (255, 255, 0), 1)
        cv2.line(frame, (0, net_line_y), (width, net_line_y), (0, 0, 255), 1)

        ideal_left_x = width // 4
        ideal_right_x = 3 * width // 4
        cv2.line(frame, (ideal_left_x, 0), (ideal_left_x, height), (255, 255, 0), 1)
        cv2.line(frame, (ideal_right_x, 0), (ideal_right_x, height), (255, 255, 0), 1)
        cv2.line(frame, (court_left_x, 0), (court_left_x, height), (0, 0, 255), 1)
        cv2.line(frame, (court_right_x, 0), (court_right_x, height), (0, 0, 255), 1)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_color = (0, 0, 255)
        thickness = 1

        net_tolerance = 50
        if abs(net_line_y - ideal_net_y) > net_tolerance:
            cv2.putText(frame, "Ajusta la camara: Mueve hacia arriba/abajo para centrar la red", (10, height - 40), font, font_scale, font_color, thickness)

        court_tolerance = 50
        if abs(court_left_x - ideal_left_x) > court_tolerance or abs(court_right_x - ideal_right_x) > court_tolerance:
            cv2.putText(frame, "Ajusta la camara: Mueve a izq/der para centrar la cancha", (10, height - 20), font, font_scale, font_color, thickness)

    except Exception as e:
        logger.warning(f"Error al dibujar líneas guía: {str(e)}")

def draw_metrics(frame, track_id, elbow_angle, wrist_speed, wrist_direction_change, movimiento_direccion, posicion_cancha, total_golpes, ritmo, detections, session_active, selected_id):
    """Dibuja las métricas biomecánicas en el frame."""
    try:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_color = (0, 255, 0)
        thickness = 1
        line_spacing = 20

        status_text = "Sesion: ACTIVA (Presiona 'p' para pausar)" if session_active else "Sesion: PAUSADA (Presiona 's' para iniciar)"
        cv2.putText(frame, status_text, (10, frame.shape[0] - 80), font, font_scale, (255, 0, 0) if session_active else (0, 0, 255), thickness)

        if session_active:
            y0, dy = 20, line_spacing
            metrics = [
                f"Track ID: {track_id}",
                f"Angulo Codo: {elbow_angle:.1f} deg",
                f"Vel. Muneca: {wrist_speed:.1f} px/s",
                f"Cambio Dir. Muneca: {wrist_direction_change:.1f}",
                f"Tipo Golpe: {movimiento_direccion}",
                f"Posicion: {posicion_cancha}",
                f"Total Golpes: {total_golpes}",
                f"Ritmo: {ritmo:.1f} golpes/min"
            ]

            for i, metric in enumerate(metrics):
                y = y0 + i * dy
                cv2.putText(frame, metric, (10, y), font, font_scale, font_color, thickness, cv2.LINE_AA)

        if selected_id is not None:
            cv2.putText(frame, f"Jugador Seleccionado: {selected_id} (Presiona 'r' para reiniciar)", (10, frame.shape[0] - 100), font, font_scale, (0, 255, 255), thickness)
        else:
            cv2.putText(frame, "Haz clic sobre un jugador para seleccionarlo (Presiona 'r' para reiniciar)", (10, frame.shape[0] - 100), font, font_scale, (0, 255, 255), thickness)

        if not detections:
            cv2.putText(frame, "No se detectan jugadores. Asegúrate de que Lety esté visible y la cancha esté bien iluminada.", (10, frame.shape[0] - 60), font, font_scale, (0, 0, 255), thickness)

    except Exception as e:
        logger.warning(f"Error al dibujar métricas: {str(e)}")

def save_results(segmentos, current_time):
    """Guarda los resultados en un archivo JSON."""
    output_dir = "scripts/livemonitor"
    os.makedirs(output_dir, exist_ok=True)

    video_duration = current_time
    total_golpes = len(segmentos)
    ritmo = (total_golpes / video_duration) * 120 if video_duration > 0 else 0
    ritmo = min(ritmo, 100)

    golpes_clasificados = {}
    for segmento in segmentos:
        tipo = segmento['movimiento_direccion']
        if tipo not in golpes_clasificados:
            golpes_clasificados[tipo] = []
        golpes_clasificados[tipo].append(segmento)

    results = {
        'player_name': "Lety",
        'session_type': "entrenamiento",
        'detected_strokes': golpes_clasificados,
        'total_golpes': total_golpes,
        'video_duration': video_duration,
        'ritmo': ritmo
    }

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f"padel_metrics_lety_entrenamiento_{timestamp}.json")
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
        logger.info(f"Resultados guardados en {output_file}")
        logger.info(f"Total golpes detectados: {total_golpes}, Ritmo: {ritmo}")
    except Exception as e:
        logger.error(f"Error al guardar resultados: {str(e)}")

def capture_padel_metrics():
    """Captura métricas de juego desde la webcam en tiempo real y las muestra en pantalla."""
    global selected_track_id
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("No se pudo abrir la webcam. Verifica permisos o conexión.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        logger.warning("FPS no detectado, usando valor predeterminado: 30")
        fps = 30

    custom_params = {
        'velocidad_umbral': 0.00001,  # Reducido para mayor sensibilidad
        'max_segment_duration': 1.5,
        'frame_skip': 1,
        'scale_factor': 0.8
    }

    velocidad_umbral = custom_params['velocidad_umbral']
    max_segment_duration = custom_params['max_segment_duration']
    frame_skip = custom_params['frame_skip']
    scale_factor = custom_params['scale_factor']

    segmentos = []
    inicio = None
    ultimo_segmento_fin = float('-inf')
    movimiento_detectado = False
    max_velocidad_segmento = 0
    movimiento_direccion_segmento = "N/A"
    posicion_cancha_segmento = "N/A"
    max_elbow_angle_segmento = 0
    session_active = False

    frame_counter = 0
    player_keypoints = {}
    start_time = datetime.now().timestamp()
    current_time = 0
    track_id = "N/A"
    elbow_angle = 0
    wrist_speed = 0
    wrist_direction_change = 0
    elbow_angle_speed = 0

    # Configurar el callback del mouse para la ventana de video
    cv2.namedWindow('Padel Metrics Capture')

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("No se pudo leer el fotograma. Verifica la webcam.")
                break

            frame_counter += 1
            if frame_counter % frame_skip != 0:
                continue

            current_time = (datetime.now().timestamp() - start_time)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 480))
            height, width = frame.shape[:2]

            # Detección de jugadores con YOLO
            results = yolo_model(frame)
            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    if int(box.cls) == 0:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf.cpu().numpy()
                        if conf > 0.1:
                            center_x = (x1 + x2) / 2
                            if center_x < width / 2:
                                conf *= 1.2
                            detections.append(([x1, y1, x2 - x1, y2 - y1], conf, 0))

            tracks = deepsort.update_tracks(detections, frame=frame)

            # Configurar el callback del mouse con los tracks actuales
            cv2.setMouseCallback('Padel Metrics Capture', mouse_callback, tracks)

            net_line_y = height // 2
            court_left_x = width // 4
            court_right_x = 3 * width // 4

            draw_camera_guidelines(frame, net_line_y, court_left_x, court_right_x)

            # Filtrar tracks para procesar solo el jugador seleccionado (si hay uno)
            filtered_tracks = tracks if selected_track_id is None else [track for track in tracks if track.track_id == selected_track_id]

            if session_active:
                for track in filtered_tracks:
                    if not track.is_confirmed():
                        continue
                    track_id = track.track_id
                    x1, y1, w, h = track.to_tlwh()
                    x2, y2 = x1 + w, y1 + h
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2

                    # Dibujar cuadro delimitador (azul si está seleccionado, verde si no)
                    color = (255, 0, 0) if track_id == selected_track_id else (0, 255, 0)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(frame, f"ID: {track_id}", (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    x1 = max(0, x1)
                    y1 = max(0, y1)
                    x2 = min(frame.shape[1], x2)
                    y2 = min(frame.shape[0], y2)
                    player_roi = frame_rgb[y1:y2, x1:x2]

                    if player_roi.size == 0:
                        logger.warning(f"ROI vacío para track_id {track_id} en t={current_time}")
                        continue

                    roi_height, roi_width = player_roi.shape[:2]
                    if roi_height <= 0 or roi_width <= 0:
                        logger.warning(f"Dimensiones inválidas del ROI para track_id {track_id}: {roi_height}x{roi_width}")
                        continue

                    new_width = int(roi_width * scale_factor)
                    new_height = int(roi_height * scale_factor)
                    new_width = max(1, new_width)
                    new_height = max(1, new_height)
                    player_roi_resized = cv2.resize(player_roi, (new_width, new_height))
                    player_roi_enhanced = enhance_image(player_roi_resized)
                    pose_results = pose.process(player_roi_enhanced)

                    wrist_speed = 0
                    elbow_angle = 90
                    wrist = [center_x, center_y]
                    wrist_direction_change = 0
                    elbow_angle_speed = 0

                    if pose_results and pose_results.pose_landmarks:
                        landmarks = pose_results.pose_landmarks.landmark
                        try:
                            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * roi_width * scale_factor + x1,
                                       landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * roi_height * scale_factor + y1]
                            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x * roi_width * scale_factor + x1,
                                     landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y * roi_height * scale_factor + y1]
                            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x * roi_width * scale_factor + x1,
                                     landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y * roi_height * scale_factor + y1]

                            elbow_angle = calculate_angle(shoulder, elbow, wrist)
                        except IndexError as e:
                            logger.warning(f"Error al acceder a landmarks para track_id {track_id}: {str(e)}")
                            continue
                    else:
                        logger.warning(f"No se detectaron landmarks para track_id {track_id} en t={current_time}")

                    if track_id not in player_keypoints:
                        player_keypoints[track_id] = []
                    player_keypoints[track_id].append({
                        'time': current_time,
                        'wrist': wrist,
                        'elbow_angle': elbow_angle
                    })

                    if len(player_keypoints[track_id]) > 1:
                        prev_keypoint = player_keypoints[track_id][-2]
                        curr_keypoint = player_keypoints[track_id][-1]
                        wrist_distance = np.sqrt((curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0])**2 + 
                                                 (curr_keypoint['wrist'][1] - prev_keypoint['wrist'][1])**2)
                        wrist_speed = wrist_distance * fps * frame_skip
                        wrist_speed = min(wrist_speed, 50)

                        elbow_angle_change = abs(curr_keypoint['elbow_angle'] - prev_keypoint['elbow_angle'])
                        time_diff = curr_keypoint['time'] - prev_keypoint['time']
                        elbow_angle_speed = elbow_angle_change / time_diff if time_diff > 0 else 0

                        wrist_direction_change = 0
                        if len(player_keypoints[track_id]) > 2:
                            prev_prev_keypoint = player_keypoints[track_id][-3]
                            dx1 = prev_keypoint['wrist'][0] - prev_prev_keypoint['wrist'][0]
                            dx2 = curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0]
                            if dx1 * dx2 < 0:
                                wrist_direction_change = abs(dx2 - dx1) * fps * frame_skip
                                wrist_direction_change = min(wrist_direction_change, 50)

                    dx = curr_keypoint['wrist'][0] - prev_keypoint['wrist'][0] if len(player_keypoints[track_id]) > 1 else 0
                    is_derecha = dx > 0

                    if elbow_angle > 120 and wrist_speed > 1.5:  # Reducido umbral de wrist_speed
                        movimiento_direccion = "smash"
                    elif 100 < elbow_angle <= 120 and wrist_speed > 1:  # Reducido umbral de wrist_speed
                        movimiento_direccion = "bandeja"
                    elif 90 < elbow_angle <= 120 and wrist_speed <= 1:
                        movimiento_direccion = "globo"
                    elif elbow_angle <= 60 and wrist_speed < 0.5:  # Reducido umbral de wrist_speed
                        movimiento_direccion = "defensivo"
                    elif 60 < elbow_angle <= 90 and wrist_speed > 0.3:  # Reducido umbral de wrist_speed
                        movimiento_direccion = "volea_" + ("derecha" if is_derecha else "reves")
                    else:
                        movimiento_direccion = "derecha" if is_derecha else "reves"

                    net_threshold = net_line_y + (center_x / width) * 50
                    posicion_cancha = "red" if center_y < net_threshold else "fondo"

                    if (wrist_speed > velocidad_umbral and wrist_speed > 0.005) or (elbow_angle_speed > 5) or (wrist_direction_change > 0.5):  # Reducidos umbrales
                        logger.info(f"Golpe detectado: wrist_speed={wrist_speed}, elbow_angle_speed={elbow_angle_speed}, wrist_direction_change={wrist_direction_change}")
                        if not movimiento_detectado:
                            logger.info(f"Registrando golpe: {movimiento_direccion} en t={current_time}")
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
                                'posicion_cancha': posicion_cancha_segmento,
                                'player_position': track_id
                            })
                        elif movimiento_detectado and (wrist_speed < (max_velocidad_segmento * 1.0) or (current_time - inicio > max_segment_duration)):
                            fin = max(current_time, inicio + 0.1)
                            segmentos[-1]['fin'] = fin
                            movimiento_detectado = False
                            ultimo_segmento_fin = fin
                            inicio = None
                            max_velocidad_segmento = 0
                            movimiento_direccion_segmento = "N/A"
                            max_elbow_angle_segmento = 0
                            posicion_cancha_segmento = "N/A"
                        elif movimiento_detectado and wrist_speed > max_velocidad_segmento:
                            max_velocidad_segmento = wrist_speed
                            segmentos[-1]['max_velocidad'] = max_velocidad_segmento
                            segmentos[-1]['movimiento_direccion'] = movimiento_direccion
                            segmentos[-1]['max_elbow_angle'] = elbow_angle
                            segmentos[-1]['posicion_cancha'] = posicion_cancha

            video_duration = current_time
            total_golpes = len(segmentos)
            ritmo = (total_golpes / video_duration) * 120 if video_duration > 0 else 0
            ritmo = min(ritmo, 100)

            draw_metrics(frame, track_id, elbow_angle, wrist_speed, wrist_direction_change, movimiento_direccion_segmento, posicion_cancha_segmento, total_golpes, ritmo, detections, session_active, selected_track_id)

            cv2.imshow('Padel Metrics Capture', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Usuario presionó 'q'. Cerrando ventana.")
                break
            elif key == ord('s'):
                if not session_active:
                    logger.info("Iniciando sesión de captura.")
                    session_active = True
                    start_time = datetime.now().timestamp()
                    current_time = 0
                    segmentos = []
                    player_keypoints = {}
            elif key == ord('p'):
                if session_active:
                    logger.info("Pausando sesión de captura.")
                    session_active = False
                    save_results(segmentos, current_time)
            elif key == ord('r'):
                logger.info("Reiniciando selección de jugador.")
                selected_track_id = None

    except KeyboardInterrupt:
        logger.info("Captura interrumpida por el usuario (Ctrl+C). Guardando resultados.")
        save_results(segmentos, current_time)
    except Exception as e:
        logger.error(f"Error en el bucle principal: {str(e)}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        save_results(segmentos, current_time)

if __name__ == "__main__":
    capture_padel_metrics()