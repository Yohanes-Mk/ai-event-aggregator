from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db import repository
from app.db.models import CuratorRun
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker
from app.services.retry_utils import run_with_retries
from agent import curator_agent

logger = logging.getLogger(__name__)

def process_curator(
    db: Session,
    tracker: PipelineTracker | None = None,
) -> CuratorRun | None:
    logger.info("=== Curator: Top 10 for Yohannes ===")

    with StageMonitor(tracker, "curator") as stage:
        digests = repository.get_recent_digests(db, hours=168)
        if not digests:
            logger.info("  No digests in the last 7 days.")
            return None

        logger.info("  Ranking %s item(s)...", len(digests))
        stage.attempt()
        stage.set_model_info(
            model_name=curator_agent.MODEL_NAME,
            prompt_version=curator_agent.PROMPT_VERSION,
        )
        stage.set_batch_info(batch_size=len(digests), total_batches=1)
        stage.set_concurrency(1)

        try:
            result = run_with_retries(
                lambda: curator_agent.run(digests),
                max_attempts=3,
                backoff_seconds=1.0,
                on_retry=lambda _attempt, _backoff: _record_retry(stage),
            )
            curator_run = repository.save_curator_run(
                db,
                ranked_articles=result.ranked_articles,
                digests=digests,
                pipeline_run_id=tracker.run.id if tracker and tracker.run is not None else None,
                model_name=curator_agent.MODEL_NAME,
                prompt_version=curator_agent.PROMPT_VERSION,
            )
        except Exception as exc:
            stage.fail(exc)
            logger.exception("Curator ranking failed")
            return None
        stage.succeed()

        logger.info("  Saved curator run id=%s", curator_run.id)

        seen = set()
        rank = 1
        for article in result.ranked_articles:
            if article.article_id in seen:
                continue
            seen.add(article.article_id)
            logger.info("  %s. [score: %s] %s", rank, article.score, article.title)
            logger.info("     %s", article.ranking_reason)
            rank += 1
        return curator_run


def _record_retry(stage: StageMonitor) -> None:
    stage.add_retry()
    stage.add_backoff()
