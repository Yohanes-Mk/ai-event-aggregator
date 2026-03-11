import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.scrapers.youtube import YouTubeScraper, CHANNELS
from app.scrapers.events import EventScraper
from app.db.session import SessionLocal
from app.db import repository
from app.services.process_digest import process_digest


def main() -> None:
    db = SessionLocal()

    print("=== YouTube Videos (last 2 days) ===")
    all_videos = []
    for ch in CHANNELS:
        scraper = YouTubeScraper(ch["channel_id"], ch["name"])
        videos = scraper.scrape(within_days=2, with_transcripts=True)
        for v in videos:
            print(f"  [{v.channel_name}] {v.title} ({v.published_at.date()})")
        all_videos.extend(videos)

    repository.save_videos(all_videos, db)
    print(f"\n  {len(all_videos)} videos saved\n")

    print("=== Upcoming Events (next 1 day) ===")
    events = EventScraper(within_days=1).scrape()
    for e in events:
        print(f"  {e.start_time.strftime('%a %b %d')} - {e.title} ({', '.join(e.sources)})")

    repository.save_events(events, db)
    print(f"\n  {len(events)} events saved\n")

    process_digest(db)

    db.close()


if __name__ == "__main__":
    main()
