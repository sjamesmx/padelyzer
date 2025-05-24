"""
Excepciones centrales de la aplicación.

Este módulo simplemente reexporta las excepciones definidas en el módulo de dependencias
para mantener compatibilidad con el código existente.
"""

from app.api.v1.dependencies.exceptions import AppException, PadelException

# Mantener compatibilidad con código que importe desde aquí
__all__ = ['AppException', 'PadelException']