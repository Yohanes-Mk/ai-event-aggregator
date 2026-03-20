from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.dashboard import render_dashboard
from app.db import repository
from app.db.models import Digest, Event, YouTubeVideo
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker

logger = logging.getLogger(__name__)

ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "dashboard.html"


def process_dashboard(db: Session, tracker: PipelineTracker | None = None) -> Path | None:
    logger.info("=== Dashboard Render ===")

    with StageMonitor(tracker, "dashboard_render") as stage:
        payload = _build_dashboard_payload(
            db,
            pipeline_run_id=tracker.run.id if tracker and tracker.run is not None else None,
        )
        stage.attempt()
        stage.set_batch_info(
            batch_size=len(payload["videos"]) + len(payload["events"]),
            total_batches=1,
        )
        stage.set_concurrency(1)
        try:
            html = render_dashboard(payload)
            ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
            ARTIFACT_PATH.write_text(html, encoding="utf-8")
        except Exception as exc:
            stage.fail(exc)
            logger.exception("Dashboard render failed")
            return None

        stage.succeed()
        logger.info("  Dashboard written to %s", ARTIFACT_PATH)
        return ARTIFACT_PATH


def _build_dashboard_payload(db: Session, pipeline_run_id: int | None = None) -> dict:
    curator_run = repository.get_latest_curator_run(db, pipeline_run_id=pipeline_run_id)
    if curator_run is None:
        curator_run = repository.get_latest_curator_run(db)

    videos = _build_video_sections(db, curator_run.id if curator_run is not None else None)
    events = _build_event_sections(db)
    generated_at = datetime.now(timezone.utc)
    return {
        "generated_at": generated_at.isoformat(),
        "recipient_name": os.getenv("DASHBOARD_RECIPIENT_NAME", "Yohannes"),
        "videos": videos,
        "events": events,
    }


def _build_video_sections(db: Session, curator_run_id: int | None) -> list[dict]:
    if curator_run_id is None:
        return []

    rankings = repository.get_curator_rankings(db, curator_run_id, limit=10)
    if not rankings:
        return []

    video_ids = [ranking.article_id for ranking in rankings if ranking.article_type == "youtube"]
    digest_map: dict[str, Digest] = {}
    if video_ids:
        digests = (
            db.query(Digest)
            .filter(Digest.article_type == "youtube", Digest.article_id.in_(video_ids))
            .all()
        )
        digest_map = {digest.article_id: digest for digest in digests}

    youtube_map: dict[str, YouTubeVideo] = {}
    if video_ids:
        videos = db.query(YouTubeVideo).filter(YouTubeVideo.video_id.in_(video_ids)).all()
        youtube_map = {video.video_id: video for video in videos}

    sections: list[dict] = []
    for ranking in rankings:
        if ranking.article_type != "youtube":
            continue
        digest = digest_map.get(ranking.article_id)
        video = youtube_map.get(ranking.article_id)
        if digest is None:
            continue

        sections.append(
            {
                "rank": ranking.rank_position,
                "title": ranking.title,
                "channel_name": video.channel_name if video is not None else digest.source,
                "channel_url": (
                    f"https://www.youtube.com/channel/{video.channel_id}"
                    if video is not None and video.channel_id
                    else ""
                ),
                "summary": digest.summary,
                "tools_concepts": _split_tools_concepts(digest.tools_concepts),
                "score": ranking.score,
                "ranking_reason": ranking.ranking_reason,
                "url": digest.url or (video.url if video is not None else ""),
            }
        )
    return sections


def _build_event_sections(db: Session) -> list[dict]:
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=14)
    events = (
        db.query(Event)
        .filter(Event.start_time >= now, Event.start_time <= cutoff)
        .order_by(Event.relevance_score.desc().nullslast(), Event.start_time.asc())
        .all()
    )

    return [
        {
            "title": event.title,
            "date": event.start_time.strftime("%a %b %d"),
            "time": _format_event_time(event.start_time, event.end_time),
            "location": event.location or "Location TBD",
            "summary": event.summary or "Summary pending.",
            "score": event.relevance_score or 0,
            "url": event.urls[0] if event.urls else "",
        }
        for event in events
    ]


def _split_tools_concepts(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _format_event_time(start_time: datetime, end_time: datetime | None) -> str:
    start_label = start_time.astimezone().strftime("%-I:%M %p")
    if end_time is None:
        return start_label
    end_label = end_time.astimezone().strftime("%-I:%M %p")
    return f"{start_label} - {end_label}"
