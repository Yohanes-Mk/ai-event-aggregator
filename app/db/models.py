from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"

    video_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    channel_name = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)


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


from app.monitoring import models as _monitoring_models  # noqa: E402,F401
