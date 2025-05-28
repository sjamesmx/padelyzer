---
description: 
globs: 
alwaysApply: false
---
# Flujo de Trabajo de Desarrollo

## Estructura del Proyecto
- `/app`: Código principal de la aplicación
- `/services`: Microservicios
- `/tests`: Pruebas unitarias y de integración
- `/config`: Archivos de configuración
- `/docs`: Documentación

## Convenciones de Código
- Usar TypeScript para el frontend
- Usar Python para el backend
- Seguir las convenciones de PEP 8 para Python
- Documentar todas las funciones y clases

## Proceso de Desarrollo
1. Crear una rama feature desde main
2. Desarrollar la funcionalidad
3. Escribir pruebas unitarias
4. Ejecutar pruebas locales
5. Crear pull request
6. Revisión de código
7. Merge a main

## Microservicios
- Mantener cada microservicio independiente
- Documentar APIs con OpenAPI/Swagger
- Implementar pruebas de integración
- Mantener versionado de APIs

## Testing
- Cobertura mínima de 80%
- Pruebas unitarias para cada componente
- Pruebas de integración para APIs
- Pruebas end-to-end para flujos críticos

## Despliegue
- Usar Docker para contenedores
- Implementar CI/CD con GitHub Actions
- Mantener ambientes separados (dev, staging, prod)
- Monitoreo y logging en producción
