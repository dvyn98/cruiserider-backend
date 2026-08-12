"""
Sync API - Admin endpoints for YouTube, Instagram and AI generation.

All mutating sync operations require an authenticated admin user.
"""

import logging
import re
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.models.video import Video
from app.models.instagram import InstagramPost
from app.models.article import Article
from app.models.users import User

from app.security.dependencies import get_current_admin

from app.services.youtube_service import (
    fetch_channel_videos,
    parse_youtube_video,
    get_channel_stats,
    duration_to_seconds
)
from app.services.instagram_service import fetch_instagram_posts
from app.services.ai_service import generate_article_from_video

from app.schemas.video import VideoStatus


logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# YOUTUBE SYNC
# ============================================================

@router.post("/youtube")
async def sync_youtube_videos(
    background_tasks: BackgroundTasks,
    max_pages: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Sync long-form videos from YouTube.

    max_pages:
        None -> sync entire channel
        N    -> sync N YouTube pages

    Each YouTube page contains up to 50 videos.

    Videos <= 3 minutes are skipped.
    """

    if max_pages is not None and max_pages < 1:
        raise HTTPException(
            status_code=400,
            detail="max_pages must be greater than 0"
        )

    background_tasks.add_task(
        _sync_youtube_background,
        db,
        max_pages
    )

    return {
        "message": "YouTube sync started in background",
        "status": "processing",
        "max_pages": max_pages,
    }


async def _sync_youtube_background(
    db: AsyncSession,
    max_pages: Optional[int]
):
    """
    Synchronize all long-form YouTube videos.

    Pagination:
        Page 1 → Page 2 → Page 3 → ... → last page

    Short videos are skipped.
    Existing videos have their YouTube metadata refreshed.
    """

    try:

        page_token = None
        pages_processed = 0

        created = 0
        updated = 0
        skipped_short = 0
        skipped_invalid = 0

        while True:

            # ------------------------------------------------
            # FETCH ONE PAGE FROM YOUTUBE
            # ------------------------------------------------

            data = await fetch_channel_videos(
                max_results=50,
                page_token=page_token
            )

            items = data.get("items", [])

            if not items:
                break

            pages_processed += 1

            logger.info(
                "Processing YouTube page %s | videos=%s",
                pages_processed,
                len(items)
            )

            # ------------------------------------------------
            # PROCESS VIDEOS
            # ------------------------------------------------

            for item in items:

                parsed = parse_youtube_video(item)

                youtube_video_id = parsed.get(
                    "youtube_video_id"
                )

                published_at = parsed.get(
                    "published_at"
                )

                if not youtube_video_id or not published_at:
                    skipped_invalid += 1
                    continue

                # ------------------------------------------------
                # LONG FORM FILTER
                # ------------------------------------------------

                duration_seconds = duration_to_seconds(
                    parsed.get("duration", "")
                )

                # <= 3 minutes = skip
                if duration_seconds <= 180:

                    skipped_short += 1

                    logger.debug(
                        "Skipping short video: %s | duration=%ss",
                        parsed["title"][:60],
                        duration_seconds
                    )

                    continue

                # ------------------------------------------------
                # CHECK IF VIDEO ALREADY EXISTS
                # ------------------------------------------------

                result = await db.execute(
                    select(Video).where(
                        Video.youtube_video_id
                        == youtube_video_id
                    )
                )

                existing = result.scalar_one_or_none()

                # ------------------------------------------------
                # EXISTING VIDEO → UPDATE YOUTUBE METADATA
                # ------------------------------------------------

                if existing:

                    existing.title = parsed["title"]
                    existing.description = parsed["description"]
                    existing.thumbnail_url = parsed["thumbnail_url"]
                    existing.published_at = parsed["published_at"]
                    existing.duration = parsed["duration"]

                    # Important:
                    # These values can change over time.
                    existing.view_count = parsed["view_count"]
                    existing.like_count = parsed["like_count"]
                    existing.comment_count = parsed["comment_count"]

                    existing.tags = parsed["tags"]

                    # These may change if our extraction improves.
                    existing.car_brand = parsed["car_brand"]
                    existing.car_model = parsed["car_model"]

                    updated += 1

                    continue

                # ------------------------------------------------
                # NEW VIDEO → INSERT
                # ------------------------------------------------

                video = Video(
                    **parsed,
                    status=VideoStatus.DRAFT.value
                )

                db.add(video)

                created += 1

                logger.info(
                    "Added YouTube video: %s",
                    parsed["title"][:60]
                )

            # ------------------------------------------------
            # COMMIT THIS PAGE
            # ------------------------------------------------

            await db.commit()

            # ------------------------------------------------
            # GET NEXT PAGE
            # ------------------------------------------------

            page_token = data.get("nextPageToken")

            if not page_token:
                break

            # ------------------------------------------------
            # OPTIONAL TEST LIMIT
            # ------------------------------------------------

            if max_pages is not None and pages_processed >= max_pages:
                break

        # ----------------------------------------------------
        # FINAL SUMMARY
        # ----------------------------------------------------

        logger.info(
            "YouTube sync complete | "
            "pages=%s created=%s updated=%s "
            "skipped_short=%s skipped_invalid=%s",
            pages_processed,
            created,
            updated,
            skipped_short,
            skipped_invalid,
        )

    except Exception:

        await db.rollback()

        logger.exception(
            "YouTube sync failed"
        )


# ============================================================
# INSTAGRAM SYNC
# ============================================================

@router.post("/instagram")
async def sync_instagram_posts(
    background_tasks: BackgroundTasks,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Sync latest Instagram posts.

    Admin only.
    """

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100"
        )

    background_tasks.add_task(
        _sync_instagram_background,
        db,
        limit
    )

    return {
        "message": "Instagram sync started in background",
        "status": "processing",
    }


async def _sync_instagram_background(
    db: AsyncSession,
    limit: int
):

    try:

        posts = await fetch_instagram_posts(
            limit=limit
        )

        created = 0

        for post_data in posts:

            instagram_post_id = post_data[
                "instagram_post_id"
            ]

            result = await db.execute(
                select(InstagramPost).where(
                    InstagramPost.instagram_post_id
                    == instagram_post_id
                )
            )

            existing = result.scalar_one_or_none()

            if existing:
                continue

            post = InstagramPost(
                **post_data
            )

            db.add(post)

            created += 1

        await db.commit()

        logger.info(
            "Instagram sync complete | created=%s",
            created
        )

    except Exception:

        await db.rollback()

        logger.exception(
            "Instagram sync failed"
        )


# ============================================================
# GENERATE ARTICLE FOR ONE VIDEO
# ============================================================

@router.post("/generate-article/{video_id}")
async def generate_article_for_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Generate an AI article for a specific video.

    Admin only.
    """

    result = await db.execute(
        select(Video).where(
            Video.id == video_id
        )
    )

    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # ---------------------------------------------
    # Prevent duplicate generation
    # ---------------------------------------------

    if video.article_generated:

        return {
            "message": "Article already generated for this video",
            "video_id": video_id,
        }

    # ---------------------------------------------
    # Generate AI article
    # ---------------------------------------------

    article_data = generate_article_from_video(
        video_title=video.title,
        video_description=video.description or "",
        car_brand=video.car_brand,
        car_model=video.car_model,
        video_url=(
            f"https://www.youtube.com/watch?v="
            f"{video.youtube_video_id}"
        ),
    )

    if not article_data:

        raise HTTPException(
            status_code=500,
            detail=(
                "AI article generation failed. "
                "Check ANTHROPIC_API_KEY."
            ),
        )

    # ---------------------------------------------
    # Generate safe slug
    # ---------------------------------------------

    slug = article_data.get(
        "slug",
        ""
    )

    slug = re.sub(
        r"[^a-z0-9-]",
        "",
        slug.lower().replace(" ", "-")
    )

    if not slug:

        slug = (
            re.sub(
                r"[^a-z0-9-]",
                "",
                video.title.lower().replace(" ", "-")
            )
        )

    # ---------------------------------------------
    # Ensure unique slug
    # ---------------------------------------------

    result = await db.execute(
        select(Article).where(
            Article.slug == slug
        )
    )

    existing_article = (
        result.scalar_one_or_none()
    )

    if existing_article:

        slug = (
            f"{slug}-"
            f"{video.youtube_video_id[:6]}"
        )

    # ---------------------------------------------
    # Create article
    # ---------------------------------------------

    article = Article(
        video_id=video.id,
        title=article_data["title"],
        slug=slug,
        excerpt=article_data.get(
            "excerpt",
            ""
        ),
        content=article_data["content"],
        meta_description=article_data.get(
            "meta_description",
            ""
        ),
        meta_keywords=article_data.get(
            "tags",
            []
        ),
        cover_image_url=video.thumbnail_url,
        category=video.category or "Review",
        car_brand=video.car_brand,
        car_model=video.car_model,
        tags=article_data.get(
            "tags",
            []
        ),
        read_time_minutes=article_data.get(
            "read_time_minutes",
            5
        ),
        is_published=False,
        is_ai_generated=True,
    )

    db.add(article)

    video.article_generated = True

    await db.commit()

    await db.refresh(article)

    return {
        "success": True,
        "article_id": article.id,
        "title": article.title,
        "slug": article.slug,
        "message": (
            "Article generated! "
            "Review in admin panel then publish."
        ),
    }


# ============================================================
# CHANNEL STATS
# ============================================================

@router.get("/channel-stats")
async def get_youtube_channel_stats(
    current_admin: User = Depends(get_current_admin),
):
    """
    Get YouTube channel statistics.

    Admin only.
    """

    return await get_channel_stats()


# ============================================================
# GENERATE ALL ARTICLES
# ============================================================

@router.post("/generate-all-articles")
async def generate_articles_for_all_videos(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Generate articles for all published videos
    that don't already have an article.

    Admin only.
    """

    background_tasks.add_task(
        _generate_all_articles_background,
        db
    )

    return {
        "message": (
            "Bulk article generation "
            "started in background"
        ),
        "status": "processing",
    }


async def _generate_all_articles_background(
    db: AsyncSession
):

    try:

        result = await db.execute(
            select(Video).where(
                Video.article_generated == False,
                Video.status == VideoStatus.PUBLISHED.value,
            )
        )

        videos = result.scalars().all()

        logger.info(
            "Generating articles for %s videos",
            len(videos)
        )

        generated = 0
        failed = 0

        for video in videos:

            try:

                article_data = (
                    generate_article_from_video(
                        video_title=video.title,
                        video_description=(
                            video.description or ""
                        ),
                        car_brand=video.car_brand,
                        car_model=video.car_model,
                        video_url=(
                            f"https://www.youtube.com/watch?v="
                            f"{video.youtube_video_id}"
                        ),
                    )
                )

                if not article_data:
                    failed += 1
                    continue

                slug = re.sub(
                    r"[^a-z0-9-]",
                    "",
                    article_data.get(
                        "slug",
                        ""
                    ).lower()
                )

                slug = (
                    f"{slug}-"
                    f"{video.youtube_video_id[:6]}"
                )

                article = Article(
                    video_id=video.id,
                    title=article_data["title"],
                    slug=slug,
                    excerpt=article_data.get(
                        "excerpt",
                        ""
                    ),
                    content=article_data["content"],
                    meta_description=article_data.get(
                        "meta_description",
                        ""
                    ),
                    meta_keywords=article_data.get(
                        "tags",
                        []
                    ),
                    tags=article_data.get(
                        "tags",
                        []
                    ),
                    cover_image_url=video.thumbnail_url,
                    category=video.category or "Review",
                    car_brand=video.car_brand,
                    car_model=video.car_model,
                    read_time_minutes=article_data.get(
                        "read_time_minutes",
                        5
                    ),
                    is_published=False,
                    is_ai_generated=True,
                )

                db.add(article)

                video.article_generated = True

                await db.commit()

                generated += 1

                logger.info(
                    "Article generated: %s",
                    article_data["title"][:60]
                )

            except Exception:

                failed += 1

                await db.rollback()

                logger.exception(
                    "Failed to generate article "
                    "for video %s",
                    video.id
                )

        logger.info(
            "Bulk article generation complete | "
            "generated=%s failed=%s",
            generated,
            failed,
        )

    except Exception:

        await db.rollback()

        logger.exception(
            "Bulk article generation failed"
        )