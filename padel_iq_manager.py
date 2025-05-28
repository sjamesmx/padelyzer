import json
from typing import Dict, List, Optional

# --- Cálculo del IQ compuesto ---
def calcular_iq_compuesto(iq_biomecanico: float, iq_tactico: float, peso_bio: float = 0.6, peso_tac: float = 0.4) -> float:
    """Calcula el IQ compuesto ponderando biomecánico y táctico."""
    return iq_biomecanico * peso_bio + iq_tactico * peso_tac

# --- Actualización del IQ global (promedio móvil ponderado) ---
def actualizar_iq_global(iq_anterior: float, iq_nuevo: float, alpha: float = 0.3) -> float:
    """Actualiza el IQ global usando un promedio móvil ponderado."""
    return (1 - alpha) * iq_anterior + alpha * iq_nuevo

# --- Gestión de historial e IQ por jugador (simulado en memoria, luego se migrará a BD) ---
class PadelIQManager:
    def __init__(self):
        # Estructura: {user_id: {'iq_global': float, 'historial': [{'video_id': str, 'iq': float, 'fecha': str}]}}
        self.iq_data: Dict[str, Dict] = {}

    def registrar_video(self, user_id: str, video_id: str, fecha: str, iq_bio: float, iq_tac: float):
        iq_comp = calcular_iq_compuesto(iq_bio, iq_tac)
        if user_id not in self.iq_data:
            self.iq_data[user_id] = {'iq_global': iq_comp, 'historial': []}
        else:
            iq_ant = self.iq_data[user_id]['iq_global']
            iq_comp = actualizar_iq_global(iq_ant, iq_comp)
            self.iq_data[user_id]['iq_global'] = iq_comp
        self.iq_data[user_id]['historial'].append({
            'video_id': video_id,
            'iq_biomecanico': iq_bio,
            'iq_tactico': iq_tac,
            'iq_compuesto': iq_comp,
            'fecha': fecha
        })
        return iq_comp

    def consultar_iq_global(self, user_id: str) -> Optional[float]:
        if user_id in self.iq_data:
            return self.iq_data[user_id]['iq_global']
        return None

    def consultar_historial(self, user_id: str) -> List[Dict]:
        if user_id in self.iq_data:
            return self.iq_data[user_id]['historial']
        return []

    def exportar_historial_json(self, user_id: str, ruta: str):
        if user_id in self.iq_data:
            with open(ruta, 'w') as f:
                json.dump(self.iq_data[user_id]['historial'], f, indent=2)

# Ejemplo de uso:
# manager = PadelIQManager()
# manager.registrar_video('user1', 'vid1', '2024-05-26', 70, 60)
# print(manager.consultar_iq_global('user1'))
# print(manager.consultar_historial('user1')) 