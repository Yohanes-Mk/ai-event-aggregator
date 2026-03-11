from __future__ import annotations

import feedparser
import httpx
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, HttpUrl
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)


class Channel(BaseModel):
    channel_id: str
    name: str


class Video(BaseModel):
    video_id: str
    title: str
    url: HttpUrl
    published_at: datetime
    channel_name: str
    channel_id: str
    transcript: str | None = None


RSS_BASE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


class YouTubeScraper:
    def __init__(self, channel_id: str, channel_name: str) -> None:
        self.channel_id = channel_id
        self.channel_name = channel_name

    def _is_short(self, video_id: str) -> bool:
        """Return True if the video is a YouTube Short."""
        try:
            r = httpx.head(
                f"https://www.youtube.com/shorts/{video_id}",
                follow_redirects=False,
                timeout=5,
            )
            return r.status_code == 200
        except Exception:
            return False

    def fetch_latest_videos(self, within_days: int = 14) -> list[Video]:
        """Fetch recent videos from the channel via its RSS feed, excluding Shorts."""
        url = RSS_BASE.format(channel_id=self.channel_id)
        feed = feedparser.parse(url)

        cutoff = datetime.now(timezone.utc) - timedelta(days=within_days)
        videos = []

        for entry in feed.entries:
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published_at < cutoff:
                continue
            if self._is_short(entry.yt_videoid):
                continue

            videos.append(
                Video(
                    video_id=entry.yt_videoid,
                    title=entry.title,
                    url=entry.link,
                    published_at=published_at,
                    channel_name=self.channel_name,
                    channel_id=self.channel_id,
                )
            )

        return videos

    def fetch_latest_video(self) -> Video | None:
        """Return the single most recent video from the channel, regardless of age."""
        url = RSS_BASE.format(channel_id=self.channel_id)
        feed = feedparser.parse(url)
        if not feed.entries:
            return None
        entry = feed.entries[0]
        return Video(
            video_id=entry.yt_videoid,
            title=entry.title,
            url=entry.link,
            published_at=datetime(*entry.published_parsed[:6], tzinfo=timezone.utc),
            channel_name=self.channel_name,
            channel_id=self.channel_id,
        )

    def fetch_transcript(self, video: Video) -> Video:
        """Fetch and attach transcript text to a Video. Returns the same object."""
        try:
            segments = YouTubeTranscriptApi().fetch(video.video_id)
            transcript = " ".join(s.text for s in segments)
        except TranscriptsDisabled, NoTranscriptFound:
            transcript = None
        return video.model_copy(update={"transcript": transcript})

    def scrape(
        self, within_days: int = 14, with_transcripts: bool = True
    ) -> list[Video]:
        """Full pipeline: fetch latest videos + optionally attach transcripts."""
        videos = self.fetch_latest_videos(within_days)
        if with_transcripts:
            videos = [self.fetch_transcript(v) for v in videos]
        return videos


if __name__ == "__main__":
    # Quick manual test
    scraper = YouTubeScraper(
        channel_id="UCsBjURrPoezykLs9EqgamOA", channel_name="Fireship"
    )
    videos = scraper.scrape(with_transcripts=False)
    for v in videos:
        print(f"{v.title} ({v.published_at.date()}) — {v.url}")
