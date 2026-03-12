from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

from sqlalchemy.orm import Session

from app.db.models import Event
from app.email.render import render_events_email
from app.monitoring import StageMonitor
from app.monitoring.tracker import PipelineTracker
from app.services.retry_utils import run_with_retries
from agent.events_email_agent import run as generate_email
from agent import events_email_agent

logger = logging.getLogger(__name__)

def _get_upcoming_events(db: Session) -> list[Event]:
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=14)
    return (
        db.query(Event)
        .filter(Event.start_time >= now, Event.start_time <= cutoff)
        .order_by(Event.start_time)
        .all()
    )


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


def process_events_email(
    db: Session,
    tracker: PipelineTracker | None = None,
    *,
    recipient: str | None = None,
) -> bool:
    logger.info("=== Events Email Digest ===")

    with StageMonitor(tracker, "events_email") as stage:
        events = _get_upcoming_events(db)
        if not events:
            logger.info("  No events in the next 14 days. Skipping email.")
            return False

        logger.info("  Found %s event(s) for the next 14 days...", len(events))
        stage.attempt()
        stage.set_model_info(
            model_name=events_email_agent.MODEL_NAME,
            prompt_version=events_email_agent.PROMPT_VERSION,
        )
        stage.set_batch_info(batch_size=len(events), total_batches=1)
        stage.set_concurrency(1)

        try:
            email_result = run_with_retries(
                lambda: generate_email(events),
                max_attempts=3,
                backoff_seconds=1.0,
                on_retry=lambda _attempt, _backoff: _record_retry(stage),
            )
        except Exception as exc:
            stage.fail(exc)
            logger.exception("Events email generation failed")
            return False

        # Build event_key -> first URL map from DB records
        event_url_map = {
            f"{e.title}||{e.start_time.isoformat()}": e.urls[0] if e.urls else ""
            for e in events
        }

        # Pin URLs from DB — never trust the LLM to pass URLs through unchanged
        for section in email_result.events:
            db_url = event_url_map.get(section.event_key, "")
            if db_url:
                section.url = db_url

        html = render_events_email(email_result)
        logger.info("  Subject: %s", email_result.subject)

        try:
            _send(email_result.subject, html, recipient=recipient)
        except Exception as exc:
            stage.fail(exc)
            logger.exception("Events email send failed")
            return False

        stage.succeed()
        logger.info("  Email sent.")
        return True


def _record_retry(stage: StageMonitor) -> None:
    stage.add_retry()
    stage.add_backoff()
