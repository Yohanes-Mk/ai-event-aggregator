from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import repository
from app.db.models import Digest
from agent import youtube_agent, event_agent


def process_digest(db: Session) -> None:
    _process_videos(db)
    _process_events(db)


def _process_videos(db: Session) -> None:
    print("=== Digesting YouTube Videos ===")
    videos = repository.get_videos(db, limit=500)
    processed = 0

    for video in videos:
        if repository.digest_exists(video.video_id, "youtube", db):
            continue

        print(f"  Processing: [{video.channel_name}] {video.title}")
        try:
            result = youtube_agent.run(video)
        except Exception as e:
            print(f"    Error: {e}")
            continue

        digest = Digest(
            article_id=video.video_id,
            article_type="youtube",
            url=video.url,
            title=result.title,
            summary=result.summary,
            tools_concepts=result.tools_concepts,
            relevance_score=None,
            source=video.channel_name,
            created_at=datetime.now(timezone.utc),
        )
        repository.save_digest(digest, db)
        processed += 1

    print(f"  {processed} new video digests saved\n")


def _process_events(db: Session) -> None:
    print("=== Digesting Events ===")
    events = repository.get_events(db, limit=500)
    processed = 0

    for event in events:
        article_id = f"{event.title}||{event.start_time.isoformat()}"
        if repository.digest_exists(article_id, "event", db):
            continue

        print(f"  Processing: {event.title}")
        try:
            result = event_agent.run(event)
        except Exception as e:
            print(f"    Error: {e}")
            continue

        url = event.urls[0] if event.urls else None
        digest = Digest(
            article_id=article_id,
            article_type="event",
            url=url,
            title=result.title,
            summary=result.summary,
            tools_concepts=None,
            relevance_score=result.relevance_score,
            source=", ".join(event.sources),
            created_at=datetime.now(timezone.utc),
        )
        repository.save_digest(digest, db)
        processed += 1

    print(f"  {processed} new event digests saved\n")
