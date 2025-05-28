def calcular_padel_iq_compuesto(tecnica, ritmo, cobertura, toma_decisiones, nivel):
    """
    Calcula el Padel IQ compuesto usando los pesos por nivel.
    Args:
        tecnica, ritmo, cobertura, toma_decisiones: dicts de KPIs
        nivel: nivel del jugador
    Returns:
        float: valor de Padel IQ
    """
    pesos = {
        'principiante': {'tecnica': 0.4, 'ritmo': 0.3, 'fuerza': 0.1, 'cobertura': 0.1, 'toma_decisiones': 0.1},
        'intermedio': {'tecnica': 0.35, 'ritmo': 0.25, 'fuerza': 0.15, 'cobertura': 0.15, 'toma_decisiones': 0.1},
        'avanzado': {'tecnica': 0.3, 'ritmo': 0.2, 'fuerza': 0.2, 'cobertura': 0.15, 'toma_decisiones': 0.15}
    }
    p = pesos.get(nivel, pesos['principiante'])
    fuerza = tecnica.get('potencia', 0)
    valor = (
        tecnica.get('precision', 0) * p['tecnica'] +
        ritmo.get('tiempo_reaccion', 0) * p['ritmo'] +
        fuerza * p['fuerza'] +
        cobertura.get('porcentaje_cobertura', 0) * p['cobertura'] +
        toma_decisiones.get('acierto_seleccion', 0) * p['toma_decisiones']
    ) / sum(p.values())
    return round(valor, 2)

def calcular_confianza(datos_crudos):
    """
    Calcula el nivel de confianza del resultado según la cantidad de datos.
    Args:
        datos_crudos: dict con datos crudos
    Returns:
        str: 'alta', 'media' o 'baja'
    """
    golpes = datos_crudos.get('strokes', [])
    if len(golpes) >= 20:
        return 'alta'
    elif len(golpes) >= 10:
        return 'media'
    else:
        return 'baja' 