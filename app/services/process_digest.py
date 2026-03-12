from __future__ import annotations

from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session

from app.db import repository
from app.db.models import Digest
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker
from agent import youtube_agent

logger = logging.getLogger(__name__)

def process_digest(db: Session, tracker: PipelineTracker | None = None) -> None:
    _process_videos(db, tracker=tracker)


def _process_videos(db: Session, tracker: PipelineTracker | None = None) -> None:
    logger.info("=== Digesting YouTube Videos ===")
    videos = repository.get_videos(db, limit=500)
    processed = 0

    with StageMonitor(tracker, "digest_videos") as stage:
        for video in videos:
            if repository.digest_exists(video.video_id, "youtube", db):
                continue

            logger.info("  Processing: [%s] %s", video.channel_name, video.title)
            stage.attempt()
            try:
                result = youtube_agent.run(video)
            except Exception as exc:
                stage.fail(exc, item_id=video.video_id)
                logger.exception("Digest generation failed for video_id=%s", video.video_id)
                continue

            digest = Digest(
                article_id=video.video_id,
                article_type="youtube",
                url=video.url,
                title=result.title,
                summary=result.summary,
                tools_concepts=result.tools_concepts,
                source=video.channel_name,
                uploaded_at=datetime.now(timezone.utc),
            )
            repository.save_digest(digest, db)
            stage.succeed()
            processed += 1

    logger.info("  %s new video digests saved", processed)
