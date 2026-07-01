"""
Database Models - Instagram Posts (synced from Graph API)
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class InstagramPost(Base):
    __tablename__ = "instagram_posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    instagram_post_id = Column(String, unique=True, nullable=False, index=True)
    media_type = Column(String(50))          # IMAGE / VIDEO / CAROUSEL_ALBUM / REEL
    media_url = Column(String(1000))
    thumbnail_url = Column(String(1000))     # For videos/reels
    permalink = Column(String(500))          # Direct Instagram link
    caption = Column(Text)
    like_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    timestamp = Column(DateTime)             # When posted on Instagram
    created_at = Column(DateTime, server_default=func.now())
