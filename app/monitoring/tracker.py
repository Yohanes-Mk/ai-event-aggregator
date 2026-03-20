from __future__ import annotations

import logging
import os
import subprocess
import traceback as traceback_lib
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.monitoring.alerts import AlertHandler, NoopAlertHandler
from app.monitoring.models import PipelineError, PipelineRun, PipelineStageMetric, RunStatus

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineTracker:
    def __init__(
        self,
        db: Session,
        trigger: str = "manual",
        alert_handler: AlertHandler | None = None,
    ) -> None:
        self.db = db
        self.trigger = trigger
        self.alert_handler = alert_handler or NoopAlertHandler()
        self.run: PipelineRun | None = None

    def start(self) -> "PipelineTracker":
        if self.run is not None:
            return self

        run = PipelineRun(
            started_at=utc_now(),
            status=RunStatus.running,
            trigger=self.trigger,
            git_sha=self._resolve_git_sha(),
            config_version=self._resolve_config_version(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        self.run = run
        logger.info(
            "Started pipeline run id=%s trigger=%s git_sha=%s config_version=%s",
            run.id,
            run.trigger,
            run.git_sha or "-",
            run.config_version or "-",
        )
        return self

    def record_error(self, stage: str, exc: Exception, item_id: str | None = None) -> PipelineError:
        run = self._require_run()

        tb = "".join(traceback_lib.format_exception(type(exc), exc, exc.__traceback__))
        error = PipelineError(
            run_id=run.id,
            stage=stage,
            occurred_at=utc_now(),
            item_id=item_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            traceback=tb,
        )
        self.db.add(error)
        self.db.commit()
        self.db.refresh(error)

        self._safe_alert_error(error, run)
        return error

    def record_stage_metric(
        self,
        stage: str,
        started_at: datetime,
        ended_at: datetime,
        items_attempted: int,
        items_succeeded: int,
        items_failed: int,
        items_skipped: int,
        cache_hit_count: int,
        network_call_count: int,
        batch_size: int | None,
        total_batches: int | None,
        retry_count: int,
        backoff_count: int,
        concurrency_level: int | None,
        model_name: str | None,
        prompt_version: str | None,
        status: RunStatus,
    ) -> PipelineStageMetric:
        run = self._require_run()
        metric = PipelineStageMetric(
            run_id=run.id,
            stage=stage,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=max((ended_at - started_at).total_seconds(), 0.0),
            items_attempted=items_attempted,
            items_succeeded=items_succeeded,
            items_failed=items_failed,
            items_skipped=items_skipped,
            cache_hit_count=cache_hit_count,
            network_call_count=network_call_count,
            batch_size=batch_size,
            total_batches=total_batches,
            retry_count=retry_count,
            backoff_count=backoff_count,
            concurrency_level=concurrency_level,
            model_name=model_name,
            prompt_version=prompt_version,
            status=status,
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def finish(self) -> None:
        run = self._require_run()
        if run.ended_at is not None:
            return

        total_failed = (
            self.db.query(func.coalesce(func.sum(PipelineStageMetric.items_failed), 0))
            .filter(PipelineStageMetric.run_id == run.id)
            .scalar()
            or 0
        )
        run.status = RunStatus.partial if total_failed > 0 else RunStatus.success
        run.ended_at = utc_now()
        self.db.commit()

        self._safe_alert_complete(run)

    def abort(self, exc: Exception) -> None:
        run = self._require_run()

        try:
            self.db.rollback()
        except Exception:
            logger.exception("Failed to roll back session before abort handling")

        if run.ended_at is not None:
            return

        try:
            self.record_error("pipeline", exc)
        except Exception:
            logger.exception("Failed to record top-level pipeline error")

        run.status = RunStatus.failed
        run.ended_at = utc_now()
        run.notes = str(exc)
        try:
            self.db.commit()
        except Exception:
            logger.exception("Failed to persist aborted pipeline run state run_id=%s", run.id)
            self.db.rollback()

        self._safe_alert_complete(run)

    def _require_run(self) -> PipelineRun:
        if self.run is None:
            raise RuntimeError("PipelineTracker.start() must be called before use")
        return self.run

    def _resolve_git_sha(self) -> str | None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception:
            logger.debug("Unable to resolve git SHA for pipeline run", exc_info=True)
            return None

        git_sha = result.stdout.strip()
        return git_sha or None

    def _resolve_config_version(self) -> str | None:
        value = os.getenv("PIPELINE_CONFIG_VERSION", "").strip()
        return value or None

    def _safe_alert_complete(self, run: PipelineRun) -> None:
        try:
            self.alert_handler.on_run_complete(run)
        except Exception:
            logger.exception("Alert handler failed on run completion run_id=%s", run.id)

    def _safe_alert_error(self, error: PipelineError, run: PipelineRun) -> None:
        try:
            self.alert_handler.on_error(error, run)
        except Exception:
            logger.exception("Alert handler failed on error run_id=%s error_id=%s", run.id, error.id)
