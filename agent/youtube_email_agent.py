from __future__ import annotations

import os
from openai import OpenAI
from pydantic import BaseModel

from agent.curator_agent import RankedArticle

MODEL_NAME = "gpt-4o-mini"
PROMPT_VERSION = "youtube-email-v1"


class VideoSection(BaseModel):
    article_id: str   # pass-through — used to pin URL from DB after generation
    title: str
    channel_name: str
    channel_url: str
    summary: str
    tools_concepts: list[str]
    score: int
    ranking_reason: str
    url: str


class YouTubeEmailResult(BaseModel):
    subject: str
    greeting: str
    introduction: str
    articles: list[VideoSection]
    signature: str


_SYSTEM_PROMPT = (
    "You are a personal AI content assistant writing a weekly video digest email for Yohannes. "
    "Write a friendly, specific greeting and 1-2 sentence introduction. "
    "For each video: keep the summary to 2-3 specific sentences about what the video actually covers. "
    "Extract tools_concepts as a clean list of strings (e.g. ['RAG', 'pgvector', 'LangGraph']). "
    "Keep ranking_reason to one sharp sentence. "
    "Write a warm, brief signature."
)


def run(ranked_articles: list[RankedArticle], article_digests: dict[str, dict]) -> YouTubeEmailResult:
    """Generate a structured YouTube digest email.

    ranked_articles: top 10 from curator_agent
    article_digests: map of article_id -> {url, tools_concepts, channel_name, channel_id}
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    items = []
    for a in ranked_articles:
        meta = article_digests.get(a.article_id, {})
        channel_id = meta.get("channel_id", "")
        channel_url = f"https://www.youtube.com/channel/{channel_id}" if channel_id else "https://www.youtube.com"
        items.append(
            f"article_id: {a.article_id}\n"
            f"title: {a.title}\n"
            f"channel_name: {meta.get('channel_name', 'Unknown Channel')}\n"
            f"channel_url: {channel_url}\n"
            f"summary: {a.summary}\n"
            f"tools_concepts: {meta.get('tools_concepts', '')}\n"
            f"score: {a.score}\n"
            f"ranking_reason: {a.ranking_reason}\n"
            f"url: {meta.get('url', '')}"
        )

    prompt = (
        "Generate a structured YouTube digest email for Yohannes with these top 10 videos:\n\n"
        + "\n\n---\n\n".join(items)
    )

    response = client.responses.parse(
        model=MODEL_NAME,
        instructions=_SYSTEM_PROMPT,
        input=prompt,
        text_format=YouTubeEmailResult,
    )
    return response.output_parsed
