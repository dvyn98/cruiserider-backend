from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoStatus

class VideoRepository:
    def __init__(self, db: AsyncSession):
        self.db=db
    async def create(self, video_data: VideoCreate) -> Video:
        video= Video(**video_data.model_dump())

        self.db.add(video)

        await self.db.commit()
        await self.db.refresh(video)

        return video

    async def get_by_id(self,video_id: str) -> Optional[Video]:
        result = await self.db.execute(
            select(Video).where(Video.id == video_id)
        )    
        return result.scalar_one_or_none()

    async def get_by_youtube_id(
            self,
            youtube_video_id: str
    )-> Optional[Video]:
        result = await self.db.execute(
            select(Video).where(
                Video.youtube_video_id == youtube_video_id
            )
        )
        return result.scalar_one_or_none()

    async def get_videos(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[VideoStatus] = None,
        category: Optional[str] = None,
        car_brand: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Video], int]:

        query = select(Video)

        if status:
            query = query.where(Video.status == status.value)

        if category:
            query = query.where(Video.category == category)

        if car_brand:
            query = query.where(
                Video.car_brand.ilike(f"%{car_brand}%")
            )

        if search:
            search_pattern = f"%{search}%"

            query = query.where(
                Video.title.ilike(search_pattern)
                | Video.description.ilike(search_pattern)
            )

        # Total count
        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = await self.db.scalar(count_query) or 0

        # Pagination
        query = (
            query
            .order_by(Video.published_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)

        videos = list(result.scalars().all())

        return videos, total

    async def update(self, video: Video) -> Video:

        await self.db.commit()
        await self.db.refresh(video)

        return video

    async def delete(self, video: Video) -> None:

        await self.db.delete(video)

        await self.db.commit()

   