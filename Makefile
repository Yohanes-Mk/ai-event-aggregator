.PHONY: help up down db-init run dashboard demo test \
	monitoring-report monitoring-runs monitoring-health \
	monitoring-stage-performance monitoring-failures \
	monitoring-throughput monitoring-batch-telemetry monitoring-summary \
	monitoring-ranking-drift monitoring-digest-freshness \
	monitoring-compare

help:
	@printf "Targets:\n"
	@printf "  up                        Start Postgres\n"
	@printf "  down                      Stop Postgres\n"
	@printf "  db-init                   Create/update tables\n"
	@printf "  run                       Run the full pipeline\n"
	@printf "  dashboard                 Render dashboard from current DB data\n"
	@printf "  demo                      Launch the Streamlit demo app\n"
	@printf "  test                      Run tests\n"
	@printf "  monitoring-report         Recent runs\n"
	@printf "  monitoring-health         Health summary\n"
	@printf "  monitoring-stage-performance Stage performance + percentiles + batch telemetry\n"
	@printf "  monitoring-failures       Failure analysis + retry summary\n"
	@printf "  monitoring-throughput     Throughput trends\n"
	@printf "  monitoring-batch-telemetry Batch/retry/concurrency telemetry\n"
	@printf "  monitoring-summary        Rule-based focus summary\n"
	@printf "  monitoring-ranking-drift  Ranking drift analytics\n"
	@printf "  monitoring-digest-freshness Digest freshness analytics\n"
	@printf "  monitoring-compare BEFORE_START=... BEFORE_END=... AFTER_START=... AFTER_END=...\n"

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

db-init:
	uv run scripts/create_tables.py

run: db-init
	uv run main.py

dashboard: db-init
	uv run python -c "from app.db.session import SessionLocal; from app.services.process_dashboard import process_dashboard; db = SessionLocal(); process_dashboard(db); db.close()"

demo: db-init
	uv run streamlit run scripts/demo_app.py

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

monitoring-batch-telemetry:
	uv run scripts/monitoring_report.py batch-telemetry --days 30

monitoring-summary:
	uv run scripts/monitoring_report.py summary --days 7

monitoring-ranking-drift:
	uv run scripts/monitoring_report.py ranking-drift --days 30 --min-score-delta 10 --limit 20

monitoring-digest-freshness:
	uv run scripts/monitoring_report.py digest-freshness --days 30 --stale-after-days 7 --limit 20

monitoring-compare:
	uv run scripts/monitoring_report.py compare \
		--before-start "$(BEFORE_START)" \
		--before-end "$(BEFORE_END)" \
		--after-start "$(AFTER_START)" \
		--after-end "$(AFTER_END)"
