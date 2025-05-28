from pydantic import BaseModel, HttpUrl, Field, AnyHttpUrl
from typing import Dict, Any, Optional, Literal, Union

class PadelIQRequest(BaseModel):
    """Modelo para la solicitud de cálculo de Padel IQ."""
    user_id: str = Field(..., description="ID del usuario que solicita el análisis")
    video_url: str = Field(..., description="URL del video a analizar (puede ser http://, https:// o file://)")
    tipo_video: Literal["entrenamiento", "juego"] = Field(..., description="Tipo de video: 'entrenamiento' o 'juego'")
    player_position: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Posición del jugador en el video"
    )
    game_splits: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Información sobre los splits del juego (opcional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "video_url": "https://example.com/video.mp4",
                "tipo_video": "entrenamiento",
                "player_position": None,
                "game_splits": None
            }
        } 