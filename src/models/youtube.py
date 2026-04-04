from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class YouTubeChannel(BaseModel):
    channel_id: str
    handle: Optional[str] = None
    title: str
    description: str
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None
    country: Optional[str] = None
    joined_at: Optional[datetime] = None
    url: str


class YouTubeVideo(BaseModel):
    video_id: str
    url: str
    title: str
    description: str
    published_at: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    channel_id: str
    channel_title: str
    tags: list[str] = []
    categories: list[str] = []
    is_live: bool = False
    age_restricted: bool = False


class YouTubeComment(BaseModel):
    comment_id: str
    text: str
    published_at: datetime
    like_count: int
    author_name: str
    author_channel_id: Optional[str] = None
    reply_count: int = 0
    is_reply: bool = False
    parent_comment_id: Optional[str] = None


class YouTubeVideoList(BaseModel):
    channel_id: str
    channel_title: str
    videos: list[YouTubeVideo]
    total: int


class YouTubeCommentList(BaseModel):
    video_id: str
    comments: list[YouTubeComment]
    total: int


class YouTubeSearchResult(BaseModel):
    query: str
    videos: list[YouTubeVideo]
    total: int
