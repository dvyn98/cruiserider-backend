from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.video_repository import VideoRepository
from app.schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoStatus,
)
from app.services.youtube_service import (
    fetch_channel_videos,
    parse_youtube_video,
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
        limit: int = 20
    ):
        """
        Get paginated videos.
        """

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1"
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )

        skip = (page - 1) * limit

        return await self.repository.get_all(
            skip=skip,
            limit=limit
        )

   

   
    # SYNC YOUTUBE VIDEOS

    async def sync_videos(
        self,
        max_results: int = 50
    ):
        """
        Fetch videos from YouTube and synchronize them
        with the Cruise Rider database.
        """

        # -----------------------------------------------------
        # STEP 1: Ask YouTubeService for videos
        # -----------------------------------------------------

        youtube_response = await fetch_channel_videos(
            max_results=max_results
        )

        youtube_items = youtube_response.get(
            "items",
            []
        )

        created = 0
       
        skipped = 0

    
        # STEP 2: Process each YouTube video
    

        for item in youtube_items:

            video_data = parse_youtube_video(item)

            youtube_video_id = video_data.get(
                "youtube_video_id"
            )

            if not youtube_video_id:
                skipped += 1
                continue

            
            # STEP 3: Check database
           

            existing_video = (
                await self.repository.get_by_youtube_id(
                    youtube_video_id
                )
            )

            # STEP 4A: Existing video → update
            

            if existing_video:

                skipped+=1
                continue

          
            create_data = VideoCreate(
                    **video_data,
                    status=VideoStatus.DRAFT
                )

            await self.repository.create(
                    create_data
                )

            created += 1

        # STEP 5: Return sync summary
       

        return {
            "total_fetched": len(youtube_items),
            "created": created,
            "skipped": skipped,
            "next_page_token": youtube_response.get(
                "nextPageToken"
            )
        }