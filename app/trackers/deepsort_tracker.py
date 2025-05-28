import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort

class DeepSortTracker:
    def __init__(self):
        self.tracker = DeepSort(max_age=50, n_init=2, nms_max_overlap=1.0, max_iou_distance=0.9, nn_budget=100)

    def update(self, detections, frame):
        # detections: [{'class': 'player', 'bbox': [x1, y1, x2, y2], 'conf': 0.9}, ...]
        ds_detections = []
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            w, h = x2 - x1, y2 - y1
            ds_detections.append(([x1, y1, w, h], det['conf'], 0))  # 0: class_id dummy
        tracks = self.tracker.update_tracks(ds_detections, frame=frame)
        results = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            results.append({
                'id': track_id,
                'bbox': [x1, y1, x2, y2],
                'class': 'player',  # Puedes mejorar esto si tienes clases
                'conf': 1.0  # DeepSORT no da confianza, puedes usar la de detección original si la asocias
            })
        return results 