#!/bin/bash

# Detener contenedores existentes
docker-compose -f docker-compose.test.yml down

# Construir y ejecutar las pruebas
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Obtener el código de salida del contenedor de pruebas
TEST_EXIT_CODE=$(docker-compose -f docker-compose.test.yml ps -q test | xargs docker inspect -f '{{.State.ExitCode}}')

# Detener los contenedores
docker-compose -f docker-compose.test.yml down

# Salir con el código de salida de las pruebas
exit $TEST_EXIT_CODE 