import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import datetime
import hashlib
from firebase_admin import firestore
import json

logger = logging.getLogger(__name__)

# Constantes de validación
MIN_RESOLUTION = (720, 480)  # 720p mínimo
MIN_FPS = 24
MAX_FPS = 60
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv']
MAX_BATCH_SIZE = 5  # Número máximo de videos por lote
CACHE_TTL = 3600  # 1 hora en segundos

class VideoOptimizer:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.db = firestore.client()
        self.cache = {}

    @lru_cache(maxsize=100)
    def get_video_hash(self, video_url: str) -> str:
        """Genera un hash único para el video basado en su URL y timestamp."""
        return hashlib.md5(f"{video_url}_{datetime.now().timestamp()}".encode()).hexdigest()

    async def validate_video_quality(self, video_path: str) -> Tuple[bool, str]:
        """
        Valida la calidad del video.
        Returns: (es_válido, mensaje_error)
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, "No se pudo abrir el video"

            # Verificar resolución
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if width < MIN_RESOLUTION[0] or height < MIN_RESOLUTION[1]:
                return False, f"Resolución insuficiente. Mínimo requerido: {MIN_RESOLUTION}"

            # Verificar FPS
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps < MIN_FPS or fps > MAX_FPS:
                return False, f"FPS fuera de rango. Debe estar entre {MIN_FPS} y {MAX_FPS}"

            # Verificar formato
            _, ext = os.path.splitext(video_path)
            if ext.lower() not in SUPPORTED_FORMATS:
                return False, f"Formato no soportado. Formatos permitidos: {SUPPORTED_FORMATS}"

            cap.release()
            return True, ""

        except Exception as e:
            logger.error(f"Error validando calidad de video: {str(e)}")
            return False, f"Error validando video: {str(e)}"

    async def optimize_video(self, video_path: str, target_resolution: Tuple[int, int] = (1280, 720)) -> str:
        """
        Optimiza el video para análisis.
        Returns: path del video optimizado
        """
        try:
            output_path = f"/tmp/optimized_{os.path.basename(video_path)}"
            
            # Configurar el writer
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, target_resolution)

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Redimensionar frame
                frame = cv2.resize(frame, target_resolution)
                out.write(frame)

            cap.release()
            out.release()
            return output_path

        except Exception as e:
            logger.error(f"Error optimizando video: {str(e)}")
            raise

    async def process_batch(self, video_urls: List[str]) -> Dict[str, Dict]:
        """
        Procesa un lote de videos de manera optimizada.
        """
        results = {}
        tasks = []

        for url in video_urls:
            # Verificar caché
            video_hash = self.get_video_hash(url)
            cached_result = await self.get_cached_result(video_hash)
            if cached_result:
                results[url] = cached_result
                continue

            # Crear tarea para el video
            task = asyncio.create_task(self.process_single_video(url))
            tasks.append((url, task))

        # Procesar tareas en paralelo
        for url, task in tasks:
            try:
                result = await task
                results[url] = result
                # Guardar en caché
                await self.cache_result(self.get_video_hash(url), result)
            except Exception as e:
                logger.error(f"Error procesando video {url}: {str(e)}")
                results[url] = {"error": str(e)}

        return results

    async def process_single_video(self, video_url: str) -> Dict:
        """
        Procesa un único video de manera optimizada.
        """
        try:
            # Descargar video
            temp_path = await self.download_video(video_url)
            
            # Validar calidad
            is_valid, error_msg = await self.validate_video_quality(temp_path)
            if not is_valid:
                return {"error": error_msg}

            # Optimizar video
            optimized_path = await self.optimize_video(temp_path)
            
            # Procesar video optimizado
            result = await self.analyze_video(optimized_path)
            
            # Limpiar archivos temporales
            os.remove(temp_path)
            os.remove(optimized_path)
            
            return result

        except Exception as e:
            logger.error(f"Error procesando video {video_url}: {str(e)}")
            return {"error": str(e)}

    async def download_video(self, video_url: str) -> str:
        """
        Descarga el video de manera optimizada usando streaming y chunks.
        """
        try:
            import aiohttp
            import tempfile

            # Crear archivo temporal
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()

            # Descargar en chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status != 200:
                        raise Exception(f"Error descargando video: {response.status}")

                    with open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)

            return temp_path

        except Exception as e:
            logger.error(f"Error descargando video {video_url}: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    async def analyze_video(self, video_path: str) -> Dict:
        """
        Analiza el video optimizado usando procesamiento por frames.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("No se pudo abrir el video para análisis")

            # Obtener información del video
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps

            # Inicializar variables para análisis
            frame_count = 0
            motion_frames = 0
            quality_score = 0
            blur_scores = []

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Procesar cada N frames para optimizar
                if frame_count % 3 == 0:  # Procesar cada 3 frames
                    # Detectar movimiento
                    if frame_count > 0:
                        prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                        curr_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        diff = cv2.absdiff(prev_frame, curr_frame)
                        if np.mean(diff) > 10:  # Umbral de movimiento
                            motion_frames += 1

                    # Calcular calidad de frame
                    blur_score = cv2.Laplacian(frame, cv2.CV_64F).var()
                    blur_scores.append(blur_score)
                    quality_score += blur_score

                prev_frame = frame.copy()
                frame_count += 1

            cap.release()

            # Calcular métricas finales
            avg_quality = quality_score / (frame_count / 3)
            motion_ratio = motion_frames / (frame_count / 3)
            avg_blur = np.mean(blur_scores)

            return {
                "duration": duration,
                "fps": fps,
                "total_frames": total_frames,
                "motion_ratio": motion_ratio,
                "quality_score": avg_quality,
                "blur_score": avg_blur,
                "is_acceptable_quality": avg_blur > 100,  # Umbral de calidad
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analizando video {video_path}: {str(e)}")
            raise

    async def get_cached_result(self, video_hash: str) -> Optional[Dict]:
        """
        Obtiene el resultado del caché si existe y no ha expirado.
        """
        try:
            cache_doc = self.db.collection("video_cache").document(video_hash).get()
            if cache_doc.exists:
                cache_data = cache_doc.to_dict()
                if datetime.now().timestamp() - cache_data["timestamp"] < CACHE_TTL:
                    return cache_data["result"]
            return None
        except Exception as e:
            logger.error(f"Error obteniendo caché: {str(e)}")
            return None

    async def cache_result(self, video_hash: str, result: Dict) -> None:
        """
        Guarda el resultado en el caché.
        """
        try:
            self.db.collection("video_cache").document(video_hash).set({
                "result": result,
                "timestamp": datetime.now().timestamp()
            })
        except Exception as e:
            logger.error(f"Error guardando en caché: {str(e)}")

    def __del__(self):
        """
        Limpia recursos al destruir la instancia.
        """
        self.executor.shutdown() 