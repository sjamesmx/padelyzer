import numpy as np

# Índices de keypoints MediaPipe Pose
HOMBRO_D = 12
CODO_D = 14
MUÑECA_D = 16
HOMBRO_I = 11
CODO_I = 13
MUÑECA_I = 15
CADERA_D = 24
CADERA_I = 23
RODILLA_D = 26
RODILLA_I = 25
TOBILLO_D = 28
TOBILLO_I = 27

# Utilidades

def get_angle(a, b, c):
    """Ángulo en grados entre tres puntos (b es el vértice)."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

def get_distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))

def get_torso_rotation(keypoints):
    """Aproximación: ángulo entre línea de hombros y eje horizontal."""
    if HOMBRO_D in keypoints and HOMBRO_I in keypoints:
        p1, p2 = keypoints[HOMBRO_D], keypoints[HOMBRO_I]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return np.degrees(np.arctan2(dy, dx))
    return None

def get_cadera_rotation(keypoints):
    if CADERA_D in keypoints and CADERA_I in keypoints:
        p1, p2 = keypoints[CADERA_D], keypoints[CADERA_I]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return np.degrees(np.arctan2(dy, dx))
    return None

def get_inclinacion_torso(keypoints):
    if CADERA_D in keypoints and CADERA_I in keypoints and HOMBRO_D in keypoints and HOMBRO_I in keypoints:
        cadera_centro = ((keypoints[CADERA_D][0] + keypoints[CADERA_I][0]) / 2, (keypoints[CADERA_D][1] + keypoints[CADERA_I][1]) / 2)
        hombro_centro = ((keypoints[HOMBRO_D][0] + keypoints[HOMBRO_I][0]) / 2, (keypoints[HOMBRO_D][1] + keypoints[HOMBRO_I][1]) / 2)
        dx = hombro_centro[0] - cadera_centro[0]
        dy = hombro_centro[1] - cadera_centro[1]
        return np.degrees(np.arctan2(dy, dx))
    return None

# Clasificación principal

def clasificar_golpe(keypoints, historial=None):
    """
    Clasifica el tipo de golpe de pádel usando keypoints (formato {idx: (x, y)}).
    Opcional: historial para análisis temporal.
    Devuelve: (tipo_golpe, detalles_dict)
    """
    # Ángulos y rotaciones
    ang_codo = ang_hombro = ang_muneca = None
    rot_torso = rot_cadera = inc_torso = None
    detalles = {}
    if HOMBRO_D in keypoints and CODO_D in keypoints and MUÑECA_D in keypoints:
        ang_codo = get_angle(keypoints[HOMBRO_D], keypoints[CODO_D], keypoints[MUÑECA_D])
    if CADERA_D in keypoints and HOMBRO_D in keypoints and CODO_D in keypoints:
        ang_hombro = get_angle(keypoints[CADERA_D], keypoints[HOMBRO_D], keypoints[CODO_D])
    if CODO_D in keypoints and MUÑECA_D in keypoints and HOMBRO_D in keypoints:
        ang_muneca = get_angle(keypoints[CODO_D], keypoints[MUÑECA_D], keypoints[HOMBRO_D])
    rot_torso = get_torso_rotation(keypoints)
    rot_cadera = get_cadera_rotation(keypoints)
    inc_torso = get_inclinacion_torso(keypoints)
    detalles.update({
        'ang_codo': ang_codo,
        'ang_hombro': ang_hombro,
        'ang_muneca': ang_muneca,
        'rot_torso': rot_torso,
        'rot_cadera': rot_cadera,
        'inc_torso': inc_torso
    })
    # --- Heurísticas por tipo de golpe ---
    # Derecha
    if ang_codo and 90 <= ang_codo <= 150 and rot_torso and 30 <= abs(rot_torso) <= 60:
        return 'Derecha', detalles
    # Revés
    if ang_codo and 30 <= ang_codo < 90 and rot_torso and 90 <= abs(rot_torso) <= 120:
        return 'Revés', detalles
    # Saque
    if ang_muneca and 30 <= ang_muneca <= 90 and ang_hombro and ang_hombro > 150:
        return 'Saque', detalles
    # Volea
    if ang_codo and 60 <= ang_codo <= 90 and inc_torso and 10 <= abs(inc_torso) <= 30:
        return 'Volea', detalles
    # Globo
    if ang_muneca and 60 <= ang_muneca <= 120 and rot_cadera and 20 <= abs(rot_cadera) <= 40:
        return 'Globo', detalles
    # Bandeja
    if ang_hombro and 90 <= ang_hombro <= 120 and ang_codo and 60 <= ang_codo <= 90:
        return 'Bandeja', detalles
    # Smash
    if ang_hombro and 160 <= ang_hombro <= 180 and rot_torso and 60 <= abs(rot_torso) <= 90:
        return 'Smash', detalles
    # Otro
    return 'Otro', detalles 