from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel

from app.db.models import Digest

MODEL_NAME = "gpt-4o-mini"
PROMPT_VERSION = "curator-v1"


USER_CONTEXT_PATH = Path(__file__).parent.parent / "docs" / "user_context.md"
CONTEXT_SNAPSHOTS_DIR = Path(__file__).parent.parent / "docs" / "context_snapshots"


class RankedArticle(BaseModel):
    article_id: str
    article_type: str
    title: str
    summary: str
    score: int
    ranking_reason: str


class CuratorResult(BaseModel):
    ranked_articles: list[RankedArticle]


def load_user_context() -> str:
    return USER_CONTEXT_PATH.read_text(encoding="utf-8")


def save_user_context(value: str) -> None:
    USER_CONTEXT_PATH.write_text(value.rstrip() + "\n", encoding="utf-8")


def snapshot_user_context(value: str | None = None, *, label: str | None = None) -> Path:
    context = value if value is not None else load_user_context()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    suffix = _slugify(label) if label else "snapshot"
    CONTEXT_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = CONTEXT_SNAPSHOTS_DIR / f"{timestamp}_{suffix}.md"
    rendered = (
        f"# User Context Snapshot\n\n"
        f"- Saved at (UTC): {datetime.now(timezone.utc).isoformat()}\n"
        f"- Source: `docs/user_context.md`\n"
        f"- Label: {label or 'snapshot'}\n\n"
        f"---\n\n"
        f"{context.rstrip()}\n"
    )
    path.write_text(rendered, encoding="utf-8")
    return path


def build_system_prompt() -> str:
    user_context = load_user_context()
    return f"""You are a personal content curator.

{user_context}

You will receive a list of content items (YouTube videos and events).
Score each item 0-100 based on how relevant and valuable it is for this person.
Select the top 10 items, ranked highest score first.
For each, provide a brief ranking_reason explaining why it scored that way."""


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
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": prompt},
        ],
        response_format=CuratorResult,
        temperature=0.3,
    )
    return response.choices[0].message.parsed


def _slugify(value: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    compact = "-".join(part for part in normalized.split("-") if part)
    return compact or "snapshot"
