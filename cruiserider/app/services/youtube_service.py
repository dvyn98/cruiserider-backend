"""
YouTube Service - Fetches videos from Priyanshu's channel via YouTube Data API v3

HOW TO GET API KEY:
1. Go to console.cloud.google.com
2. Create new project "CruiseRider"
3. Enable "YouTube Data API v3"
4. Go to Credentials → Create API Key
5. Paste in .env as YOUTUBE_API_KEY=...

HOW TO GET CHANNEL ID:
- Go to youtube.com/@CruiseRider (Priyanshu's channel)
- View page source → search for "channelId"
- Or use: https://www.youtube.com/channel/CHANNEL_ID_HERE
"""

import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

YOUTUBE_BASE_URL = "https://www.googleapis.com/youtube/v3"


async def fetch_channel_videos(max_results: int = 50, page_token: Optional[str] = None) -> Dict:
    """
    Fetch latest videos from Priyanshu's YouTube channel.
    Returns list of video items + nextPageToken for pagination.
    
    YouTube Data API v3 - Search endpoint
    Quota cost: 100 units per call (daily limit: 10,000 units free)
    """
    if not settings.YOUTUBE_API_KEY:
        logger.warning("⚠️  YOUTUBE_API_KEY not set in .env")
        return {"items": [], "nextPageToken": None}

    params = {
        "part": "snippet",
        "channelId": settings.YOUTUBE_CHANNEL_ID,
        "maxResults": min(max_results, 50),  # API max is 50
        "order": "date",                      # Latest first
        "type": "video",
        "key": settings.YOUTUBE_API_KEY,
    }
    if page_token:
        params["pageToken"] = page_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Search for video IDs
        search_resp = await client.get(f"{YOUTUBE_BASE_URL}/search", params=params)
        search_resp.raise_for_status()
        search_data = search_resp.json()

        video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
        if not video_ids:
            return {"items": [], "nextPageToken": None}

        # Step 2: Get full details for those video IDs (stats + duration)
        details_resp = await client.get(
            f"{YOUTUBE_BASE_URL}/videos",
            params={
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(video_ids),
                "key": settings.YOUTUBE_API_KEY,
            },
        )
        details_resp.raise_for_status()
        details = details_resp.json()

        return {
            "items": details.get("items", []),
            "nextPageToken": search_data.get("nextPageToken"),
        }


def parse_youtube_video(item: Dict[str, Any]) -> Dict:
    """
    Normalize a raw YouTube API video item into our DB format.
    """
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content_details = item.get("contentDetails", {})

    # Pick best thumbnail
    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = (
        thumbnails.get("maxres", {}).get("url")
        or thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or ""
    )

    # Parse published date
    published_raw = snippet.get("publishedAt", "")
    try:
        published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
    except Exception:
        published_at = None

    title = snippet.get("title", "")
    description = snippet.get("description", "")
    tags = snippet.get("tags", [])

    # Simple car brand/model extraction from title
    car_brand, car_model = extract_car_info_from_title(title)

    return {
        "youtube_video_id": item.get("id", ""),
        "title": title,
        "description": description,
        "thumbnail_url": thumbnail_url,
        "published_at": published_at,
        "duration": content_details.get("duration", ""),
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
        "comment_count": int(stats.get("commentCount", 0)),
        "tags": tags,
        "car_brand": car_brand,
        "car_model": car_model,
    }


def extract_car_info_from_title(title: str):
    """
    Basic extraction of car brand/model from video title.
    Extend this list as Priyanshu's content grows.
    Later: replace with Claude AI extraction.
    """
    title_lower = title.lower()
    
    brand_keywords = {
        "mahindra": ["thar", "scorpio", "xuv", "bolero", "be6", "be 6", "be9"],
        "tata": ["nexon", "harrier", "safari", "punch", "altroz", "curvv", "sierra"],
        "maruti": ["brezza", "ertiga", "grand vitara", "jimny", "swift", "baleno"],
        "hyundai": ["creta", "venue", "alcazar", "tucson", "exter", "i20"],
        "kia": ["seltos", "sonet", "carens", "ev6", "syros"],
        "toyota": ["fortuner", "innova", "hyryder", "camry", "urban cruiser"],
        "honda": ["city", "amaze", "elevate", "wr-v"],
        "mgmotor": ["hector", "astor", "gloster", "zs ev", "windsor"],
        "jeep": ["compass", "meridian", "wrangler", "grand cherokee"],
        "ford": ["endeavour", "ecosport", "mustang"],
        "volkswagen": ["taigun", "virtus", "tiguan"],
        "skoda": ["kushaq", "slavia", "kodiaq", "superb"],
        "renault": ["kwid", "kiger", "triber", "duster"],
        "nissan": ["magnite", "kicks", "x-trail"],
    }

    for brand, models in brand_keywords.items():
        if brand in title_lower:
            for model in models:
                if model in title_lower:
                    return brand.capitalize(), model.capitalize()
            return brand.capitalize(), None

    return None, None


async def fetch_video_by_id(video_id: str) -> Optional[Dict]:
    """Fetch a single YouTube video by its ID"""
    if not settings.YOUTUBE_API_KEY:
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{YOUTUBE_BASE_URL}/videos",
            params={
                "part": "snippet,contentDetails,statistics",
                "id": video_id,
                "key": settings.YOUTUBE_API_KEY,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        return items[0] if items else None


async def get_channel_stats() -> Dict:
    """Get channel-level stats (subscribers, total views, video count)"""
    if not settings.YOUTUBE_API_KEY or not settings.YOUTUBE_CHANNEL_ID:
        return {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{YOUTUBE_BASE_URL}/channels",
            params={
                "part": "snippet,statistics,brandingSettings",
                "id": settings.YOUTUBE_CHANNEL_ID,
                "key": settings.YOUTUBE_API_KEY,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return {}
        
        stats = items[0].get("statistics", {})
        return {
            "subscriber_count": int(stats.get("subscriberCount", 0)),
            "view_count": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
        }
