.PHONY: up down db-init run test

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

db-init:
	uv run scripts/create_tables.py

run:
	uv run main.py

test:
	uv run pytest
