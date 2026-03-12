from __future__ import annotations

from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session

from app.db import repository
from app.db.models import Digest
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker
from app.services.retry_utils import run_with_retries
from agent import youtube_agent

logger = logging.getLogger(__name__)

def process_digest(db: Session, tracker: PipelineTracker | None = None) -> None:
    _process_videos(db, tracker=tracker)


def _process_videos(db: Session, tracker: PipelineTracker | None = None) -> None:
    logger.info("=== Digesting YouTube Videos ===")
    videos = repository.get_videos(db, limit=500)
    processed = 0
    now = datetime.now(timezone.utc)
    pending_videos = [video for video in videos if not repository.digest_exists(video.video_id, "youtube", db)]

    with StageMonitor(tracker, "digest_videos") as stage:
        stage.set_model_info(
            model_name=youtube_agent.MODEL_NAME,
            prompt_version=youtube_agent.PROMPT_VERSION,
        )
        stage.set_batch_info(batch_size=1, total_batches=len(pending_videos))
        stage.set_concurrency(1)
        for video in videos:
            if repository.digest_exists(video.video_id, "youtube", db):
                repository.touch_digest(
                    video.video_id,
                    "youtube",
                    db,
                    seen_at=now,
                    source_updated_at=video.published_at,
                )
                continue

            logger.info("  Processing: [%s] %s", video.channel_name, video.title)
            stage.attempt()
            try:
                result = run_with_retries(
                    lambda: youtube_agent.run(video),
                    max_attempts=3,
                    backoff_seconds=1.0,
                    on_retry=lambda _attempt, _backoff: _record_retry(stage),
                )
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
                uploaded_at=now,
                digest_version=1,
                digest_generated_at=now,
                source_updated_at=video.published_at,
                content_last_seen_at=now,
                model_name=youtube_agent.MODEL_NAME,
                prompt_version=youtube_agent.PROMPT_VERSION,
            )
            repository.save_digest(digest, db)
            stage.succeed()
            processed += 1

    logger.info("  %s new video digests saved", processed)


def _record_retry(stage: StageMonitor) -> None:
    stage.add_retry()
    stage.add_backoff()
