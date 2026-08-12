"""
YouTube Service
---------------
Responsible only for communication with the YouTube Data API
and normalization of YouTube data for Cruise Rider.

Responsibilities:
    - Get channel uploads playlist
    - Fetch channel videos using uploads playlist pagination
    - Fetch a single video
    - Get channel statistics
    - Parse YouTube video data
    - Extract basic car information from title
    - Convert YouTube ISO 8601 duration to seconds

The service does NOT decide which videos Cruise Rider stores.
That business logic belongs in sync.py.
"""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)

YOUTUBE_BASE_URL = "https://www.googleapis.com/youtube/v3"


# ============================================================
# DURATION HELPERS
# ============================================================

def duration_to_seconds(duration: str) -> int:
    """
    Convert YouTube ISO 8601 duration into seconds.

    Examples:
        PT30S       -> 30
        PT3M20S     -> 200
        PT1H5M10S   -> 3910
    """

    if not duration:
        return 0

    match = re.match(
        r"PT"
        r"(?:(\d+)H)?"
        r"(?:(\d+)M)?"
        r"(?:(\d+)S)?",
        duration
    )

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


# ============================================================
# CHANNEL → UPLOADS PLAYLIST
# ============================================================

async def get_uploads_playlist_id() -> Optional[str]:
    """
    Get the uploads playlist ID for the configured YouTube channel.

    Every YouTube channel has an uploads playlist containing
    the videos uploaded by that channel.

    This is preferable to the Search API for Cruise Rider's
    historical video import.
    """

    if not settings.YOUTUBE_API_KEY:
        logger.warning(
            "YOUTUBE_API_KEY not set in .env"
        )
        return None

    if not settings.YOUTUBE_CHANNEL_ID:
        logger.warning(
            "YOUTUBE_CHANNEL_ID not set in .env"
        )
        return None

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        response = await client.get(
            f"{YOUTUBE_BASE_URL}/channels",
            params={
                "part": "contentDetails",
                "id": settings.YOUTUBE_CHANNEL_ID,
                "key": settings.YOUTUBE_API_KEY,
            },
        )

        response.raise_for_status()

        data = response.json()

        items = data.get("items", [])

        if not items:

            logger.warning(
                "YouTube channel not found: %s",
                settings.YOUTUBE_CHANNEL_ID
            )

            return None

        uploads_playlist_id = (
            items[0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )

        logger.info(
            "YouTube uploads playlist ID: %s",
            uploads_playlist_id
        )

        return uploads_playlist_id


# ============================================================
# FETCH CHANNEL VIDEOS
# ============================================================

async def fetch_channel_videos(
    max_results: int = 50,
    page_token: Optional[str] = None
) -> Dict:
    """
    Fetch videos from the channel's uploads playlist.

    This function supports pagination.

    max_results:
        Maximum 50 per YouTube API request.

    page_token:
        Token returned from the previous request.

    Returns:

        {
            "items": [...],
            "nextPageToken": "..."
        }

    The returned items contain:
        - snippet
        - contentDetails
        - statistics
    """

    if not settings.YOUTUBE_API_KEY:
        logger.warning(
            "YOUTUBE_API_KEY not set in .env"
        )

        return {
            "items": [],
            "nextPageToken": None
        }

    # --------------------------------------------------------
    # Get channel uploads playlist
    # --------------------------------------------------------

    uploads_playlist_id = await get_uploads_playlist_id()

    if not uploads_playlist_id:

        return {
            "items": [],
            "nextPageToken": None
        }

    params = {
        "part": "snippet,contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": min(max_results, 50),
        "key": settings.YOUTUBE_API_KEY,
    }

    if page_token:
        params["pageToken"] = page_token

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        # ----------------------------------------------------
        # STEP 1
        # Get videos from uploads playlist
        # ----------------------------------------------------

        playlist_response = await client.get(
            f"{YOUTUBE_BASE_URL}/playlistItems",
            params=params
        )

        playlist_response.raise_for_status()

        playlist_data = playlist_response.json()

        playlist_items = playlist_data.get(
            "items",
            []
        )

        video_ids = []

        for item in playlist_items:

            video_id = (
                item
                .get("contentDetails", {})
                .get("videoId")
            )

            if video_id:
                video_ids.append(video_id)

        next_page_token = playlist_data.get(
            "nextPageToken"
        )

        logger.info(
            "Uploads playlist returned %s videos | nextPageToken=%s",
            len(video_ids),
            next_page_token
        )

        # ----------------------------------------------------
        # No videos
        # ----------------------------------------------------

        if not video_ids:

            return {
                "items": [],
                "nextPageToken": None
            }

        # ----------------------------------------------------
        # STEP 2
        # Get full details
        #
        # snippet
        # contentDetails → duration
        # statistics → views/likes/comments
        # ----------------------------------------------------

        details_response = await client.get(
            f"{YOUTUBE_BASE_URL}/videos",
            params={
                "part": (
                    "snippet,"
                    "contentDetails,"
                    "statistics"
                ),
                "id": ",".join(video_ids),
                "key": settings.YOUTUBE_API_KEY,
            },
        )

        details_response.raise_for_status()

        details = details_response.json()

        items = details.get(
            "items",
            []
        )

        logger.info(
            "YouTube details returned %s videos",
            len(items)
        )

        return {
            "items": items,
            "nextPageToken": next_page_token
        }


# ============================================================
# PARSE YOUTUBE VIDEO
# ============================================================

def parse_youtube_video(
    item: Dict[str, Any]
) -> Dict:
    """
    Normalize a raw YouTube API video item
    into the Cruise Rider database format.
    """

    snippet = item.get(
        "snippet",
        {}
    )

    stats = item.get(
        "statistics",
        {}
    )

    content_details = item.get(
        "contentDetails",
        {}
    )

    # --------------------------------------------------------
    # Thumbnail
    # --------------------------------------------------------

    thumbnails = snippet.get(
        "thumbnails",
        {}
    )

    thumbnail_url = (
        thumbnails.get(
            "maxres",
            {}
        ).get("url")

        or thumbnails.get(
            "high",
            {}
        ).get("url")

        or thumbnails.get(
            "medium",
            {}
        ).get("url")

        or thumbnails.get(
            "default",
            {}
        ).get("url")

        or ""
    )

    # --------------------------------------------------------
    # Published date
    # --------------------------------------------------------

    published_raw = snippet.get(
        "publishedAt",
        ""
    )

    try:

        published_at = datetime.fromisoformat(
            published_raw.replace(
                "Z",
                "+00:00"
            )
        )

    except Exception:

        published_at = None

    # --------------------------------------------------------
    # Basic metadata
    # --------------------------------------------------------

    title = snippet.get(
        "title",
        ""
    )

    description = snippet.get(
        "description",
        ""
    )

    tags = snippet.get(
        "tags",
        []
    )

    duration = content_details.get(
        "duration",
        ""
    )

    # --------------------------------------------------------
    # Car extraction
    # --------------------------------------------------------

    car_brand, car_model = (
        extract_car_info_from_title(
            title
        )
    )

    # --------------------------------------------------------
    # Return normalized object
    # --------------------------------------------------------

    return {

        "youtube_video_id": item.get(
            "id",
            ""
        ),

        "title": title,

        "description": description,

        "thumbnail_url": thumbnail_url,

        "published_at": published_at,

        "duration": duration,

        "view_count": int(
            stats.get(
                "viewCount",
                0
            )
        ),

        "like_count": int(
            stats.get(
                "likeCount",
                0
            )
        ),

        "comment_count": int(
            stats.get(
                "commentCount",
                0
            )
        ),

        "tags": tags,

        "car_brand": car_brand,

        "car_model": car_model,
    }


# ============================================================
# CAR BRAND / MODEL EXTRACTION
# ============================================================

def extract_car_info_from_title(
    title: str
):
    """
    Basic extraction of car brand/model from
    the YouTube video title.

    This is intentionally simple.

    Later we can replace this with an AI-based
    extraction pipeline.
    """

    title_lower = title.lower()

    brand_keywords = {

        "mahindra": [
            "thar",
            "scorpio",
            "xuv",
            "bolero",
            "be6",
            "be 6",
            "be9",
        ],

        "tata": [
            "nexon",
            "harrier",
            "safari",
            "punch",
            "altroz",
            "curvv",
            "sierra",
        ],

        "maruti": [
            "brezza",
            "ertiga",
            "grand vitara",
            "jimny",
            "swift",
            "baleno",
            "dzire",
            "wagonr",
            "wagon r",
            "xl6",
        ],

        "hyundai": [
            "creta",
            "venue",
            "alcazar",
            "tucson",
            "exter",
            "i20",
        ],

        "kia": [
            "seltos",
            "sonet",
            "carens",
            "ev6",
            "syros",
        ],

        "toyota": [
            "fortuner",
            "innova",
            "hyryder",
            "camry",
            "urban cruiser",
        ],

        "honda": [
            "city",
            "amaze",
            "elevate",
            "wr-v",
        ],

        "mgmotor": [
            "hector",
            "astor",
            "gloster",
            "zs ev",
            "windsor",
        ],

        "jeep": [
            "compass",
            "meridian",
            "wrangler",
            "grand cherokee",
        ],

        "ford": [
            "endeavour",
            "ecosport",
            "mustang",
        ],

        "volkswagen": [
            "taigun",
            "virtus",
            "tiguan",
        ],

        "skoda": [
            "kushaq",
            "slavia",
            "kodiaq",
            "superb",
        ],

        "renault": [
            "kwid",
            "kiger",
            "triber",
            "duster",
        ],

        "nissan": [
            "magnite",
            "kicks",
            "x-trail",
        ],
    }

    for brand, models in brand_keywords.items():

        if brand in title_lower:

            for model in models:

                if model in title_lower:

                    return (
                        brand.capitalize(),
                        model.capitalize()
                    )

            return (
                brand.capitalize(),
                None
            )

        # ----------------------------------------------------
        # Some titles only contain the model name.
        # Example:
        # "New Maruti Dzire..."
        #
        # We also check model names independently.
        # ----------------------------------------------------

        for model in models:

            if model in title_lower:

                return (
                    brand.capitalize(),
                    model.capitalize()
                )

    return None, None


# ============================================================
# FETCH SINGLE VIDEO
# ============================================================

async def fetch_video_by_id(
    video_id: str
) -> Optional[Dict]:
    """
    Fetch a single YouTube video by ID.

    Returns the raw YouTube API object.
    """

    if not settings.YOUTUBE_API_KEY:

        logger.warning(
            "YOUTUBE_API_KEY not set"
        )

        return None

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        response = await client.get(
            f"{YOUTUBE_BASE_URL}/videos",
            params={
                "part": (
                    "snippet,"
                    "contentDetails,"
                    "statistics"
                ),
                "id": video_id,
                "key": settings.YOUTUBE_API_KEY,
            },
        )

        response.raise_for_status()

        data = response.json()

        items = data.get(
            "items",
            []
        )

        if not items:
            return None

        return items[0]


# ============================================================
# CHANNEL STATISTICS
# ============================================================

async def get_channel_stats() -> Dict:
    """
    Get YouTube channel-level statistics.

    Returns:
        subscriber_count
        view_count
        video_count
    """

    if not settings.YOUTUBE_API_KEY:

        logger.warning(
            "YOUTUBE_API_KEY not set"
        )

        return {}

    if not settings.YOUTUBE_CHANNEL_ID:

        logger.warning(
            "YOUTUBE_CHANNEL_ID not set"
        )

        return {}

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        response = await client.get(
            f"{YOUTUBE_BASE_URL}/channels",
            params={
                "part": (
                    "snippet,"
                    "statistics,"
                    "brandingSettings"
                ),
                "id": settings.YOUTUBE_CHANNEL_ID,
                "key": settings.YOUTUBE_API_KEY,
            },
        )

        response.raise_for_status()

        data = response.json()

        items = data.get(
            "items",
            []
        )

        if not items:
            return {}

        stats = items[0].get(
            "statistics",
            {}
        )

        return {

            "subscriber_count": int(
                stats.get(
                    "subscriberCount",
                    0
                )
            ),

            "view_count": int(
                stats.get(
                    "viewCount",
                    0
                )
            ),

            "video_count": int(
                stats.get(
                    "videoCount",
                    0
                )
            ),
        }