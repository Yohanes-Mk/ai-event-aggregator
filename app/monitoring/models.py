from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text

from app.db.models import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(str, Enum):
    running = "running"
    success = "success"
    partial = "partial"
    failed = "failed"


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        SAEnum(RunStatus, name="pipeline_status", native_enum=True),
        nullable=False,
        default=RunStatus.running,
    )
    trigger = Column(String, nullable=False, default="manual")
    git_sha = Column(String, nullable=True)
    config_version = Column(String, nullable=True)
    notes = Column(Text, nullable=True)


class PipelineStageMetric(Base):
    __tablename__ = "pipeline_stage_metrics"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    items_attempted = Column(Integer, nullable=False, default=0)
    items_succeeded = Column(Integer, nullable=False, default=0)
    items_failed = Column(Integer, nullable=False, default=0)
    items_skipped = Column(Integer, nullable=False, default=0)
    cache_hit_count = Column(Integer, nullable=False, default=0)
    network_call_count = Column(Integer, nullable=False, default=0)
    batch_size = Column(Integer, nullable=True)
    total_batches = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    backoff_count = Column(Integer, nullable=False, default=0)
    concurrency_level = Column(Integer, nullable=True)
    model_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    status = Column(
        SAEnum(RunStatus, name="pipeline_status", native_enum=True),
        nullable=False,
        default=RunStatus.running,
    )


class PipelineError(Base):
    __tablename__ = "pipeline_errors"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String, nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    item_id = Column(String, nullable=True)
    error_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
