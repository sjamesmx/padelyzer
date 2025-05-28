import os
import logging
import tensorflow as tf
import cv2
import numpy as np
from datetime import datetime
from config.mock_firebase import client
from .pair_metrics import calculate_pair_metrics
from typing import Dict, Any, Optional
from app.services.padel_iq_calculator import calculate_padel_iq_granular
from app.services.video_processor import VideoProcessor
from app.services.player_detector import PlayerDetector
import torch

# Suppress TensorFlow warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # 0 = all logs, 1 = filter INFO, 2 = filter WARNING, 3 = filter ERROR
tf.get_logger().setLevel(logging.ERROR)

# Configurar logging con formato detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Firestore client
db = client()

class AnalysisManager:
    """Administra la flexibilidad del análisis y aprende de históricos para mejorar la precisión."""
    
    def __init__(self):
        logger.info("Inicializando AnalysisManager")
        self.video_processor = VideoProcessor()
        self.player_detector = PlayerDetector()
        self.default_params = {
            'velocidad_umbral': 0.0001,
            'max_segment_duration': 1.5,
            'frame_skip': 12,
            'scale_factor': 0.8,
            'min_detection_confidence': 0.05,
            'min_tracking_confidence': 0.05
        }
        self.historical_data = []
        self.load_historical_data()

    def load_historical_data(self):
        """Carga datos históricos desde Firestore."""
        try:
            historical_ref = db.collection('historical_analysis').get()
            for doc in historical_ref:
                self.historical_data.append(doc.to_dict())
            logger.info(f"Cargados {len(self.historical_data)} registros históricos.")
        except Exception as e:
            logger.error(f"Error al cargar datos históricos: {str(e)}")
            self.historical_data = []

    def save_historical_data(self, video_id, golpes_clasificados, video_conditions):
        """Guarda los datos del análisis en Firestore para aprendizaje futuro."""
        try:
            historical_entry = {
                'video_id': video_id,
                'golpes_clasificados': golpes_clasificados,
                'video_conditions': video_conditions,
                'timestamp': datetime.now()
            }
            db.collection('historical_analysis').add(historical_entry)
            self.historical_data.append(historical_entry)
            logger.info(f"Datos históricos guardados para video {video_id}.")
        except Exception as e:
            logger.error(f"Error al guardar datos históricos: {str(e)}")

    def analyze_video_conditions(self, video_path):
        """Analiza las condiciones del video para ajustar parámetros dinámicamente."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error("No se pudo abrir el video para análisis de condiciones.")
                return self.default_params

            frames_to_analyze = 10
            frame_interval = 30  # Analizar cada 30 frames
            brightness_values = []
            contrast_values = []
            frame_count = 0
            total_frames = 0

            while cap.isOpened() and len(brightness_values) < frames_to_analyze:
                ret, frame = cap.read()
                if not ret:
                    break

                total_frames += 1
                if total_frames % frame_interval != 0:
                    continue

                # Convertir a tensor y mover a GPU si está disponible
                if torch.backends.mps.is_available():
                    frame_tensor = torch.from_numpy(frame).to("mps")
                    gray_tensor = frame_tensor.mean(dim=2)  # Promedio de canales RGB
                    brightness = float(gray_tensor.mean().cpu().numpy())
                    contrast = float(gray_tensor.std().cpu().numpy())
                else:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    brightness = np.mean(gray)
                    contrast = np.std(gray)

                brightness_values.append(brightness)
                contrast_values.append(contrast)
                frame_count += 1

            cap.release()

            if not brightness_values:
                logger.warning("No se pudieron analizar frames, usando parámetros por defecto")
                return self.default_params

            avg_brightness = np.mean(brightness_values)
            avg_contrast = np.mean(contrast_values)

            params = self.default_params.copy()
            
            # Ajustar parámetros basados en condiciones
            if avg_brightness < 50:
                params['min_detection_confidence'] = 0.3
                params['min_tracking_confidence'] = 0.3
                params['scale_factor'] = 0.9
                logger.info(f"Video oscuro detectado (brillo: {avg_brightness:.2f}), ajustando parámetros")
            elif avg_brightness > 200:
                params['min_detection_confidence'] = 0.6
                params['min_tracking_confidence'] = 0.6
                logger.info(f"Video muy brillante detectado (brillo: {avg_brightness:.2f}), ajustando parámetros")

            if avg_contrast < 30:
                params['velocidad_umbral'] = 0.0005
                params['frame_skip'] = 15
                logger.info(f"Bajo contraste detectado ({avg_contrast:.2f}), ajustando parámetros")
            elif avg_contrast > 70:
                params['velocidad_umbral'] = 0.0001
                params['frame_skip'] = 10
                logger.info(f"Alto contraste detectado ({avg_contrast:.2f}), ajustando parámetros")

            return params

        except Exception as e:
            logger.error(f"Error en analyze_video_conditions: {str(e)}", exc_info=True)
            return self.default_params

    def optimize_parameters(self, video_path):
        """Optimiza los parámetros de análisis basándose en las condiciones del video y datos históricos."""
        params = self.analyze_video_conditions(video_path)

        if self.historical_data:
            avg_wrist_speed = np.mean([golpe['max_wrist_speed'] for entry in self.historical_data for golpe in entry['golpes_clasificados'].values() for golpe in golpe])
            if avg_wrist_speed < 10:
                params['velocidad_umbral'] = max(0.0001, params['velocidad_umbral'] * 0.5)
                logger.info(f"Ajustando velocidad_umbral a {params['velocidad_umbral']} basado en datos históricos.")
            elif avg_wrist_speed > 40:
                params['velocidad_umbral'] = min(0.002, params['velocidad_umbral'] * 1.5)
                logger.info(f"Ajustando velocidad_umbral a {params['velocidad_umbral']} basado en datos históricos.")

        return params

    def post_filter_strokes(self, golpes_clasificados):
        """Aplica un post-filtro para descartar golpes que no cumplan con criterios estrictos."""
        filtered_golpes = {}
        for tipo, golpes in golpes_clasificados.items():
            filtered = []
            for golpe in golpes:
                if golpe['max_wrist_speed'] < 0.5:  # Relajar aún más
                    logger.info(f"Descartando golpe {tipo} en {golpe['inicio']} por baja velocidad: {golpe['max_wrist_speed']}")
                    continue
                filtered.append(golpe)
            if filtered:
                filtered_golpes[tipo] = filtered

        return filtered_golpes

    def process_video(self, video_url, player_position, game_splits, video_id):
        """Procesa un video con parámetros optimizados, aplica post-filtro y guarda los resultados históricos."""
        try:
            logger.info(f"Iniciando procesamiento de video: {video_url}")
            video_conditions = self.analyze_video_conditions(video_url)
            params = self.optimize_parameters(video_url)

            # Procesar video usando VideoProcessor
            frames = self.video_processor.process_video(video_url)
            logger.debug(f"Procesados {len(frames)} frames del video")

            # Detectar jugador si no se proporciona posición
            if not player_position:
                logger.debug("Detectando posición del jugador automáticamente")
                player_position = self.player_detector.detect_player(frames[0])

            # Analizar el juego
            game_data = self.video_processor.analyze_game(frames, player_position)
            logger.info(f"Análisis de juego completado: {len(game_data.get('strokes', []))} golpes detectados")

            # Aplicar post-filtro a los golpes
            strokes = game_data.get('strokes', [])
            filtered_strokes = self.post_filter_strokes({'all': strokes})
            game_data['strokes'] = filtered_strokes.get('all', [])

            # Calcular métricas de pareja si hay trayectorias disponibles
            player_trajectories = game_data.get('player_trajectories', [])
            pair_metrics = calculate_pair_metrics(player_trajectories, {'all': game_data['strokes']})

            # Guardar datos históricos
            self.save_historical_data(video_id, {'all': game_data['strokes']}, video_conditions)

            return game_data['strokes'], game_data.get('video_duration', 0), pair_metrics

        except Exception as e:
            logger.error(f"Error en process_video: {str(e)}", exc_info=True)
            raise

    def analyze_training_video(self, video_url: str, player_position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analiza un video de entrenamiento y calcula el Padel IQ."""
        try:
            logger.info(f"Iniciando análisis de video de entrenamiento: {video_url}")
            
            # Procesar video
            frames = self.video_processor.process_video(video_url)
            logger.debug(f"Procesados {len(frames)} frames del video")
            
            # Detectar jugador si no se proporciona posición
            if not player_position:
                logger.debug("Detectando posición del jugador automáticamente")
                player_position = self.player_detector.detect_player(frames[0])

            # Analizar golpes
            strokes = self.video_processor.analyze_strokes(frames, player_position)
            logger.info(f"Detectados {len(strokes)} golpes en el video")

            if not strokes:
                logger.warning(f"No se detectaron golpes en el video: {video_url}")
                metrics = {
                    'total_strokes': 0,
                    'stroke_types': {},
                    'max_elbow_angle': 0,
                    'max_wrist_speed': 0,
                    'avg_stroke_interval': 0
                }
                padel_iq = {
                    'tecnica': 0,
                    'fuerza': 0,
                    'ritmo': 0,
                    'repeticion': 0,
                    'padel_iq': 0
                }
                return {
                    'padel_iq': padel_iq,
                    'metrics': metrics,
                    'strokes': []
                }

            # Calcular métricas
            metrics = {
                'total_strokes': len(strokes),
                'stroke_types': self._count_stroke_types(strokes),
                'max_elbow_angle': max(s['elbow_angle'] for s in strokes),
                'max_wrist_speed': max(s['wrist_speed'] for s in strokes),
                'avg_stroke_interval': self._calculate_avg_interval(strokes)
            }
            logger.debug(f"Métricas calculadas: {metrics}")

            # Calcular Padel IQ
            padel_iq = calculate_padel_iq_granular(
                max_elbow_angle=metrics['max_elbow_angle'],
                max_wrist_speed=metrics['max_wrist_speed'],
                tipo='training'
            )
            logger.info(f"Padel IQ calculado: {padel_iq['padel_iq']}")

            return {
                'padel_iq': padel_iq,
                'metrics': metrics,
                'strokes': strokes
            }

        except Exception as e:
            logger.error(f"Error en análisis de entrenamiento: {str(e)}", exc_info=True)
            raise