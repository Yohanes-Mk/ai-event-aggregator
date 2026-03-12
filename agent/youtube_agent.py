from __future__ import annotations

import os
from openai import OpenAI
from pydantic import BaseModel

from app.db.models import YouTubeVideo

MODEL_NAME = "gpt-4o-mini"
PROMPT_VERSION = "youtube-digest-v1"


class YouTubeDigestResult(BaseModel):
    title: str
    summary: str
    tools_concepts: str


_SYSTEM_PROMPT = (
    "You are a tech content curator. Extract the core insight, "
    "tools mentioned, and why a software engineer should care. Be specific."
)


def run(video: YouTubeVideo) -> YouTubeDigestResult:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    prompt = (
        f"Channel: {video.channel_name}\n"
        f"Title: {video.title}\n\n"
        f"Transcript:\n{video.transcript or '(no transcript available)'}"
    )

    response = client.beta.chat.completions.parse(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=YouTubeDigestResult,
        temperature=0.7,
    )
    return response.choices[0].message.parsed
