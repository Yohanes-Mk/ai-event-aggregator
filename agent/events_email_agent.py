from __future__ import annotations

import os
from openai import OpenAI
from pydantic import BaseModel

from app.db.models import Event


class EventSection(BaseModel):
    event_key: str       # "{title}||{start_time}" — used to pin URL from DB after generation
    title: str
    date_time: str       # e.g. "Wednesday, March 19 · 6:30 – 8:30 PM"
    location: str
    summary: str
    relevance_score: int
    ranking_reason: str
    url: str


class EventsEmailResult(BaseModel):
    subject: str
    greeting: str
    introduction: str
    events: list[EventSection]
    signature: str


_SYSTEM_PROMPT = (
    "You are a personal AI content assistant writing a tech events digest email for Yohannes. "
    "Write a friendly greeting and 1-2 sentence introduction. "
    "For each event: format date_time as 'Weekday, Month DD · HH:MM – HH:MM timezone'. "
    "Keep summary to 2-3 specific sentences about what the event is and why it's worth attending. "
    "Keep ranking_reason to one sharp sentence. "
    "Write a warm, brief signature."
)


def run(events: list[Event]) -> EventsEmailResult:
    """Generate a structured tech events digest email for the next 14 days."""
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    items = []
    for e in events:
        url = e.urls[0] if e.urls else ""
        location = e.location or "Online / TBD"
        end_str = e.end_time.strftime("%H:%M UTC") if e.end_time else ""
        time_str = e.start_time.strftime("%A, %B %d · %H:%M UTC")
        if end_str:
            time_str += f" – {end_str}"
        event_key = f"{e.title}||{e.start_time.isoformat()}"
        items.append(
            f"event_key: {event_key}\n"
            f"title: {e.title}\n"
            f"when: {time_str}\n"
            f"location: {location}\n"
            f"relevance_score: {e.relevance_score}\n"
            f"summary: {e.summary or 'N/A'}\n"
            f"url: {url}"
        )

    prompt = (
        "Generate a structured tech events digest email for Yohannes covering these upcoming events "
        "(DC/Baltimore area, next 14 days):\n\n"
        + "\n\n---\n\n".join(items)
    )

    response = client.responses.parse(
        model="gpt-4o-mini",
        instructions=_SYSTEM_PROMPT,
        input=prompt,
        text_format=EventsEmailResult,
    )
    return response.output_parsed
