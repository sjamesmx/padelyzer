from typing import Dict, Any, Optional
import logging
from app.services.analysis_manager import AnalysisManager
from app.services.padel_iq_calculator import calculate_padel_iq_granular

logger = logging.getLogger(__name__)

class PadelIQService:
    def __init__(self):
        self.analysis_manager = AnalysisManager()

    async def calculate_padel_iq(self, video_url: str, tipo_video: str, player_position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calcula el Padel IQ para un video dado.
        
        Args:
            video_url: URL del video a analizar
            tipo_video: Tipo de video ('entrenamiento' o 'juego')
            player_position: Posición del jugador en el video
            
        Returns:
            Dict con las métricas calculadas
        """
        try:
            if tipo_video == "entrenamiento":
                result = self.analysis_manager.analyze_training_video(
                    video_url=video_url,
                    player_position=player_position
                )
            elif tipo_video == "juego":
                result = self.analysis_manager.analyze_game_video(
                    video_url=video_url,
                    player_position=player_position
                )
            else:
                raise ValueError(f"Tipo de video no soportado: {tipo_video}")

            # Calcular Padel IQ granular
            padel_iq = calculate_padel_iq_granular(
                max_elbow_angle=result['metrics'].get('max_elbow_angle', 0),
                max_wrist_speed=result['metrics'].get('max_wrist_speed', 0),
                tipo=tipo_video
            )

            # Integrar resultados
            response = {
                "padel_iq": padel_iq['padel_iq'],
                "metrics": {
                    "tecnica": padel_iq['tecnica'],
                    "fuerza": padel_iq['fuerza'],
                    "ritmo": padel_iq['ritmo'],
                    "repeticion": padel_iq['repeticion']
                },
                "video_metrics": result['metrics']
            }

            if tipo_video == "juego":
                response["game_data"] = result.get('game_data', {})

            return response

        except Exception as e:
            logger.error(f"Error calculando Padel IQ: {str(e)}")
            raise

    def determine_force_category(self, padel_iq: float, tecnica: float, ritmo: float, fuerza: float) -> str:
        """
        Determina la categoría de fuerza del jugador basada en sus métricas.
        
        Args:
            padel_iq: Puntuación total de Padel IQ
            tecnica: Puntuación de técnica
            ritmo: Puntuación de ritmo
            fuerza: Puntuación de fuerza
            
        Returns:
            Categoría de fuerza del jugador
        """
        if padel_iq > 85 and tecnica > 80 and ritmo > 80 and fuerza > 80:
            return "primera_fuerza"
        elif padel_iq > 75 and tecnica > 70 and ritmo > 70 and fuerza > 70:
            return "segunda_fuerza"
        elif padel_iq > 65 and tecnica > 60 and ritmo > 60 and fuerza > 60:
            return "tercera_fuerza"
        elif padel_iq > 45 and tecnica > 40 and ritmo > 40 and fuerza > 40:
            return "cuarta_fuerza"
        else:
            return "quinta_fuerza" 