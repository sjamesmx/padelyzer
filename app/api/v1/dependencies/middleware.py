import logging
import traceback
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from .exceptions import PadelException, AppException

logger = logging.getLogger(__name__)

def create_error_response(status_code: int, message: str, error_type: str) -> JSONResponse:
    """Helper function to create a consistent error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": status_code,
                "message": message,
                "type": error_type
            }
        }
    )

async def error_handling_middleware(request: Request, call_next):
    """
    Middleware para manejar errores de forma global.
    Captura excepciones y devuelve respuestas JSON estandarizadas.
    """
    try:
        return await call_next(request)
    except HTTPException as exc:
        # Manejar excepciones HTTP estándar
        logger.error(
            f"Error HTTP en {request.method} {request.url.path}: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        )
        return create_error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            error_type=exc.__class__.__name__
        )
    except AppException as exc:
        # Manejar excepciones personalizadas de la aplicación
        logger.error(
            f"Error de aplicación en {request.method} {request.url.path}: {exc.message}",
            extra={
                "status_code": exc.status_code,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        )
        return create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            error_type=exc.__class__.__name__
        )
    except PadelException as exc:
        # Manejar excepciones específicas de Padelyzer
        logger.error(
            f"Error en {request.method} {request.url.path}: {exc.message}",
            extra={
                "status_code": exc.status_code,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        )
        return create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            error_type=exc.__class__.__name__
        )
    except Exception as exc:
        # Manejar excepciones no controladas
        error_detail = str(exc)
        stack_trace = traceback.format_exc()
        
        logger.error(
            f"Error inesperado en {request.method} {request.url.path}: {error_detail}",
            extra={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
                "stack_trace": stack_trace
            }
        )
        
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error interno del servidor",
            error_type="InternalServerError"
        ) 