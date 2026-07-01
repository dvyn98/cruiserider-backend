"""
Articles API - Blog/SEO article management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update
from typing import Optional
from app.core.database import get_db
from app.models.article import Article
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    car_brand: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get published articles with pagination - for blog listing page"""
    query = select(Article).where(Article.is_published == True)

    if category:
        query = query.where(Article.category == category)
    if car_brand:
        query = query.where(Article.car_brand.ilike(f"%{car_brand}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(desc(Article.published_at)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "articles": [article_to_dict(a, include_content=False) for a in articles],
    }


@router.get("/latest")
async def get_latest_articles(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get latest published articles - homepage sidebar"""
    query = (
        select(Article)
        .where(Article.is_published == True)
        .order_by(desc(Article.published_at))
        .limit(limit)
    )
    result = await db.execute(query)
    articles = result.scalars().all()
    return [article_to_dict(a, include_content=False) for a in articles]


@router.get("/{slug}")
async def get_article_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single article by its URL slug - for article detail page"""
    result = await db.execute(
        select(Article).where(Article.slug == slug, Article.is_published == True)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    await db.execute(
        update(Article).where(Article.id == article.id).values(views=Article.views + 1)
    )
    await db.commit()

    return article_to_dict(article, include_content=True)


@router.patch("/{article_id}/publish")
async def publish_article(article_id: str, db: AsyncSession = Depends(get_db)):
    """Publish a draft article (admin action)"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_published = True
    article.published_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Article published", "slug": article.slug}


def article_to_dict(a: Article, include_content: bool = True) -> dict:
    data = {
        "id": a.id,
        "video_id": a.video_id,
        "title": a.title,
        "slug": a.slug,
        "excerpt": a.excerpt,
        "meta_description": a.meta_description,
        "cover_image_url": a.cover_image_url,
        "author": a.author,
        "category": a.category,
        "car_brand": a.car_brand,
        "car_model": a.car_model,
        "tags": a.tags or [],
        "is_published": a.is_published,
        "is_ai_generated": a.is_ai_generated,
        "views": a.views,
        "read_time_minutes": a.read_time_minutes,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
    if include_content:
        data["content"] = a.content
    return data
