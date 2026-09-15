.PHONY: install test lint up down

install:
	pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check etl tests

up:
	docker compose up -d
	@echo "Airflow UI: http://localhost:8080 (password in the airflow container logs)"
	@echo "MinIO console: http://localhost:9001 (minioadmin / minioadmin)"

down:
	docker compose down -v
