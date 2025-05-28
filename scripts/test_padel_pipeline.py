import sys
from app.detectors.yolo_detector import YOLODetector
from app.trackers.deepsort_tracker import DeepSortTracker
import cv2
import csv
import numpy as np
import os

# Nombres COCO para 17 keypoints (pueden variar según el modelo)
KEYPOINT_NAMES = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
]
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4), # cabeza
    (0, 5), (0, 6), # cuello a hombros
    (5, 7), (7, 9), # brazo izq
    (6, 8), (8, 10), # brazo der
    (5, 11), (6, 12), # hombros a cadera
    (11, 13), (13, 15), # pierna izq
    (12, 14), (14, 16) # pierna der
]

def draw_keypoints_and_skeleton(frame, keypoints, track_ids=None, threshold=0.2):
    for idx_p, person in enumerate(keypoints):
        # Dibujar keypoints
        for idx, (x, y, score) in enumerate(person):
            if score > threshold:
                color = (0, 255, 0)
                cv2.circle(frame, (int(x), int(y)), 3, color, -1)
        # Dibujar conexiones
        for i, j in SKELETON_CONNECTIONS:
            if i < len(person) and j < len(person):
                xi, yi, si = person[i]
                xj, yj, sj = person[j]
                if si > threshold and sj > threshold:
                    cv2.line(frame, (int(xi), int(yi)), (int(xj), int(yj)), (255, 0, 0), 2)
        # Dibujar ID de tracking
        if track_ids is not None and idx_p < len(track_ids):
            x0, y0, s0 = person[0]
            cv2.putText(frame, f'ID:{track_ids[idx_p]}', (int(x0), int(y0)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
    return frame

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/test_padel_pipeline.py <ruta_video_entrada> [ruta_video_salida]")
        sys.exit(1)
    video_in = sys.argv[1]
    video_out = sys.argv[2] if len(sys.argv) > 2 else None
    yolo_detector = YOLODetector(model_path='yolov8n-pose.pt')
    deepsort = DeepSortTracker()
    cap = cv2.VideoCapture(video_in)
    frame_idx = 0
    csv_file = open('keypoints_output.csv', 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['frame', 'track_id', 'person_id', 'keypoint_id', 'keypoint_name', 'x', 'y', 'score'])
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = yolo_detector.gym(frame)
        keypoints = results.keypoints if hasattr(results, 'keypoints') and results.keypoints is not None else np.array([])
        # Obtener bounding boxes y confianzas para DeepSORT
        boxes = results.boxes.xyxy.cpu().numpy() if hasattr(results, 'boxes') and results.boxes is not None else np.array([])
        confs = results.boxes.conf.cpu().numpy() if hasattr(results, 'boxes') and results.boxes is not None else np.array([])
        # Preparar detecciones para DeepSortTracker
        detections = []
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            conf = confs[i] if i < len(confs) else 1.0
            detections.append({'class': 'player', 'bbox': [x1, y1, x2, y2], 'conf': float(conf)})
        tracks = deepsort.update(detections, frame) if len(detections) > 0 else []
        track_ids = [t['id'] for t in tracks] if len(tracks) > 0 else [None]*len(keypoints)
        # Exportar a CSV
        for pid, person in enumerate(keypoints):
            tid = track_ids[pid] if pid < len(track_ids) else None
            for kidx, (x, y, score) in enumerate(person):
                name = KEYPOINT_NAMES[kidx] if kidx < len(KEYPOINT_NAMES) else f"kp_{kidx}"
                csv_writer.writerow([frame_idx, tid, pid, kidx, name, x, y, score])
        frame = draw_keypoints_and_skeleton(frame, keypoints, track_ids)
        cv2.imshow("YOLO Pose + DeepSORT", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        frame_idx += 1
    cap.release()
    csv_file.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 