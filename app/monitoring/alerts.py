from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.monitoring.models import PipelineError, PipelineRun

logger = logging.getLogger(__name__)


class AlertHandler(Protocol):
    def on_run_complete(self, run: PipelineRun) -> None: ...

    def on_error(self, error: PipelineError, run: PipelineRun) -> None: ...


class NoopAlertHandler:
    """Default alert handler that only logs events."""

    def on_run_complete(self, run: PipelineRun) -> None:
        logger.info(
            "Run complete id=%s status=%s trigger=%s notes=%s",
            run.id,
            run.status.value,
            run.trigger,
            run.notes or "",
        )

    def on_error(self, error: PipelineError, run: PipelineRun) -> None:
        logger.error(
            "Run error id=%s run_id=%s stage=%s type=%s message=%s item_id=%s",
            error.id,
            run.id,
            error.stage,
            error.error_type,
            error.error_message,
            error.item_id or "",
        )
