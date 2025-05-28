import numpy as np

def calcular_consistencia(datos_crudos, nivel):
    """
    Calcula la consistencia de golpes: % de golpes cuya variabilidad es baja.
    Args:
        datos_crudos: dict con datos de golpes detectados (strokes)
        nivel: nivel del jugador
    Returns:
        float: porcentaje de golpes estables
    """
    golpes = datos_crudos.get('strokes', [])
    if not golpes or len(golpes) < 2:
        return 0.0
    angulos = [g.get('raqueta_angulo', 0) for g in golpes]
    velocidades = [g.get('raqueta_velocidad', 0) for g in golpes]
    # Umbrales por nivel (ejemplo)
    umbral_angulo = 8 if nivel == 'principiante' else 5
    umbral_velocidad = 2 if nivel == 'principiante' else 1
    std_angulo = np.std(angulos)
    std_velocidad = np.std(velocidades)
    golpes_estables = 0
    for a, v in zip(angulos, velocidades):
        if abs(a - np.mean(angulos)) <= umbral_angulo and abs(v - np.mean(velocidades)) <= umbral_velocidad:
            golpes_estables += 1
    return round((golpes_estables / len(golpes)) * 100, 2) 