def calcular_precision(datos_crudos, nivel):
    """
    Calcula la precisión de golpes clave.
    Args:
        datos_crudos: dict con datos de golpes detectados (strokes)
        nivel: nivel del jugador (principiante, intermedio, avanzado)
    Returns:
        float: porcentaje de golpes perfectos
    """
    golpes = datos_crudos.get('strokes', [])
    if not golpes:
        return 0.0
    golpes_correctos = 0
    total_golpes = 0
    # Criterios por tipo de golpe y nivel (ejemplo simplificado)
    criterios = {
        'derecha': {'angulo': (25, 35), 'flexion': 30, 'velocidad': 5},
        'smash': {'angulo': (10, 20), 'flexion': 45, 'velocidad': 15},
        # Agregar más golpes y criterios según nivel
    }
    for golpe in golpes:
        tipo = golpe.get('type')
        if tipo not in criterios:
            continue
        angulo = golpe.get('raqueta_angulo', 0)
        flexion = golpe.get('rodilla_flexion', 0)
        velocidad = golpe.get('raqueta_velocidad', 0)
        c = criterios[tipo]
        if (c['angulo'][0] <= angulo <= c['angulo'][1] and
            flexion >= c['flexion'] and
            velocidad >= c['velocidad']):
            golpes_correctos += 1
        total_golpes += 1
    if total_golpes == 0:
        return 0.0
    return round((golpes_correctos / total_golpes) * 100, 2) 