def calcular_tiempo_reaccion(datos_crudos, nivel):
    """
    Calcula el tiempo de reacción promedio.
    Args:
        datos_crudos: dict con datos de eventos de reacción
        nivel: nivel del jugador
    Returns:
        float: tiempo de reacción promedio (s)
    """
    reacciones = datos_crudos.get('reacciones', [])
    if not reacciones:
        return 0.0
    tiempos = [r.get('tiempo_reaccion', 0) for r in reacciones if r.get('tiempo_reaccion', 0) > 0]
    if not tiempos:
        return 0.0
    return round(sum(tiempos) / len(tiempos), 2) 