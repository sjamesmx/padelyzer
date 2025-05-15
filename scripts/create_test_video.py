import cv2
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_video(output_path='test_videos', filename='test_training.mp4'):
    """Crea un video de prueba simple con movimientos básicos."""
    try:
        # Crear directorio si no existe
        os.makedirs(output_path, exist_ok=True)
        
        # Configuración del video
        width, height = 640, 480
        fps = 30
        duration = 5  # segundos
        
        # Crear objeto VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            os.path.join(output_path, filename),
            fourcc,
            fps,
            (width, height)
        )
        
        # Generar frames
        for i in range(fps * duration):
            # Crear frame base
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Dibujar cancha de pádel (simplificada)
            cv2.rectangle(frame, (50, 50), (width-50, height-50), (0, 255, 0), 2)
            cv2.line(frame, (width//2, 50), (width//2, height-50), (0, 255, 0), 2)
            
            # Simular movimiento de jugador
            t = i / fps
            x = int(width//4 + 100 * np.sin(t * 2))
            y = int(height//2 + 50 * np.cos(t * 3))
            
            # Dibujar jugador
            cv2.circle(frame, (x, y), 20, (255, 0, 0), -1)  # cuerpo
            cv2.line(frame, (x, y), (x + 40, y - 40), (255, 0, 0), 3)  # brazo
            
            # Escribir frame
            out.write(frame)
        
        # Liberar recursos
        out.release()
        
        logger.info(f"Video de prueba creado en {os.path.join(output_path, filename)}")
        return os.path.join(output_path, filename)
        
    except Exception as e:
        logger.error(f"Error al crear video de prueba: {str(e)}")
        raise e

if __name__ == '__main__':
    video_path = create_test_video()
    logger.info(f"Video de prueba creado exitosamente en: {video_path}") 