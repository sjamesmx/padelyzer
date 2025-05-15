import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """
    Configura el sistema de logging para la aplicación.
    - Configura el formato de los logs
    - Crea un directorio de logs si no existe
    - Configura el handler para archivo y consola
    """
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configurar el logger
    logger = logging.getLogger("pdzr")
    logger.setLevel(logging.INFO)

    # Formato de los logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler para archivo
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger 