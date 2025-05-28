def calcular_acierto_seleccion(datos_crudos, nivel):
    """
    Calcula el % de golpes apropiados según contexto.
    Args:
        datos_crudos: dict con datos de golpes y contexto
        nivel: nivel del jugador
    Returns:
        float: porcentaje de acierto en selección
    """
    golpes = datos_crudos.get('strokes', [])
    if not golpes:
        return 0.0
    apropiados = [g for g in golpes if g.get('decision_apropiada', False)]
    return round((len(apropiados) / len(golpes)) * 100, 2) if golpes else 0.0 