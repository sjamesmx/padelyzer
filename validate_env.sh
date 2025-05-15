#!/bin/bash

# 1. Verifica que el entorno virtual existe
echo "Verificando entorno virtual..."
if [ ! -f "venv/bin/activate" ]; then
  echo "[ERROR] El entorno virtual no existe en ./venv."
  exit 1
fi

echo "[OK] Entorno virtual encontrado."

# 2. Activa el entorno virtual
source venv/bin/activate
echo "[OK] Entorno virtual activado."

# 3. Muestra el intérprete de Python activo
echo -n "Python activo: "
which python

# 4. Muestra los paquetes instalados relevantes
echo "\nPaquetes relevantes instalados:"
pip show fastapi PyJWT google-cloud-firestore 2>/dev/null || echo "Algunos paquetes no están instalados."

# 5. Prueba importar los módulos desde Python
echo "\nProbando importaciones en Python..."
python -c "import fastapi; import jwt; from google.cloud import firestore; print('Importaciones exitosas')" || echo "[ERROR] Fallo al importar módulos."

echo "\nValidación finalizada." 