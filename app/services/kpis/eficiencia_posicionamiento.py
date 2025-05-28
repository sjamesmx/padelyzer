def calcular_eficiencia_posicionamiento(datos_crudos, nivel):
    """
    Calcula el % de tiempo en zona óptima.
    Args:
        datos_crudos: dict con datos de posiciones y zonas óptimas
        nivel: nivel del jugador
    Returns:
        float: porcentaje de tiempo en zona óptima
    """
    posiciones = datos_crudos.get('posiciones', [])
    zonas_optimas = datos_crudos.get('zonas_optimas', [])
    if not posiciones or not zonas_optimas:
        return 0.0
    en_zona = 0
    for pos in posiciones:
        if any(z[0] <= pos[0] <= z[1] and z[2] <= pos[1] <= z[3] for z in zonas_optimas):
            en_zona += 1
    return round((en_zona / len(posiciones)) * 100, 2) if posiciones else 0.0 