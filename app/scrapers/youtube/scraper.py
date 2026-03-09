from __future__ import annotations

import feedparser
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)

RSS_BASE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


@dataclass
class Video:
    video_id: str
    title: str
    url: str
    published_at: datetime
    channel_name: str
    channel_id: str
    transcript: str | None = None


def fetch_latest_videos(
    channel_id: str,
    channel_name: str,
    within_days: int = 14,
) -> list[Video]:
    """Fetch recent videos from a channel via its RSS feed."""
    url = RSS_BASE.format(channel_id=channel_id)
    feed = feedparser.parse(url)

    cutoff = datetime.now(timezone.utc) - timedelta(days=within_days)
    videos = []

    for entry in feed.entries:
        published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published_at < cutoff:
            continue

        video_id = entry.yt_videoid
        videos.append(
            Video(
                video_id=video_id,
                title=entry.title,
                url=entry.link,
                published_at=published_at,
                channel_name=channel_name,
                channel_id=channel_id,
            )
        )

    return videos


def fetch_transcript(video: Video) -> Video:
    """Fetch and attach transcript text to a Video. Returns the same object."""
    try:
        segments = YouTubeTranscriptApi().fetch(video.video_id)
        video.transcript = " ".join(s.text for s in segments)
    except TranscriptsDisabled, NoTranscriptFound:
        video.transcript = None
    return video


def scrape_channel(
    channel_id: str,
    channel_name: str,
    within_days: int = 14,
    with_transcripts: bool = True,
) -> list[Video]:
    """Full pipeline: fetch latest videos + optionally attach transcripts."""
    videos = fetch_latest_videos(channel_id, channel_name, within_days)
    if with_transcripts:
        videos = [fetch_transcript(v) for v in videos]
    return videos


# …existing code…

if __name__ == "__main__":
    # Example usage:
    channel_id = "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # Google Developers
    channel_name = "Google Developers"

    # fetch videos and transcripts
    videos = scrape_channel(
        channel_id,
        channel_name,
        within_days=14,
        with_transcripts=True,
    )

    print(f"Found {len(videos)} recent videos for channel '{channel_name}':")
    for v in videos:
        print(
            f"{v.title} ({v.published_at.date()}) - "
            f"Transcript length: {len(v.transcript) if v.transcript else 'N/A'}"
        )
        # print transcript of videos    for v in videos:
        print(
            f"\nTranscript for '{v.title}':\n{v.transcript[:500]}..."
        )  # Print first 500 chars of transcript
