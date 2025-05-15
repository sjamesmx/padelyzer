import logging
from datetime import datetime
from config.mock_firebase import client
from .video_processing import procesar_video_juego
from .pair_metrics import calculate_pair_metrics

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firestore client
db = client()

class AnalysisManager:
    """Administra la flexibilidad del análisis y aprende de históricos para mejorar la precisión."""
    
    def __init__(self):
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
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("No se pudo abrir el video para análisis de condiciones.")
            return self.default_params

        frames_to_analyze = 10
        brightness_values = []
        contrast_values = []
        frame_count = 0

        while cap.isOpened() and frame_count < frames_to_analyze:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            contrast = np.std(gray)

            brightness_values.append(brightness)
            contrast_values.append(contrast)
            frame_count += 1

        cap.release()

        avg_brightness = np.mean(brightness_values) if brightness_values else 128
        avg_contrast = np.mean(contrast_values) if contrast_values else 50

        params = self.default_params.copy()
        if avg_brightness < 50:
            params['min_detection_confidence'] = 0.3
            params['min_tracking_confidence'] = 0.3
            params['scale_factor'] = 0.9
            logger.info("Video oscuro detectado, ajustando parámetros.")
        elif avg_brightness > 200:
            params['min_detection_confidence'] = 0.6
            params['min_tracking_confidence'] = 0.6
            logger.info("Video muy brillante detectado, ajustando parámetros.")

        if avg_contrast < 30:
            params['velocidad_umbral'] = 0.0005
            params['frame_skip'] = 15
            logger.info("Bajo contraste detectado, ajustando parámetros.")
        elif avg_contrast > 70:
            params['velocidad_umbral'] = 0.0001
            params['frame_skip'] = 10
            logger.info("Alto contraste detectado, ajustando parámetros.")

        return params

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
        video_conditions = self.analyze_video_conditions(video_url)
        params = self.optimize_parameters(video_url)

        golpes_clasificados, video_duration, player_trajectories = procesar_video_juego(
            video_url,
            player_position,
            game_splits=game_splits,
            custom_params=params
        )

        golpes_clasificados = self.post_filter_strokes(golpes_clasificados)

        pair_metrics = calculate_pair_metrics(player_trajectories, golpes_clasificados)

        self.save_historical_data(video_id, golpes_clasificados, video_conditions)

        return golpes_clasificados, video_duration, pair_metrics