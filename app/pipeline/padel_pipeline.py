import cv2
import os
from datetime import datetime

class PadelAnalysisPipeline:
    def __init__(self, yolo, deepsort, mediapipe=None, openpose=None, slowfast=None, detectron2=None, redis_cache=None):
        self.yolo = yolo
        self.deepsort = deepsort
        self.mediapipe = mediapipe
        self.openpose = openpose
        self.slowfast = slowfast
        self.detectron2 = detectron2
        self.redis_cache = redis_cache

    def detect_yolo(self, frame):
        # Paso 1: Detección y análisis de pose con YOLOv11/AIGym
        if self.yolo:
            results = self.yolo.gym(frame)
            # results.keypoints: keypoints detectados
            # results.metrics: métricas deportivas
            # results.plot_im: frame anotado
            return results
        return None

    def track_deepsort(self, detections, frame):
        # Paso 2: Rastreo con DeepSORT
        # Debe retornar [{'bbox': (x1, y1, x2, y2), 'id': id_jugador, 'class': ...}, ...]
        if self.deepsort:
            return self.deepsort.update(detections, frame)
        return []

    def analyze_pose_openpose(self, player_frame):
        # Paso 3a: Keypoints con OpenPose (stub)
        if self.openpose:
            return self.openpose.infer(player_frame)
        return None

    def analyze_pose_mediapipe(self, player_frame):
        # Paso 6: Keypoints con MediaPipe (rápido, fallback)
        if self.mediapipe:
            return self.mediapipe.infer(player_frame)
        return None

    def classify_shot_slowfast(self, sequence_frames):
        # Paso 4: Confirmación de golpe con SlowFast (stub)
        if self.slowfast:
            return self.slowfast.classify(sequence_frames)
        return None

    def validate_detectron2(self, frame):
        # Paso 5: Validación con Detectron2 (stub)
        if self.detectron2:
            return self.detectron2.detect(frame)
        return None

    def biomechanical_analysis(self, keypoints):
        # Paso 6: Análisis biomecánico rápido (stub)
        # Aquí puedes calcular ángulos, velocidades, etc.
        return {}

    def cache_results(self, key, value):
        # Paso 7: Caching con Redis (stub)
        if self.redis_cache:
            self.redis_cache.set(key, value)

    def process_video(self, video_path, output_path=None, max_frames=None, fps_subsample=10):
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        if output_path is None:
            base = os.path.splitext(os.path.basename(video_path))[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"{base}_pipeline_{timestamp}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        while True:
            ret, frame = cap.read()
            if not ret or (max_frames and frame_count >= max_frames):
                break
            # Submuestreo de frames
            if frame_count % int(fps // fps_subsample) != 0:
                frame_count += 1
                continue
            # 1. Detección y análisis de pose con YOLOv11/AIGym
            results = self.detect_yolo(frame)
            if results is not None:
                # Puedes acceder a results.keypoints, results.metrics, etc.
                frame_annotated = results.plot_im
                # Aquí puedes agregar lógica para análisis de métricas, eventos, etc.
                out.write(frame_annotated)
            else:
                out.write(frame)
            frame_count += 1
        cap.release()
        out.release()
        print(f"Procesados {frame_count} frames. Video guardado en: {output_path}") 