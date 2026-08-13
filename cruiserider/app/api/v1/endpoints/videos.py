from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status as http_status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.video import (
    VideoResponse,
    VideoListResponse,
    VideoStatus,
    YouTubeVideoCreate
)
from app.services.video_service import VideoService
from app.security.dependencies import get_current_admin
from app.models.users import User


router = APIRouter()


def get_video_service(
    db: AsyncSession = Depends(get_db),
) -> VideoService:

    return VideoService(db)


@router.get(
    "/",
    response_model=VideoListResponse
)
async def get_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    status_filter: Optional[VideoStatus] = Query(
        None,
        alias="status"
    ),
    category: Optional[str] = None,
    car_brand: Optional[str] = None,
    search: Optional[str] = None,
    service: VideoService = Depends(get_video_service),
):

    return await service.get_videos(
        page=page,
        limit=limit,
        status_filter=status_filter,
        category=category,
        car_brand=car_brand,
        search=search,
    )

"""@router.post("/sync/youtube")
async def sync_youtube_videos(
    max_results: int = Query(50, ge=1, le=50),
    service: VideoService = Depends(get_video_service),
    current_admin: User = Depends(get_current_admin),
):

    return await service.sync_videos(
        max_results=max_results
    )
"""
@router.get(
    "/featured",
    response_model=list[VideoResponse]
)
async def get_featured_videos(
    limit: int = Query(6, ge=1, le=12),
    service: VideoService = Depends(get_video_service),
):

    result = await service.get_videos(
        page=1,
        limit=limit,
        status_filter=VideoStatus.PUBLISHED,
    )

    return [
        video
        for video in result["videos"]
        if video.is_featured
    ]


@router.get(
    "/latest",
    response_model=list[VideoResponse]
)
async def get_latest_videos(
    limit: int = Query(8, ge=1, le=20),
    service: VideoService = Depends(get_video_service),
):

    result = await service.get_videos(
        page=1,
        limit=limit,
        status_filter=VideoStatus.PUBLISHED,
    )

    return result["videos"]

@router.post(
    "/youtube",
    response_model=VideoResponse,
    status_code=http_status.HTTP_201_CREATED
)
async def add_youtube_video(
    video_data: YouTubeVideoCreate,
    service: VideoService = Depends(get_video_service),
    current_admin: User = Depends(get_current_admin),
):
    """
    Add a single YouTube video to Cruise Rider.

    Admin only.
    """

    return await service.add_youtube_video(
        video_data.youtube_video_id
    )
@router.get(
    "/{video_id}",
    response_model=VideoResponse
)
async def get_video(
    video_id: str,
    service: VideoService = Depends(get_video_service),
):

    return await service.get_video(video_id)


@router.post(
    "/{video_id}/publish",
    response_model=VideoResponse
)
async def publish_video(
    video_id: str,
    service: VideoService = Depends(get_video_service),
    current_admin: User = Depends(get_current_admin),
):

    return await service.publish_video(video_id)


@router.post(
    "/{video_id}/unpublish",
    response_model=VideoResponse
)
async def unpublish_video(
    video_id: str,
    service: VideoService = Depends(get_video_service),
    current_admin: User = Depends(get_current_admin),
):

    return await service.unpublish_video(video_id)


@router.post(
    "/{video_id}/archive",
    response_model=VideoResponse
)
async def archive_video(
    video_id: str,
    service: VideoService = Depends(get_video_service),
    current_admin: User = Depends(get_current_admin),
):

    return await service.archive_video(video_id)


@router.patch(
    "/{video_id}/feature",
    response_model=VideoResponse
)
async def toggle_feature(
    video_id: str,
    service: VideoService = Depends(get_video_service),
    current_admin: User = Depends(get_current_admin),
):

    return await service.toggle_feature(video_id)


@router.delete(
    "/{video_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
async def delete_video(
    video_id: str,
    service: VideoService = Depends(get_video_service),
    current_admin: User = Depends(get_current_admin),
):

    await service.delete_video(video_id)


