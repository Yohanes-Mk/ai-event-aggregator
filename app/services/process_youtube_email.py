from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

from sqlalchemy.orm import Session

from app.db import repository
from app.db.models import YouTubeVideo
from app.email.render import render_youtube_email
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker
from app.services.retry_utils import run_with_retries
from agent import curator_agent
from agent.youtube_email_agent import run as generate_email
from agent import youtube_email_agent

logger = logging.getLogger(__name__)


def _send(subject: str, html: str, recipient: str | None = None) -> None:
    sender = os.environ["GMAIL_SENDER"]
    recipient = recipient or os.environ["GMAIL_RECIPIENT"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(sender, app_password)
        server.sendmail(sender, recipient, msg.as_string())


def process_youtube_email(
    db: Session,
    tracker: PipelineTracker | None = None,
    *,
    recipient: str | None = None,
) -> bool:
    logger.info("=== YouTube Email Digest ===")

    with StageMonitor(tracker, "youtube_email") as stage:
        digests = repository.get_recent_digests(db, hours=168)  # last 7 days
        if not digests:
            logger.info("  No digests in the last 7 days. Skipping email.")
            return False

        logger.info("  Preparing %s item(s) for email...", len(digests))
        stage.attempt()
        stage.set_model_info(
            model_name=youtube_email_agent.MODEL_NAME,
            prompt_version=youtube_email_agent.PROMPT_VERSION,
        )
        stage.set_batch_info(batch_size=min(len(digests), 10), total_batches=1)
        stage.set_concurrency(1)

        # Pull channel_id from youtube_videos for link building
        video_ids = [d.article_id for d in digests if d.article_type == "youtube"]
        channel_id_map: dict[str, str] = {}
        if video_ids:
            rows = db.query(YouTubeVideo.video_id, YouTubeVideo.channel_id).filter(
                YouTubeVideo.video_id.in_(video_ids)
            ).all()
            channel_id_map = {r.video_id: r.channel_id for r in rows}

        # Build lookup map: article_id -> {url, tools_concepts, channel_name, channel_id}
        digest_map = {
            d.article_id: {
                "url": d.url or "",
                "tools_concepts": d.tools_concepts or "",
                "channel_name": d.source or "Unknown Channel",
                "channel_id": channel_id_map.get(d.article_id, ""),
                "summary": d.summary,
            }
            for d in digests
        }

        latest_curator_run = repository.get_latest_curator_run(
            db,
            pipeline_run_id=tracker.run.id if tracker and tracker.run is not None else None,
        )

        top_10 = []
        if latest_curator_run is not None:
            logger.info("  Reusing curator run id=%s for email...", latest_curator_run.id)
            for ranking in repository.get_curator_rankings(db, latest_curator_run.id, limit=10):
                meta = digest_map.get(ranking.article_id)
                if meta is None:
                    continue
                top_10.append(
                    curator_agent.RankedArticle(
                        article_id=ranking.article_id,
                        article_type=ranking.article_type,
                        title=ranking.title,
                        summary=meta["summary"],
                        score=ranking.score,
                        ranking_reason=ranking.ranking_reason,
                    )
                )
        else:
            logger.info("  No saved curator run found. Ranking %s item(s) directly for email...", len(digests))
            try:
                curator_result = run_with_retries(
                    lambda: curator_agent.run(digests),
                    max_attempts=3,
                    backoff_seconds=1.0,
                    on_retry=lambda _attempt, _backoff: _record_retry(stage),
                )
            except Exception as exc:
                stage.fail(exc)
                logger.exception("Curator ranking failed for youtube email")
                return False

            seen: set[str] = set()
            for article in curator_result.ranked_articles:
                if article.article_id in seen:
                    continue
                seen.add(article.article_id)
                top_10.append(article)

        if not top_10:
            logger.info("  No ranked YouTube items available for email.")
            return False

        try:
            email_result = run_with_retries(
                lambda: generate_email(top_10, digest_map),
                max_attempts=3,
                backoff_seconds=1.0,
                on_retry=lambda _attempt, _backoff: _record_retry(stage),
            )
        except Exception as exc:
            stage.fail(exc)
            logger.exception("YouTube email generation failed")
            return False

        # Pin URLs from DB — never trust the LLM to pass URLs through unchanged
        for section in email_result.articles:
            db_url = digest_map.get(section.article_id, {}).get("url", "")
            if db_url:
                section.url = db_url

        html = render_youtube_email(email_result)
        logger.info("  Subject: %s", email_result.subject)

        try:
            _send(email_result.subject, html, recipient=recipient)
        except Exception as exc:
            stage.fail(exc)
            logger.exception("YouTube email send failed")
            return False

        stage.succeed()
        logger.info("  Email sent.")
        return True


def _record_retry(stage: StageMonitor) -> None:
    stage.add_retry()
    stage.add_backoff()
