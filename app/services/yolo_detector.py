import cv2
import numpy as np
import torch
from ultralytics import YOLO, solutions
from typing import Dict, Any, List, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class YOLODetector:
    """Clase para manejar la detección de objetos usando YOLOv11."""
    
    def __init__(self, model_path='yolo11n-pose.pt', device='cpu', conf_threshold=0.3):
        """
        Inicializa el detector YOLO.
        
        Args:
            model_path: Ruta al modelo YOLOv11
            device: Dispositivo para inferencia ('cpu', 'cuda', 'mps')
            conf_threshold: Umbral de confianza para la detección
        """
        self.model = YOLO(model_path)
        self.device = device
        self.conf_threshold = conf_threshold
        # Inicializar AIGym para análisis de pose y métricas deportivas si es necesario
        self.gym = solutions.AIGym(model=model_path, show=False)
        self.confidence_threshold = 0.5
        self.class_names = self.model.names
        
    def _setup_device(self, device: Optional[str]) -> str:
        """Configura el dispositivo para inferencia."""
        if device is None:
            if torch.backends.mps.is_available():
                logger.info("Utilizando MPS (Metal Performance Shaders) para aceleración")
                return "mps"
            elif torch.cuda.is_available():
                logger.info("Utilizando CUDA para aceleración")
                return "cuda"
            else:
                logger.info("Usando CPU para inferencia")
                return "cpu"
        return device
    
    def _load_model(self) -> YOLO:
        """Carga el modelo YOLOv8."""
        try:
            model_path = f"yolov8{self.model_size}.pt"
            if not Path(model_path).exists():
                logger.info(f"Descargando modelo YOLOv8-{self.model_size}...")
                model = YOLO(f"yolov8{self.model_size}")
            else:
                model = YOLO(model_path)
            
            # Mover modelo al dispositivo
            model.to(self.device)
            logger.info(f"Modelo YOLOv8-{self.model_size} cargado en {self.device}")
            return model
            
        except Exception as e:
            logger.error(f"Error al cargar modelo YOLO: {str(e)}")
            raise
    
    def detect(self, frame: np.ndarray, classes: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Detecta objetos en un frame.
        
        Args:
            frame: Frame de imagen (BGR)
            classes: Lista de clases a detectar (None para todas)
            
        Returns:
            Lista de detecciones con formato:
            {
                'bbox': [x1, y1, x2, y2],
                'confidence': float,
                'class_id': int,
                'class_name': str
            }
        """
        try:
            with torch.no_grad():
                results = self.model(frame, conf=self.confidence_threshold, classes=classes)
            
            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf.cpu().numpy())
                    cls_id = int(box.cls.cpu().numpy())
                    
                    detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': conf,
                        'class_id': cls_id,
                        'class_name': self.class_names[cls_id]
                    })
            
            return detections
            
        except Exception as e:
            logger.error(f"Error en detección: {str(e)}")
            return []
    
    def detect_batch(self, frames: List[np.ndarray], classes: Optional[List[int]] = None) -> List[List[Dict[str, Any]]]:
        """
        Detecta objetos en un lote de frames.
        
        Args:
            frames: Lista de frames
            classes: Lista de clases a detectar
            
        Returns:
            Lista de listas de detecciones
        """
        try:
            with torch.no_grad():
                results = self.model(frames, conf=self.confidence_threshold, classes=classes)
            
            batch_detections = []
            for r in results:
                frame_detections = []
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf.cpu().numpy())
                    cls_id = int(box.cls.cpu().numpy())
                    
                    frame_detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': conf,
                        'class_id': cls_id,
                        'class_name': self.class_names[cls_id]
                    })
                batch_detections.append(frame_detections)
            
            return batch_detections
            
        except Exception as e:
            logger.error(f"Error en detección por lotes: {str(e)}")
            return [[] for _ in frames]
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """
        Dibuja las detecciones en el frame.
        
        Args:
            frame: Frame original
            detections: Lista de detecciones
            
        Returns:
            Frame con detecciones dibujadas
        """
        frame_with_boxes = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            cls_name = det['class_name']
            
            # Dibujar bbox
            cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Dibujar etiqueta
            label = f"{cls_name}: {conf:.2f}"
            cv2.putText(frame_with_boxes, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame_with_boxes 