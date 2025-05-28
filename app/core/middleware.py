from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
import time
from typing import Callable
from app.api.v1.dependencies.exceptions import AppException, PadelException

logger = logging.getLogger(__name__)

async def error_handling_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware para manejar excepciones de manera global y formatear las respuestas de error.

    Args:
        request: Objeto Request de FastAPI
        call_next: Función para llamar al siguiente middleware o endpoint

    Returns:
        Response objeto de respuesta HTTP
    """
    start_time = time.time()

    try:
        # Intentar ejecutar la solicitud normalmente
        response = await call_next(request)

        # Registrar tiempo de respuesta para métricas
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except AppException as e:
        # Manejar excepciones específicas de la aplicación
        logger.error(f"Error de aplicación: {e.message}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "code": e.status_code,
                    "message": e.message,
                    "type": e.__class__.__name__,
                    "details": e.details
                }
            }
        )

    except PadelException as e:
        # Manejar excepciones específicas de pádel
        logger.error(f"Error de pádel: {e.message}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "code": e.status_code,
                    "message": e.message,
                    "type": e.__class__.__name__,
                    "details": e.details
                }
            }
        )

    except Exception as e:
        # Manejar excepciones no controladas
        logger.error(f"Error interno del servidor: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Error interno del servidor",
                    "type": "InternalServerError"
                }
            }
        )
    """
    Middleware para manejar errores de manera consistente en toda la aplicación.
    """
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except AppException as e:
        logger.error(f"Error de aplicación: {e.message}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "code": e.status_code,
                    "message": e.message,
                    "type": e.__class__.__name__
                }
            }
        )
    except PadelException as e:
        logger.error(f"Error de dominio: {e.message}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "code": e.status_code,
                    "message": e.message,
                    "type": e.__class__.__name__
                }
            }
        )
    except Exception as e:
        logger.error(f"Error no manejado: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Error interno del servidor",
                    "type": "InternalServerError"
                }
            }
        )
