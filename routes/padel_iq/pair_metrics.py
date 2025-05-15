import logging
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_pair_metrics(player_trajectories, golpes_clasificados, team_a_positions=(1, 2), team_b_positions=(3, 4)):
    """Calcula métricas para las parejas (Equipo A: Jugadores 1 y 2, Equipo B: Jugadores 3 y 4)."""
    team_a_metrics = {
        'court_coverage': 0.0,
        'movement_synchronization': 0.0,
        'participation_balance': 0.0,
        'joint_response': 0.0,
        'positioning_errors': 0,
        'positioning_error_responsible': None
    }
    team_b_metrics = {
        'court_coverage': 0.0,
        'movement_synchronization': 0.0,
        'participation_balance': 0.0,
        'joint_response': 0.0,
        'positioning_errors': 0,
        'positioning_error_responsible': None
    }

    # Contar golpes por jugador para calcular el balance de participación
    team_a_strokes = {1: 0, 2: 0}
    team_b_strokes = {3: 0, 4: 0}
    for tipo, golpes in golpes_clasificados.items():
        for golpe in golpes:
            player_pos = golpe.get('player_position')
            if player_pos in team_a_strokes:
                team_a_strokes[player_pos] += 1
            elif player_pos in team_b_strokes:
                team_b_strokes[player_pos] += 1

    # Calcular balance de participación
    total_team_a_strokes = team_a_strokes[1] + team_a_strokes[2]
    total_team_b_strokes = team_b_strokes[3] + team_b_strokes[4]
    if total_team_a_strokes > 0:
        participation_1 = (team_a_strokes[1] / total_team_a_strokes) * 100
        participation_2 = (team_a_strokes[2] / total_team_a_strokes) * 100
        team_a_metrics['participation_balance'] = abs(participation_1 - participation_2)
    if total_team_b_strokes > 0:
        participation_3 = (team_b_strokes[3] / total_team_b_strokes) * 100
        participation_4 = (team_b_strokes[4] / total_team_b_strokes) * 100
        team_b_metrics['participation_balance'] = abs(participation_3 - participation_4)

    # Analizar métricas por golpe
    total_team_a_strokes = 0
    total_team_b_strokes = 0
    coverage_team_a = 0
    coverage_team_b = 0
    sync_team_a = 0
    sync_team_b = 0
    joint_response_team_a = 0
    joint_response_team_b = 0
    errors_team_a = 0
    errors_team_b = 0
    errors_by_player_team_a = {1: 0, 2: 0}
    errors_by_player_team_b = {3: 0, 4: 0}

    for tipo, golpes in golpes_clasificados.items():
        for golpe in golpes:
            start_time = golpe['inicio']
            end_time = golpe.get('fin', start_time + 0.5)
            striker_pos = golpe['player_position']

            if striker_pos in team_a_positions:
                total_team_a_strokes += 1
                striker_team = 'team_a'
                defending_team = 'team_b'
                defending_positions = team_b_positions
                striker_team_positions = team_a_positions
            elif striker_pos in team_b_positions:
                total_team_b_strokes += 1
                striker_team = 'team_b'
                defending_team = 'team_a'
                defending_positions = team_a_positions
                striker_team_positions = team_b_positions
            else:
                continue  # Saltar si el jugador no pertenece a ningún equipo

            # 1. Cobertura de la cancha y sincronización de movimientos para el equipo que golpea
            striker_positions = {}
            for pos in striker_team_positions:
                for track_id, traj in player_trajectories.items():
                    if any(t['player_position'] == pos for t in traj):
                        positions = [p for p in traj if start_time <= p['time'] <= end_time]
                        if positions:
                            striker_positions[pos] = positions

            if len(striker_positions) == 2:
                pos_1 = striker_positions[striker_team_positions[0]]
                pos_2 = striker_positions[striker_team_positions[1]]
                # Cobertura
                avg_y_1 = np.mean([p['position'][1] for p in pos_1]) if pos_1 else 0
                avg_y_2 = np.mean([p['position'][1] for p in pos_2]) if pos_2 else 0
                zone_1 = 'red' if avg_y_1 < 240 else 'fondo'
                zone_2 = 'red' if avg_y_2 < 240 else 'fondo'
                if zone_1 != zone_2:
                    if striker_team == 'team_a':
                        coverage_team_a += 1
                    else:
                        coverage_team_b += 1

                # Sincronización de movimientos
                if len(pos_1) > 1 and len(pos_2) > 1:
                    dy_1 = pos_1[-1]['position'][1] - pos_1[0]['position'][1]
                    dy_2 = pos_2[-1]['position'][1] - pos_2[0]['position'][1]
                    if (dy_1 < 0 and dy_2 > 0) or (dy_1 > 0 and dy_2 < 0):
                        if striker_team == 'team_a':
                            sync_team_a += 1
                        else:
                            sync_team_b += 1

            # 2. Respuesta conjunta y errores de posicionamiento para el equipo defensor
            defender_positions = {}
            for pos in defending_positions:
                for track_id, traj in player_trajectories.items():
                    if any(t['player_position'] == pos for t in traj):
                        positions = [p for p in traj if start_time <= p['time'] <= end_time]
                        if positions:
                            defender_positions[pos] = positions

            if len(defender_positions) == 2:
                pos_1 = defender_positions[defending_positions[0]]
                pos_2 = defender_positions[defending_positions[1]]
                # Respuesta conjunta
                if len(pos_1) > 1 and len(pos_2) > 1:
                    last_pos_1 = pos_1[-1]['position']
                    last_pos_2 = pos_2[-1]['position']
                    # Asumimos que la pelota está cerca del jugador que golpea
                    striker_pos_xy = None
                    for track_id, traj in player_trajectories.items():
                        if any(t['player_position'] == striker_pos for t in traj):
                            positions = [p for p in traj if start_time <= p['time'] <= end_time]
                            if positions:
                                striker_pos_xy = positions[-1]['position']
                                break
                    if not striker_pos_xy:
                        striker_pos_xy = (0, 0)

                    dist_1_to_ball = np.sqrt((last_pos_1[0] - striker_pos_xy[0])**2 + (last_pos_1[1] - striker_pos_xy[1])**2)
                    dist_2_to_ball = np.sqrt((last_pos_2[0] - striker_pos_xy[0])**2 + (last_pos_2[1] - striker_pos_xy[1])**2)
                    # Si uno se mueve hacia la pelota y el otro se reposiciona
                    if (dist_1_to_ball < dist_2_to_ball and pos_2[-1]['position'][1] > pos_2[0]['position'][1]) or \
                       (dist_2_to_ball < dist_1_to_ball and pos_1[-1]['position'][1] > pos_1[0]['position'][1]):
                        if defending_team == 'team_a':
                            joint_response_team_a += 1
                        else:
                            joint_response_team_b += 1

                # Errores de posicionamiento
                avg_y_1 = np.mean([p['position'][1] for p in pos_1]) if pos_1 else 0
                avg_y_2 = np.mean([p['position'][1] for p in pos_2]) if pos_2 else 0
                zone_1 = 'red' if avg_y_1 < 240 else 'fondo'
                zone_2 = 'red' if avg_y_2 < 240 else 'fondo'
                dist_between = np.sqrt((avg_y_1 - avg_y_2)**2 + (pos_1[-1]['position'][0] - pos_2[-1]['position'][0])**2) if pos_1 and pos_2 else 0

                if dist_between < 100 or dist_between > 400 or zone_1 == zone_2:
                    if defending_team == 'team_a':
                        errors_team_a += 1
                        if zone_1 == zone_2:
                            ideal_zone_1 = 'red' if avg_y_1 < avg_y_2 else 'fondo'
                            ideal_zone_2 = 'fondo' if ideal_zone_1 == 'red' else 'red'
                            if zone_1 != ideal_zone_1:
                                errors_by_player_team_a[defending_positions[0]] += 1
                            if zone_2 != ideal_zone_2:
                                errors_by_player_team_a[defending_positions[1]] += 1
                    else:
                        errors_team_b += 1
                        if zone_1 == zone_2:
                            ideal_zone_1 = 'red' if avg_y_1 < avg_y_2 else 'fondo'
                            ideal_zone_2 = 'fondo' if ideal_zone_1 == 'red' else 'red'
                            if zone_1 != ideal_zone_1:
                                errors_by_player_team_b[defending_positions[0]] += 1
                            if zone_2 != ideal_zone_2:
                                errors_by_player_team_b[defending_positions[1]] += 1

    # Calcular porcentajes para métricas del equipo que golpea
    if total_team_a_strokes > 0:
        team_a_metrics['court_coverage'] = (coverage_team_a / total_team_a_strokes) * 100
        team_a_metrics['movement_synchronization'] = (sync_team_a / total_team_a_strokes) * 100
    if total_team_b_strokes > 0:
        team_b_metrics['court_coverage'] = (coverage_team_b / total_team_b_strokes) * 100
        team_b_metrics['movement_synchronization'] = (sync_team_b / total_team_b_strokes) * 100

    # Calcular porcentajes para métricas del equipo defensor
    if total_team_b_strokes > 0:
        team_a_metrics['joint_response'] = (joint_response_team_a / total_team_b_strokes) * 100
    if total_team_a_strokes > 0:
        team_b_metrics['joint_response'] = (joint_response_team_b / total_team_a_strokes) * 100

    # Asignar métricas de errores
    team_a_metrics['positioning_errors'] = errors_team_a
    team_b_metrics['positioning_errors'] = errors_team_b
    team_a_metrics['positioning_error_responsible'] = max(errors_by_player_team_a, key=errors_by_player_team_a.get) if errors_team_a > 0 else None
    team_b_metrics['positioning_error_responsible'] = max(errors_by_player_team_b, key=errors_by_player_team_b.get) if errors_team_b > 0 else None

    return {'team_a': team_a_metrics, 'team_b': team_b_metrics}