from typing import Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_padel_iq_granular(max_elbow_angle: float, max_wrist_speed: float, tipo: str) -> Dict[str, float]:
    """Calcula el Padel IQ de forma granular.
    
    Args:
        max_elbow_angle: Ángulo máximo del codo en grados
        max_wrist_speed: Velocidad máxima de la muñeca en m/s
        tipo: Tipo de análisis ('training' o 'game')
    
    Returns:
        Dict con las métricas calculadas
    """
    try:
        # Normalizar métricas
        tecnica = _normalize_technique(max_elbow_angle)
        fuerza = _normalize_strength(max_wrist_speed)
        ritmo = _calculate_rhythm(max_elbow_angle, max_wrist_speed)
        repeticion = _calculate_repetition(max_elbow_angle, max_wrist_speed)

        # Calcular Padel IQ base
        padel_iq = _calculate_base_iq(tecnica, fuerza, ritmo, repeticion)

        # Ajustar según tipo
        if tipo == 'game':
            padel_iq = _adjust_for_game(padel_iq, max_elbow_angle, max_wrist_speed)

        return {
            'tecnica': tecnica,
            'fuerza': fuerza,
            'ritmo': ritmo,
            'repeticion': repeticion,
            'padel_iq': padel_iq
        }

    except Exception as e:
        logger.error(f"Error calculando Padel IQ: {str(e)}")
        raise

def _normalize_technique(elbow_angle: float) -> float:
    """Normaliza el ángulo del codo a una puntuación de técnica."""
    # Ángulo óptimo: 90 grados
    # Rango aceptable: 60-120 grados
    if elbow_angle < 60 or elbow_angle > 120:
        return 0.0
    
    # Calcular distancia al ángulo óptimo
    distance = abs(elbow_angle - 90)
    
    # Normalizar a 100 puntos
    score = 100 * (1 - distance / 30)
    return max(0, min(100, score))

def _normalize_strength(wrist_speed: float) -> float:
    """Normaliza la velocidad de la muñeca a una puntuación de fuerza."""
    # Velocidad óptima: 15 m/s
    # Rango aceptable: 5-25 m/s
    if wrist_speed < 5 or wrist_speed > 25:
        return 0.0
    
    # Calcular distancia a la velocidad óptima
    distance = abs(wrist_speed - 15)
    
    # Normalizar a 100 puntos
    score = 100 * (1 - distance / 10)
    return max(0, min(100, score))

def _calculate_rhythm(elbow_angle: float, wrist_speed: float) -> float:
    """Calcula la puntuación de ritmo basada en la consistencia."""
    # Usar la desviación estándar de las métricas como indicador de ritmo
    metrics = [elbow_angle, wrist_speed]
    std_dev = np.std(metrics)
    
    # Normalizar a 100 puntos (menor desviación = mejor ritmo)
    score = 100 * (1 - std_dev / 50)
    return max(0, min(100, score))

def _calculate_repetition(elbow_angle: float, wrist_speed: float) -> float:
    """Calcula la puntuación de repetición basada en la consistencia."""
    # Similar al ritmo, pero con un peso diferente
    metrics = [elbow_angle, wrist_speed]
    std_dev = np.std(metrics)
    
    # Normalizar a 100 puntos
    score = 100 * (1 - std_dev / 40)
    return max(0, min(100, score))

def _calculate_base_iq(tecnica: float, fuerza: float, ritmo: float, repeticion: float) -> float:
    """Calcula el Padel IQ base usando los pesos definidos."""
    # Pesos: Técnica (40%), Fuerza (30%), Ritmo (20%), Repetición (10%)
    return (
        tecnica * 0.4 +
        fuerza * 0.3 +
        ritmo * 0.2 +
        repeticion * 0.1
    )

def _adjust_for_game(base_iq: float, elbow_angle: float, wrist_speed: float) -> float:
    """Ajusta el Padel IQ para videos de juego."""
    # Ajustar según la efectividad en situaciones de juego
    game_factor = 1.0
    
    # Penalizar técnica deficiente en juego
    if elbow_angle < 60 or elbow_angle > 120:
        game_factor *= 0.8
    
    # Penalizar falta de fuerza en juego
    if wrist_speed < 5:
        game_factor *= 0.8
    
    return base_iq * game_factor