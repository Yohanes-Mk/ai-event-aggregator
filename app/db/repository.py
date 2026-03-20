from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.orm import Session
from app.db.models import (
    CuratorRanking,
    CuratorRun,
    Digest,
    Event,
    YouTubeVideo,
    YouTubeVideoClassification,
)
from app.scrapers.youtube.scraper import Video
from app.scrapers.events.scraper import Event as ScrapedEvent
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker
from app.services.retry_utils import run_with_retries

logger = logging.getLogger(__name__)


def save_videos(videos: list[Video], db: Session) -> None:
    """Upsert scraped videos — safe to call on every run."""
    for v in videos:
        row = YouTubeVideo(
            video_id=v.video_id,
            title=v.title,
            url=str(v.url),
            published_at=v.published_at,
            channel_name=v.channel_name,
            channel_id=v.channel_id,
            transcript=v.transcript,
        )
        db.merge(row)
    db.commit()


def save_events(
    events: list[ScrapedEvent],
    db: Session,
    tracker: PipelineTracker | None = None,
) -> None:
    """Upsert scraped events. Generates a summary for new events only."""
    from agent import event_agent

    with StageMonitor(tracker, "events_enrichment") as stage:
        pending_events = [
            event for event in events
            if not (existing := db.get(Event, (event.title, event.start_time))) or not existing.summary
        ]
        stage.set_model_info(
            model_name=event_agent.MODEL_NAME,
            prompt_version=event_agent.PROMPT_VERSION,
        )
        stage.set_batch_info(batch_size=1, total_batches=len(pending_events))
        stage.set_concurrency(1)
        for e in events:
            existing = db.get(Event, (e.title, e.start_time))
            summary = existing.summary if existing and existing.summary else None
            relevance_score = (
                existing.relevance_score
                if existing and existing.relevance_score is not None
                else None
            )

            if summary is None:
                stage.attempt()
                try:
                    temp = Event(
                        title=e.title,
                        start_time=e.start_time,
                        end_time=e.end_time,
                        location=e.location,
                        urls=e.urls,
                        sources=e.sources,
                    )
                    result = run_with_retries(
                        lambda: event_agent.run(temp),
                        max_attempts=3,
                        backoff_seconds=1.0,
                        on_retry=lambda _attempt, _backoff: _record_retry(stage),
                    )
                    summary = result.summary
                    relevance_score = result.relevance_score
                    stage.succeed()
                except Exception as ex:
                    item_id = f"{e.title}||{e.start_time.isoformat()}"
                    stage.fail(ex, item_id=item_id)
                    logger.exception("Event enrichment failed for %s", e.title)

            row = Event(
                title=e.title,
                start_time=e.start_time,
                end_time=e.end_time,
                location=e.location,
                urls=e.urls,
                sources=e.sources,
                summary=summary,
                relevance_score=relevance_score,
            )
            db.merge(row)
    db.commit()


def get_existing_video_ids(db: Session) -> set[str]:
    rows = db.query(YouTubeVideo.video_id).all()
    return {r.video_id for r in rows}


def get_video_classifications(db: Session, video_ids: list[str]) -> dict[str, bool]:
    if not video_ids:
        return {}
    rows = (
        db.query(YouTubeVideoClassification)
        .filter(YouTubeVideoClassification.video_id.in_(video_ids))
        .all()
    )
    return {row.video_id: row.is_short for row in rows}


def save_video_classifications(
    classifications: dict[str, bool],
    db: Session,
    *,
    checked_at: datetime | None = None,
) -> None:
    if not classifications:
        return

    checked_at = checked_at or datetime.now(timezone.utc)
    for video_id, is_short in classifications.items():
        db.merge(
            YouTubeVideoClassification(
                video_id=video_id,
                is_short=is_short,
                checked_at=checked_at,
            )
        )
    db.commit()


def get_videos(db: Session, limit: int = 50) -> list[YouTubeVideo]:
    return db.query(YouTubeVideo).order_by(YouTubeVideo.published_at.desc()).limit(limit).all()


def get_events(db: Session, limit: int = 50) -> list[Event]:
    return db.query(Event).order_by(Event.start_time).limit(limit).all()


def digest_exists(article_id: str, article_type: str, db: Session) -> bool:
    return db.get(Digest, (article_id, article_type)) is not None


def save_digest(digest: Digest, db: Session) -> None:
    existing = db.get(Digest, (digest.article_id, digest.article_type))
    if existing is not None:
        digest.digest_version = existing.digest_version
        if (
            digest.title != existing.title
            or digest.summary != existing.summary
            or digest.tools_concepts != existing.tools_concepts
        ):
            digest.digest_version = existing.digest_version + 1
        if digest.digest_generated_at is None:
            digest.digest_generated_at = existing.digest_generated_at
        if digest.content_last_seen_at is None:
            digest.content_last_seen_at = existing.content_last_seen_at
    else:
        if digest.digest_version is None:
            digest.digest_version = 1
    db.merge(digest)
    db.commit()


def touch_digest(
    article_id: str,
    article_type: str,
    db: Session,
    *,
    seen_at: datetime | None = None,
    source_updated_at: datetime | None = None,
) -> None:
    digest = db.get(Digest, (article_id, article_type))
    if digest is None:
        return

    seen_at = seen_at or datetime.now(timezone.utc)
    digest.content_last_seen_at = seen_at
    if source_updated_at is not None:
        digest.source_updated_at = source_updated_at
    db.commit()


def get_recent_digests(db: Session, hours: int = 24) -> list[Digest]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return db.query(Digest).filter(Digest.uploaded_at >= cutoff).order_by(Digest.uploaded_at.desc()).all()


def save_curator_run(
    db: Session,
    *,
    ranked_articles,
    digests: list[Digest],
    pipeline_run_id: int | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
    notes: str | None = None,
) -> CuratorRun:
    now = datetime.now(timezone.utc)
    run = CuratorRun(
        pipeline_run_id=pipeline_run_id,
        started_at=now,
        ended_at=now,
        model_name=model_name,
        prompt_version=prompt_version,
        notes=notes,
    )
    db.add(run)
    db.flush()

    digest_map = {(d.article_id, d.article_type): d for d in digests}
    seen: set[tuple[str, str]] = set()
    rank_position = 1
    for article in ranked_articles:
        key = (article.article_id, article.article_type)
        if key in seen:
            continue
        seen.add(key)
        digest = digest_map.get(key)
        db.add(
            CuratorRanking(
                curator_run_id=run.id,
                article_id=article.article_id,
                article_type=article.article_type,
                title=article.title,
                score=article.score,
                rank_position=rank_position,
                ranking_reason=article.ranking_reason,
                digest_version=digest.digest_version if digest is not None else None,
                digest_generated_at=digest.digest_generated_at if digest is not None else None,
            )
        )
        rank_position += 1

    db.commit()
    db.refresh(run)
    return run


def get_latest_curator_run(db: Session, pipeline_run_id: int | None = None) -> CuratorRun | None:
    query = db.query(CuratorRun)
    if pipeline_run_id is not None:
        query = query.filter(CuratorRun.pipeline_run_id == pipeline_run_id)
    return query.order_by(CuratorRun.started_at.desc()).first()


def get_curator_rankings(db: Session, curator_run_id: int, limit: int = 10) -> list[CuratorRanking]:
    return (
        db.query(CuratorRanking)
        .filter(CuratorRanking.curator_run_id == curator_run_id)
        .order_by(CuratorRanking.rank_position.asc())
        .limit(limit)
        .all()
    )


def _record_retry(stage: StageMonitor) -> None:
    stage.add_retry()
    stage.add_backoff()
