from __future__ import annotations

import os
from openai import OpenAI
from pydantic import BaseModel

from app.db.models import Event


class EventSummaryResult(BaseModel):
    summary: str
    relevance_score: int  # 0-100, how relevant for an AI/software engineer


_SYSTEM_PROMPT = (
    "You are a tech event curator. Write a 1-2 sentence summary of this event "
    "for an AI/software engineer deciding whether to attend. Be specific and concise. "
    "Also rate relevance 0-100 for an AI engineer building applied systems."
)


def run(event: Event) -> EventSummaryResult:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    urls_str = ", ".join(event.urls) if event.urls else "N/A"
    location = event.location or "Unknown"
    end_time = event.end_time.strftime("%Y-%m-%d %H:%M UTC") if event.end_time else "N/A"

    prompt = (
        f"Title: {event.title}\n"
        f"Date: {event.start_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"End: {end_time}\n"
        f"Location: {location}\n"
        f"URLs: {urls_str}\n"
        f"Sources: {', '.join(event.sources)}"
    )

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=EventSummaryResult,
        temperature=0.7,
    )
    return response.choices[0].message.parsed
