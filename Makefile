.PHONY: up down db-init run test \
	monitoring-report monitoring-runs monitoring-health \
	monitoring-stage-performance monitoring-failures \
	monitoring-throughput monitoring-summary monitoring-compare

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

monitoring-report:
	uv run scripts/monitoring_report.py recent-runs --limit 10

monitoring-runs:
	uv run scripts/monitoring_report.py recent-runs --limit 10

monitoring-health:
	uv run scripts/monitoring_report.py health --days 30 --limit 10

monitoring-stage-performance:
	uv run scripts/monitoring_report.py stage-performance --days 30

monitoring-failures:
	uv run scripts/monitoring_report.py failures --days 30 --limit 20

monitoring-throughput:
	uv run scripts/monitoring_report.py throughput --days 30

monitoring-summary:
	uv run scripts/monitoring_report.py summary --days 7

monitoring-compare:
	uv run scripts/monitoring_report.py compare \
		--before-start "$(BEFORE_START)" \
		--before-end "$(BEFORE_END)" \
		--after-start "$(AFTER_START)" \
		--after-end "$(AFTER_END)"
