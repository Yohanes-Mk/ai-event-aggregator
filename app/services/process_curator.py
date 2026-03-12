from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db import repository
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker
from agent import curator_agent

logger = logging.getLogger(__name__)

def process_curator(db: Session, tracker: PipelineTracker | None = None) -> None:
    logger.info("=== Curator: Top 10 for Yohannes ===")

    with StageMonitor(tracker, "curator") as stage:
        digests = repository.get_recent_digests(db, hours=24)
        if not digests:
            logger.info("  No digests in the last 24 hours.")
            return

        logger.info("  Ranking %s item(s)...", len(digests))
        stage.attempt()

        try:
            result = curator_agent.run(digests)
        except Exception as exc:
            stage.fail(exc)
            logger.exception("Curator ranking failed")
            return
        stage.succeed()

        seen = set()
        rank = 1
        for article in result.ranked_articles:
            if article.article_id in seen:
                continue
            seen.add(article.article_id)
            logger.info("  %s. [score: %s] %s", rank, article.score, article.title)
            logger.info("     %s", article.ranking_reason)
            rank += 1
