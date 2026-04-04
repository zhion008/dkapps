from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class InstagramProfile(BaseModel):
    user_id: str
    username: str
    full_name: str
    biography: str
    follower_count: int
    following_count: int
    media_count: int
    profile_pic_url: Optional[str] = None
    is_private: bool
    is_verified: bool
    external_url: Optional[str] = None
    category: Optional[str] = None


class InstagramPost(BaseModel):
    media_id: str
    shortcode: str
    url: str
    media_type: str  # "photo", "video", "album"
    caption: Optional[str] = None
    like_count: int
    comment_count: int
    taken_at: datetime
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    video_duration: Optional[float] = None
    location: Optional[str] = None
    username: str
    user_id: str


class InstagramComment(BaseModel):
    comment_id: str
    text: str
    created_at: datetime
    like_count: int
    username: str
    user_id: str
    replied_to_comment_id: Optional[str] = None


class InstagramPostList(BaseModel):
    username: str
    posts: list[InstagramPost]
    total: int


class InstagramCommentList(BaseModel):
    media_id: str
    comments: list[InstagramComment]
    total: int
