import cv2
import numpy as np
import os

def generate_test_video(output_path: str, duration: int = 5, fps: int = 30):
    """Genera un video de prueba simple con un rectángulo moviéndose."""
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Configuración del video
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Generar frames
    for i in range(duration * fps):
        # Crear frame negro
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Calcular posición del rectángulo
        x = int((i / (duration * fps)) * (width - 100))
        y = height // 2 - 50
        
        # Dibujar rectángulo
        cv2.rectangle(frame, (x, y), (x + 100, y + 100), (0, 255, 0), -1)
        
        # Escribir frame
        out.write(frame)
    
    # Liberar recursos
    out.release()

if __name__ == '__main__':
    # Generar video de prueba
    test_video_path = 'tests/test_videos/test_video.mp4'
    generate_test_video(test_video_path)
    print(f"Video de prueba generado en: {test_video_path}") 