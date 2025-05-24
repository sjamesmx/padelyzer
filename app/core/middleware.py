from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
import time
from typing import Callable
from app.api.v1.dependencies.exceptions import AppException, PadelException

logger = logging.getLogger(__name__)

async def error_handling_middleware(request: Request, call_next: Callable) -> Response:
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