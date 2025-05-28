import numpy as np
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)

class MovementAnalyzer:
    def __init__(self):
        self.court_dimensions = (20, 10)  # Dimensiones de la pista en metros
        self.pixel_to_meter_ratio = 0.01  # Ratio aproximado píxeles a metros
        
    def analyze_position(self, detection: Dict) -> Tuple[float, float]:
        """
        Analiza la posición del jugador a partir de una detección.
        
        Args:
            detection: Diccionario con la detección del jugador
            
        Returns:
            Tuple[float, float]: Posición (x, y) del jugador
        """
        try:
            if not detection or 'bbox' not in detection:
                logger.warning("Detección inválida o sin bbox")
                return (0, 0)
                
            bbox = detection['bbox']
            if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                logger.warning(f"Bbox inválido: {bbox}")
                return (0, 0)
                
            x = (bbox[0] + bbox[2]) / 2
            y = (bbox[1] + bbox[3]) / 2
            return (x, y)
        except Exception as e:
            logger.error(f"Error analizando posición: {str(e)}")
            return (0, 0)
            
    def analyze_movements(self, positions: List[Dict]) -> Dict:
        """
        Analiza los movimientos del jugador a lo largo del tiempo.
        
        Args:
            positions: Lista de posiciones del jugador
            
        Returns:
            Dict con métricas de movimiento
        """
        try:
            if not positions:
                logger.warning("No hay posiciones para analizar")
                return {
                    'total_distance': 0.0,
                    'average_speed': 0.0,
                    'court_coverage': 0.0
                }
                
            # Convertir posiciones a coordenadas (x,y)
            coords = []
            for pos in positions:
                if isinstance(pos, dict) and 'position' in pos:
                    coords.append(pos['position'])
                elif isinstance(pos, tuple) and len(pos) == 2:
                    coords.append(pos)
                else:
                    logger.warning(f"Posición inválida: {pos}")
                    continue
                    
            if not coords:
                logger.warning("No hay coordenadas válidas para analizar")
                return {
                    'total_distance': 0.0,
                    'average_speed': 0.0,
                    'court_coverage': 0.0
                }
                
            # Calcular distancia total
            total_distance = 0.0
            for i in range(1, len(coords)):
                dx = coords[i][0] - coords[i-1][0]
                dy = coords[i][1] - coords[i-1][1]
                distance = np.sqrt(dx*dx + dy*dy) * self.pixel_to_meter_ratio
                total_distance += distance
                
            # Calcular velocidad promedio (m/s)
            # Asumimos 30 fps
            time_seconds = len(coords) / 30
            average_speed = total_distance / time_seconds if time_seconds > 0 else 0
            
            # Calcular cobertura de la pista
            court_coverage = self.calculate_court_coverage(coords)
            
            return {
                'total_distance': float(total_distance),
                'average_speed': float(average_speed),
                'court_coverage': float(court_coverage)
            }
            
        except Exception as e:
            logger.error(f"Error analizando movimientos: {str(e)}")
            return {
                'total_distance': 0.0,
                'average_speed': 0.0,
                'court_coverage': 0.0
            }
            
    def calculate_court_coverage(self, positions: List[Tuple[float, float]]) -> float:
        """
        Calcula el porcentaje de cobertura de la pista.
        
        Args:
            positions: Lista de posiciones (x,y)
            
        Returns:
            float: Porcentaje de cobertura (0-1)
        """
        try:
            if not positions:
                return 0.0
                
            # Crear grid de la pista
            grid_size = 10  # 10x10 grid
            grid = np.zeros((grid_size, grid_size))
            
            # Convertir posiciones a coordenadas del grid
            for x, y in positions:
                grid_x = int(x * grid_size)
                grid_y = int(y * grid_size)
                if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                    grid[grid_y, grid_x] = 1
                    
            # Calcular porcentaje de cobertura
            coverage = np.sum(grid) / (grid_size * grid_size)
            return float(coverage)
            
        except Exception as e:
            logger.error(f"Error calculando cobertura: {str(e)}")
            return 0.0 