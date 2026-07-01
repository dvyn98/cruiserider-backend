"""
Database Models - AI-Generated Articles / Blog Posts
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String, ForeignKey("videos.id"), nullable=True)  # Linked video
    title = Column(String(500), nullable=False)
    slug = Column(String(600), unique=True, nullable=False, index=True)  # URL slug
    excerpt = Column(Text)               # Short summary for cards
    content = Column(Text, nullable=False)  # Full HTML content
    meta_description = Column(String(300))  # SEO meta description
    meta_keywords = Column(JSON, default=list)  # SEO keywords list
    cover_image_url = Column(String(1000))
    author = Column(String(100), default="Priyanshu")
    category = Column(String(100))       # "Review", "News", "Comparison", "Guide"
    car_brand = Column(String(100))
    car_model = Column(String(100))
    tags = Column(JSON, default=list)
    is_published = Column(Boolean, default=False)
    is_ai_generated = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    read_time_minutes = Column(Integer, default=5)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime, nullable=True)
