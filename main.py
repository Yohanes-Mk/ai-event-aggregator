import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.scrapers.youtube import YouTubeScraper, CHANNELS
from app.scrapers.events import EventScraper
from app.db.session import SessionLocal
from app.db import repository


def main() -> None:
    db = SessionLocal()

    print("=== YouTube Videos (last 14 days) ===")
    all_videos = []
    for ch in CHANNELS:
        scraper = YouTubeScraper(ch["channel_id"], ch["name"])
        videos = scraper.scrape(with_transcripts=True)
        for v in videos:
            print(f"  [{v.channel_name}] {v.title} ({v.published_at.date()})")
        all_videos.extend(videos)

    repository.save_videos(all_videos, db)
    print(f"\n  {len(all_videos)} videos saved\n")

    print("=== Upcoming Events (next 14 days) ===")
    events = EventScraper().scrape()
    for e in events:
        print(f"  {e.start_time.strftime('%a %b %d')} - {e.title} ({', '.join(e.sources)})")

    repository.save_events(events, db)
    print(f"\n  {len(events)} events saved")

    db.close()


if __name__ == "__main__":
    main()
