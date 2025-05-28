from app.detectors.yolo_detector import YOLODetector
from app.trackers.deepsort_tracker import DeepSortTracker
from app.detectors.mediapipe_detector import MediaPipeDetector
from app.pipeline.padel_pipeline import PadelAnalysisPipeline
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m app.pipeline <video_path> [max_frames]")
        sys.exit(1)
    video_path = sys.argv[1]
    max_frames = int(sys.argv[2]) if len(sys.argv) > 2 else None
    yolo = YOLODetector()
    deepsort = DeepSortTracker()
    mediapipe = MediaPipeDetector()
    pipeline = PadelAnalysisPipeline(yolo, deepsort, mediapipe)
    pipeline.process_video(video_path, max_frames=max_frames) 