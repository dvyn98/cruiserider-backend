from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoResponse, VideoUpdate

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

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> list[Video]:

        result = await self.db.execute(
            select(Video)
            .offset(skip)
            .limit(limit)
            .order_by(Video.published_at.desc())
        )

        return list(result.scalars().all())

   