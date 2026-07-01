"""
Instagram Service - Fetches posts via Instagram Graph API

HOW TO SET UP:
1. Go to developers.facebook.com
2. Create App → Business type
3. Add "Instagram Graph API" product
4. Connect Instagram Business Account (Priyanshu must convert to Business/Creator)
5. Generate a long-lived access token (60 days validity, then refresh)

IMPORTANT: Instagram Basic Display API was deprecated in Dec 2024.
You MUST use the Instagram Graph API with a Business/Creator account.

TOKEN REFRESH: Set up a cron job to refresh token every 50 days:
  GET https://graph.instagram.com/refresh_access_token
     ?grant_type=ig_refresh_token&access_token=YOUR_TOKEN
"""

import httpx
from typing import List, Dict, Optional, Any
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.instagram.com/v19.0"


async def fetch_instagram_posts(limit: int = 20) -> List[Dict]:
    """
    Fetch latest posts from Priyanshu's Instagram account.
    Returns normalized list of post data.
    """
    if not settings.INSTAGRAM_ACCESS_TOKEN:
        logger.warning("⚠️  INSTAGRAM_ACCESS_TOKEN not set in .env")
        return []

    fields = "id,media_type,media_url,thumbnail_url,permalink,caption,like_count,comments_count,timestamp"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{GRAPH_BASE_URL}/{settings.INSTAGRAM_USER_ID}/media",
            params={
                "fields": fields,
                "limit": limit,
                "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
            },
        )
        
        if resp.status_code == 401:
            logger.error("❌ Instagram token expired. Refresh your access token.")
            return []
        
        resp.raise_for_status()
        data = resp.json()
        return [parse_instagram_post(item) for item in data.get("data", [])]


def parse_instagram_post(item: Dict[str, Any]) -> Dict:
    """Normalize raw Instagram API response"""
    raw_ts = item.get("timestamp", "")
    try:
        timestamp = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
    except Exception:
        timestamp = None

    return {
        "instagram_post_id": item.get("id", ""),
        "media_type": item.get("media_type", "IMAGE"),
        "media_url": item.get("media_url", ""),
        "thumbnail_url": item.get("thumbnail_url", ""),
        "permalink": item.get("permalink", ""),
        "caption": item.get("caption", ""),
        "like_count": item.get("like_count", 0),
        "comments_count": item.get("comments_count", 0),
        "timestamp": timestamp,
    }


async def get_instagram_account_info() -> Dict:
    """Get basic account info (follower count, etc.)"""
    if not settings.INSTAGRAM_ACCESS_TOKEN:
        return {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{GRAPH_BASE_URL}/{settings.INSTAGRAM_USER_ID}",
            params={
                "fields": "id,username,account_type,media_count,followers_count,follows_count",
                "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
            },
        )
        if resp.status_code != 200:
            return {}
        return resp.json()


async def refresh_access_token() -> Optional[str]:
    """
    Refresh Instagram long-lived token (call every 50 days via cron).
    Returns new token or None on failure.
    """
    if not settings.INSTAGRAM_ACCESS_TOKEN:
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            "https://graph.instagram.com/refresh_access_token",
            params={
                "grant_type": "ig_refresh_token",
                "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            new_token = data.get("access_token")
            logger.info(f"✅ Instagram token refreshed. Expires in {data.get('expires_in')} seconds")
            return new_token
        else:
            logger.error(f"❌ Token refresh failed: {resp.text}")
            return None
