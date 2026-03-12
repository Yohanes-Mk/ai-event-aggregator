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
from agent.events_email_agent import run as generate_email

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


def _send(subject: str, html: str) -> None:
    sender = os.environ["GMAIL_SENDER"]
    recipient = os.environ["GMAIL_RECIPIENT"]
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


def process_events_email(db: Session, tracker: PipelineTracker | None = None) -> None:
    logger.info("=== Events Email Digest ===")

    with StageMonitor(tracker, "events_email") as stage:
        events = _get_upcoming_events(db)
        if not events:
            logger.info("  No events in the next 14 days. Skipping email.")
            return

        logger.info("  Found %s event(s) for the next 14 days...", len(events))
        stage.attempt()

        try:
            email_result = generate_email(events)
        except Exception as exc:
            stage.fail(exc)
            logger.exception("Events email generation failed")
            return

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
            _send(email_result.subject, html)
        except Exception as exc:
            stage.fail(exc)
            logger.exception("Events email send failed")
            return

        stage.succeed()
        logger.info("  Email sent.")
