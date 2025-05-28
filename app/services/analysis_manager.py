from typing import Dict, Any, Optional, List
import logging
from .video_processor import VideoProcessor
from .player_detector import PlayerDetector
from app.services.padel_iq_calculator import calculate_padel_iq_granular
import torch
import gc
import numpy as np

logger = logging.getLogger(__name__)

class AnalysisManager:
    """Gestor de análisis de videos de pádel."""
    
    def __init__(self, model_size: str = "n", device: str = "mps"):
        """
        Inicializa el gestor de análisis.
        
        Args:
            model_size: Tamaño del modelo YOLO ('n', 's', 'm', 'l', 'x')
            device: Dispositivo para inferencia ('cpu', 'cuda', 'mps')
        """
        self.model_size = model_size
        self.device = device
        self.video_processor = VideoProcessor(model_size=model_size, device=device)
        self.player_detector = PlayerDetector(model_size=model_size, device=device)
        logger.info("Modelos de ML inicializados correctamente")
    
    def _calculate_padel_iq(self, video_analysis: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcula el PadelIQ basado en el análisis del video.
        
        Args:
            video_analysis: Resultados del análisis del video
            
        Returns:
            Diccionario con puntuaciones PadelIQ
        """
        try:
            analysis = video_analysis['analysis']
            
            # Calcular puntuaciones individuales
            technique_score = self._calculate_technique_score(analysis)
            movement_score = self._calculate_movement_score(analysis)
            strategy_score = self._calculate_strategy_score(analysis)
            
            # Calcular PadelIQ total (promedio ponderado)
            total_iq = (
                technique_score * 0.4 +  # 40% técnica
                movement_score * 0.3 +   # 30% movimiento
                strategy_score * 0.3     # 30% estrategia
            )
            
            return {
                'total': total_iq,
                'technique': technique_score,
                'movement': movement_score,
                'strategy': strategy_score
            }
            
        except Exception as e:
            logger.error(f"Error calculando PadelIQ: {str(e)}")
            return {
                'total': 0.0,
                'technique': 0.0,
                'movement': 0.0,
                'strategy': 0.0
            }
    
    def _calculate_technique_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calcula la puntuación técnica basada en:
        - Precisión de golpes
        - Variedad de golpes
        - Consistencia en la ejecución
        """
        try:
            strokes = analysis.get('strokes', [])
            if not strokes:
                return 0.0
                
            # Calcular métricas técnicas
            total_strokes = len(strokes)
            stroke_types = len(set(s.get('type', '') for s in strokes))
            consistency = sum(s.get('consistency', 0.0) for s in strokes) / total_strokes
            
            # Ponderar métricas
            technique_score = (
                (total_strokes / 50) * 30 +  # Hasta 30 puntos por volumen de golpes
                (stroke_types / 5) * 20 +    # Hasta 20 puntos por variedad
                consistency * 50             # Hasta 50 puntos por consistencia
            )
            
            # Ajustar para nivel profesional (mínimo 70)
            return max(70.0, min(100.0, technique_score))
            
        except Exception as e:
            logger.error(f"Error calculando puntuación técnica: {str(e)}")
            return 0.0
    
    def _calculate_movement_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calcula la puntuación de movimiento basada en:
        - Cobertura de la pista
        - Eficiencia de movimiento
        - Velocidad y agilidad
        """
        try:
            movements = analysis.get('movements', {})
            if not movements:
                return 0.0
                
            # Calcular métricas de movimiento
            court_coverage = movements.get('court_coverage', 0.0)
            avg_speed = movements.get('average_speed', 0.0)
            total_distance = movements.get('total_distance', 0.0)
            
            # Ponderar métricas
            movement_score = (
                (court_coverage / 100) * 40 +  # Hasta 40 puntos por cobertura
                (avg_speed / 30) * 30 +        # Hasta 30 puntos por velocidad
                (total_distance / 2000) * 30   # Hasta 30 puntos por distancia
            )
            
            # Ajustar para nivel profesional (mínimo 75)
            return max(75.0, min(100.0, movement_score))
            
        except Exception as e:
            logger.error(f"Error calculando puntuación de movimiento: {str(e)}")
            return 0.0
    
    def _calculate_strategy_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calcula la puntuación de estrategia basada en:
        - Posicionamiento en la pista
        - Elección de golpes
        - Efectividad de los golpes
        """
        try:
            strokes = analysis.get('strokes', [])
            if not strokes:
                return 0.0
                
            # Calcular métricas de estrategia
            total_strokes = len(strokes)
            effective_strokes = sum(1 for s in strokes if s.get('effectiveness', 0.0) > 0.7)
            positioning_score = sum(s.get('positioning', 0.0) for s in strokes) / total_strokes
            
            # Ponderar métricas
            strategy_score = (
                (effective_strokes / total_strokes) * 40 +  # Hasta 40 puntos por efectividad
                positioning_score * 40 +                    # Hasta 40 puntos por posicionamiento
                (total_strokes / 50) * 20                   # Hasta 20 puntos por volumen
            )
            
            # Ajustar para nivel profesional (mínimo 65)
            return max(65.0, min(100.0, strategy_score))
            
        except Exception as e:
            logger.error(f"Error calculando puntuación de estrategia: {str(e)}")
            return 0.0

    def _calculate_metrics(self, strokes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula métricas detalladas de los golpes."""
        total_strokes = len(strokes)
        stroke_types = {}
        max_elbow_angle = 0
        max_wrist_speed = 0
        total_interval = 0

        for i, stroke in enumerate(strokes):
            # Contar tipos de golpes
            stroke_type = stroke.get('type', 'unknown')
            stroke_types[stroke_type] = stroke_types.get(stroke_type, 0) + 1

            # Actualizar máximos
            max_elbow_angle = max(max_elbow_angle, stroke.get('elbow_angle', 0))
            max_wrist_speed = max(max_wrist_speed, stroke.get('wrist_speed', 0))

            # Calcular intervalo entre golpes
            if i > 0:
                interval = stroke.get('timestamp', 0) - strokes[i-1].get('timestamp', 0)
                total_interval += interval

        return {
            'total_strokes': total_strokes,
            'stroke_types': stroke_types,
            'max_elbow_angle': max_elbow_angle,
            'max_wrist_speed': max_wrist_speed,
            'avg_stroke_interval': total_interval / (total_strokes - 1) if total_strokes > 1 else 0
        }

    def _calculate_game_metrics(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas detalladas del juego."""
        return {
            'total_points': game_data.get('total_points', 0),
            'points_won': game_data.get('points_won', 0),
            'net_effectiveness': game_data.get('net_effectiveness', 0),
            'court_coverage': game_data.get('court_coverage', 0),
            'max_elbow_angle': game_data.get('max_elbow_angle', 0),
            'max_wrist_speed': game_data.get('max_wrist_speed', 0)
        }

    def _cleanup_resources(self, frames: List[np.ndarray]):
        """Limpia recursos y libera memoria."""
        try:
            # Limpiar frames
            frames.clear()

            # Limpiar caché del procesador de video
            self.video_processor.clear_cache()

            # Forzar recolección de basura
            gc.collect()

            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

        except Exception as e:
            logger.error(f"Error limpiando recursos: {str(e)}")

    def __del__(self):
        """Limpia recursos al destruir el objeto."""
        try:
            if hasattr(self, 'video_processor'):
                del self.video_processor
            if hasattr(self, 'player_detector'):
                del self.player_detector
        except Exception as e:
            logger.error(f"Error limpiando recursos: {str(e)}")

    def post_filter_strokes(self, strokes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aplica filtros post-procesamiento a los golpes detectados.
        
        Args:
            strokes: Lista de golpes detectados
            
        Returns:
            Lista filtrada de golpes
        """
        try:
            filtered_strokes = []
            
            for stroke in strokes:
                # Obtener métricas del golpe
                stroke_type = stroke.get('type', 'unknown')
                wrist_speed = stroke.get('wrist_speed', 0)
                elbow_angle = stroke.get('elbow_angle', 0)
                duration = stroke.get('duration', 0)
                
                # Verificar duración mínima
                if duration < 0.03:  # Reducido de 0.05 a 0.03
                    logger.info(f"Golpe descartado por duración muy corta: {duration:.2f}s")
                    continue
                
                # Verificar velocidad mínima según tipo de golpe
                min_speed = {
                    'smash': 0.6,    # Reducido de 0.8 a 0.6
                    'bandeja': 0.4,  # Reducido de 0.6 a 0.4
                    'globo': 0.3,    # Reducido de 0.4 a 0.3
                    'defensivo': 0.15, # Reducido de 0.2 a 0.15
                    'volea': 0.2     # Reducido de 0.3 a 0.2
                }.get(stroke_type, 0.2)
                
                if wrist_speed < min_speed:
                    logger.info(f"Golpe descartado por velocidad baja: {wrist_speed:.2f} < {min_speed}")
                    continue
                
                # Verificar ángulo de codo según tipo de golpe
                min_angle = {
                    'smash': 80,     # Reducido de 90 a 80
                    'bandeja': 70,   # Reducido de 80 a 70
                    'globo': 60,     # Reducido de 70 a 60
                    'defensivo': 30, # Reducido de 40 a 30
                    'volea': 40      # Reducido de 50 a 40
                }.get(stroke_type, 30)
                
                if elbow_angle < min_angle:
                    logger.info(f"Golpe descartado por ángulo bajo: {elbow_angle:.2f} < {min_angle}")
                    continue
                    
                filtered_strokes.append(stroke)
                
            return filtered_strokes
            
        except Exception as e:
            logger.error(f"Error en post_filter_strokes: {str(e)}")
            return strokes
