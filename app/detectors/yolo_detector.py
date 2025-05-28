import cv2
from ultralytics import YOLO, solutions

class YOLODetector:
    def __init__(self, model_path='yolo11n-pose.pt', device='cpu', conf_threshold=0.3):
        self.model = YOLO(model_path)
        self.device = device
        self.conf_threshold = conf_threshold
        # Si se requiere análisis de pose o métricas deportivas, inicializar AIGym
        self.gym = solutions.AIGym(model=model_path, show=False)
        # Puedes ajustar las clases según tu modelo
        self.class_map = {0: 'player', 1: 'ball'}  # Ajusta según tu modelo

    def detect(self, frame):
        results = self.model(frame, conf=self.conf_threshold)
        detections = []
        for result in results:
            boxes = result.boxes
            keypoints = getattr(result, 'keypoints', None)
            for i, box in enumerate(boxes):
                cls_id = int(box.cls)
                conf = float(box.conf)
                if conf < self.conf_threshold:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_name = self.class_map.get(cls_id, str(cls_id))
                det = {
                    'class': class_name,
                    'bbox': [x1, y1, x2, y2],
                    'conf': conf
                }
                # Si hay keypoints, agrégalos
                if keypoints is not None and len(keypoints) > i:
                    # keypoints.xyxy shape: (num_personas, num_keypoints, 2)
                    det['keypoints'] = keypoints[i].xy.cpu().numpy().tolist() if hasattr(keypoints[i], 'xy') else keypoints[i].cpu().numpy().tolist()
                detections.append(det)
        return detections 