def calcular_potencia(datos_crudos, nivel):
    """
    Calcula la potencia promedio de los golpes (W).
    Args:
        datos_crudos: dict con datos de golpes detectados (strokes)
        nivel: nivel del jugador
    Returns:
        float: potencia promedio (W)
    """
    golpes = datos_crudos.get('strokes', [])
    if not golpes:
        return 0.0
    m = 0.056  # kg, peso de la pelota de pádel
    tiempo_contacto = 0.01  # s
    potencias = []
    for g in golpes:
        v = g.get('pelota_velocidad', 0)
        if v > 0:
            p = 0.5 * m * (v ** 2) / tiempo_contacto
            potencias.append(p)
    if not potencias:
        return 0.0
    return round(sum(potencias) / len(potencias), 2) 