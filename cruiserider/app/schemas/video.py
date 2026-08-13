from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


class VideoStatus(str,Enum):
    DRAFT="DRAFT"
    PUBLISHED="PUBLISHED"
    ARCHIVED="ARCHIVED"
    
class YouTubeVideoCreate(BaseModel):
    youtube_video_id: str = Field(
        ...,
        min_length=1,
        max_length=100
    )
class VideoCreate(BaseModel):
    youtube_video_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str]= None

    thumbnail_url: Optional[str]= Field(
        default=None,
        max_length=1000
    )
    published_at: Optional[datetime] = None

    duration: Optional[str] = Field(
        default=None,
        max_length=20
    )

    view_count: int= Field(default=0,ge=0)
    like_count: int= Field(default=0,ge=0)
    comment_count: int=Field(default=0,ge=0)

    tags: list[str]=Field(default_factory=list)
    category: Optional[str]= Field(
        default=None,
        max_length=100
    )

    car_brand: Optional[str]= Field(
        default=None,
        max_length=100
    )
    car_model: Optional[str]=Field(
        default=None,
        max_length=100
    )

    is_featured: bool =False
    status: VideoStatus=VideoStatus.DRAFT



class VideoResponse(BaseModel):
    id: str
    youtube_video_id: str
    title: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    published_at: Optional[datetime]
    duration: Optional[str]

    view_count: int
    like_count: int
    comment_count: int

    tags: list[str]
    category: Optional[str]

    car_brand: Optional[str]
    car_model: Optional[str]

    is_featured: bool
    status: VideoStatus
    article_generated: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)    

class VideoListResponse(BaseModel):
    total:int
    page:int
    limit: int
    pages: int
    videos: list[VideoResponse]    
