# Padelyzer Backend

Backend para la aplicación Padelyzer, un sistema de análisis de videos de pádel que utiliza inteligencia artificial para detectar y analizar golpes.

## Características

- Análisis de videos de entrenamiento y partidos
- Detección de jugadores y golpes
- Cálculo de métricas de rendimiento
- Sistema de monitoreo con Prometheus y Grafana
- Procesamiento asíncrono con Celery
- Almacenamiento en Firebase

## Requisitos

- Python 3.12+
- Docker y Docker Compose
- Cuenta de Firebase con credenciales
- Redis

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/yourusername/padelyzer-backend.git
cd padelyzer-backend
```

2. Crear un entorno virtual e instalar dependencias:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. Configurar Firebase:
- Crear un proyecto en Firebase
- Descargar las credenciales y guardarlas como `firebase-credentials.json`

## Uso

### Desarrollo

1. Iniciar los servicios con Docker Compose:
```bash
docker-compose up -d
```

2. La API estará disponible en `http://localhost:8000`
3. Grafana estará disponible en `http://localhost:3000`
4. Prometheus estará disponible en `http://localhost:9090`

### Producción

1. Construir las imágenes:
```bash
docker-compose build
```

2. Iniciar los servicios:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Estructura del Proyecto

```
padelyzer-backend/
├── api/                    # Endpoints de la API
├── services/              # Servicios de negocio
├── models/                # Modelos de datos
├── tasks/                 # Tareas de Celery
├── tests/                 # Tests
├── prometheus/           # Configuración de Prometheus
├── grafana/              # Configuración de Grafana
├── docker-compose.yml    # Configuración de Docker Compose
├── Dockerfile            # Configuración de Docker
├── requirements.txt      # Dependencias de Python
└── README.md            # Este archivo
```

## Testing

Ejecutar los tests:
```bash
pytest
```

Ejecutar los tests con cobertura:
```bash
pytest --cov=.
```

## Monitoreo

- Grafana: `http://localhost:3000` (admin/admin)
- Prometheus: `http://localhost:9090`

## Contribuir

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tutwitter](https://twitter.com/tutwitter) - email@example.com

Link del Proyecto: [https://github.com/yourusername/padelyzer-backend](https://github.com/yourusername/padelyzer-backend) 