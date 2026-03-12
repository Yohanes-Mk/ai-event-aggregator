from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import repository
from app.db.models import Digest
from agent import youtube_agent


def process_digest(db: Session) -> None:
    _process_videos(db)


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
            source=video.channel_name,
            uploaded_at=datetime.now(timezone.utc),
        )
        repository.save_digest(digest, db)
        processed += 1

    print(f"  {processed} new video digests saved\n")
