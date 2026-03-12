from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.orm import Session
from app.db.models import YouTubeVideo, Event, Digest
from app.scrapers.youtube.scraper import Video
from app.scrapers.events.scraper import Event as ScrapedEvent
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker

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
                    result = event_agent.run(temp)
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


def get_videos(db: Session, limit: int = 50) -> list[YouTubeVideo]:
    return db.query(YouTubeVideo).order_by(YouTubeVideo.published_at.desc()).limit(limit).all()


def get_events(db: Session, limit: int = 50) -> list[Event]:
    return db.query(Event).order_by(Event.start_time).limit(limit).all()


def digest_exists(article_id: str, article_type: str, db: Session) -> bool:
    return db.get(Digest, (article_id, article_type)) is not None


def save_digest(digest: Digest, db: Session) -> None:
    db.merge(digest)
    db.commit()


def get_recent_digests(db: Session, hours: int = 24) -> list[Digest]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return db.query(Digest).filter(Digest.uploaded_at >= cutoff).all()
