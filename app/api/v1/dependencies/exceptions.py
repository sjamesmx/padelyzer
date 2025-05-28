"""
Excepciones personalizadas para la API de Padelyzer.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status

class AppException(HTTPException):
    """Excepción base para errores de la aplicación."""
    def __init__(self, status_code: int, message: str, details: dict = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.details = details or {}

class PadelException(AppException):
    """Excepción específica para errores relacionados con el pádel."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            details=details
        )

class VideoProcessingException(AppException):
    """Excepción para errores en el procesamiento de videos."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            details=details
        )

class AuthenticationException(AppException):
    """Excepción para errores de autenticación."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            details=details
        )

class ValidationException(AppException):
    """Excepción para errores de validación."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            details=details
        )

class AuthorizationException(AppException):
    """Excepción para errores de autorización."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            details=details
        )

class ResourceNotFoundException(AppException):
    """Excepción para recursos no encontrados."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            details=details
        ) 