from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

import httpx
from icalendar import Calendar
from pydantic import BaseModel, HttpUrl

from .feeds import FEEDS


class Event(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime | None
    location: str | None
    urls: list[str] = []
    sources: list[str] = []


def _to_utc_datetime(dt: datetime | date) -> datetime:
    """Convert a date or naive datetime to a timezone-aware UTC datetime."""
    if isinstance(dt, datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)


class EventScraper:
    def __init__(self, feeds: list[dict] = FEEDS, within_days: int = 14) -> None:
        self.feeds = feeds
        self.within_days = within_days

    def _fetch_feed(self, url: str) -> bytes:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; event-aggregator/1.0)"}
        response = httpx.get(url, follow_redirects=True, timeout=10, headers=headers)
        response.raise_for_status()
        return response.content

    def _parse_feed(self, raw: bytes, source: str) -> list[Event]:
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=self.within_days)

        # Fix malformed durations — Tockify emits P15M (months) instead of PT15M (minutes)
        # Affects X-PUBLISHED-TTL and REFRESH-INTERVAL fields
        raw = re.sub(rb":P(\d+)M\r", rb":PT\1M\r", raw)
        cal = Calendar.from_ical(raw)
        events = []

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            dtstart = component.get("DTSTART")
            if dtstart is None:
                continue

            start_time = _to_utc_datetime(dtstart.dt)
            if not (now <= start_time <= cutoff):
                continue

            dtend = component.get("DTEND")
            end_time = _to_utc_datetime(dtend.dt) if dtend else None

            location = str(component.get("LOCATION")) or None
            raw_url = component.get("URL")
            url = str(raw_url) if raw_url else None

            events.append(
                Event(
                    title=str(component.get("SUMMARY", "")),
                    start_time=start_time,
                    end_time=end_time,
                    location=location if location else None,
                    urls=[url] if url else [],
                    sources=[source],
                )
            )

        return events

    def _deduplicate(self, events: list[Event]) -> list[Event]:
        """Merge events with the same title and date, combining URLs and sources."""
        seen: dict[tuple, Event] = {}

        for event in events:
            key = (event.title.strip().lower(), event.start_time.date())
            if key in seen:
                existing = seen[key]
                # Merge in any new URLs and sources not already present
                merged_urls = existing.urls + [u for u in event.urls if u not in existing.urls]
                merged_sources = existing.sources + [s for s in event.sources if s not in existing.sources]
                seen[key] = existing.model_copy(update={"urls": merged_urls, "sources": merged_sources})
            else:
                seen[key] = event

        return list(seen.values())

    def scrape(self) -> list[Event]:
        """Fetch all feeds, deduplicate, return sorted by start time."""
        all_events: list[Event] = []

        for feed in self.feeds:
            try:
                raw = self._fetch_feed(feed["url"])
                all_events.extend(self._parse_feed(raw, feed["name"]))
            except httpx.HTTPError as e:
                print(f"[EventScraper] Failed to fetch {feed['name']}: {e}")

        return sorted(self._deduplicate(all_events), key=lambda e: e.start_time)
