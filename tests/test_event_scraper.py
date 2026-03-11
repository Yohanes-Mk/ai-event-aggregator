"""
Integration tests for the EventScraper.
These hit the real iCal feeds — no mocks.
"""
from datetime import datetime, timedelta, timezone

from app.scrapers.events import EventScraper, Event


def test_scrape_returns_events():
    scraper = EventScraper()
    events = scraper.scrape()

    assert isinstance(events, list)
    assert len(events) > 0, "Expected at least one upcoming event across both feeds"

    for event in events:
        assert isinstance(event, Event)
        assert event.title
        assert isinstance(event.start_time, datetime)
        assert isinstance(event.sources, list)
        assert len(event.sources) > 0
        print(f"[{', '.join(event.sources)}] {event.title} — {event.start_time.date()}")


def test_events_are_upcoming():
    scraper = EventScraper(within_days=14)
    events = scraper.scrape()

    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=14)

    for event in events:
        assert event.start_time >= now, f"Event is in the past: {event.title}"
        assert event.start_time <= cutoff, f"Event is beyond 14 days: {event.title}"


def test_events_sorted_by_start_time():
    events = EventScraper().scrape()
    start_times = [e.start_time for e in events]
    assert start_times == sorted(start_times), "Events are not sorted by start_time"
