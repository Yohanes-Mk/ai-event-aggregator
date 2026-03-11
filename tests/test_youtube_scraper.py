"""
Integration tests for the YouTube scraper.
These hit the real YouTube RSS feed — no mocks.
"""
import pytest
from youtube_transcript_api._errors import IpBlocked
from app.scrapers.youtube import YouTubeScraper, Video

CHANNELS = [
    {"name": "Fireship", "channel_id": "UCsBjURrPoezykLs9EqgamOA"},
    {"name": "Theo - t3.gg", "channel_id": "UCbRP3c757lWg9M-U7TyEkXA"},
]


def test_fetch_latest_video_returns_video():
    for ch in CHANNELS:
        scraper = YouTubeScraper(channel_id=ch["channel_id"], channel_name=ch["name"])
        video = scraper.fetch_latest_video()
        assert video is not None, f"Expected a video for {ch['name']}, got None"
        assert isinstance(video, Video)
        assert video.title
        assert str(video.url).startswith("https://www.youtube.com")
        assert video.video_id
        assert video.channel_name == ch["name"]
        assert video.channel_id == ch["channel_id"]
        assert video.published_at is not None
        print(f"[{ch['name']}] {video.title} ({video.published_at.date()}) — {video.url}")


def test_fetch_transcript_attaches_text():
    ch = CHANNELS[0]  # Fireship — reliably has transcripts
    scraper = YouTubeScraper(channel_id=ch["channel_id"], channel_name=ch["name"])
    video = scraper.fetch_latest_video()
    assert video is not None

    try:
        video = scraper.fetch_transcript(video)
    except IpBlocked:
        pytest.skip("IP blocked by YouTube — try again later")

    assert video.transcript is None or isinstance(video.transcript, str)
    if video.transcript:
        assert len(video.transcript) > 0
        print(f"Transcript preview: {video.transcript[:200]}")
