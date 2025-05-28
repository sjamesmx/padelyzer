import yaml
import logging
import json
import uuid
from typing import Any, Dict, Optional, Union
import cv2
import os
import csv
from app.detectors.yolo_detector import YOLODetector
from app.trackers.deepsort_tracker import DeepSortTracker
import numpy as np
from collections import Counter
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class VideoPipeline:
    def __init__(self, config: Union[str, dict], analysis_id: Optional[str] = None, num_workers: int = 4, batch_size: int = 8):
        self.frame_count = 0  # Inicializar antes de cualquier log
        self.config = self.load_config(config)
        self.analysis_id = analysis_id or str(uuid.uuid4())
        self.setup_logging()
        self.init_modules()
        self.csv_writer = None
        self.csv_file = None
        self.video_writer = None
        self.last_detections = []
        self.fixed_track_ids = None  # IDs fijados tras los primeros frames
        self.fixation_frames = self.config.get('fixation_frames', 15)
        self.fixation_done = False
        # Configuración de hooks HTTP
        self.hooks_cfg = self.config.get('hooks', {})
        self.hooks_enabled = self.hooks_cfg.get('enabled', False)
        self.hook_urls = {
            'before_frame': self.hooks_cfg.get('before_frame_url'),
            'after_frame': self.hooks_cfg.get('after_frame_url'),
            'on_finish': self.hooks_cfg.get('on_finish_url'),
        }
        self.num_workers = num_workers
        self.batch_size = batch_size

    def load_config(self, config: Union[str, dict]) -> Dict[str, Any]:
        if isinstance(config, dict):
            return config
        with open(config, 'r') as f:
            return yaml.safe_load(f)

    def setup_logging(self):
        log_cfg = self.config.get('logging', {})
        log_level = getattr(logging, log_cfg.get('level', 'INFO').upper(), logging.INFO)
        log_file = log_cfg.get('log_file')
        self.logger = logging.getLogger(f'VideoPipeline.{self.analysis_id}')
        self.logger.setLevel(log_level)
        formatter = logging.Formatter('%(message)s')
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        if not self.logger.hasHandlers():
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def log_structured(self, level, message, **kwargs):
        log_entry = {"analysis_id": self.analysis_id, "frame": self.frame_count, **kwargs, "message": message}
        self.logger.log(level, json.dumps(log_entry, ensure_ascii=False))

    def init_modules(self):
        input_cfg = self.config['input']
        source = input_cfg.get('source', 0)
        if isinstance(source, str) and source.isdigit():
            source = int(source)
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            self.log_structured(logging.ERROR, f'No se pudo abrir la fuente de video: {source}', step="init_modules")
            raise RuntimeError(f'No se pudo abrir la fuente de video: {source}')
        self.resize = input_cfg.get('resize', None)
        self.preprocess = input_cfg.get('preprocess', {})

        det_cfg = self.config['detector']
        self.detector = YOLODetector(
            model_path=det_cfg.get('model', 'yolov8n-pose.pt'),
            device=det_cfg.get('device', 'cpu'),
            conf_threshold=det_cfg.get('confidence_threshold', 0.3)
        )
        self.tracker = DeepSortTracker()

        output_cfg = self.config.get('output', {})
        self.save_video = output_cfg.get('save_video', False)
        self.output_path = output_cfg.get('output_path', 'output/analysed_video.mp4')
        self.export_csv = output_cfg.get('export_csv', False)
        self.csv_path = output_cfg.get('csv_path', 'output/keypoints.csv')
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

    def preprocess_frame(self, frame):
        resize_mode = self.config.get('input', {}).get('resize_mode', 'keep_aspect')
        if self.resize:
            w, h = self.resize.get('width'), self.resize.get('height')
            if w and h:
                if resize_mode == 'keep_aspect':
                    orig_h, orig_w = frame.shape[:2]
                    scale = min(w / orig_w, h / orig_h)
                    new_w, new_h = int(orig_w * scale), int(orig_h * scale)
                    frame_resized = cv2.resize(frame, (new_w, new_h))
                    pad_w, pad_h = w - new_w, h - new_h
                    top = pad_h // 2
                    bottom = pad_h - top
                    left = pad_w // 2
                    right = pad_w - left
                    frame = cv2.copyMakeBorder(frame_resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0,0,0])
                else:
                    frame = cv2.resize(frame, (w, h))
        if self.preprocess.get('normalize'):
            frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
        if self.preprocess.get('grayscale'):
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame

    def init_video_writer(self, frame):
        if self.save_video and self.video_writer is None:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            height, width = frame.shape[:2]
            self.video_writer = cv2.VideoWriter(self.output_path, fourcc, 25, (width, height))
            self.log_structured(logging.INFO, f'Video procesado se guardará en: {self.output_path}', step="init_video_writer")

    def init_csv_writer(self):
        if self.export_csv and self.csv_writer is None:
            self.csv_file = open(self.csv_path, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(['frame', 'track_id', 'x1', 'y1', 'x2', 'y2', 'keypoints'])
            self.log_structured(logging.INFO, f'CSV de resultados se guardará en: {self.csv_path}', step="init_csv_writer")

    def write_csv_row(self, frame_idx, track, keypoints=None):
        if self.csv_writer:
            x1, y1, x2, y2 = track['bbox']
            kp_str = json.dumps(keypoints) if keypoints is not None else ''
            self.csv_writer.writerow([frame_idx, track['id'], x1, y1, x2, y2, kp_str])

    def associate_keypoints(self, tracks, detections):
        def bbox_center(bbox):
            x1, y1, x2, y2 = bbox
            return ((x1 + x2) // 2, (y1 + y2) // 2)
        associated = {}
        for track in tracks:
            t_cx, t_cy = bbox_center(track['bbox'])
            min_dist = float('inf')
            best_kp = None
            for det in detections:
                if 'keypoints' in det:
                    d_cx, d_cy = bbox_center(det['bbox'])
                    dist = (t_cx - d_cx) ** 2 + (t_cy - d_cy) ** 2
                    if dist < min_dist:
                        min_dist = dist
                        best_kp = det['keypoints']
            associated[track['id']] = best_kp
        return associated

    def filter_players(self, detections, frame_shape):
        video_type = self.config.get('video_type', 'game')
        player_side = self.config.get('player_side', None)
        if not detections:
            return []
        if video_type == 'game':
            h = frame_shape[0]
            dets_sorted = sorted(detections, key=lambda d: (d['bbox'][1]+d['bbox'][3])//2, reverse=True)
            filtered = dets_sorted[:2]
            if player_side and len(filtered) == 2:
                w = frame_shape[1]
                left_player = min(filtered, key=lambda d: (d['bbox'][0]+d['bbox'][2])//2)
                right_player = max(filtered, key=lambda d: (d['bbox'][0]+d['bbox'][2])//2)
                for det in filtered:
                    det['is_user'] = (player_side == 'left' and det == left_player) or (player_side == 'right' and det == right_player)
            return filtered
        elif video_type == 'training':
            w = frame_shape[1]
            center_x = w // 2
            det = min(detections, key=lambda d: abs(((d['bbox'][0]+d['bbox'][2])//2) - center_x))
            det['is_user'] = True
            return [det]
        else:
            return detections

    def call_hook(self, hook_type, payload):
        if self.hooks_enabled and self.hook_urls.get(hook_type):
            try:
                requests.post(self.hook_urls[hook_type], json=payload, timeout=2)
            except Exception as e:
                self.log_structured(logging.WARNING, f'Error en hook {hook_type}: {e}', step='hook')

    def run(self):
        self.log_structured(logging.INFO, 'Iniciando pipeline de video...', step="start")
        fixation_candidates = []
        batch = []
        batch_indices = []
        results_by_index = {}
        def process_frame(idx, frame):
            self.call_hook('before_frame', {'analysis_id': self.analysis_id, 'frame': idx})
            frame = self.preprocess_frame(frame)
            self.init_video_writer(frame)
            self.init_csv_writer()
            try:
                detections = self.detector.detect(frame)
            except Exception as det_err:
                self.log_structured(logging.ERROR, f'Error en detección: {det_err}', step="detection")
                detections = []
            detections = self.filter_players(detections, frame.shape)
            try:
                tracks = self.tracker.update(detections, frame)
            except Exception as track_err:
                self.log_structured(logging.ERROR, f'Error en tracking: {track_err}', step="tracking")
                tracks = []
            # Visualización y CSV
            keypoints_map = {}
            for track in tracks:
                x1, y1, x2, y2 = track['bbox']
                track_id = track['id']
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, f'ID:{track_id}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                keypoints = keypoints_map.get(track_id)
                if keypoints:
                    for kp in keypoints:
                        if isinstance(kp, (list, tuple)) and len(kp) == 2:
                            kx, ky = int(kp[0]), int(kp[1])
                            cv2.circle(frame, (kx, ky), 3, (255, 0, 0), -1)
                self.write_csv_row(idx, track, keypoints=keypoints)
            if self.save_video and self.video_writer:
                self.video_writer.write(frame)
            self.call_hook('after_frame', {'analysis_id': self.analysis_id, 'frame': idx, 'tracks': [t['id'] for t in tracks]})
            return {'frame': frame, 'idx': idx}
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {}
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    self.log_structured(logging.INFO, 'Fin del video o error de captura.', step="read_frame")
                    break
                batch.append(frame)
                batch_indices.append(self.frame_count)
                if len(batch) == self.batch_size:
                    for i, f in zip(batch_indices, batch):
                        futures[executor.submit(process_frame, i, f)] = i
                    batch = []
                    batch_indices = []
                self.frame_count += 1
            # Procesar los frames restantes
            for i, f in zip(batch_indices, batch):
                futures[executor.submit(process_frame, i, f)] = i
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results_by_index[idx] = result
                except Exception as e:
                    self.log_structured(logging.ERROR, f'Error procesando frame {idx}: {str(e)}', step="main_loop")
        # Mostrar los frames procesados (opcional)
        for idx in sorted(results_by_index.keys()):
            result = results_by_index[idx]
            frame = result['frame']
            if self.save_video and self.video_writer:
                self.video_writer.write(frame)
            cv2.imshow('VideoPipeline', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.log_structured(logging.INFO, 'Procesamiento interrumpido por usuario.', step="user_interrupt")
                break
        self.cap.release()
        if self.video_writer:
            self.video_writer.release()
        if self.csv_file:
            self.csv_file.close()
        cv2.destroyAllWindows()
        self.call_hook('on_finish', {'analysis_id': self.analysis_id, 'total_frames': self.frame_count})

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Video Pipeline Runner')
    parser.add_argument('--config', type=str, required=True, help='Ruta al archivo de configuración YAML')
    parser.add_argument('--analysis_id', type=str, required=False, help='ID único de análisis (opcional)')
    parser.add_argument('--num_workers', type=int, required=False, help='Número de workers para procesar frames en paralelo')
    parser.add_argument('--batch_size', type=int, required=False, help='Tamaño del batch para procesar frames')
    args = parser.parse_args()
    pipeline = VideoPipeline(args.config, analysis_id=args.analysis_id, num_workers=args.num_workers, batch_size=args.batch_size)
    pipeline.run() 