import cv2
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import torch
from functools import lru_cache
import os
from .player_detector import PlayerDetector
from datetime import datetime
from .stroke_detector import StrokeDetector
from .movement_analyzer import MovementAnalyzer
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Clase para procesar videos de pádel."""
    
    def __init__(self, model_size="n", device="mps", num_workers: int = 4, batch_size: int = 8):
        """
        Inicializa el procesador de video.
        
        Args:
            model_size: Tamaño del modelo YOLO ('n', 's', 'm', 'l', 'x')
            device: Dispositivo para inferencia ('cpu', 'cuda', 'mps')
            num_workers: Número de hilos para procesamiento paralelo
            batch_size: Tamaño de lote de frames a procesar en paralelo
        """
        self.model_size = model_size
        self.device = device
        self.player_detector = PlayerDetector(model_size=model_size, device=device)
        self.frame_cache = []
        self.stroke_detector = StrokeDetector()
        self.movement_analyzer = MovementAnalyzer()
        self.frame_rate = 30
        self.resolution = (1280, 720)
        self.batch_size = batch_size
        self.num_workers = num_workers
        
    def process_video(self, video_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Procesa un video de pádel y genera métricas de análisis.
        
        Args:
            video_path: Ruta al video a procesar
            output_path: Ruta opcional para guardar el video procesado
            
        Returns:
            Diccionario con resultados del análisis
        """
        try:
            # Abrir video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el video: {video_path}")
                
            # Obtener propiedades del video
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            # Inicializar variables de análisis
            strokes = []
            player_positions = []
            frame_count = 0
            active_player = None
            last_stroke_frame = -1
            min_frames_between_strokes = int(fps * 0.5)  # Mínimo 0.5 segundos entre golpes
            batch = []
            batch_indices = []
            results_by_index = {}
            
            def process_frame(idx, frame):
                frame = cv2.resize(frame, self.resolution)
                detections = self.player_detector.detect(frame)
                local_strokes = []
                local_positions = []
                local_active_player = self._find_active_player(detections, frame) if detections else None
                local_last_stroke_frame = None
                stroke_info = None
                if detections:
                    if local_active_player and (idx - last_stroke_frame) >= min_frames_between_strokes:
                        if self.stroke_detector.detect_stroke(frame, local_active_player):
                            stroke_info = {
                                'frame': idx,
                                'player_id': local_active_player.get('id', 0),
                                'type': self._classify_stroke(local_active_player),
                                'position': self.movement_analyzer.analyze_position(local_active_player),
                                'consistency': self._calculate_stroke_consistency(local_active_player),
                                'effectiveness': self._calculate_stroke_effectiveness(local_active_player),
                                'positioning': self._calculate_positioning_score(local_active_player),
                                'timestamp': idx / fps
                            }
                            local_strokes.append(stroke_info)
                            local_last_stroke_frame = idx
                    for det in detections:
                        local_positions.append({
                            'player_id': det.get('id', 0),
                            'position': self.movement_analyzer.analyze_position(det),
                            'timestamp': idx / fps
                        })
                return {
                    'frame': frame,
                    'strokes': local_strokes,
                    'positions': local_positions,
                    'last_stroke_frame': local_last_stroke_frame
                }
            
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = {}
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    batch.append(frame)
                    batch_indices.append(frame_count)
                    if len(batch) == self.batch_size:
                        for i, f in zip(batch_indices, batch):
                            futures[executor.submit(process_frame, i, f)] = i
                        batch = []
                        batch_indices = []
                    frame_count += 1
                # Procesar los frames restantes
                for i, f in zip(batch_indices, batch):
                    futures[executor.submit(process_frame, i, f)] = i
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        result = future.result()
                        results_by_index[idx] = result
                    except Exception as e:
                        logger.error(f"Error procesando frame {idx}: {str(e)}")
            
            # Ordenar resultados por índice de frame
            for idx in sorted(results_by_index.keys()):
                result = results_by_index[idx]
                if output_path:
                    self.frame_cache.append(result['frame'])
                if result['strokes']:
                    strokes.extend(result['strokes'])
                    if result['last_stroke_frame'] is not None:
                        last_stroke_frame = result['last_stroke_frame']
                if result['positions']:
                    player_positions.extend(result['positions'])
            
            # Liberar recursos
            cap.release()
            
            # Analizar movimientos
            movements = self.movement_analyzer.analyze_movements(player_positions)
            
            # Generar video de salida
            if output_path and self.frame_cache:
                self._generate_output_video(output_path, fps)
            
            # Preparar resultados
            results = {
                'duration': duration,
                'total_frames': total_frames,
                'analysis': {
                    'strokes': strokes,
                    'movements': movements,
                    'stroke_types': self._analyze_stroke_types(strokes),
                    'consistency': self._calculate_consistency(strokes),
                    'technique': self._calculate_technique_score(strokes),
                    'movement_quality': self._analyze_movement_quality(player_positions)
                }
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error procesando video: {str(e)}")
            raise
            
    def _classify_stroke(self, detection: Dict[str, Any]) -> str:
        """Clasifica el tipo de golpe basado en la detección."""
        try:
            # Extraer métricas del golpe
            wrist_speed = detection.get('wrist_speed', 0)
            elbow_angle = detection.get('elbow_angle', 0)
            wrist_direction = detection.get('wrist_direction', 0)
            
            # Clasificar el golpe basado en las métricas
            if elbow_angle > 100 and wrist_speed > 0.6:  # Reducido de 120/0.8 a 100/0.6
                return "smash"
            elif 80 < elbow_angle <= 100 and wrist_speed > 0.4:  # Reducido de 100/0.6 a 80/0.4
                return "bandeja"
            elif 70 < elbow_angle <= 100 and wrist_speed <= 0.4:  # Reducido de 90/0.6 a 70/0.4
                return "globo"
            elif elbow_angle <= 50 and wrist_speed < 0.2:  # Reducido de 60/0.3 a 50/0.2
                return "defensivo"
            elif 50 < elbow_angle <= 80 and wrist_speed > 0.15:  # Reducido de 60/0.2 a 50/0.15
                return "volea_" + ("derecha" if wrist_direction > 0 else "reves")
            else:
                return "derecha" if wrist_direction > 0 else "reves"
                
        except Exception as e:
            logger.error(f"Error clasificando golpe: {str(e)}")
            return "unknown"
        
    def _calculate_stroke_consistency(self, detection: Dict[str, Any]) -> float:
        """Calcula la consistencia del golpe."""
        try:
            wrist_speed = detection.get('wrist_speed', 0)
            elbow_angle = detection.get('elbow_angle', 0)
            
            # Calcular consistencia basada en la estabilidad de las métricas
            speed_consistency = min(1.0, wrist_speed / 2.0)  # Normalizar velocidad
            angle_consistency = min(1.0, abs(90 - elbow_angle) / 90.0)  # Normalizar ángulo
            
            return (speed_consistency + angle_consistency) / 2.0
            
        except Exception as e:
            logger.error(f"Error calculando consistencia: {str(e)}")
            return 0.0
        
    def _calculate_stroke_effectiveness(self, detection: Dict[str, Any]) -> float:
        """Calcula la efectividad del golpe."""
        try:
            wrist_speed = detection.get('wrist_speed', 0)
            elbow_angle = detection.get('elbow_angle', 0)
            position = detection.get('position', 'unknown')
            
            # Calcular efectividad basada en múltiples factores
            speed_score = min(1.0, wrist_speed / 2.0)
            angle_score = min(1.0, abs(90 - elbow_angle) / 90.0)
            position_score = 0.8 if position in ['red', 'fondo'] else 0.5
            
            return (speed_score + angle_score + position_score) / 3.0
            
        except Exception as e:
            logger.error(f"Error calculando efectividad: {str(e)}")
            return 0.0
        
    def _calculate_positioning_score(self, detection: Dict[str, Any]) -> float:
        """Calcula la puntuación de posicionamiento."""
        try:
            position = detection.get('position', 'unknown')
            wrist_speed = detection.get('wrist_speed', 0)
            
            # Calcular puntuación de posicionamiento
            position_score = 0.8 if position in ['red', 'fondo'] else 0.5
            speed_score = min(1.0, wrist_speed / 2.0)
            
            return (position_score + speed_score) / 2.0
            
        except Exception as e:
            logger.error(f"Error calculando posicionamiento: {str(e)}")
            return 0.0
        
    def _analyze_stroke_types(self, strokes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analiza la distribución de tipos de golpes."""
        stroke_types = {}
        for stroke in strokes:
            stroke_type = stroke['type']
            stroke_types[stroke_type] = stroke_types.get(stroke_type, 0) + 1
        return stroke_types
        
    def _calculate_consistency(self, strokes: List[Dict[str, Any]]) -> float:
        """Calcula la consistencia general de los golpes."""
        if not strokes:
            return 0.0
        return sum(s['consistency'] for s in strokes) / len(strokes)
        
    def _calculate_technique_score(self, strokes: List[Dict[str, Any]]) -> float:
        """Calcula la puntuación técnica basada en los golpes."""
        if not strokes:
            return 0.0
        return sum(s['effectiveness'] for s in strokes) / len(strokes)
        
    def _analyze_movement_quality(self, positions: List[Dict[str, Any]]) -> float:
        """Analiza la calidad del movimiento."""
        if not positions:
            return 0.0
        # TODO: Implementar análisis de calidad de movimiento
        return 0.85  # Por ahora retornamos un valor por defecto
        
    def _generate_output_video(self, output_path: str, fps: float):
        """Genera el video de salida con anotaciones."""
        try:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, self.resolution)
            
            for frame in self.frame_cache:
                out.write(frame)
                
            out.release()
            
        except Exception as e:
            logger.error(f"Error generando video de salida: {str(e)}")
            raise
            
    def __del__(self):
        """Limpia recursos al destruir el objeto."""
        self.frame_cache.clear()

    def _find_active_player(self, detections: List[Dict[str, Any]], frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Encuentra el jugador que está ejecutando un golpe.
        
        Args:
            detections: Lista de detecciones de jugadores
            frame: Frame actual
            
        Returns:
            Dict con información del jugador activo o None si no hay ninguno
        """
        try:
            active_player = None
            max_motion_score = 0
            
            for detection in detections:
                # Calcular métricas de movimiento
                wrist_speed = detection.get('wrist_speed', 0)
                elbow_angle = detection.get('elbow_angle', 0)
                wrist_direction = detection.get('wrist_direction', 0)
                
                # Calcular score de movimiento
                motion_score = 0
                
                # Score por velocidad de muñeca
                if wrist_speed > 0.5:  # Reducido de 1.0 a 0.5
                    motion_score += min(1.0, wrist_speed / 2.0)
                
                # Score por ángulo de codo
                if 60 <= elbow_angle <= 150:  # Rango más amplio
                    angle_score = 1.0 - abs(90 - elbow_angle) / 90.0
                    motion_score += angle_score
                
                # Score por cambio de dirección
                if abs(wrist_direction) > 0.3:  # Reducido de 0.5 a 0.3
                    motion_score += min(1.0, abs(wrist_direction))
                
                # Actualizar jugador activo si tiene mayor score
                if motion_score > max_motion_score:
                    max_motion_score = motion_score
                    active_player = detection
            
            # Solo considerar jugador activo si supera un umbral mínimo
            if max_motion_score > 0.5:  # Reducido de 1.0 a 0.5
                return active_player
            
            return None
            
        except Exception as e:
            logger.error(f"Error encontrando jugador activo: {str(e)}")
            return None
