"""
Instagram API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.instagram import InstagramPost

router = APIRouter()


@router.get("/posts")
async def get_instagram_posts(
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get latest Instagram posts for website feed/widget"""
    result = await db.execute(
        select(InstagramPost)
        .where(InstagramPost.is_published == True)
        .order_by(desc(InstagramPost.timestamp))
        .limit(limit)
    )
    posts = result.scalars().all()
    return [
        {
            "id": p.instagram_post_id,
            "media_type": p.media_type,
            "media_url": p.media_url,
            "thumbnail_url": p.thumbnail_url,
            "permalink": p.permalink,
            "caption": p.caption,
            "like_count": p.like_count,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
        }
        for p in posts
    ]
