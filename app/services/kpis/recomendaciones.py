def generar_recomendaciones(tecnica, ritmo, cobertura, toma_decisiones, nivel):
    """
    Genera recomendaciones automáticas según los KPIs y el nivel del jugador.
    Args:
        tecnica, ritmo, cobertura, toma_decisiones: dicts de KPIs
        nivel: nivel del jugador
    Returns:
        list de recomendaciones (str)
    """
    recomendaciones = []
    if tecnica['precision'] < 60:
        recomendaciones.append("Trabaja en la flexión de rodillas para mejorar la precisión de tus golpes.")
    if tecnica['consistencia'] < 60:
        recomendaciones.append("Practica la regularidad de tu swing para mejorar la consistencia.")
    if ritmo['tiempo_reaccion'] > 0.8:
        recomendaciones.append("Anticipa el golpe rival para reducir tu tiempo de reacción.")
    if cobertura['porcentaje_cobertura'] < 50:
        recomendaciones.append("Desplázate más hacia la red para mejorar tu cobertura de pista.")
    if toma_decisiones['acierto_seleccion'] < 60:
        recomendaciones.append("Elige más globos en defensa para mejorar tu toma de decisiones.")
    if not recomendaciones:
        recomendaciones.append("¡Sigue así! Estás alcanzando un gran nivel.")
    return recomendaciones 