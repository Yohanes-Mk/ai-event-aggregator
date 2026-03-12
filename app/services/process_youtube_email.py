from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.db import repository
from app.db.models import YouTubeVideo
from app.email.render import render_youtube_email
from agent import curator_agent
from agent.youtube_email_agent import run as generate_email


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


def process_youtube_email(db: Session) -> None:
    print("=== YouTube Email Digest ===")

    digests = repository.get_recent_digests(db, hours=168)  # last 7 days
    if not digests:
        print("  No digests in the last 7 days. Skipping email.\n")
        return

    print(f"  Ranking {len(digests)} item(s) for email...\n")

    try:
        curator_result = curator_agent.run(digests)
    except Exception as e:
        print(f"  Curator error: {e}\n")
        return

    # Deduplicate and take top 10
    seen: set[str] = set()
    top_10 = []
    for article in curator_result.ranked_articles:
        if article.article_id in seen:
            continue
        seen.add(article.article_id)
        top_10.append(article)

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
        }
        for d in digests
    }

    try:
        email_result = generate_email(top_10, digest_map)
    except Exception as e:
        print(f"  Email generation error: {e}\n")
        return

    # Pin URLs from DB — never trust the LLM to pass URLs through unchanged
    for section in email_result.articles:
        db_url = digest_map.get(section.article_id, {}).get("url", "")
        if db_url:
            section.url = db_url

    html = render_youtube_email(email_result)

    print(f"  Subject: {email_result.subject}\n")

    try:
        _send(email_result.subject, html)
        print("  Email sent.\n")
    except Exception as e:
        print(f"  Send error: {e}\n")
