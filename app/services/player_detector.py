import cv2
import numpy as np
import math
from ultralytics import YOLO
import mediapipe as mp
from typing import Dict, Any, List, Tuple, Optional
import logging
from .yolo_detector import YOLODetector
import requests
import base64

logger = logging.getLogger(__name__)

class PlayerDetector:
    """Clase para detectar y rastrear jugadores en videos de pádel."""
    
    def __init__(self, model_size='n', device='cuda:0', confidence_threshold=0.3, min_confidence=0.1, max_track_history=30, min_track_points=5, track_threshold=100, backend='yolo', roboflow_api_key=None, roboflow_model_url=None):
        """
        Inicializa el detector de jugadores.
        
        Args:
            model_size: Tamaño del modelo YOLO ('n', 's', 'm', 'l', 'x')
            device: Dispositivo para inferencia ('cpu', 'cuda', 'mps')
            confidence_threshold: Umbral de confianza para detectar jugadores
            min_confidence: Umbral mínimo de confianza para aceptar una detección (por defecto 0.1 para dibujar todas las posibles)
            max_track_history: Máximo de puntos en la historia de seguimiento
            min_track_points: Mínimo de puntos para considerar un track válido
            track_threshold: Distancia máxima para asociar detecciones
            backend: 'yolo' o 'roboflow'
            roboflow_api_key: API key de Roboflow (si se usa backend 'roboflow')
            roboflow_model_url: URL del endpoint de Roboflow (si se usa backend 'roboflow')
        """
        self.backend = backend
        self.roboflow_api_key = roboflow_api_key
        self.roboflow_model_url = roboflow_model_url
        if backend == 'yolo':
            self.model = YOLO(f'yolov8{model_size}.pt')
            self.device = device
            self.model.to(device)
        self.confidence_threshold = confidence_threshold
        self.min_confidence = min_confidence
        self.class_ids = {'jugador': 0, 'derecha': 1, 'revés': 2, 'saque': 3, 'volea': 4, 'globo': 5, 'bandeja': 6, 'smash': 7}
        self.track_history = {}
        self.max_track_history = max_track_history
        self.min_track_points = min_track_points
        self.track_threshold = track_threshold
        self.mp_pose = mp.solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def detect(self, frame):
        if self.backend == 'roboflow':
            return self.detect_with_roboflow(frame)
        results = self.model(frame, conf=self.confidence_threshold)
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls)
                conf = float(box.conf)
                if cls in self.class_ids.values() and conf >= self.min_confidence:
                    x1, y1, x2, y2 = box.xyxy[0]
                    area = (x2 - x1) * (y2 - y1)
                    if area > 1000:
                        detections.append({
                            'class': list(self.class_ids.keys())[list(self.class_ids.values()).index(cls)],
                            'box': [x1, y1, x2, y2],
                            'conf': conf,
                            'center': [(x1 + x2) / 2, (y1 + y2) / 2]
                        })
        return detections

    def detect_with_roboflow(self, frame):
        if self.roboflow_api_key is None or self.roboflow_model_url is None:
            logger.error("Roboflow API key o URL no configurados.")
            return []
        # Convertir frame a JPEG y luego a base64
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        try:
            logger.info("Enviando frame a Roboflow...")
            response = requests.post(
                f"{self.roboflow_model_url}?api_key={self.roboflow_api_key}",
                data=img_base64,
                headers=headers,
                timeout=10
            )
            logger.info("Respuesta recibida de Roboflow.")
            response.raise_for_status()
            result = response.json()
            self.last_roboflow_response = result  # Guardar para depuración
            detections = []
            for pred in result.get('predictions', []):
                if pred.get('class') == 'player' and pred.get('confidence', 0) >= self.min_confidence:
                    x = pred['x']
                    y = pred['y']
                    width = pred['width']
                    height = pred['height']
                    x1 = x - width / 2
                    y1 = y - height / 2
                    x2 = x + width / 2
                    y2 = y + height / 2
                    detections.append({
                        'class': 'jugador',
                        'box': [x1, y1, x2, y2],
                        'conf': pred['confidence'],
                        'center': [x, y]
                    })
            return detections
        except Exception as e:
            logger.error(f"Error en la detección con Roboflow: {e}")
            self.last_roboflow_response = str(e)
            return []

    def track_players(self, frame):
        detections = self.detect(frame)
        player_detections = [d for d in detections if d['class'] == 'jugador']
        stroke_detections = [d for d in detections if d['class'] != 'jugador']
        
        tracked_players = []
        for det in player_detections:
            center = det['center']
            track_id = self._assign_track_id(center)
            self.track_history.setdefault(track_id, []).append(center)
            if len(self.track_history[track_id]) > self.max_track_history:
                self.track_history[track_id].pop(0)
            
            speed, direction = 0, 0
            if len(self.track_history[track_id]) >= 2:
                dx = center[0] - self.track_history[track_id][-2][0]
                dy = center[1] - self.track_history[track_id][-2][1]
                speed = (dx**2 + dy**2)**0.5
                direction = math.atan2(dy, dx)
            
            tracked_players.append({
                'track_id': track_id,
                'box': det['box'],
                'conf': det['conf'],
                'speed': speed,
                'direction': direction
            })
        
        tracked_strokes = []
        for stroke in stroke_detections:
            stroke_center = stroke['center']
            closest_player = min(tracked_players, key=lambda p: ((p['box'][0] + p['box'][2])/2 - stroke_center[0])**2 + ((p['box'][1] + p['box'][3])/2 - stroke_center[1])**2, default=None)
            if closest_player and ((closest_player['box'][0] + closest_player['box'][2])/2 - stroke_center[0])**2 + ((closest_player['box'][1] + closest_player['box'][3])/2 - stroke_center[1])**2 < self.track_threshold**2:
                pose_result = self.analyze_stroke_pose(frame, stroke)
                if pose_result:
                    tracked_strokes.append({
                        'track_id': closest_player['track_id'],
                        'stroke': pose_result['stroke'],
                        'box': stroke['box'],
                        'conf': pose_result['confidence']
                    })
        
        return tracked_players, tracked_strokes

    def _assign_track_id(self, center):
        min_dist = float('inf')
        track_id = None
        for tid, history in self.track_history.items():
            last_center = history[-1]
            dist = ((center[0] - last_center[0])**2 + (center[1] - last_center[1])**2)**0.5
            if dist < min_dist and dist < self.track_threshold:
                min_dist = dist
                track_id = tid
        if track_id is None:
            track_id = len(self.track_history)
        self.track_history[track_id] = self.track_history.get(track_id, []) + [center]
        return track_id

    def analyze_stroke_pose(self, frame, stroke_detection):
        x1, y1, x2, y2 = stroke_detection['box']
        cropped_frame = frame[int(y1):int(y2), int(x1):int(x2)]
        results = self.mp_pose.process(cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB))
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            elbow_angle = self._calculate_angle(
                landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER],
                landmarks[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW],
                landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]
            )
            if 90 < elbow_angle < 150 and stroke_detection['stroke'] == 'derecha':
                return {'stroke': 'derecha', 'confidence': stroke_detection['conf'] * 0.9}
            # Agregar más reglas para otros golpes (revés, saque, etc.)
        return None

    def _calculate_angle(self, p1, p2, p3):
        v1 = np.array([p1.x - p2.x, p1.y - p2.y])
        v2 = np.array([p3.x - p2.x, p3.y - p2.y])
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    def draw_tracking(self, frame, tracked_players, tracked_strokes):
        for player in tracked_players:
            x1, y1, x2, y2 = map(int, player['box'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {player['track_id']}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        for stroke in tracked_strokes:
            x1, y1, x2, y2 = map(int, stroke['box'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, f"{stroke['stroke']} (ID: {stroke['track_id']})", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return frame

    def get_player_positions(self, detections: List[Dict[str, Any]]) -> Dict[int, Tuple[int, int]]:
        """
        Obtiene las posiciones actuales de los jugadores.
        
        Args:
            detections: Lista de detecciones con tracking
            
        Returns:
            Diccionario con ID de jugador y posición (x, y)
        """
        positions = {}
        for det in detections:
            track_id = det['track_id']
            bbox = det['bbox']
            center_x = (bbox[0] + bbox[2]) // 2
            center_y = (bbox[1] + bbox[3]) // 2
            positions[track_id] = (center_x, center_y)
        
        return positions 