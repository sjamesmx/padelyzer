def calcular_cobertura(datos_crudos, nivel):
    """
    Calcula el porcentaje de cobertura de pista.
    Args:
        datos_crudos: dict con datos de posiciones del jugador
        nivel: nivel del jugador
    Returns:
        float: porcentaje de cancha cubierta
    """
    posiciones = datos_crudos.get('posiciones', [])
    if not posiciones:
        return 0.0
    # Suponiendo que cada posición es (x, y) en metros
    cancha_total = 200  # m2 (10x20)
    # Usar un grid para estimar área cubierta
    grid = set()
    for pos in posiciones:
        x = int(pos[0])
        y = int(pos[1])
        grid.add((x, y))
    area_cubierta = len(grid)  # cada celda = 1 m2
    return round((area_cubierta / cancha_total) * 100, 2) 