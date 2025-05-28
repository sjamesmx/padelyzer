from typing import Dict, Any, List
from datetime import datetime

# Importar cada KPI desde su propio archivo
from .kpis.precision import calcular_precision
from .kpis.consistencia import calcular_consistencia
from .kpis.velocidad import calcular_velocidad
from .kpis.potencia import calcular_potencia
from .kpis.tiempo_reaccion import calcular_tiempo_reaccion
from .kpis.cobertura import calcular_cobertura
from .kpis.eficiencia_posicionamiento import calcular_eficiencia_posicionamiento
from .kpis.acierto_seleccion import calcular_acierto_seleccion
from .kpis.recomendaciones import generar_recomendaciones
from .kpis.padel_iq_compuesto import calcular_padel_iq_compuesto, calcular_confianza


def calcular_metricas_padel_iq(datos_crudos: Dict[str, Any], nivel: str) -> Dict[str, Any]:
    """
    Orquesta el cálculo de todos los KPIs y el Padel IQ compuesto.
    Retorna la estructura lista para guardar en Firestore.
    """
    # Técnica
    precision = calcular_precision(datos_crudos, nivel)
    consistencia = calcular_consistencia(datos_crudos, nivel)
    velocidad = calcular_velocidad(datos_crudos, nivel)
    potencia = calcular_potencia(datos_crudos, nivel)

    # Ritmo
    tiempo_reaccion = calcular_tiempo_reaccion(datos_crudos, nivel)

    # Cobertura
    porcentaje_cobertura = calcular_cobertura(datos_crudos, nivel)
    eficiencia_posicionamiento = calcular_eficiencia_posicionamiento(datos_crudos, nivel)

    # Toma de decisiones
    acierto_seleccion = calcular_acierto_seleccion(datos_crudos, nivel)

    # KPIs agrupados
    tecnica = {
        "precision": precision,
        "consistencia": consistencia,
        "velocidad": velocidad,
        "potencia": potencia
    }
    ritmo = {"tiempo_reaccion": tiempo_reaccion}
    cobertura = {
        "porcentaje_cobertura": porcentaje_cobertura,
        "eficiencia_posicionamiento": eficiencia_posicionamiento
    }
    toma_decisiones = {"acierto_seleccion": acierto_seleccion}

    # Cálculo compuesto y confianza
    padel_iq_valor = calcular_padel_iq_compuesto(tecnica, ritmo, cobertura, toma_decisiones, nivel)
    confianza = calcular_confianza(datos_crudos)

    # Recomendaciones
    recomendaciones = generar_recomendaciones(tecnica, ritmo, cobertura, toma_decisiones, nivel)

    # Fecha de cálculo
    fecha_calculo = datetime.utcnow().strftime("%Y-%m-%d")

    # Estructura final
    return {
        "metrics": {
            "tecnica": tecnica,
            "ritmo": ritmo,
            "cobertura": cobertura,
            "toma_decisiones": toma_decisiones,
            "padel_iq": {
                "valor": padel_iq_valor,
                "confianza": confianza,
                "fecha_calculo": fecha_calculo
            },
            "recomendaciones": recomendaciones
        }
    } 