"""
Sync API - Admin endpoints to pull data from YouTube and Instagram
These should be called:
  - Manually from Priyanshu's admin dashboard
  - Via a scheduled cron job (daily/every 6 hours)

⚠️  In production, protect these with an API key or admin auth.
"""

from fastapi import APIRouter, Depends, BackgroundTasks, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.video import Video
from app.models.instagram import InstagramPost
from app.models.article import Article
from app.services.youtube_service import fetch_channel_videos, parse_youtube_video, get_channel_stats
from app.services.instagram_service import fetch_instagram_posts
from app.services.ai_service import generate_article_from_video
import logging
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)
router = APIRouter()


def require_admin(x_admin_key: Optional[str] = Header(None)):
    """Simple admin key check - set ADMIN_KEY in .env"""
    # For dev: skip auth. In production, set ADMIN_KEY and uncomment below.
    # if x_admin_key != settings.ADMIN_KEY:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    pass


@router.post("/youtube")
async def sync_youtube_videos(
    background_tasks: BackgroundTasks,
    max_results: int = 20,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    """
    Sync latest videos from Priyanshu's YouTube channel to DB.
    Call this daily or whenever Priyanshu uploads a new video.
    
    Returns: count of new videos added
    """
    background_tasks.add_task(_sync_youtube_background, db, max_results)
    return {"message": "YouTube sync started in background", "status": "processing"}


async def _sync_youtube_background(db: AsyncSession, max_results: int):
    """Background task: fetch and upsert YouTube videos"""
    try:
        data = await fetch_channel_videos(max_results=max_results)
        new_count = 0

        for item in data.get("items", []):
            parsed = parse_youtube_video(item)
            yt_id = parsed["youtube_video_id"]

            # Check if already exists
            existing = await db.execute(
                select(Video).where(Video.youtube_video_id == yt_id)
            )
            if existing.scalar_one_or_none():
                continue  # Skip - already in DB

            # Insert new video
            video = Video(**parsed)
            db.add(video)
            new_count += 1
            logger.info(f"✅ Added video: {parsed['title'][:60]}")

        await db.commit()
        logger.info(f"🎬 YouTube sync complete. Added {new_count} new videos.")

    except Exception as e:
        logger.error(f"❌ YouTube sync failed: {e}")


@router.post("/instagram")
async def sync_instagram_posts(
    background_tasks: BackgroundTasks,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    """
    Sync latest Instagram posts to DB.
    Call this daily.
    """
    background_tasks.add_task(_sync_instagram_background, db, limit)
    return {"message": "Instagram sync started in background", "status": "processing"}


async def _sync_instagram_background(db: AsyncSession, limit: int):
    try:
        posts = await fetch_instagram_posts(limit=limit)
        new_count = 0

        for post_data in posts:
            ig_id = post_data["instagram_post_id"]
            existing = await db.execute(
                select(InstagramPost).where(InstagramPost.instagram_post_id == ig_id)
            )
            if existing.scalar_one_or_none():
                continue

            post = InstagramPost(**post_data)
            db.add(post)
            new_count += 1

        await db.commit()
        logger.info(f"📸 Instagram sync complete. Added {new_count} new posts.")

    except Exception as e:
        logger.error(f"❌ Instagram sync failed: {e}")


@router.post("/generate-article/{video_id}")
async def generate_article_for_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    """
    Generate an AI article for a specific video.
    Call after sync to create blog post from video content.
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.article_generated:
        return {"message": "Article already generated for this video", "video_id": video_id}

    # Generate article using Claude AI
    article_data = generate_article_from_video(
        video_title=video.title,
        video_description=video.description or "",
        car_brand=video.car_brand,
        car_model=video.car_model,
        video_url=f"https://www.youtube.com/watch?v={video.youtube_video_id}",
    )

    if not article_data:
        raise HTTPException(status_code=500, detail="AI article generation failed. Check ANTHROPIC_API_KEY.")

    # Ensure unique slug
    slug = article_data.get("slug", "")
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower().replace(" ", "-"))

    existing_slug = await db.execute(select(Article).where(Article.slug == slug))
    if existing_slug.scalar_one_or_none():
        slug = f"{slug}-{video.youtube_video_id[:6]}"

    article = Article(
        video_id=video.id,
        title=article_data["title"],
        slug=slug,
        excerpt=article_data.get("excerpt", ""),
        content=article_data["content"],
        meta_description=article_data.get("meta_description", ""),
        meta_keywords=article_data.get("tags", []),
        cover_image_url=video.thumbnail_url,
        category=video.category or "Review",
        car_brand=video.car_brand,
        car_model=video.car_model,
        tags=article_data.get("tags", []),
        read_time_minutes=article_data.get("read_time_minutes", 5),
        is_published=False,  # Priyanshu reviews before publishing
        is_ai_generated=True,
    )

    db.add(article)
    video.article_generated = True
    await db.commit()

    return {
        "success": True,
        "article_id": article.id,
        "title": article.title,
        "slug": article.slug,
        "message": "Article generated! Review in admin panel then publish.",
    }


@router.get("/channel-stats")
async def get_youtube_channel_stats(_: None = Depends(require_admin)):
    """Get YouTube channel statistics"""
    stats = await get_channel_stats()
    return stats


@router.post("/generate-all-articles")
async def generate_articles_for_all_videos(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Generate articles for all videos that don't have one yet"""
    background_tasks.add_task(_generate_all_articles_background, db)
    return {"message": "Bulk article generation started in background"}


async def _generate_all_articles_background(db: AsyncSession):
    result = await db.execute(
        select(Video).where(Video.article_generated == False, Video.is_published == True)
    )
    videos = result.scalars().all()
    logger.info(f"Generating articles for {len(videos)} videos...")

    for video in videos:
        try:
            article_data = generate_article_from_video(
                video_title=video.title,
                video_description=video.description or "",
                car_brand=video.car_brand,
                car_model=video.car_model,
            )
            if article_data:
                slug = re.sub(r"[^a-z0-9-]", "", article_data.get("slug", "").lower())
                article = Article(
                    video_id=video.id,
                    title=article_data["title"],
                    slug=f"{slug}-{video.youtube_video_id[:6]}",
                    excerpt=article_data.get("excerpt", ""),
                    content=article_data["content"],
                    meta_description=article_data.get("meta_description", ""),
                    tags=article_data.get("tags", []),
                    cover_image_url=video.thumbnail_url,
                    car_brand=video.car_brand,
                    car_model=video.car_model,
                    is_published=False,
                    is_ai_generated=True,
                )
                db.add(article)
                video.article_generated = True
                await db.commit()
                logger.info(f"✅ Article generated: {article_data['title'][:60]}")
        except Exception as e:
            logger.error(f"❌ Failed for video {video.id}: {e}")
