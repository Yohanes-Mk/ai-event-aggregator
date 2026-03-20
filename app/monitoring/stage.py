from __future__ import annotations

from datetime import datetime, timezone

from app.monitoring.models import RunStatus
from app.monitoring.tracker import PipelineTracker


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StageMonitor:
    def __init__(self, tracker: PipelineTracker | None, stage: str) -> None:
        self.tracker = tracker
        self.stage = stage
        self.items_attempted = 0
        self.items_succeeded = 0
        self.items_failed = 0
        self.items_skipped = 0
        self.cache_hit_count = 0
        self.network_call_count = 0
        self.batch_size: int | None = None
        self.total_batches: int | None = None
        self.retry_count = 0
        self.backoff_count = 0
        self.concurrency_level: int | None = None
        self.model_name: str | None = None
        self.prompt_version: str | None = None
        self.started_at = utc_now()
        self.ended_at: datetime | None = None

    def __enter__(self) -> "StageMonitor":
        self.started_at = utc_now()
        return self

    def __exit__(self, exc_type, exc, _tb) -> bool:
        self.ended_at = utc_now()

        if exc is not None and self.items_failed == 0:
            self.fail(exc)

        if self.tracker is not None:
            status = self._compute_status(exc)
            self.tracker.record_stage_metric(
                stage=self.stage,
                started_at=self.started_at,
                ended_at=self.ended_at,
                items_attempted=self.items_attempted,
                items_succeeded=self.items_succeeded,
                items_failed=self.items_failed,
                items_skipped=self.items_skipped,
                cache_hit_count=self.cache_hit_count,
                network_call_count=self.network_call_count,
                batch_size=self.batch_size,
                total_batches=self.total_batches,
                retry_count=self.retry_count,
                backoff_count=self.backoff_count,
                concurrency_level=self.concurrency_level,
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                status=status,
            )

        return False

    def attempt(self) -> None:
        self.items_attempted += 1

    def succeed(self) -> None:
        self.items_succeeded += 1

    def fail(self, exc: Exception, item_id: str | None = None) -> None:
        self.items_failed += 1
        if self.tracker is not None:
            self.tracker.record_error(stage=self.stage, exc=exc, item_id=item_id)

    def skip(self, count: int = 1) -> None:
        self.items_skipped += count

    def add_cache_hit(self, count: int = 1) -> None:
        self.cache_hit_count += count

    def add_network_call(self, count: int = 1) -> None:
        self.network_call_count += count

    def set_batch_info(self, *, batch_size: int | None = None, total_batches: int | None = None) -> None:
        self.batch_size = batch_size
        self.total_batches = total_batches

    def add_retry(self, count: int = 1) -> None:
        self.retry_count += count

    def add_backoff(self, count: int = 1) -> None:
        self.backoff_count += count

    def set_concurrency(self, level: int | None) -> None:
        self.concurrency_level = level

    def set_model_info(self, *, model_name: str | None = None, prompt_version: str | None = None) -> None:
        self.model_name = model_name
        self.prompt_version = prompt_version

    def _compute_status(self, exc: Exception | None) -> RunStatus:
        if exc is not None:
            return RunStatus.failed
        if self.items_failed > 0:
            return RunStatus.partial
        return RunStatus.success
