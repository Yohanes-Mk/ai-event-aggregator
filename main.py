import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from app.db import repository
from app.db.session import SessionLocal
from app.monitoring import PipelineTracker, StageMonitor, configure_logging
from app.scrapers.events import EventScraper
from app.scrapers.youtube import CHANNELS, YouTubeScraper
from app.services.process_curator import process_curator
from app.services.process_digest import process_digest
from app.services.process_events_email import process_events_email
from app.services.process_youtube_email import process_youtube_email

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()

    db = SessionLocal()
    tracker = PipelineTracker(db, trigger="manual").start()

    try:
        logger.info("=== YouTube Videos (last 5 days) ===")
        existing_ids = repository.get_existing_video_ids(db)
        all_videos = []
        with StageMonitor(tracker, "youtube_scrape") as stage, StageMonitor(
            tracker, "youtube_short_checks"
        ) as shorts_stage:
            shorts_stage.set_concurrency(1)
            shorts_stage.set_batch_info(total_batches=len(CHANNELS))
            for ch in CHANNELS:
                scraper = YouTubeScraper(
                    ch["channel_id"],
                    ch["name"],
                    load_classifications=lambda video_ids: repository.get_video_classifications(db, video_ids),
                    save_classifications=lambda classifications: repository.save_video_classifications(classifications, db),
                )
                videos = scraper.scrape(
                    within_days=5,
                    with_transcripts=True,
                    skip_ids=existing_ids,
                    shorts_stage=shorts_stage,
                )
                for video in videos:
                    stage.attempt()
                    stage.succeed()
                    logger.info(
                        "  [%s] %s (%s)",
                        video.channel_name,
                        video.title,
                        video.published_at.date(),
                    )
                all_videos.extend(videos)
            repository.save_videos(all_videos, db)

        logger.info("  %s videos saved", len(all_videos))

        logger.info("=== Upcoming Events (next 14 days) ===")
        with StageMonitor(tracker, "events_scrape") as stage:
            events = EventScraper(within_days=14).scrape()
            for event in events:
                stage.attempt()
                stage.succeed()
                logger.info(
                    "  %s - %s (%s)",
                    event.start_time.strftime("%a %b %d"),
                    event.title,
                    ", ".join(event.sources),
                )
            repository.save_events(events, db, tracker=tracker)

        logger.info("  %s events saved", len(events))

        process_digest(db, tracker=tracker)
        process_curator(db, tracker=tracker)
        process_youtube_email(db, tracker=tracker)
        process_events_email(db, tracker=tracker)

        tracker.finish()
    except Exception as exc:
        logger.exception("Pipeline run aborted")
        tracker.abort(exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
