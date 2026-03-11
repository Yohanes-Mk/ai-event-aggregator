from sqlalchemy.orm import Session
from app.db.models import YouTubeVideo, Event, Digest
from app.scrapers.youtube.scraper import Video
from app.scrapers.events.scraper import Event as ScrapedEvent


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


def save_events(events: list[ScrapedEvent], db: Session) -> None:
    """Upsert scraped events — safe to call on every run."""
    for e in events:
        row = Event(
            title=e.title,
            start_time=e.start_time,
            end_time=e.end_time,
            location=e.location,
            urls=e.urls,
            sources=e.sources,
        )
        db.merge(row)
    db.commit()


def get_videos(db: Session, limit: int = 50) -> list[YouTubeVideo]:
    return db.query(YouTubeVideo).order_by(YouTubeVideo.published_at.desc()).limit(limit).all()


def get_events(db: Session, limit: int = 50) -> list[Event]:
    return db.query(Event).order_by(Event.start_time).limit(limit).all()


def digest_exists(article_id: str, article_type: str, db: Session) -> bool:
    return db.get(Digest, (article_id, article_type)) is not None


def save_digest(digest: Digest, db: Session) -> None:
    db.merge(digest)
    db.commit()
