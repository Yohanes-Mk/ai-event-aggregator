import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.scrapers.youtube import YouTubeScraper, CHANNELS
from app.scrapers.events import EventScraper


def main() -> None:
    print("=== YouTube Videos (last 14 days) ===")
    total_videos = 0
    for ch in CHANNELS:
        scraper = YouTubeScraper(ch["channel_id"], ch["name"])
        videos = scraper.scrape(with_transcripts=False)
        for v in videos:
            print(f"  [{v.channel_name}] {v.title} ({v.published_at.date()})")
        total_videos += len(videos)

    print(f"\n  {total_videos} videos found\n")

    print("=== Upcoming Events (next 14 days) ===")
    events = EventScraper().scrape()
    for e in events:
        print(f"  {e.start_time.strftime('%a %b %d')} - {e.title} ({', '.join(e.sources)})")

    print(f"\n  {len(events)} events found")


if __name__ == "__main__":
    main()
