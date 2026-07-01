"""
API v1 Router - Connects all endpoint modules
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    videos,
    articles,
    cars,
    instagram,
    consultancy,
    sync,
)

api_router = APIRouter()

api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
api_router.include_router(articles.router, prefix="/articles", tags=["Articles"])
api_router.include_router(cars.router, prefix="/cars", tags=["Cars & Prices"])
api_router.include_router(instagram.router, prefix="/instagram", tags=["Instagram"])
api_router.include_router(consultancy.router, prefix="/consultancy", tags=["Consultancy"])
api_router.include_router(sync.router, prefix="/sync", tags=["Admin - Sync"])
