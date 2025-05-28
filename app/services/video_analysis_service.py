from typing import Dict, Any, Optional, List
import logging
import cv2
import numpy as np
from .video_processor import VideoProcessor
from .player_detector import PlayerDetector
from .stroke_detector import StrokeDetector
from .movement_analyzer import MovementAnalyzer
import os

logger = logging.getLogger(__name__)

class VideoAnalysisService:
    """Servicio para análisis de videos de pádel y detección de golpes."""
    
    def __init__(
        self,
        model_size: str = "n",
        device: str = "cpu",
        backend: str = "yolo",
        roboflow_api_key: str = None,
        roboflow_model_url: str = None
    ):
        """
        Inicializa el servicio de análisis de video.
        
        Args:
            model_size: Tamaño del modelo YOLO ("n", "s", "m", "l", "x")
            device: Dispositivo para inferencia ("cpu", "cuda", "mps")
            backend: 'yolo' o 'roboflow'
            roboflow_api_key: API key privada de Roboflow (ejemplo: 'hQ56LqFHKY5SGZc7YkDf')
            roboflow_model_url: URL del endpoint de Roboflow (ejemplo: 'https://detect.roboflow.com/padel-player-detection-mffhh-kxrrq/1')
        """
        self.player_detector = PlayerDetector(
            model_size=model_size,
            device=device,
            backend=backend,
            roboflow_api_key=roboflow_api_key,
            roboflow_model_url=roboflow_model_url
        )
        self.stroke_detector = StrokeDetector()
        self.movement_analyzer = MovementAnalyzer()
        self.tracked_players = {}  # Diccionario para mantener el seguimiento de jugadores
        
    def _find_active_player(self, detections: List[Dict[str, Any]], frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Encuentra el jugador activo en el frame actual."""
        try:
            if not detections:
                return None
                
            active_player = None
            max_motion_score = 0
            
            for detection in detections:
                if not isinstance(detection, dict):
                    continue
                    
                # Calcular métricas de movimiento
                wrist_speed = detection.get('wrist_speed', 0)
                elbow_angle = detection.get('elbow_angle', 0)
                wrist_direction = detection.get('wrist_direction', 0)
                
                # Calcular score de movimiento
                motion_score = 0
                
                # Score por velocidad de muñeca
                if wrist_speed > 0.5:
                    motion_score += min(1.0, wrist_speed / 2.0)
                
                # Score por ángulo de codo
                if 60 <= elbow_angle <= 150:
                    angle_score = 1.0 - abs(90 - elbow_angle) / 90.0
                    motion_score += angle_score
                
                # Score por cambio de dirección
                if abs(wrist_direction) > 0.3:
                    motion_score += min(1.0, abs(wrist_direction))
                
                # Actualizar jugador activo si tiene mayor score
                if motion_score > max_motion_score:
                    max_motion_score = motion_score
                    active_player = detection
            
            # Solo considerar jugador activo si supera un umbral mínimo
            if max_motion_score > 0.5:
                return active_player
            
            return None
            
        except Exception as e:
            logger.error(f"Error encontrando jugador activo: {str(e)}")
            return None
            
    def _classify_stroke(self, detection: Dict[str, Any]) -> str:
        """Clasifica el tipo de golpe basado en las métricas del jugador."""
        try:
            if not detection:
                return "desconocido"
                
            wrist_speed = detection.get('wrist_speed', 0)
            elbow_angle = detection.get('elbow_angle', 0)
            wrist_direction = detection.get('wrist_direction', 0)
            
            # Clasificar basado en métricas
            if wrist_speed > 0.8 and elbow_angle > 90:
                return "smash"
            elif wrist_speed > 0.5 and elbow_angle > 80:
                return "bandeja"
            elif wrist_speed > 0.2 and elbow_angle < 90:
                return "volea_derecha" if wrist_direction > 0 else "volea_reves"
            else:
                return "derecha" if wrist_direction > 0 else "reves"
                
        except Exception as e:
            logger.error(f"Error clasificando golpe: {str(e)}")
            return "desconocido"
            
    def _analyze_stroke_types(self, strokes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analiza la distribución de tipos de golpes."""
        try:
            stroke_types = {}
            for stroke in strokes:
                if not isinstance(stroke, dict) or 'type' not in stroke:
                    continue
                    
                stroke_type = stroke['type']
                stroke_types[stroke_type] = stroke_types.get(stroke_type, 0) + 1
                
            return stroke_types
            
        except Exception as e:
            logger.error(f"Error analizando tipos de golpes: {str(e)}")
            return {} 