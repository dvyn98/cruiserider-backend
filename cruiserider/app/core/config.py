"""
Configuration - All settings loaded from .env file
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────
    APP_NAME: str = "CruiseRider"
    APP_ENV: str = "development"          # development | production
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ADMIN_KEY: str = "change-me-in-production"
    DEBUG: bool = True

    # ─── CORS ─────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",           # React dev server
        "http://localhost:5173",           # Vite dev server
        "https://yourdomain.com",          # Production frontend
    ]

    # ─── Database ─────────────────────────────────────────
    # SQLite for local dev; swap to PostgreSQL for production
   # DATABASE_URL: str = "sqlite+aiosqlite:///./cruiserider.db"
    # For PostgreSQL: "postgresql+asyncpg://user:password@localhost/cruiserider"
    DATABASE_URL: str="postgresql+asyncpg://postgres:Cruise%40123@localhost:5434/cruiserider"
    # ─── YouTube Data API v3 ──────────────────────────────
    # Get from: console.cloud.google.com → APIs → YouTube Data API v3
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_CHANNEL_ID: str = ""         # Priyanshu's channel ID (UC...)

    # ─── Instagram Graph API ──────────────────────────────
    # Get from: developers.facebook.com → Instagram Graph API
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_USER_ID: str = ""
    FACEBOOK_PAGE_ID: str = ""

    # ─── Anthropic / Claude AI ────────────────────────────
    # For AI blog generation from video transcripts
    ANTHROPIC_API_KEY: str = ""

    # ─── Google Cloud (optional - for GCP deployment) ─────
    GOOGLE_CLOUD_PROJECT: str = ""
    GCP_BUCKET_NAME: str = ""            # For storing media/thumbnails

    # ─── CarDekho / CarWale APIs ──────────────────────────
    # CarDekho Partner API (contact: partners@cardekho.com)
    CARDEKHO_API_KEY: str = ""
    CARDEKHO_BASE_URL: str = "https://api.cardekho.com/v1"
    
    # CarWale API (contact: api@carwale.com)  
    CARWALE_API_KEY: str = ""
    CARWALE_BASE_URL: str = "https://api.carwale.com"
    
    # Zigwheels API (free tier available)
    ZIGWHEELS_API_KEY: str = ""

    # ─── Email (for consultancy notifications) ─────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""              # Use App Password for Gmail
    NOTIFICATION_EMAIL: str = ""        # Priyanshu's email for leads

    # ─── Redis (optional - for caching) ───────────────────
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600        # 1 hour cache for car prices

    # ─── Security ─────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
