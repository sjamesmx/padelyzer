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

## Video Upload Endpoint

The video upload functionality has been unified into a single endpoint:

- **Endpoint**: `POST /api/v1/video/upload`
- **Description**: Uploads a video to Firebase Storage and initiates analysis
- **Authentication**: Requires Firebase JWT token
- **Implementation**: Uses `upload_video` from `app/services/video_service.py`

### Request Format

```http
POST /api/v1/video/upload
Content-Type: multipart/form-data
Authorization: Bearer <firebase_jwt_token>

file: <video_file>
video_type: training|game|torneo
description: <optional_description>
player_position: <optional_json_string>
```

### Response Format

```json
{
    "video_id": "unique-video-id",
    "url": "https://firebasestorage.googleapis.com/v0/b/pdzr-458820.appspot.com/o/videos/...",
    "status": "pending|processing|completed|failed",
    "created_at": "2024-05-19T10:00:00Z",
    "message": "Video uploaded successfully"
}
```

### Features

- Validates video file type and size
- Generates unique blueprint to prevent duplicates
- Stores video in Firebase Storage
- Creates analysis record in Firestore
- Returns signed URL for video access
- Handles duplicate uploads gracefully

### Notes

- Removed redundant `/api/v1/videos/upload` endpoint (19/05/2024)
- All video uploads now use the correct Firebase Storage URL format
- Video analysis is initiated automatically after upload
- Player position information is optional but recommended for better analysis 

## Stabilization Notes (19/05/2025)
- Fixed `ModuleNotFoundError` by creating `app/api/v1/dependencies/exceptions.py` with `PadelException` and `AppException`.
- Unified video upload endpoint handles errors with custom exceptions.
- Added test for invalid file type handling.
- All tests pass and server starts successfully.

## TensorFlow Warning Suppression (19/05/2025)
- Suppressed non-critical TensorFlow Lite warnings during server startup
- Set TensorFlow logging level to ERROR to filter out WARNING and INFO messages
- Configured via `TF_CPP_MIN_LOG_LEVEL=2` environment variable
- No impact on video analysis functionality
- Added test coverage in `tests/test_analysis_manager.py` 

## Deployment Notes (19/05/2025)
- Fixed `protobuf` conflict by pinning `protobuf>=5.26.1,<6.0dev` in `requirements-ml.txt`.
- Updated `email-validator` to `2.2.0` to avoid yanked version.
- Deployed to Cloud Run using Dockerfile with `libmagic1` and `ffmpeg`.
- CI/CD configured with `cloudbuild.yaml` for automated builds.

### Verification Steps

**Test Dependencies Locally:**
```bash
python -m venv test-venv
source test-venv/bin/activate
pip install -r requirements-base.txt -r requirements-ml.txt
# Expected: No conflicts.
```

**Build Image:**
```bash
docker build -t padelyzer .
docker run -p 8000:8000 padelyzer
# Expected: Container runs, accessible at http://localhost:8000/docs.
```

**Test Endpoint:**
```bash
curl -X POST http://localhost:8000/api/v1/video/upload \
-H "Authorization: Bearer <your_jwt_token>" \
-F "filename=test.mp4" \
-F "file=@/path/to/test.mp4"
# Expected: Valid response.
```

**Deploy:**
```bash
docker tag padelyzer us-central1-docker.pkg.dev/pdzr-458820/padelyzer-repo/padelyzer
docker push us-central1-docker.pkg.dev/pdzr-458820/padelyzer-repo/padelyzer
gcloud run deploy padelyzer \
  --image us-central1-docker.pkg.dev/pdzr-458820/padelyzer-repo/padelyzer \
  --region us-central1 \
  --allow-unauthenticated \
  --project pdzr-458820
```

**Commit:**
```bash
git add requirements-base.txt requirements-ml.txt Dockerfile cloudbuild.yaml README.md
git commit -m "Resolved protobuf conflict and updated deployment setup"
git push origin main
```

**Potential Issues:**
- Persistent Conflict: If protobuf conflict persists, try mediapipe==0.10.14 (older version) or grpcio-status==1.62.2.
- Build Fails: Check Cloud Build logs:
```bash
gcloud builds list --project pdzr-458820
```
- Runtime Errors: Test endpoints in the deployed service to catch protobuf-related issues.

**Output:**
- Stable Docker image without dependency conflicts.
- Successful deployment to Cloud Run.
- Updated documentation and CI/CD pipeline. 

## Notas de Despliegue (19/05/2025)
- Resuelto conflicto de `protobuf` actualizando `mediapipe` a `0.10.14`.
- Compilado y desplegado con éxito en Cloud Run vía Cloud Build.
- Probado el endpoint `/api/v1/video/upload` en producción.

### Pasos de Verificación

**Probar Dependencias Localmente:**
```bash
rm -rf test-venv
python -m venv test-venv
source test-venv/bin/activate
pip install --upgrade pip
pip install -r requirements-base.txt -r requirements-ml.txt
# Esperado: Sin conflictos.
```

**Compilar Localmente (si Docker está instalado):**
```bash
docker build -t padelyzer .
docker run -p 8000:8000 padelyzer
curl -X POST http://localhost:8000/api/v1/video/upload \
  -H "Authorization: Bearer <your_jwt_token>" \
  -F "filename=test.mp4" \
  -F "file=@/path/to/test.mp4"
```

**Cloud Build:**
```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/pdzr-458820/padelyzer-repo/padelyzer --project=pdzr-458820 .
```

**Desplegar:**
```bash
gcloud run deploy padelyzer \
  --image us-central1-docker.pkg.dev/pdzr-458820/padelyzer-repo/padelyzer \
  --region us-central1 \
  --allow-unauthenticated \
  --project pdzr-458820
```

**Probar Servicio:**
```bash
curl -X POST <service-url>/api/v1/video/upload \
  -H "Authorization: Bearer <your_jwt_token>" \
  -F "filename=test.mp4" \
  -F "file=@/path/to/test.mp4"
```

**Subir Cambios:**
```bash
git add requirements-ml.txt README.md
git commit -m "Corregido conflicto de protobuf con mediapipe 0.10.14 para Cloud Build"
git push origin main
```

**Problemas Potenciales:**
- Conflicto Persistente: Prueba mediapipe==0.10.11 o reduce grpcio-status==1.62.2 en requirements-base.txt.
- Fallo en Cloud Build: Revisa los logs:
```bash
gcloud builds log <build-id>
```
- Errores en Tiempo de Ejecución: Prueba los endpoints de Firebase para detectar problemas con protobuf.

**Salida Esperada:**
- Imagen de Docker estable compilada y desplegada.
- Servicio de Cloud Run ejecutando Padelyzer.
- Documentación actualizada. 