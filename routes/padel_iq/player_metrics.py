import numpy as np
import logging

logger = logging.getLogger(__name__)

def assign_player_positions(tracks, existing_positions=None):
    """Asigna posiciones de jugador a cada pista (track) basándose en su ubicación en la cancha."""
    if existing_positions is None:
        existing_positions = {}

    updated_positions = existing_positions.copy()

    for track in tracks:
        if not track.is_confirmed():
            continue
        track_id = track.track_id
        if track_id in updated_positions:
            continue

        x1, y1, w, h = track.to_tlwh()
        center_x = x1 + w / 2
        center_y = y1 + h / 2

        # Determinar el lado y la zona del jugador
        side = 'left' if center_x < 320 else 'right'
        zone = 'net' if center_y < 240 else 'back'

        # Asignar posiciones basadas en el lado y la zona
        # Jugadores 1 y 2 (Equipo A), Jugadores 3 y 4 (Equipo B)
        if side == 'left':
            if zone == 'net':
                player_position = 1  # Jugador 1 (Equipo A, red, izquierda)
            else:
                player_position = 2  # Jugador 2 (Equipo A, fondo, izquierda)
        else:
            if zone == 'net':
                player_position = 3  # Jugador 3 (Equipo B, red, derecha)
            else:
                player_position = 4  # Jugador 4 (Equipo B, fondo, derecha)

        updated_positions[track_id] = player_position
        logger.info(f"Asignado player_position {player_position} al track_id {track_id} (side: {side}, zone: {zone})")

    # Verificar que no se asignen valores inválidos
    for track_id, player_pos in updated_positions.items():
        if player_pos not in [1, 2, 3, 4]:
            logger.error(f"Valor inválido de player_position: {player_pos} para track_id {track_id}")
            # Asignar un valor por defecto basado en la posición existente más común
            most_common = max(set(updated_positions.values()), key=list(updated_positions.values()).count)
            updated_positions[track_id] = most_common
            logger.info(f"Corregido player_position a {most_common} para track_id {track_id}")

    return updated_positions

def interpolate_elbow_angle(player_keypoints, track_id, current_time):
    """Interpolar el ángulo del codo cuando MediaPipe no detecta puntos clave."""
    if track_id not in player_keypoints or len(player_keypoints[track_id]) < 1:
        logger.warning(f"No hay datos para interpolar el ángulo del codo para track_id {track_id} en t={current_time}")
        return 90  # Valor predeterminado si no hay datos

    keypoints = player_keypoints[track_id]
    # Filtrar puntos con ángulos válidos (distintos de 90)
    valid_keypoints = [kp for kp in keypoints if kp['elbow_angle'] != 90]

    if len(valid_keypoints) < 2:
        # Si no hay suficientes puntos válidos, buscar el punto más cercano con ángulo válido
        closest = min(keypoints, key=lambda kp: abs(kp['time'] - current_time), default=None)
        if closest and closest['elbow_angle'] != 90:
            logger.info(f"Usando ángulo más cercano: {closest['elbow_angle']} para track_id {track_id} en t={current_time}")
            return closest['elbow_angle']
        logger.warning(f"No hay puntos válidos para interpolar en t={current_time}, track_id={track_id}")
        return 90  # Valor predeterminado si no se puede interpolar

    # Encontrar el punto anterior y posterior más cercano con ángulos válidos
    before = None
    after = None
    for kp in valid_keypoints:
        if kp['time'] < current_time:
            before = kp
        elif kp['time'] > current_time and after is None:
            after = kp

    if before is None or after is None:
        # Si no hay puntos antes y después, usar el más cercano
        closest = min(valid_keypoints, key=lambda kp: abs(kp['time'] - current_time))
        logger.info(f"Usando ángulo más cercano: {closest['elbow_angle']} para track_id {track_id} en t={current_time}")
        return closest['elbow_angle']

    # Interpolación lineal
    time_span = after['time'] - before['time']
    if time_span == 0:
        return before['elbow_angle']

    weight = (current_time - before['time']) / time_span
    interpolated_angle = before['elbow_angle'] + weight * (after['elbow_angle'] - before['elbow_angle'])
    
    logger.info(f"Ángulo del codo interpolado: {interpolated_angle} para track_id {track_id} en t={current_time}")
    return interpolated_angle

def calculate_metrics_for_non_striking_players(striking_player, start_time, end_time, player_trajectories, ball_position):
    """Calcula métricas para jugadores que no están golpeando la pelota."""
    metrics = {}
    for track_id, trajectory in player_trajectories.items():
        player_position = trajectory[-1]['player_position'] if trajectory else 0
        if player_position == striking_player or player_position == 0:
            continue

        relevant_points = [p for p in trajectory if start_time <= p['time'] <= end_time]
        if not relevant_points:
            continue

        positions = [p['position'] for p in relevant_points]
        body_orientations = []
        distances_moved = []
        reaction_times = []

        for i in range(len(relevant_points)):
            point = relevant_points[i]
            body_orientation = 'facing' if point['zone'] == 'net' else 'not_facing'
            body_orientations.append(body_orientation)

            if i > 0:
                prev_point = relevant_points[i-1]
                distance = np.sqrt((point['position'][0] - prev_point['position'][0])**2 +
                                   (point['position'][1] - prev_point['position'][1])**2)
                distances_moved.append(distance)
                reaction_time = point['time'] - prev_point['time']
                reaction_times.append(reaction_time)

        average_position = 'red' if any(p['zone'] == 'net' for p in relevant_points) else 'fondo'
        avg_body_orientation = max(set(body_orientations), key=body_orientations.count) if body_orientations else None
        total_distance_moved = sum(distances_moved) if distances_moved else 0
        movement_activity = 'moving' if total_distance_moved > 0 else 'static'
        avg_reaction_time = sum(reaction_times) / len(reaction_times) if reaction_times else None

        metrics[player_position] = {
            'average_position': average_position,
            'body_orientation': avg_body_orientation,
            'distance_moved': total_distance_moved,
            'movement_activity': movement_activity,
            'reaction_time': avg_reaction_time
        }

    return metrics