from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db.models import Base
from app.db.session import engine


def ensure_tables(target_engine: Engine = engine) -> str:
    Base.metadata.create_all(target_engine)

    if target_engine.dialect.name == "postgresql":
        with target_engine.begin() as connection:
            connection.execute(text("ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS git_sha VARCHAR"))
            connection.execute(text("ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS config_version VARCHAR"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS batch_size INTEGER"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS total_batches INTEGER"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS retry_count INTEGER"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS backoff_count INTEGER"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS concurrency_level INTEGER"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS items_skipped INTEGER"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS cache_hit_count INTEGER"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS network_call_count INTEGER"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS model_name VARCHAR"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ADD COLUMN IF NOT EXISTS prompt_version VARCHAR"))
            connection.execute(text("UPDATE pipeline_stage_metrics SET retry_count = COALESCE(retry_count, 0)"))
            connection.execute(text("UPDATE pipeline_stage_metrics SET backoff_count = COALESCE(backoff_count, 0)"))
            connection.execute(text("UPDATE pipeline_stage_metrics SET items_skipped = COALESCE(items_skipped, 0)"))
            connection.execute(text("UPDATE pipeline_stage_metrics SET cache_hit_count = COALESCE(cache_hit_count, 0)"))
            connection.execute(text("UPDATE pipeline_stage_metrics SET network_call_count = COALESCE(network_call_count, 0)"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN retry_count SET DEFAULT 0"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN backoff_count SET DEFAULT 0"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN items_skipped SET DEFAULT 0"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN cache_hit_count SET DEFAULT 0"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN network_call_count SET DEFAULT 0"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN retry_count SET NOT NULL"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN backoff_count SET NOT NULL"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN items_skipped SET NOT NULL"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN cache_hit_count SET NOT NULL"))
            connection.execute(text("ALTER TABLE pipeline_stage_metrics ALTER COLUMN network_call_count SET NOT NULL"))
            connection.execute(text("ALTER TABLE digests ADD COLUMN IF NOT EXISTS digest_version INTEGER"))
            connection.execute(text("ALTER TABLE digests ADD COLUMN IF NOT EXISTS digest_generated_at TIMESTAMPTZ"))
            connection.execute(text("ALTER TABLE digests ADD COLUMN IF NOT EXISTS source_updated_at TIMESTAMPTZ"))
            connection.execute(text("ALTER TABLE digests ADD COLUMN IF NOT EXISTS content_last_seen_at TIMESTAMPTZ"))
            connection.execute(text("ALTER TABLE digests ADD COLUMN IF NOT EXISTS model_name VARCHAR"))
            connection.execute(text("ALTER TABLE digests ADD COLUMN IF NOT EXISTS prompt_version VARCHAR"))
            connection.execute(text("UPDATE digests SET digest_version = COALESCE(digest_version, 1)"))
            connection.execute(text("UPDATE digests SET digest_generated_at = COALESCE(digest_generated_at, uploaded_at)"))
            connection.execute(text("UPDATE digests SET content_last_seen_at = COALESCE(content_last_seen_at, uploaded_at)"))
            connection.execute(text("ALTER TABLE digests ALTER COLUMN digest_version SET DEFAULT 1"))
            connection.execute(text("ALTER TABLE digests ALTER COLUMN digest_version SET NOT NULL"))
            connection.execute(text("ALTER TABLE digests ALTER COLUMN digest_generated_at SET NOT NULL"))

    return ", ".join(sorted(Base.metadata.tables.keys()))
