from __future__ import annotations

import os
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel

from app.db.models import Digest


_USER_CONTEXT = (Path(__file__).parent.parent / "docs" / "user_context.md").read_text()

_SYSTEM_PROMPT = f"""You are a personal content curator.

{_USER_CONTEXT}

You will receive a list of content items (YouTube videos and events).
Score each item 0-100 based on how relevant and valuable it is for this person.
Select the top 10 items, ranked highest score first.
For each, provide a brief ranking_reason explaining why it scored that way."""


class RankedArticle(BaseModel):
    article_id: str
    article_type: str
    title: str
    summary: str
    score: int
    ranking_reason: str


class CuratorResult(BaseModel):
    ranked_articles: list[RankedArticle]


def run(digests: list[Digest]) -> CuratorResult:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    items = []
    for d in digests:
        item = (
            f"article_id: {d.article_id}\n"
            f"type: {d.article_type}\n"
            f"Title: {d.title}\n"
            f"Summary: {d.summary}\n"
        )
        if d.tools_concepts:
            item += f"Tools/Concepts: {d.tools_concepts}\n"
        items.append(item)

    prompt = "Here are today's content items to rank:\n\n" + "\n---\n".join(items)

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=CuratorResult,
        temperature=0.3,
    )
    return response.choices[0].message.parsed
