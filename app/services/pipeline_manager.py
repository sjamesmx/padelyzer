import tempfile
import requests
import shutil
import subprocess
import os
from datetime import datetime
from typing import Dict, Optional
from google.cloud import storage

class PipelineManager:
    def __init__(self, model_size: str = "n", device: str = None, num_workers: int = None, batch_size: int = None, output_dir: Optional[str] = None, gcs_bucket: Optional[str] = None):
        self.model_size = model_size
        self.device = device or os.getenv("PIPELINE_DEVICE", "mps")
        self.num_workers = num_workers if num_workers is not None else int(os.getenv("PIPELINE_NUM_WORKERS", "4"))
        self.batch_size = batch_size if batch_size is not None else int(os.getenv("PIPELINE_BATCH_SIZE", "8"))
        self.output_dir = output_dir or os.getenv("PIPELINE_OUTPUT_DIR", "/tmp/pipeline_results")
        os.makedirs(self.output_dir, exist_ok=True)
        self.gcs_bucket = gcs_bucket or os.getenv("PIPELINE_GCS_BUCKET")
        self.video_processor = VideoProcessor(model_size=model_size, device=self.device, num_workers=self.num_workers, batch_size=self.batch_size)
        logger.info(f"PipelineManager inicializado con device={self.device}, workers={self.num_workers}, batch_size={self.batch_size}, output_dir={self.output_dir}, gcs_bucket={self.gcs_bucket}")

    def _download_video(self, video_url: str) -> str:
        """
        Descarga el video a /tmp si es remoto (http(s) o gs://). Devuelve la ruta local.
        """
        if video_url.startswith('/'):  # Ruta local
            return video_url
        tmp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        tmp_path = tmp_file.name
        tmp_file.close()
        try:
            if video_url.startswith('http'):  # HTTP/HTTPS
                with requests.get(video_url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(tmp_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
            elif video_url.startswith('gs://'):  # Google Cloud Storage
                subprocess.run(['gsutil', 'cp', video_url, tmp_path], check=True)
            else:
                raise ValueError(f"URL de video no soportada: {video_url}")
            logger.info(f"[Pipeline] Video descargado temporalmente en: {tmp_path}")
            return tmp_path
        except Exception as e:
            logger.error(f"[Pipeline] Error descargando video: {str(e)}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def _upload_to_gcs(self, local_path: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Sube el archivo local a Cloud Storage y devuelve la URL firmada.
        """
        if not self.gcs_bucket:
            logger.warning("[Pipeline] No se configuró PIPELINE_GCS_BUCKET. No se subirá el video procesado a GCS.")
            return None
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.gcs_bucket)
            filename = os.path.basename(local_path)
            if user_id:
                blob_path = f"processed_videos/{user_id}/{filename}"
            else:
                blob_path = f"processed_videos/{filename}"
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            url = blob.generate_signed_url(expiration=3600*24*7)  # 7 días
            logger.info(f"[Pipeline] Video procesado subido a GCS: {url}")
            return url
        except Exception as e:
            logger.error(f"[Pipeline] Error subiendo video a GCS: {str(e)}")
            return None

    def analyze(self, video_path: str, tipo: str = "game", nivel: str = "intermedio", user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Orquesta el análisis completo de un video y el cálculo de KPIs y Padel IQ.
        """
        temp_video_path = None
        output_path = None
        try:
            logger.info(f"[Pipeline] Iniciando análisis para video: {video_path} (tipo={tipo}, nivel={nivel})")
            # Descargar video si es remoto
            temp_video_path = self._download_video(video_path)
            output_path = os.path.join(self.output_dir, f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            # Procesar video y extraer datos crudos
            video_results = self.video_processor.process_video(temp_video_path, output_path=output_path)
            logger.info(f"[Pipeline] Procesamiento de video completado. Frames: {video_results['total_frames']}")
            # Determinar nivel (placeholder, se puede mejorar)
            nivel_detectado = nivel
            # Calcular KPIs y Padel IQ
            datos_crudos = video_results['analysis']
            metricas = calcular_metricas_padel_iq(datos_crudos, nivel_detectado)
            logger.info(f"[Pipeline] KPIs y Padel IQ calculados correctamente.")
            # Subir video procesado a GCS
            gcs_url = self._upload_to_gcs(output_path, user_id=user_id) if output_path and os.path.exists(output_path) else None
            # Estructura final para exportar/guardar
            resultado = {
                "user_id": user_id,
                "video_path": video_path,
                "tipo": tipo,
                "nivel": nivel_detectado,
                "created_at": datetime.utcnow().isoformat(),
                "metrics": metricas["metrics"],
                "raw_analysis": video_results['analysis'],
                "duration": video_results['duration'],
                "total_frames": video_results['total_frames'],
                "output_video": output_path,
                "output_video_gcs_url": gcs_url
            }
            logger.info(f"[Pipeline] Análisis completo finalizado para video: {video_path}")
            return resultado
        except Exception as e:
            logger.error(f"[Pipeline] Error en el análisis del pipeline: {str(e)}", exc_info=True)
            return {"error": str(e), "video_path": video_path}
        finally:
            # Limpieza del archivo temporal
            if temp_video_path and temp_video_path != video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                    logger.info(f"[Pipeline] Archivo temporal eliminado: {temp_video_path}")
                except Exception as del_err:
                    logger.warning(f"[Pipeline] No se pudo eliminar el archivo temporal: {del_err}")
            # Limpieza del video procesado local
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.info(f"[Pipeline] Video procesado local eliminado: {output_path}")
                except Exception as del_err:
                    logger.warning(f"[Pipeline] No se pudo eliminar el video procesado local: {del_err}") 