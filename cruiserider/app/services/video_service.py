from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.video_repository import VideoRepository
from app.schemas.video import (
    VideoCreate,
    VideoStatus,
)
from app.services.youtube_service import (
    fetch_channel_videos,
    parse_youtube_video,
    duration_to_seconds,
    fetch_video_by_id
)


class VideoService:

    def __init__(self, db: AsyncSession):
        self.repository = VideoRepository(db)


    # CREATE VIDEO
   

    async def create_video(
        self,
        video_data: VideoCreate
    ):
        """
        Create a video manually in the database.
        """

        # Check if YouTube video already exists
        existing_video = await self.repository.get_by_youtube_id(
            video_data.youtube_video_id
        )

        if existing_video:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A video with this YouTube video ID already exists"
            )

        return await self.repository.create(video_data)


    async def add_youtube_video(
    self,
    youtube_video_id: str
        ):
        """
    Fetch one video from YouTube and add it to the database.
    Only long-form videos are allowed.
        """

    # 1. Check if video already exists
        existing_video = await self.repository.get_by_youtube_id(
        youtube_video_id
    )

        if existing_video:
            raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A video with this YouTube video ID already exists"
        )

    # 2. Fetch ONE video from YouTube
        youtube_video = await fetch_video_by_id(
        youtube_video_id
    )

    # 3. YouTube video not found
        if not youtube_video:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="YouTube video not found"
        )

    # 4. Parse / normalize YouTube response
        video_data = parse_youtube_video(
        youtube_video
    )

    # 5. Validate required fields
        parsed_video_id = video_data.get(
        "youtube_video_id"
    )

        published_at = video_data.get(
        "published_at"
    )

        if not parsed_video_id or not published_at:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube video data"
        )

    # 6. Check Shorts
        duration_seconds = duration_to_seconds(
            video_data.get("duration", "")
    )

        if duration_seconds <= 180:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube Shorts are not supported"
        )

    # 7. Convert YouTube data into VideoCreate
        create_data = VideoCreate(
        **video_data,
        status=VideoStatus.DRAFT
    )

    # 8. Save to database
        return await self.repository.create(
        create_data
    )
   
    # GET SINGLE VIDEO
    
    async def get_video(
        self,
        video_id: str
    ):
        """
        Get a single video by internal database ID.
        """

        video = await self.repository.get_by_id(video_id)

        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

        return video

   

    async def get_videos(
        self,
        page: int = 1,
        limit: int = 20,
        status_filter: VideoStatus | None= None,
        category: str | None=None,
        car_brand: str | None=None,
        search: str | None=None,
    ):
        """
        Get paginated videos.
        """

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1"
            )

        

        skip = (page - 1) * limit
        videos, total = await self.repository.get_videos(
            skip=skip,
            limit=limit,
            status=status_filter,
            category=category,
            car_brand=car_brand,
            search=search,
        )
        pages=(total+limit-1)//limit

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
            "videos": videos,
        }
   

   
    async def publish_video(
        self,
        video_id: str
    ):

        video = await self.get_video(video_id)

        video.status = VideoStatus.PUBLISHED.value

        return await self.repository.update(video)

    async def unpublish_video(
        self,
        video_id: str
    ):

        video = await self.get_video(video_id)

        video.status = VideoStatus.DRAFT.value

        return await self.repository.update(video)

    async def archive_video(
        self,
        video_id: str
    ):

        video = await self.get_video(video_id)

        video.status = VideoStatus.ARCHIVED.value
        video.is_featured = False

        return await self.repository.update(video)


    async def toggle_feature(
        self,
        video_id: str
    ):

        video = await self.get_video(video_id)

        video.is_featured = not video.is_featured

        return await self.repository.update(video)

    async def delete_video(
        self,
        video_id: str
    ):

        video = await self.get_video(video_id)

        await self.repository.delete(video)

    async def sync_videos(
        self,
        max_results: int = 50
    ):

        if max_results < 1 or max_results > 50:
            raise HTTPException(
                status_code=400,
                detail="max_results must be between 1 and 50"
            )

        youtube_response = await fetch_channel_videos(
            max_results=max_results
        )

        youtube_items = youtube_response.get("items", [])

        created = 0
        updated = 0
        skipped = 0

        for item in youtube_items:

            video_data = parse_youtube_video(item)

            youtube_video_id = video_data.get(
                "youtube_video_id"
            )

            published_at = video_data.get("published_at")

            if not youtube_video_id or not published_at:
                skipped += 1
                continue

            existing_video = (
                await self.repository.get_by_youtube_id(
                    youtube_video_id
                )
            )

            if existing_video:

                # Update YouTube-owned fields
                existing_video.title = video_data["title"]
                existing_video.description = video_data["description"]
                existing_video.thumbnail_url = video_data["thumbnail_url"]
                existing_video.published_at = video_data["published_at"]
                existing_video.duration = video_data["duration"]
                existing_video.view_count = video_data["view_count"]
                existing_video.like_count = video_data["like_count"]
                existing_video.comment_count = video_data["comment_count"]
                existing_video.tags = video_data["tags"]
                existing_video.car_brand = video_data["car_brand"]
                existing_video.car_model = video_data["car_model"]

                await self.repository.update(existing_video)

                updated += 1

                continue

            create_data = VideoCreate(
                **video_data,
                status=VideoStatus.DRAFT
            )

            await self.repository.create(create_data)

            created += 1

        return {
            "total_fetched": len(youtube_items),
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "next_page_token": youtube_response.get(
                "nextPageToken"
            ),
        }