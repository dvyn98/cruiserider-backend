"""
Videos API - CRUD for YouTube videos synced to CruiseRider
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from app.core.database import get_db
from app.models.video import Video
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    category: Optional[str] = None,
    car_brand: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all videos with pagination and filtering.
    Used by: Homepage video grid, Videos listing page
    """
    query = select(Video).where(Video.is_published == True)

    if category:
        query = query.where(Video.category == category)
    if car_brand:
        query = query.where(Video.car_brand.ilike(f"%{car_brand}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.order_by(desc(Video.published_at))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    videos = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "videos": [video_to_dict(v) for v in videos],
    }


@router.get("/featured")
async def get_featured_videos(
    limit: int = Query(6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """Get featured videos for homepage hero section"""
    query = (
        select(Video)
        .where(Video.is_published == True, Video.is_featured == True)
        .order_by(desc(Video.published_at))
        .limit(limit)
    )
    result = await db.execute(query)
    videos = result.scalars().all()
    return [video_to_dict(v) for v in videos]


@router.get("/latest")
async def get_latest_videos(
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get latest videos - used for homepage 'Recent Reviews' section"""
    query = (
        select(Video)
        .where(Video.is_published == True)
        .order_by(desc(Video.published_at))
        .limit(limit)
    )
    result = await db.execute(query)
    videos = result.scalars().all()
    return [video_to_dict(v) for v in videos]


@router.get("/{youtube_video_id}")
async def get_video(youtube_video_id: str, db: AsyncSession = Depends(get_db)):
    """Get single video by YouTube video ID"""
    result = await db.execute(
        select(Video).where(Video.youtube_video_id == youtube_video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video_to_dict(video)


@router.patch("/{video_id}/feature")
async def toggle_feature(video_id: str, db: AsyncSession = Depends(get_db)):
    """Toggle featured status of a video (admin action)"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    video.is_featured = not video.is_featured
    await db.commit()
    return {"message": f"Featured set to {video.is_featured}", "video_id": video_id}



def video_to_dict(v: Video) -> dict:
    return {
        "id": v.id,
        "youtube_video_id": v.youtube_video_id,
        "title": v.title,
        "description": v.description,
        "thumbnail_url": v.thumbnail_url,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "duration": v.duration,
        "view_count": v.view_count,
        "like_count": v.like_count,
        "tags": v.tags or [],
        "category": v.category,
        "car_brand": v.car_brand,
        "car_model": v.car_model,
        "is_featured": v.is_featured,
        "article_generated": v.article_generated,
        "youtube_url": f"https://www.youtube.com/watch?v={v.youtube_video_id}",
        "embed_url": f"https://www.youtube.com/embed/{v.youtube_video_id}",
    }
