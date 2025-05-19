# Padelyzer Backend

Backend API para la aplicación Padelyzer, un sistema de análisis biomecánico para pádel que utiliza inteligencia artificial para mejorar el rendimiento de los jugadores.

## Características

- Análisis biomecánico de videos de pádel
- Cálculo de Padel IQ y métricas de rendimiento
- Sistema de matchmaking basado en niveles
- Autenticación con Firebase
- Almacenamiento de videos en Firebase Storage
- Base de datos en Firestore

## Requisitos

- Python 3.8+
- Firebase project
- Redis (para tareas asíncronas)
- OpenCV
- MediaPipe
- TensorFlow

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/yourusername/padelyzer-backend.git
cd padelyzer-backend
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales de Firebase
```

## Configuración

1. Crear un proyecto en Firebase Console
2. Obtener las credenciales de servicio
3. Configurar las variables de entorno en `.env`:
```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email
```

## Uso

1. Iniciar el servidor:
```bash
uvicorn main:app --reload
```

2. Acceder a la documentación API:
```
http://localhost:8000/docs
```

## Estructura del Proyecto

```
padelyzer-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/
│   ├── schemas/
│   └── services/
├── routes/
│   └── padel_iq/
├── tests/
├── .env.example
├── main.py
└── requirements.txt
```

## Endpoints Principales

- `POST /api/calculate_padel_iq`: Calcula métricas de Padel IQ
- `POST /analyze/training`: Analiza video de entrenamiento
- `POST /analyze/game`: Analiza video de juego
- `GET /status/{task_id}`: Consulta estado del análisis
- `GET /history/{user_id}`: Obtiene historial de análisis

## Testing

```bash
pytest
```

## Contribución

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tutwitter](https://twitter.com/tutwitter) - email@example.com

Link del Proyecto: [https://github.com/yourusername/padelyzer-backend](https://github.com/yourusername/padelyzer-backend) 