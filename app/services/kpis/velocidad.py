def calcular_velocidad(datos_crudos, nivel):
    """
    Calcula la velocidad promedio de la raqueta durante los golpes.
    Args:
        datos_crudos: dict con datos de golpes detectados (strokes)
        nivel: nivel del jugador
    Returns:
        float: velocidad promedio (m/s)
    """
    golpes = datos_crudos.get('strokes', [])
    if not golpes:
        return 0.0
    velocidades = [g.get('raqueta_velocidad', 0) for g in golpes]
    if not velocidades:
        return 0.0
    return round(sum(velocidades) / len(velocidades), 2) 