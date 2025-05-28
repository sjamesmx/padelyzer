FROM python:3.10-slim

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
COPY . /app
WORKDIR /app

# Variables de entorno para producción
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Expón el puerto para Cloud Run
EXPOSE 8080

# Comando de inicio (ajusta si tu main es diferente)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 