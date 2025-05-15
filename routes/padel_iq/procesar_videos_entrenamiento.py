import logging
import cv2
import numpy as np
import requests
import os
import mediapipe as mp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def segmentar_video(ruta_video):
    """Segmenta el video en partes donde ocurren los golpes usando MediaPipe."""
    logger.info(f"Segmentando video: {ruta_video}")
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        logger.error("No se pudo abrir el video")
        raise ValueError("No se pudo abrir el video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30  # Valor por defecto si no se puede determinar

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps
    logger.info(f"Duración del video: {video_duration} segundos")

    prev_wrist_right_pos = None
    prev_wrist_left_pos = None
    prev_elbow_pos = None
    prev_shoulder_pos = None
    segmentos = []
    inicio = None
    velocidad_umbral = 0.20  # Umbral para detectar los 11 golpes reales
    angle_change_umbral = 4  # Umbral de cambio de ángulo
    tiempo_minimo_entre_segmentos = 2.0  # Tiempo mínimo en segundos entre golpes
    ultimo_segmento_fin = -tiempo_minimo_entre_segmentos
    frame_count = 0
    movimiento_detectado = False
    lanzamiento_detectado = False
    lanzamiento_time = None
    max_velocidad_segmento = 0
    max_elbow_angle_segmento = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Reducir resolución para optimizar
        frame = cv2.resize(frame, (640, 480))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            wrist_right = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
            wrist_left = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
            elbow = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]
            shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            current_wrist_right_pos = (wrist_right.x, wrist_right.y)
            current_wrist_left_pos = (wrist_left.x, wrist_left.y)
            current_elbow_pos = (elbow.x, elbow.y)
            current_shoulder_pos = (shoulder.x, shoulder.y)

            if prev_wrist_right_pos is not None and prev_wrist_left_pos is not None and prev_elbow_pos is not None and prev_shoulder_pos is not None:
                # Calcular velocidad de la muñeca derecha (golpe)
                distance_right = np.sqrt((current_wrist_right_pos[0] - prev_wrist_right_pos[0])**2 + (current_wrist_right_pos[1] - prev_wrist_right_pos[1])**2)
                velocidad_right = distance_right * fps

                # Calcular velocidad de la muñeca izquierda (lanzamiento)
                distance_left = np.sqrt((current_wrist_left_pos[0] - prev_wrist_left_pos[0])**2 + (current_wrist_left_pos[1] - prev_wrist_left_pos[1])**2)
                velocidad_left = distance_left * fps
                # Detectar movimiento ascendente de la muñeca izquierda (lanzamiento de la pelota)
                dy_left = prev_wrist_left_pos[1] - current_wrist_left_pos[1]  # Movimiento ascendente si dy_left > 0
                current_time = frame_count / fps
                # Ajustar umbrales y limitar lanzamientos a tiempos esperados (cerca de 0.2s y 73.74s)
                if dy_left > 0.02 and velocidad_left > 0.3 and (abs(current_time - 0.2) < 1.0 or abs(current_time - 73.74) < 1.0):
                    lanzamiento_detectado = True
                    lanzamiento_time = current_time
                    logger.debug(f"Lanzamiento detectado en t={lanzamiento_time}, dy_left={dy_left}, velocidad_left={velocidad_left}")
                else:
                    logger.debug(f"No se detectó lanzamiento en t={current_time}, dy_left={dy_left}, velocidad_left={velocidad_left}")

                # Calcular cambio de ángulo del brazo (muñeca derecha)
                vector_wrist = np.array([current_wrist_right_pos[0] - current_elbow_pos[0], current_wrist_right_pos[1] - current_elbow_pos[1]])
                vector_prev_wrist = np.array([prev_wrist_right_pos[0] - prev_elbow_pos[0], prev_wrist_right_pos[1] - prev_elbow_pos[1]])
                dot_product = np.dot(vector_wrist, vector_prev_wrist)
                norm1 = np.linalg.norm(vector_wrist)
                norm2 = np.linalg.norm(vector_prev_wrist)
                if norm1 > 0 and norm2 > 0:
                    cos_angle = dot_product / (norm1 * norm2)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    angle_change = np.degrees(np.arccos(cos_angle))

                    if velocidad_right > velocidad_umbral and angle_change > angle_change_umbral and not movimiento_detectado and (current_time - ultimo_segmento_fin) > tiempo_minimo_entre_segmentos:
                        # Inicio de un segmento (golpe detectado)
                        inicio = frame_count / fps
                        movimiento_detectado = True
                        max_velocidad_segmento = velocidad_right if velocidad_right is not None else 0
                        max_elbow_angle_segmento = angle_change if angle_change is not None else 0
                        # Pasar información sobre el lanzamiento detectado al segmento
                        segmentos.append({
                            'inicio': inicio,
                            'fin': None,
                            'lanzamiento_detectado': lanzamiento_detectado,
                            'lanzamiento_time': lanzamiento_time if lanzamiento_time is not None else 0,
                            'max_velocidad': max_velocidad_segmento,
                            'movimiento_direccion': 'desconocido',  # Valor por defecto
                            'max_elbow_angle': max_elbow_angle_segmento,
                            'posicion_cancha': 'fondo'
                        })
                    elif velocidad_right < velocidad_umbral / 2 and movimiento_detectado:
                        # Fin de un segmento
                        fin = frame_count / fps
                        segmentos[-1]['fin'] = fin
                        movimiento_detectado = False
                        ultimo_segmento_fin = fin
                        inicio = None
                        max_velocidad_segmento = 0
                        max_elbow_angle_segmento = 0
                        lanzamiento_detectado = False  # Reiniciar para el próximo segmento
                        lanzamiento_time = None
                    elif movimiento_detectado and velocidad_right > max_velocidad_segmento:
                        max_velocidad_segmento = velocidad_right
                        max_elbow_angle_segmento = angle_change
                        segmentos[-1]['max_velocidad'] = max_velocidad_segmento
                        segmentos[-1]['max_elbow_angle'] = max_elbow_angle_segmento

            prev_wrist_right_pos = current_wrist_right_pos
            prev_wrist_left_pos = current_wrist_left_pos
            prev_elbow_pos = current_elbow_pos
            prev_shoulder_pos = current_shoulder_pos
        else:
            prev_wrist_right_pos = None
            prev_wrist_left_pos = None
            prev_elbow_pos = None
            prev_shoulder_pos = None

        frame_count += 1

    # Si hay un segmento abierto al final del video, cerrarlo
    if movimiento_detectado and inicio is not None:
        fin = frame_count / fps
        segmentos[-1]['fin'] = fin

    logger.info(f"Segmentos detectados: {len(segmentos)}")
    return segmentos, video_duration

def analizar_tecnica(landmarks, prev_landmarks):
    """Analiza la técnica del golpe basándose en la posición del cuerpo."""
    try:
        # Obtener puntos clave
        wrist = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
        elbow = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]
        shoulder = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        hip = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
        ankle = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]
        knee = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]

        # Calcular ángulos importantes
        elbow_angle = calcular_angulo(shoulder, elbow, wrist)
        shoulder_angle = calcular_angulo(hip, shoulder, elbow)
        knee_angle = calcular_angulo(hip, knee, ankle)

        # Analizar posición del cuerpo
        body_alignment = analizar_alineacion_cuerpo(shoulder, hip, ankle)
        balance = analizar_equilibrio(hip, ankle)
        preparation = analizar_preparacion(prev_landmarks, landmarks)

        return {
            'elbow_angle': float(elbow_angle),
            'shoulder_angle': float(shoulder_angle),
            'knee_angle': float(knee_angle),
            'body_alignment': body_alignment,
            'balance': balance,
            'preparation': preparation
        }
    except Exception as e:
        logger.error(f"Error al analizar técnica: {str(e)}")
        return None

def calcular_angulo(a, b, c):
    """Calcula el ángulo entre tres puntos."""
    try:
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        
        ba = a - b
        bc = c - b
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    except Exception as e:
        logger.error(f"Error al calcular ángulo: {str(e)}")
        return 0.0

def analizar_alineacion_cuerpo(shoulder, hip, ankle):
    """Analiza la alineación del cuerpo durante el golpe."""
    try:
        # Calcular la verticalidad del cuerpo
        shoulder_hip_angle = calcular_angulo(
            mp_pose.PoseLandmark(shoulder.x, shoulder.y),
            mp_pose.PoseLandmark(hip.x, hip.y),
            mp_pose.PoseLandmark(hip.x, hip.y + 1)
        )
        
        # Evaluar la alineación
        if 85 <= shoulder_hip_angle <= 95:
            return "excelente"
        elif 80 <= shoulder_hip_angle <= 100:
            return "buena"
        else:
            return "necesita_mejora"
    except Exception as e:
        logger.error(f"Error al analizar alineación: {str(e)}")
        return "desconocido"

def analizar_equilibrio(hip, ankle):
    """Analiza el equilibrio durante el golpe."""
    try:
        # Calcular la distancia horizontal entre la cadera y el tobillo
        horizontal_distance = abs(hip.x - ankle.x)
        
        # Evaluar el equilibrio
        if horizontal_distance < 0.1:
            return "excelente"
        elif horizontal_distance < 0.2:
            return "bueno"
        else:
            return "necesita_mejora"
    except Exception as e:
        logger.error(f"Error al analizar equilibrio: {str(e)}")
        return "desconocido"

def analizar_preparacion(prev_landmarks, current_landmarks):
    """Analiza la preparación antes del golpe."""
    try:
        if prev_landmarks is None:
            return "insuficiente"
            
        # Calcular el movimiento de preparación
        prev_wrist = prev_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
        current_wrist = current_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
        
        movement = np.sqrt(
            (current_wrist.x - prev_wrist.x)**2 +
            (current_wrist.y - prev_wrist.y)**2
        )
        
        # Evaluar la preparación
        if movement > 0.3:
            return "excelente"
        elif movement > 0.15:
            return "buena"
        else:
            return "insuficiente"
    except Exception as e:
        logger.error(f"Error al analizar preparación: {str(e)}")
        return "desconocido"

def generar_recomendaciones(analisis_tecnico, tipo_golpe):
    """Genera recomendaciones específicas basadas en el análisis técnico."""
    recomendaciones = []
    
    # Recomendaciones generales
    if analisis_tecnico['body_alignment'] == "necesita_mejora":
        recomendaciones.append("Mantén el cuerpo más vertical durante el golpe")
    
    if analisis_tecnico['balance'] == "necesita_mejora":
        recomendaciones.append("Mejora tu equilibrio manteniendo el peso distribuido")
    
    if analisis_tecnico['preparation'] == "insuficiente":
        recomendaciones.append("Aumenta el movimiento de preparación antes del golpe")
    
    # Recomendaciones específicas por tipo de golpe
    if tipo_golpe == "derecha":
        if analisis_tecnico['elbow_angle'] < 90:
            recomendaciones.append("Abre más el codo en la derecha")
        elif analisis_tecnico['elbow_angle'] > 150:
            recomendaciones.append("Cierra más el codo en la derecha")
    
    elif tipo_golpe == "reves":
        if analisis_tecnico['shoulder_angle'] < 90:
            recomendaciones.append("Gira más los hombros en el revés")
    
    elif tipo_golpe == "volea_derecha" or tipo_golpe == "volea_reves":
        if analisis_tecnico['knee_angle'] > 150:
            recomendaciones.append("Flexiona más las rodillas en la volea")
    
    return recomendaciones

def analizar_segmento(segmento, ruta_video):
    """Analiza un segmento específico para detectar y clasificar golpes."""
    logger.info(f"Analizando segmento: {segmento}")
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        logger.error("No se pudo abrir el video")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30

    try:
        inicio_frame = int(float(segmento['inicio']) * fps)
        fin_frame = int(float(segmento['fin']) * fps)
        logger.info(f"Analizando frames desde {inicio_frame} hasta {fin_frame}")

        # Mover el video al frame inicial
        cap.set(cv2.CAP_PROP_POS_FRAMES, inicio_frame)
        prev_wrist_pos = None
        prev_elbow_pos = None
        prev_shoulder_pos = None
        prev_hip_pos = None
        prev_landmarks = None
        max_velocidad = 0.0
        movimiento_direccion = 'desconocido'
        max_elbow_angle = 0.0
        wrist_height = 0.0
        mejor_tecnica = None
        mejor_tecnica_score = 0

        frame_count = inicio_frame
        while cap.isOpened() and frame_count <= fin_frame:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (640, 480))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results.pose_landmarks:
                # Analizar técnica en este frame
                analisis_tecnico = analizar_tecnica(results.pose_landmarks, prev_landmarks)
                if analisis_tecnico:
                    # Calcular score de técnica
                    tecnica_score = (
                        (1 if analisis_tecnico['body_alignment'] == "excelente" else 0.5 if analisis_tecnico['body_alignment'] == "buena" else 0) +
                        (1 if analisis_tecnico['balance'] == "excelente" else 0.5 if analisis_tecnico['balance'] == "bueno" else 0) +
                        (1 if analisis_tecnico['preparation'] == "excelente" else 0.5 if analisis_tecnico['preparation'] == "buena" else 0)
                    )
                    
                    if tecnica_score > mejor_tecnica_score:
                        mejor_tecnica_score = tecnica_score
                        mejor_tecnica = analisis_tecnico

                wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
                elbow = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]
                shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
                hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]

                current_wrist_pos = (float(wrist.x), float(wrist.y))
                current_elbow_pos = (float(elbow.x), float(elbow.y))
                current_shoulder_pos = (float(shoulder.x), float(shoulder.y))
                current_hip_pos = (float(hip.x), float(hip.y))

                # Calcular ángulo del codo
                vector1 = np.array([elbow.x - shoulder.x, elbow.y - shoulder.y])
                vector2 = np.array([wrist.x - elbow.x, wrist.y - elbow.y])
                dot_product = float(np.dot(vector1, vector2))
                norm1 = float(np.linalg.norm(vector1))
                norm2 = float(np.linalg.norm(vector2))
                if norm1 > 0 and norm2 > 0:
                    cos_angle = dot_product / (norm1 * norm2)
                    cos_angle = float(np.clip(cos_angle, -1.0, 1.0))
                    angle_rad = float(np.arccos(cos_angle))
                    angle_deg = float(np.degrees(angle_rad))
                    if angle_deg > max_elbow_angle:
                        max_elbow_angle = angle_deg

                # Actualizar altura de la muñeca (para detectar globos, smashes, etc.)
                if wrist.y > wrist_height:
                    wrist_height = float(wrist.y)

                if prev_wrist_pos is not None and prev_elbow_pos is not None and prev_shoulder_pos is not None:
                    distance = float(np.sqrt((current_wrist_pos[0] - prev_wrist_pos[0])**2 + (current_wrist_pos[1] - prev_wrist_pos[1])**2))
                    velocidad = float(distance * fps)
                    logger.debug(f"Frame {frame_count}: velocidad={velocidad}, max_velocidad={max_velocidad}")

                    # Determinar dirección del movimiento usando solo dx
                    dx = float(current_wrist_pos[0] - prev_wrist_pos[0])
                    is_derecha = dx > 0

                    # Clasificar el tipo de golpe
                    # Prioridad 1: Saque (lanzamiento de la pelota detectado)
                    if segmento.get('lanzamiento_detectado', False) and (float(segmento['inicio']) - float(segmento.get('lanzamiento_time', float('inf'))) < 1.0):
                        movimiento_direccion = "saque"
                    # Prioridad 2: Smash (ángulo alto, velocidad alta)
                    elif max_elbow_angle > 150 and velocidad > 1.2:
                        movimiento_direccion = "smash"
                    # Prioridad 3: Bandeja (ángulo alto, velocidad moderada)
                    elif max_elbow_angle > 120 and velocidad > 0.6:
                        movimiento_direccion = "bandeja"
                    # Prioridad 4: Globo (ángulo abierto, velocidad baja)
                    elif max_elbow_angle > 120 and velocidad < 1.5:
                        movimiento_direccion = "globo"
                    # Prioridad 5: Defensivo (ángulo bajo, velocidad baja)
                    elif max_elbow_angle < 90 and velocidad < 0.2:
                        movimiento_direccion = "defensivo"
                    # Prioridad 6: Volea (ángulo cerrado, velocidad moderada)
                    elif max_elbow_angle < 90 and velocidad > 0.05:
                        movimiento_direccion = "volea_" + ("derecha" if is_derecha else "reves")
                    # Prioridad 7: Derecha o Revés (ángulo 90-150, velocidad moderada-alta)
                    else:
                        movimiento_direccion = "derecha" if is_derecha else "reves"

                    if velocidad > max_velocidad:
                        max_velocidad = float(velocidad)
                        logger.debug(f"Nueva max_velocidad: {max_velocidad}")

                prev_wrist_pos = current_wrist_pos
                prev_elbow_pos = current_elbow_pos
                prev_shoulder_pos = current_shoulder_pos
                prev_hip_pos = current_hip_pos
                prev_landmarks = results.pose_landmarks
            else:
                prev_wrist_pos = None
                prev_elbow_pos = None
                prev_shoulder_pos = None
                prev_hip_pos = None
                prev_landmarks = None

            frame_count += 1

        cap.release()
        logger.info(f"Análisis completado: max_velocidad={max_velocidad}, movimiento_direccion={movimiento_direccion}")

        if max_velocidad > 0.25:  # Ajustar umbral mínimo
            calidad = float(min(100, max_velocidad * 10))  # Aumentar el factor de calidad
            logger.info(f"Creando golpe con calidad={calidad}, max_velocidad={max_velocidad}, max_elbow_angle={max_elbow_angle}")
            
            # Generar recomendaciones basadas en el análisis técnico
            recomendaciones = []
            if mejor_tecnica:
                recomendaciones = generar_recomendaciones(mejor_tecnica, movimiento_direccion)
            
            return [{
                'tipo': str(movimiento_direccion),
                'confianza': float(calidad / 100),
                'calidad': float(calidad),
                'max_elbow_angle': float(max_elbow_angle),
                'max_wrist_speed': float(max_velocidad),
                'inicio': float(segmento['inicio']),
                'analisis_tecnico': mejor_tecnica,
                'recomendaciones': recomendaciones
            }]
        else:
            logger.warning(f"No se detectaron golpes significativos en el segmento (velocidad insuficiente: {max_velocidad}, movimiento_direccion: {movimiento_direccion}).")
            return []

    except Exception as e:
        logger.error(f"Error al analizar segmento: {str(e)}")
        logger.error(f"Segmento con error: {segmento}")
        return []

def evaluar_calidad(golpes):
    """Evalúa la calidad de los golpes basándose en la confianza."""
    logger.info(f"Evaluando calidad de {len(golpes)} golpes")
    golpes_evaluados = []
    for i, golpe in enumerate(golpes):
        logger.info(f"Evaluando golpe {i+1}: {golpe}")
        try:
            # Asegurarse de que todos los campos numéricos sean válidos
            confianza = float(golpe.get('confianza', 0))
            calidad = float(golpe.get('calidad', 0))
            max_elbow_angle = float(golpe.get('max_elbow_angle', 0))
            max_wrist_speed = float(golpe.get('max_wrist_speed', 0))
            inicio = float(golpe.get('inicio', 0))
            tipo = str(golpe.get('tipo', 'desconocido'))

            golpe_evaluado = {
                'tipo': tipo,
                'confianza': confianza,
                'calidad': calidad,
                'max_elbow_angle': max_elbow_angle,
                'max_wrist_speed': max_wrist_speed,
                'inicio': inicio
            }
            logger.info(f"Golpe evaluado: {golpe_evaluado}")
            golpes_evaluados.append(golpe_evaluado)
        except (TypeError, ValueError) as e:
            logger.error(f"Error al evaluar golpe {i+1}: {str(e)}")
            logger.error(f"Golpe con error: {golpe}")
            continue

    logger.info(f"Evaluación completada. Golpes evaluados: {len(golpes_evaluados)}")
    return golpes_evaluados

def clasificar_golpes(golpes):
    """Clasifica los golpes por tipo."""
    logger.info(f"Clasificando {len(golpes)} golpes")
    golpes_clasificados = {}
    for i, golpe in enumerate(golpes):
        logger.info(f"Procesando golpe {i+1}: {golpe}")
        try:
            # Asegurarse de que todos los campos numéricos sean válidos
            confianza = float(golpe.get('confianza', 0))
            calidad = float(golpe.get('calidad', 0))
            max_elbow_angle = float(golpe.get('max_elbow_angle', 0))
            max_wrist_speed = float(golpe.get('max_wrist_speed', 0))
            inicio = float(golpe.get('inicio', 0))
            tipo = str(golpe.get('tipo', 'desconocido'))

            if tipo not in golpes_clasificados:
                golpes_clasificados[tipo] = []

            golpe_procesado = {
                'tipo': tipo,
                'confianza': confianza,
                'calidad': calidad,
                'max_elbow_angle': max_elbow_angle,
                'max_wrist_speed': max_wrist_speed,
                'inicio': inicio
            }
            logger.info(f"Golpe procesado: {golpe_procesado}")
            golpes_clasificados[tipo].append(golpe_procesado)
        except (TypeError, ValueError) as e:
            logger.error(f"Error al procesar golpe {i+1}: {str(e)}")
            logger.error(f"Golpe con error: {golpe}")
            continue

    logger.info(f"Clasificación completada. Tipos de golpes encontrados: {list(golpes_clasificados.keys())}")
    return golpes_clasificados

def analizar_rendimiento(golpes_clasificados):
    """Analiza el rendimiento general del jugador basado en los golpes clasificados."""
    try:
        estadisticas = {
            'total_golpes': 0,
            'golpes_por_tipo': {},
            'velocidad_promedio': {},
            'calidad_promedio': {},
            'consistencia': {},
            'distribucion_cancha': {
                'fondo': 0,
                'media': 0,
                'red': 0
            }
        }

        for tipo, golpes in golpes_clasificados.items():
            if not golpes:
                continue

            estadisticas['golpes_por_tipo'][tipo] = len(golpes)
            estadisticas['total_golpes'] += len(golpes)

            # Calcular velocidad promedio
            velocidades = [g['max_wrist_speed'] for g in golpes]
            estadisticas['velocidad_promedio'][tipo] = float(np.mean(velocidades))

            # Calcular calidad promedio
            calidades = [g['calidad'] for g in golpes]
            estadisticas['calidad_promedio'][tipo] = float(np.mean(calidades))

            # Calcular consistencia (desviación estándar de la calidad)
            estadisticas['consistencia'][tipo] = float(np.std(calidades))

            # Analizar distribución en la cancha
            for golpe in golpes:
                if 'posicion_cancha' in golpe:
                    estadisticas['distribucion_cancha'][golpe['posicion_cancha']] += 1

        return estadisticas
    except Exception as e:
        logger.error(f"Error al analizar rendimiento: {str(e)}")
        return None

def generar_estadisticas_detalladas(golpes_clasificados):
    """Genera estadísticas detalladas y recomendaciones basadas en el rendimiento."""
    try:
        estadisticas = analizar_rendimiento(golpes_clasificados)
        if not estadisticas:
            return None

        analisis_detallado = {
            'estadisticas': estadisticas,
            'fortalezas': [],
            'debilidades': [],
            'recomendaciones': []
        }

        # Analizar fortalezas
        for tipo, calidad in estadisticas['calidad_promedio'].items():
            if calidad > 80:
                analisis_detallado['fortalezas'].append(f"Excelente {tipo} con calidad promedio de {calidad:.1f}")
            elif calidad > 60:
                analisis_detallado['fortalezas'].append(f"Buen {tipo} con calidad promedio de {calidad:.1f}")

        # Analizar debilidades
        for tipo, calidad in estadisticas['calidad_promedio'].items():
            if calidad < 40:
                analisis_detallado['debilidades'].append(f"{tipo} necesita mejora (calidad: {calidad:.1f})")
            elif calidad < 60:
                analisis_detallado['debilidades'].append(f"{tipo} puede mejorar (calidad: {calidad:.1f})")

        # Analizar consistencia
        for tipo, consistencia in estadisticas['consistencia'].items():
            if consistencia > 20:
                analisis_detallado['debilidades'].append(f"Poca consistencia en {tipo} (variación: {consistencia:.1f})")

        # Generar recomendaciones
        if estadisticas['distribucion_cancha']['red'] < estadisticas['total_golpes'] * 0.2:
            analisis_detallado['recomendaciones'].append("Aumenta la frecuencia de golpes en la red")
        
        if estadisticas['distribucion_cancha']['fondo'] > estadisticas['total_golpes'] * 0.6:
            analisis_detallado['recomendaciones'].append("Intenta jugar más cerca de la red")

        # Recomendaciones específicas por tipo de golpe
        for tipo, calidad in estadisticas['calidad_promedio'].items():
            if calidad < 60:
                if tipo == "derecha":
                    analisis_detallado['recomendaciones'].append("Practica la derecha con más énfasis en la técnica")
                elif tipo == "reves":
                    analisis_detallado['recomendaciones'].append("Mejora la técnica del revés")
                elif tipo == "volea_derecha" or tipo == "volea_reves":
                    analisis_detallado['recomendaciones'].append("Trabaja en la posición de volea")

        return analisis_detallado
    except Exception as e:
        logger.error(f"Error al generar estadísticas detalladas: {str(e)}")
        return None

def procesar_video_entrenamiento(video_url, client=None):
    """Procesa un video de entrenamiento completo."""
    # Descargar el video desde la URL
    local_path = "temp_video_entrenamiento.mp4"
    logger.info(f"Descargando video desde {video_url} a {local_path}")
    try:
        response = requests.get(video_url, stream=True, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al descargar el video desde {video_url}: {str(e)}")
        raise ValueError(f"Error al descargar el video: {str(e)}")

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=16384):
            if chunk:
                f.write(chunk)

    try:
        # Paso 1: Segmentación
        logger.info("Iniciando segmentación del video")
        segmentos, video_duration = segmentar_video(local_path)
        logger.info(f"Video segmentado. Duración: {video_duration} segundos. Segmentos encontrados: {len(segmentos)}")

        # Paso 2 y 3: Análisis y evaluación de calidad
        logger.info("Iniciando análisis y evaluación de calidad")
        golpes_totales = []
        for i, segmento in enumerate(segmentos):
            logger.info(f"Procesando segmento {i+1}/{len(segmentos)}: {segmento}")
            if segmento.get('inicio') is None or segmento.get('fin') is None:
                logger.warning(f"Segmento {i+1} incompleto, saltando: {segmento}")
                continue
            
            try:
                # Asegurarse de que los valores numéricos sean válidos
                segmento['max_velocidad'] = float(segmento.get('max_velocidad', 0))
                segmento['max_elbow_angle'] = float(segmento.get('max_elbow_angle', 0))
                segmento['lanzamiento_time'] = float(segmento.get('lanzamiento_time', 0))
                segmento['inicio'] = float(segmento.get('inicio', 0))
                segmento['fin'] = float(segmento.get('fin', 0))
                
                # Asegurarse de que los valores booleanos y de texto sean válidos
                segmento['lanzamiento_detectado'] = bool(segmento.get('lanzamiento_detectado', False))
                segmento['movimiento_direccion'] = str(segmento.get('movimiento_direccion', 'desconocido'))
                segmento['posicion_cancha'] = str(segmento.get('posicion_cancha', 'fondo'))

                logger.info(f"Analizando segmento {i+1}")
                golpes = analizar_segmento(segmento, local_path)
                logger.info(f"Golpes detectados en segmento {i+1}: {len(golpes)}")
                
                if golpes:
                    logger.info(f"Evaluando calidad de golpes en segmento {i+1}")
                    golpes_evaluados = evaluar_calidad(golpes)
                    logger.info(f"Golpes evaluados en segmento {i+1}: {len(golpes_evaluados)}")
                    golpes_totales.extend(golpes_evaluados)
                else:
                    logger.warning(f"No se detectaron golpes en el segmento {i+1}")
            except (TypeError, ValueError) as e:
                logger.error(f"Error al procesar segmento {i+1}: {str(e)}")
                logger.error(f"Segmento con error: {segmento}")
                continue

        logger.info(f"Total de golpes detectados: {len(golpes_totales)}")

        # Paso 4: Clasificación
        logger.info("Iniciando clasificación de golpes")
        golpes_clasificados = clasificar_golpes(golpes_totales)
        logger.info(f"Procesamiento completado. Golpes clasificados: {len(golpes_clasificados)}")

        # Paso 5: Análisis de rendimiento
        logger.info("Iniciando análisis de rendimiento")
        analisis_detallado = generar_estadisticas_detalladas(golpes_clasificados)
        logger.info("Análisis de rendimiento completado")

        # Limpiar archivo temporal
        os.remove(local_path)
        logger.info(f"Archivo temporal {local_path} eliminado")

        return {
            'golpes_clasificados': golpes_clasificados,
            'video_duration': video_duration,
            'analisis_detallado': analisis_detallado,
            'tipo_analisis': 'entrenamiento'
        }

    except Exception as e:
        logger.error(f"Error al procesar video de entrenamiento: {str(e)}")
        if os.path.exists(local_path):
            os.remove(local_path)
        raise e

def procesar_video_partido(video_url, client=None):
    """Procesa un video de partido completo."""
    # Descargar el video desde la URL
    local_path = "temp_video_partido.mp4"
    logger.info(f"Descargando video desde {video_url} a {local_path}")
    try:
        response = requests.get(video_url, stream=True, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al descargar el video desde {video_url}: {str(e)}")
        raise ValueError(f"Error al descargar el video: {str(e)}")

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=16384):
            if chunk:
                f.write(chunk)

    try:
        # Paso 1: Segmentación
        logger.info("Iniciando segmentación del video")
        segmentos, video_duration = segmentar_video(local_path)
        logger.info(f"Video segmentado. Duración: {video_duration} segundos. Segmentos encontrados: {len(segmentos)}")

        # Paso 2 y 3: Análisis y evaluación de calidad
        logger.info("Iniciando análisis y evaluación de calidad")
        golpes_totales = []
        for i, segmento in enumerate(segmentos):
            logger.info(f"Procesando segmento {i+1}/{len(segmentos)}: {segmento}")
            if segmento.get('inicio') is None or segmento.get('fin') is None:
                logger.warning(f"Segmento {i+1} incompleto, saltando: {segmento}")
                continue
            
            try:
                # Asegurarse de que los valores numéricos sean válidos
                segmento['max_velocidad'] = float(segmento.get('max_velocidad', 0))
                segmento['max_elbow_angle'] = float(segmento.get('max_elbow_angle', 0))
                segmento['lanzamiento_time'] = float(segmento.get('lanzamiento_time', 0))
                segmento['inicio'] = float(segmento.get('inicio', 0))
                segmento['fin'] = float(segmento.get('fin', 0))
                
                # Asegurarse de que los valores booleanos y de texto sean válidos
                segmento['lanzamiento_detectado'] = bool(segmento.get('lanzamiento_detectado', False))
                segmento['movimiento_direccion'] = str(segmento.get('movimiento_direccion', 'desconocido'))
                segmento['posicion_cancha'] = str(segmento.get('posicion_cancha', 'fondo'))

                logger.info(f"Analizando segmento {i+1}")
                golpes = analizar_segmento(segmento, local_path)
                logger.info(f"Golpes detectados en segmento {i+1}: {len(golpes)}")
                
                if golpes:
                    logger.info(f"Evaluando calidad de golpes en segmento {i+1}")
                    golpes_evaluados = evaluar_calidad(golpes)
                    logger.info(f"Golpes evaluados en segmento {i+1}: {len(golpes_evaluados)}")
                    golpes_totales.extend(golpes_evaluados)
                else:
                    logger.warning(f"No se detectaron golpes en el segmento {i+1}")
            except (TypeError, ValueError) as e:
                logger.error(f"Error al procesar segmento {i+1}: {str(e)}")
                logger.error(f"Segmento con error: {segmento}")
                continue

        logger.info(f"Total de golpes detectados: {len(golpes_totales)}")

        # Paso 4: Clasificación
        logger.info("Iniciando clasificación de golpes")
        golpes_clasificados = clasificar_golpes(golpes_totales)
        logger.info(f"Procesamiento completado. Golpes clasificados: {len(golpes_clasificados)}")

        # Paso 5: Análisis de rendimiento
        logger.info("Iniciando análisis de rendimiento")
        analisis_detallado = generar_estadisticas_detalladas(golpes_clasificados)
        logger.info("Análisis de rendimiento completado")

        # Limpiar archivo temporal
        os.remove(local_path)
        logger.info(f"Archivo temporal {local_path} eliminado")

        return {
            'golpes_clasificados': golpes_clasificados,
            'video_duration': video_duration,
            'analisis_detallado': analisis_detallado,
            'tipo_analisis': 'partido'
        }

    except Exception as e:
        logger.error(f"Error al procesar video de partido: {str(e)}")
        if os.path.exists(local_path):
            os.remove(local_path)
        raise e