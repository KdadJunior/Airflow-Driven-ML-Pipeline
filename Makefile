SHELL := /bin/bash

COMPOSE := docker compose -f docker/docker-compose.yaml --env-file .env

.PHONY: up down logs fmt lint test dag-check build backfill seed airflow

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs -f

fmt:
	pre-commit run --all-files

lint:
	ruff check .
	mypy src

test:
	pytest

dag-check:
	PYTHONPATH=$(PWD) python tests/test_dag_import.py

build:
	$(COMPOSE) build

backfill:
	@if [ -z "$$START" ] || [ -z "$$END" ]; then \
		echo "Usage: make backfill START=YYYY-MM-DD END=YYYY-MM-DD"; \
		exit 1; \
	fi
	$(COMPOSE) run --rm airflow-cli airflow dags backfill mlops_imdb --start-date "$$START" --end-date "$$END"

seed:
	PYTHONPATH=$(PWD) python scripts/seed_data.py

airflow:
	@echo "Airflow UI: http://localhost:8080 (user: airflow / password: airflow)"


