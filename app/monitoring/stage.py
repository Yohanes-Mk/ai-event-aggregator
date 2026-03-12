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

    def _compute_status(self, exc: Exception | None) -> RunStatus:
        if exc is not None:
            return RunStatus.failed
        if self.items_failed > 0:
            return RunStatus.partial
        return RunStatus.success
