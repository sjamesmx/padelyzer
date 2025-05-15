.PHONY: help build up down restart logs test lint clean

help: ## Muestra la ayuda
	@echo "Comandos disponibles:"
	@echo ""
	@echo "  make build    - Construye las imágenes de Docker"
	@echo "  make up       - Inicia los servicios"
	@echo "  make down     - Detiene los servicios"
	@echo "  make restart  - Reinicia los servicios"
	@echo "  make logs     - Muestra los logs de los servicios"
	@echo "  make test     - Ejecuta los tests"
	@echo "  make lint     - Ejecuta el linter"
	@echo "  make clean    - Limpia archivos temporales"
	@echo ""

build: ## Construye las imágenes de Docker
	docker-compose build

up: ## Inicia los servicios
	docker-compose up -d

down: ## Detiene los servicios
	docker-compose down

restart: down up ## Reinicia los servicios

logs: ## Muestra los logs de los servicios
	docker-compose logs -f

test: ## Ejecuta los tests
	pytest

lint: ## Ejecuta el linter
	flake8 .
	black . --check
	isort . --check-only

clean: ## Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name "*.log" -delete
	find . -type f -name "*.pid" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "*.sqlite3" -delete
	find . -type f -name "*.bak" -delete
	find . -type f -name "*.tmp" -delete
	find . -type f -name "*.swp" -delete
	find . -type f -name "*.swo" -delete
	find . -type f -name "*~" -delete 