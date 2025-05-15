# Pruebas de Padelyzer

Este documento describe cómo ejecutar y mantener las pruebas automatizadas de Padelyzer.

## Configuración del Entorno

1. Instalar dependencias de prueba:
```bash
pip install pytest pytest-asyncio pytest-cov fastapi[all] firebase-admin opencv-python-headless numpy
```

2. Configurar variables de entorno:
```bash
# Para desarrollo local
export FIRESTORE_EMULATOR_HOST="localhost:8080"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

## Estructura de Pruebas

```
backend/
├── tests/
│   ├── __init__.py
│   ├── init_test_data.py     # Datos de prueba y utilidades
│   ├── test_complete_flow.py # Pruebas del flujo completo
│   └── test_concurrency.py   # Pruebas de concurrencia
└── docs/
    └── testing.md            # Esta documentación
```

## Ejecución de Pruebas

1. Ejecutar todas las pruebas:
```bash
pytest tests/ -v
```

2. Ejecutar pruebas específicas:
```bash
pytest tests/test_complete_flow.py -v
pytest tests/test_concurrency.py -v
```

3. Ejecutar pruebas con cobertura:
```bash
pytest --cov=app tests/ -v
```

## Casos de Prueba

### Autenticación y Usuarios
- `test_signup_and_login`: Prueba el flujo de registro y login
  - Registro exitoso
  - Registro fallido (email duplicado)
  - Login exitoso
  - Login fallido

### Suscripciones
- `test_subscriptions`: Prueba el flujo de suscripciones
  - Crear suscripción
  - Listar suscripciones
  - Cancelar suscripción

### Búsqueda de Jugadores
- `test_search_players`: Prueba la búsqueda de jugadores
  - Búsqueda por ubicación
  - Filtrado por Padel IQ
  - Ordenamiento por distancia

### Onboarding
- `test_onboarding`: Prueba el flujo de onboarding
  - Configuración de ubicación
  - Preferencias de juego
  - Disponibilidad

### Flujo de Entrenamiento
- `test_upload_and_analyze_training_video`: Prueba el flujo completo de subida y análisis de video de entrenamiento
  - Subida de video
  - Cálculo de Padel IQ
  - Verificación de perfil
  - Validación de métricas

### Flujo de Partido
- `test_upload_and_analyze_match_video`: Prueba el flujo completo de subida y análisis de video de partido
  - Subida de video
  - Cálculo de Padel IQ con métricas de pareja
  - Verificación de perfil

### Pruebas de Concurrencia
- `test_concurrent_uploads`: Prueba subidas concurrentes de videos
- `test_concurrent_padel_iq_calculations`: Prueba cálculos concurrentes de Padel IQ
- `test_concurrent_profile_updates`: Prueba actualizaciones concurrentes de perfiles
- `test_concurrent_search_requests`: Prueba búsquedas concurrentes de jugadores

## Integración Continua (CI)

### Configuración de GitHub Actions
El proyecto utiliza GitHub Actions para CI. El flujo de trabajo se ejecuta en:
- Push a la rama main
- Pull requests a la rama main

### Pasos del CI
1. Configuración del entorno
   - Instalación de Python 3.9
   - Instalación de dependencias
   - Configuración del emulador de Firestore

2. Ejecución de pruebas
   - Ejecución de todas las pruebas
   - Generación de reporte de cobertura
   - Subida de cobertura a Codecov

3. Verificación de resultados
   - Validación de resultados de pruebas
   - Verificación de cobertura mínima

### Configuración de Secretos
Los siguientes secretos deben configurarse en GitHub:
- `GOOGLE_APPLICATION_CREDENTIALS`: Credenciales de Firebase
- `CODECOV_TOKEN`: Token de Codecov (opcional)

## Mantenimiento

### Agregar Nuevas Pruebas
1. Crear función de prueba en el archivo correspondiente
2. Agregar datos de prueba necesarios en `init_test_data.py`
3. Documentar el caso de prueba en esta documentación

### Actualizar Datos de Prueba
1. Modificar funciones en `init_test_data.py`
2. Asegurar que los datos cumplan con el esquema de Firestore
3. Actualizar pruebas afectadas

### Solución de Problemas
1. Verificar logs de prueba:
```bash
pytest tests/ -v --log-cli-level=DEBUG
```

2. Verificar datos en Firestore:
```bash
firebase emulators:start
```

3. Limpiar datos de prueba:
```python
from tests.init_test_data import clear_test_data
clear_test_data()
```

4. Verificar resultados de CI:
   - Revisar la pestaña "Actions" en GitHub
   - Verificar reportes de cobertura en Codecov
   - Revisar logs de errores en caso de fallo

# Testing Guide

## Prerequisites

1. Python 3.8+ installed
2. Virtual environment activated
3. Dependencies installed: `pip install -r requirements.txt`
4. Firebase emulator installed: `npm install -g firebase-tools`

## Environment Setup

1. Set up environment variables:
```bash
export FIRESTORE_EMULATOR_HOST="localhost:8080"
export ENVIRONMENT="development"
```

2. Start the Firebase emulator:
```bash
firebase emulators:start --only firestore
```

## Running Tests

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_auth.py
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## API Endpoints

All endpoints are prefixed with `/api/v1`:

### Authentication
- POST `/api/v1/auth/signup` - Register new user
- POST `/api/v1/auth/login` - User login

### Users
- GET `/api/v1/users/me` - Get current user info
- PUT `/api/v1/users/me` - Update current user info

### Video Analysis
- POST `/api/v1/video/upload` - Upload video for analysis

## Test Data

The test suite uses the Firebase emulator and doesn't require real credentials. All tests are designed to work with the emulator by default.

## Common Issues

1. **404 Errors**: Ensure you're using the correct route prefixes (`/api/v1/...`)
2. **Firebase Errors**: Make sure the emulator is running and `FIRESTORE_EMULATOR_HOST` is set
3. **Validation Errors**: Check that test payloads match the expected schema

## Best Practices

1. Always run tests with the emulator in development
2. Use the correct route prefixes in all tests
3. Mock external dependencies when appropriate
4. Test both success and error cases
5. Keep test data isolated and clean 