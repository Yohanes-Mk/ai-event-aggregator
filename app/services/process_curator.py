from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import repository
from agent import curator_agent


def process_curator(db: Session) -> None:
    print("=== Curator: Top 10 for Yohannes ===")

    digests = repository.get_recent_digests(db, hours=24)
    if not digests:
        print("  No digests in the last 24 hours.\n")
        return

    print(f"  Ranking {len(digests)} item(s)...\n")

    try:
        result = curator_agent.run(digests)
    except Exception as e:
        print(f"  Error: {e}\n")
        return

    seen = set()
    rank = 1
    for article in result.ranked_articles:
        if article.article_id in seen:
            continue
        seen.add(article.article_id)
        print(f"  {rank}. [score: {article.score}] {article.title}")
        print(f"     {article.ranking_reason}")
        print()
        rank += 1
