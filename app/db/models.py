from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"

    video_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    channel_name = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)


class YouTubeVideoClassification(Base):
    __tablename__ = "youtube_video_classifications"

    video_id = Column(String, primary_key=True)
    is_short = Column(Boolean, nullable=False)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class Event(Base):
    __tablename__ = "events"

    # Natural key: title + start_time
    title = Column(String, primary_key=True, nullable=False)
    start_time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)
    urls = Column(ARRAY(Text), nullable=False, default=list)
    sources = Column(ARRAY(Text), nullable=False, default=list)
    summary = Column(Text, nullable=True)
    relevance_score = Column(Integer, nullable=True)  # 0-100, AI-rated for AI engineers


class Digest(Base):
    __tablename__ = "digests"

    # Composite PK: article_id + article_type (enables upsert via db.merge)
    article_id = Column(String, primary_key=True, nullable=False)
    article_type = Column(String, primary_key=True, nullable=False)  # "youtube" | "event"
    url = Column(String, nullable=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    tools_concepts = Column(Text, nullable=True)
    source = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False)
    digest_version = Column(Integer, nullable=False, default=1)
    digest_generated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    source_updated_at = Column(DateTime(timezone=True), nullable=True)
    content_last_seen_at = Column(DateTime(timezone=True), nullable=True)
    model_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)


class CuratorRun(Base):
    __tablename__ = "curator_runs"

    id = Column(Integer, primary_key=True)
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    model_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    notes = Column(Text, nullable=True)


class CuratorRanking(Base):
    __tablename__ = "curator_rankings"

    id = Column(Integer, primary_key=True)
    curator_run_id = Column(Integer, ForeignKey("curator_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(String, nullable=False, index=True)
    article_type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    rank_position = Column(Integer, nullable=False)
    ranking_reason = Column(Text, nullable=False)
    digest_version = Column(Integer, nullable=True)
    digest_generated_at = Column(DateTime(timezone=True), nullable=True)


from app.monitoring import models as _monitoring_models  # noqa: E402,F401
