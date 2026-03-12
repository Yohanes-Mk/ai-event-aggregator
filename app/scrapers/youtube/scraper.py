from __future__ import annotations

import os
from collections.abc import Callable
import feedparser
import httpx
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, HttpUrl
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    IpBlocked,
)
from youtube_transcript_api.proxies import WebshareProxyConfig

from app.monitoring.stage import StageMonitor


def _build_transcript_api() -> YouTubeTranscriptApi:
    username = os.getenv("WEBSHARE_PROXY_USERNAME")
    password = os.getenv("WEBSHARE_PROXY_PASSWORD")
    if username and password:
        return YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=username,
                proxy_password=password,
            )
        )
    return YouTubeTranscriptApi()


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
    def __init__(
        self,
        channel_id: str,
        channel_name: str,
        *,
        load_classifications: Callable[[list[str]], dict[str, bool]] | None = None,
        save_classifications: Callable[[dict[str, bool]], None] | None = None,
    ) -> None:
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.load_classifications = load_classifications
        self.save_classifications = save_classifications
        self._classification_cache: dict[str, bool] = {}

    def _is_short(self, video_id: str, client: httpx.Client) -> bool:
        """Return True if the video is a YouTube Short."""
        r = client.head(
            f"https://www.youtube.com/shorts/{video_id}",
            follow_redirects=False,
            timeout=5,
        )
        return r.status_code == 200

    def fetch_latest_videos(
        self,
        within_days: int = 14,
        skip_ids: set[str] | None = None,
        shorts_stage: StageMonitor | None = None,
    ) -> list[Video]:
        """Fetch recent videos from the channel via its RSS feed, excluding Shorts.

        skip_ids: video_ids already in the DB — skips Shorts check + avoids duplicate work.
        """
        url = RSS_BASE.format(channel_id=self.channel_id)
        feed = feedparser.parse(url)

        cutoff = datetime.now(timezone.utc) - timedelta(days=within_days)
        candidate_entries = []

        for entry in feed.entries:
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published_at < cutoff:
                continue
            if skip_ids and entry.yt_videoid in skip_ids:
                continue
            candidate_entries.append((entry, published_at))

        video_ids = [entry.yt_videoid for entry, _ in candidate_entries]
        self._hydrate_classification_cache(video_ids)

        videos = []
        pending_updates: dict[str, bool] = {}
        with httpx.Client() as client:
            for entry, published_at in candidate_entries:
                video_id = entry.yt_videoid
                if shorts_stage is not None:
                    shorts_stage.attempt()

                cached = self._classification_cache.get(video_id)
                if cached is not None:
                    if shorts_stage is not None:
                        shorts_stage.add_cache_hit()
                    is_short = cached
                    classification_success = True
                else:
                    if shorts_stage is not None:
                        shorts_stage.add_network_call()
                    classification_resolved = True
                    try:
                        is_short = self._is_short(video_id, client)
                    except Exception as exc:
                        is_short = False
                        classification_resolved = False
                        if shorts_stage is not None:
                            shorts_stage.fail(exc, item_id=video_id)
                    if classification_resolved:
                        self._classification_cache[video_id] = is_short
                        pending_updates[video_id] = is_short
                    classification_success = classification_resolved

                if is_short:
                    if shorts_stage is not None:
                        shorts_stage.skip()
                    continue

                if shorts_stage is not None and classification_success:
                    shorts_stage.succeed()

                videos.append(
                    Video(
                        video_id=video_id,
                        title=entry.title,
                        url=entry.link,
                        published_at=published_at,
                        channel_name=self.channel_name,
                        channel_id=self.channel_id,
                    )
                )

        if pending_updates and self.save_classifications is not None:
            self.save_classifications(pending_updates)

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
            segments = _build_transcript_api().fetch(video.video_id)
            transcript = " ".join(s.text for s in segments)
        except (TranscriptsDisabled, NoTranscriptFound, IpBlocked):
            transcript = None
        return video.model_copy(update={"transcript": transcript})

    def scrape(
        self,
        within_days: int = 14,
        with_transcripts: bool = True,
        skip_ids: set[str] | None = None,
        shorts_stage: StageMonitor | None = None,
    ) -> list[Video]:
        """Full pipeline: fetch latest videos + optionally attach transcripts."""
        videos = self.fetch_latest_videos(
            within_days,
            skip_ids=skip_ids,
            shorts_stage=shorts_stage,
        )
        if with_transcripts:
            videos = [self.fetch_transcript(v) for v in videos]
        return videos

    def _hydrate_classification_cache(self, video_ids: list[str]) -> None:
        missing_ids = [video_id for video_id in video_ids if video_id not in self._classification_cache]
        if not missing_ids or self.load_classifications is None:
            return

        cached = self.load_classifications(missing_ids)
        self._classification_cache.update(cached)


if __name__ == "__main__":
    # Quick manual test
    scraper = YouTubeScraper(
        channel_id="UCsBjURrPoezykLs9EqgamOA", channel_name="Fireship"
    )
    videos = scraper.scrape(with_transcripts=False)
    for v in videos:
        print(f"{v.title} ({v.published_at.date()}) — {v.url}")
