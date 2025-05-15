import json
import time
from datetime import datetime
from google.cloud import firestore
from google.cloud import monitoring_v3
import firebase_admin
from firebase_admin import credentials
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_metrics():
    """Obtiene métricas de Prometheus/Grafana."""
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path("padelyzer")
    
    # Obtener métricas de los últimos 24 horas
    interval = monitoring_v3.TimeInterval({
        "end_time": {"seconds": int(time.time())},
        "start_time": {"seconds": int(time.time() - 86400)}
    })
    
    metrics = {
        'latency': get_metric(client, project_name, 'padel_iq_analysis_latency_seconds', interval),
        'accuracy': get_metric(client, project_name, 'padel_iq_analysis_accuracy', interval),
        'cpu_usage': get_metric(client, project_name, 'padel_iq_analysis_cpu_usage', interval),
        'memory_usage': get_metric(client, project_name, 'padel_iq_analysis_memory_usage', interval),
        'nps': get_metric(client, project_name, 'padel_iq_analysis_nps', interval)
    }
    
    return metrics

def get_metric(client, project_name, metric_name, interval):
    """Obtiene una métrica específica."""
    try:
        request = monitoring_v3.ListTimeSeriesRequest(
            name=project_name,
            filter=f'metric.type = "custom.googleapis.com/{metric_name}"',
            interval=interval,
            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
        )
        
        results = client.list_time_series(request)
        if not results:
            return None
            
        # Obtener el valor más reciente
        return results[0].points[-1].value.double_value
    except Exception as e:
        logger.error(f"Error obteniendo métrica {metric_name}: {str(e)}")
        return None

def generate_report():
    """Genera el reporte final de pruebas."""
    # Inicializar Firebase
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate("firebase-credentials.json")
        firebase_admin.initialize_app(cred)
    
    # Obtener cliente de Firestore
    db = firestore.client()
    
    # Obtener resultados de pruebas
    test_reports = db.collection('test_reports').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()
    if not test_reports:
        logger.error("No se encontraron reportes de prueba")
        return
    
    latest_report = test_reports[0].to_dict()
    
    # Obtener métricas
    metrics = get_metrics()
    
    # Generar reporte
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'test_results': latest_report,
        'metrics': metrics,
        'recommendations': []
    }
    
    # Analizar resultados y generar recomendaciones
    if metrics['latency'] and metrics['latency'] > 300:
        report['recommendations'].append("Optimizar latencia: La latencia p95 excede 300 segundos")
    
    if metrics['accuracy'] and metrics['accuracy'] < 95:
        report['recommendations'].append("Mejorar precisión: La precisión está por debajo del 95%")
    
    if metrics['cpu_usage'] and metrics['cpu_usage'] > 80:
        report['recommendations'].append("Optimizar uso de CPU: El uso excede el 80%")
    
    if metrics['memory_usage'] and metrics['memory_usage'] > 80:
        report['recommendations'].append("Optimizar uso de memoria: El uso excede el 80%")
    
    if metrics['nps'] and metrics['nps'] < 50:
        report['recommendations'].append("Mejorar experiencia de usuario: NPS por debajo de 50")
    
    # Guardar reporte en Firestore
    db.collection('test_reports').document(report['timestamp']).set(report)
    
    # Generar archivo Markdown
    with open('test_report.md', 'w') as f:
        f.write(f"# Reporte de Pruebas - {report['timestamp']}\n\n")
        
        f.write("## Resumen de Pruebas\n")
        f.write(f"- Total de videos: {report['test_results']['total_videos']}\n")
        f.write(f"- Análisis exitosos: {report['test_results']['successful_analyses']}\n")
        f.write(f"- Latencia promedio: {report['test_results']['average_latency']:.2f} segundos\n\n")
        
        f.write("## Métricas del Sistema\n")
        if metrics['latency']:
            f.write(f"- Latencia p95: {metrics['latency']:.2f} segundos\n")
        if metrics['accuracy']:
            f.write(f"- Precisión: {metrics['accuracy']:.2f}%\n")
        if metrics['cpu_usage']:
            f.write(f"- Uso de CPU: {metrics['cpu_usage']:.2f}%\n")
        if metrics['memory_usage']:
            f.write(f"- Uso de Memoria: {metrics['memory_usage']:.2f}%\n")
        if metrics['nps']:
            f.write(f"- NPS: {metrics['nps']:.2f}\n")
        
        f.write("\n## Resultados Detallados\n")
        for result in report['test_results']['results']:
            f.write(f"\n### {result['video_name']}\n")
            f.write(f"- Golpes detectados: {result['detected_strokes']} (esperados: {result['expected_strokes']})\n")
            f.write(f"- Padel IQ: {result['padel_iq']['padel_iq']}\n")
            f.write(f"- Latencia: {result['latency']:.2f} segundos\n")
            f.write(f"- Estado: {result['status']}\n")
        
        if report['recommendations']:
            f.write("\n## Recomendaciones\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")

if __name__ == "__main__":
    generate_report() 