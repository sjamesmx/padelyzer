from services.padel_iq_calculator import calculate_padel_iq_granular
from services.video_processor import VideoProcessor
from services.player_detector import PlayerDetector
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AnalysisManager:
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.player_detector = PlayerDetector()

    def analyze_training_video(self, video_url: str, player_position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analiza un video de entrenamiento y calcula el Padel IQ."""
        try:
            # Procesar video
            frames = self.video_processor.process_video(video_url)
            
            # Detectar jugador si no se proporciona posición
            if not player_position:
                player_position = self.player_detector.detect_player(frames[0])

            # Analizar golpes
            strokes = self.video_processor.analyze_strokes(frames, player_position)

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

            # Calcular Padel IQ
            padel_iq = calculate_padel_iq_granular(
                max_elbow_angle=metrics['max_elbow_angle'],
                max_wrist_speed=metrics['max_wrist_speed'],
                tipo='training'
            )

            return {
                'padel_iq': padel_iq,
                'metrics': metrics,
                'strokes': strokes
            }

        except Exception as e:
            logger.error(f"Error en análisis de entrenamiento: {str(e)}")
            raise

    def analyze_game_video(self, video_url: str, player_position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analiza un video de juego y calcula el Padel IQ."""
        try:
            # Procesar video
            frames = self.video_processor.process_video(video_url)
            
            # Detectar jugador si no se proporciona posición
            if not player_position:
                player_position = self.player_detector.detect_player(frames[0])

            # Analizar jugada
            game_data = self.video_processor.analyze_game(frames, player_position)

            # Si no hay golpes detectados en game_data, devolver métricas por defecto
            strokes = game_data.get('strokes', []) if isinstance(game_data, dict) else []
            if not strokes:
                logger.warning(f"No se detectaron golpes en el video de juego: {video_url}")
                metrics = {
                    'total_points': 0,
                    'points_won': 0,
                    'net_effectiveness': 0,
                    'court_coverage': 0,
                    'max_elbow_angle': 0,
                    'max_wrist_speed': 0
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
                    'game_data': game_data
                }

            # Calcular métricas
            metrics = {
                'total_points': game_data['total_points'],
                'points_won': game_data['points_won'],
                'net_effectiveness': game_data['net_effectiveness'],
                'court_coverage': game_data['court_coverage'],
                'max_elbow_angle': game_data['max_elbow_angle'],
                'max_wrist_speed': game_data['max_wrist_speed']
            }

            # Calcular Padel IQ
            padel_iq = calculate_padel_iq_granular(
                max_elbow_angle=metrics['max_elbow_angle'],
                max_wrist_speed=metrics['max_wrist_speed'],
                tipo='game'
            )

            return {
                'padel_iq': padel_iq,
                'metrics': metrics,
                'game_data': game_data
            }

        except Exception as e:
            logger.error(f"Error en análisis de juego: {str(e)}")
            raise

    def _count_stroke_types(self, strokes: list) -> Dict[str, int]:
        """Cuenta los tipos de golpes en el video."""
        stroke_types = {}
        for stroke in strokes:
            stroke_type = stroke['type']
            stroke_types[stroke_type] = stroke_types.get(stroke_type, 0) + 1
        return stroke_types

    def _calculate_avg_interval(self, strokes: list) -> float:
        """Calcula el intervalo promedio entre golpes."""
        if len(strokes) < 2:
            return 0.0
        
        intervals = []
        for i in range(1, len(strokes)):
            interval = strokes[i]['timestamp'] - strokes[i-1]['timestamp']
            intervals.append(interval)
        
        return sum(intervals) / len(intervals) 