from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TikTokProfile(BaseModel):
    user_id: str
    username: str
    nickname: str
    biography: str
    follower_count: int
    following_count: int
    like_count: int
    video_count: int
    profile_pic_url: Optional[str] = None
    is_verified: bool
    is_private: bool
    region: Optional[str] = None


class TikTokVideo(BaseModel):
    video_id: str
    url: str
    description: str
    created_at: datetime
    duration: int  # seconds
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    play_count: int
    cover_url: Optional[str] = None
    download_url: Optional[str] = None
    music_title: Optional[str] = None
    music_author: Optional[str] = None
    hashtags: list[str] = []
    username: str
    user_id: str


class TikTokComment(BaseModel):
    comment_id: str
    text: str
    created_at: datetime
    like_count: int
    username: str
    user_id: str
    reply_count: int = 0


class TikTokVideoList(BaseModel):
    username: str
    videos: list[TikTokVideo]
    total: int


class TikTokCommentList(BaseModel):
    video_id: str
    comments: list[TikTokComment]
    total: int
