"""
Database Models - YouTube Videos
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_video_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    thumbnail_url = Column(String(1000))
    published_at = Column(DateTime)
    duration = Column(String(20))         # ISO 8601 duration e.g. PT15M30S
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    tags = Column(JSON, default=list)     # List of tags from YouTube
    category = Column(String(100))        # e.g. "Review", "Comparison", "News"
    car_brand = Column(String(100))       # Extracted: "Mahindra", "Tata"
    car_model = Column(String(100))       # Extracted: "Thar", "Nexon"
    is_featured = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)
    article_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
