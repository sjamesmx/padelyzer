import cv2
import numpy as np
import logging
from typing import Tuple, Dict, Optional, Any

logger = logging.getLogger(__name__)

class StrokeDetector:
    def __init__(self):
        self.motion_threshold = 1  # Reducido de 2 a 1 para detectar movimientos más sutiles
        self.min_stroke_frames = 1
        self.stroke_buffer = []
        self.last_frame = None
        self.min_motion_area = 3  # Reducido de 5 a 3 para capturar movimientos más pequeños
        self.max_motion_area = 40000  # Aumentado de 30000 a 40000 para permitir movimientos más amplios
        self.player_buffers = {}  # Buffer por jugador
        self.last_player_frames = {}  # Último frame por jugador
        self.stroke_cooldown = 0.3  # Reducido de 0.5 a 0.3 para permitir golpes más rápidos
        self.last_stroke_frame = {}
        self.velocity_threshold = 1  # Reducido de 2 a 1 para detectar movimientos más lentos
        self.motion_peak_threshold = 1.05  # Reducido de 1.1 a 1.05 para detectar picos más sutiles
        self.min_velocity_peak = 0.5  # Reducido de 1 a 0.5 para detectar movimientos más lentos
        self.max_velocity_peak = 200  # Aumentado de 100 a 200 para permitir movimientos más rápidos
        
    def detect_stroke(self, frame: np.ndarray, player_pos: Dict[str, Any]) -> bool:
        """
        Detecta si hay un golpe en el frame actual.
        
        Args:
            frame: Frame actual del video
            player_pos: Posición actual del jugador (x, y)
            
        Returns:
            bool: True si se detectó un golpe, False en caso contrario
        """
        try:
            player_id = player_pos.get('track_id', 0)
            frame_number = player_pos.get('frame_number', 0)
            
            if player_id in self.last_stroke_frame:
                if frame_number - self.last_stroke_frame[player_id] < self.stroke_cooldown:
                    return False
            
            if player_id not in self.player_buffers:
                self.player_buffers[player_id] = []
                self.last_player_frames[player_id] = None
                self.last_stroke_frame[player_id] = 0
            
            roi = self._get_player_roi(frame, player_pos)
            if roi is None:
                return False
                
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            if self.last_player_frames[player_id] is None:
                self.last_player_frames[player_id] = gray_roi
                return False
                
            frame_diff = cv2.absdiff(gray_roi, self.last_player_frames[player_id])
            
            _, thresh = cv2.threshold(frame_diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
            
            motion_area = np.sum(thresh) / 255
            
            if motion_area < self.min_motion_area or motion_area > self.max_motion_area:
                self.last_player_frames[player_id] = gray_roi
                return False
            
            self.player_buffers[player_id].append(motion_area)
            if len(self.player_buffers[player_id]) > self.min_stroke_frames:
                self.player_buffers[player_id].pop(0)
            
            velocity = player_pos.get('velocity', (0, 0))
            velocity_magnitude = np.sqrt(velocity[0]**2 + velocity[1]**2)
            
            is_stroke = self._analyze_motion_pattern(player_id, velocity_magnitude)
            
            self.last_player_frames[player_id] = gray_roi
            if is_stroke:
                self.last_stroke_frame[player_id] = frame_number
            
            return is_stroke
            
        except Exception as e:
            logger.error(f"Error detectando golpe: {str(e)}")
            return False
            
    def _get_player_roi(self, frame: np.ndarray, player_pos: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Obtiene la región de interés del jugador.
        
        Args:
            frame: Frame completo
            player_pos: Posición y dimensiones del jugador
            
        Returns:
            ROI del jugador o None si no se puede obtener
        """
        try:
            x = int(player_pos.get('x', 0))
            y = int(player_pos.get('y', 0))
            w = int(player_pos.get('width', 0))
            h = int(player_pos.get('height', 0))
            
            x = max(0, x)
            y = max(0, y)
            w = min(w, frame.shape[1] - x)
            h = min(h, frame.shape[0] - y)
            
            if w <= 0 or h <= 0:
                return None
                
            return frame[y:y+h, x:x+w]
            
        except Exception as e:
            logger.error(f"Error obteniendo ROI: {str(e)}")
            return None
            
    def _analyze_motion_pattern(self, player_id: int, velocity_magnitude: float) -> bool:
        """
        Analiza el patrón de movimiento para determinar si es un golpe.
        
        Args:
            player_id: ID del jugador
            velocity_magnitude: Magnitud de la velocidad del jugador
            
        Returns:
            bool: True si el patrón corresponde a un golpe
        """
        if len(self.player_buffers[player_id]) < self.min_stroke_frames:
            return False
            
        mean_motion = np.mean(self.player_buffers[player_id])
        max_motion = np.max(self.player_buffers[player_id])
        
        # Detectar pico de movimiento
        has_peak = max_motion > mean_motion * self.motion_peak_threshold
        
        # Detectar disminución después del pico
        has_decrease = self.player_buffers[player_id][-1] < max_motion * 0.8
        
        # Verificar velocidad
        has_velocity = self.min_velocity_peak < velocity_magnitude < self.max_velocity_peak
        
        # Verificar consistencia del movimiento
        is_consistent = True
        if len(self.player_buffers[player_id]) > 1:
            # Verificar que hay un patrón de aceleración seguido de desaceleración
            increasing = True
            peak_found = False
            for i in range(len(self.player_buffers[player_id])-1):
                if increasing and self.player_buffers[player_id][i] > self.player_buffers[player_id][i+1]:
                    increasing = False
                    peak_found = True
                elif not increasing and self.player_buffers[player_id][i] < self.player_buffers[player_id][i+1]:
                    is_consistent = False
                    break
            
            # Requerir que se haya encontrado un pico
            if not peak_found:
                is_consistent = False
        
        return has_peak and has_decrease and is_consistent and has_velocity 