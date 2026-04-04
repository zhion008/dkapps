"""
TikTok scraper using the TikTokApi library (v6+).

TikTokApi v6 uses Playwright to simulate real browser behaviour, which is
required because TikTok signs requests with device-specific tokens.

Setup:
  1. pip install TikTokApi playwright
  2. playwright install chromium   (or 'ms-edge' if available)
  3. Optionally set TIKTOK_MS_TOKEN in .env for better reliability.
     Obtain it by logging into tiktok.com in a browser and copying
     the value of the 'msToken' cookie.

All methods on this class are async and must be awaited.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from TikTokApi import TikTokApi
from TikTokApi.exceptions import (
    TikTokException,
)

from src.config import settings
from src.models.tiktok import (
    TikTokComment,
    TikTokCommentList,
    TikTokProfile,
    TikTokVideo,
    TikTokVideoList,
)

logger = logging.getLogger(__name__)


class TikTokScraper:
    """Async wrapper around TikTokApi with typed return values."""

    async def get_profile(self, username: str) -> TikTokProfile:
        """Fetch public profile info for a TikTok username."""
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[settings.tiktok_ms_token] if settings.tiktok_ms_token else None,
                num_sessions=1,
                sleep_after=3,
                headless=True,
            )
            try:
                user = api.user(username=username)
                info = await user.info()
            except TikTokException as exc:
                raise ValueError(f"TikTok user not found: {username} — {exc}")

        stats = info.get("stats", {})
        user_info = info.get("userInfo", {}).get("user", info.get("user", {}))

        return TikTokProfile(
            user_id=user_info.get("id", ""),
            username=user_info.get("uniqueId", username),
            nickname=user_info.get("nickname", ""),
            biography=user_info.get("signature", ""),
            follower_count=stats.get("followerCount", 0),
            following_count=stats.get("followingCount", 0),
            like_count=stats.get("heartCount", 0),
            video_count=stats.get("videoCount", 0),
            profile_pic_url=user_info.get("avatarLarger") or user_info.get("avatarThumb"),
            is_verified=user_info.get("verified", False),
            is_private=user_info.get("privateAccount", False),
            region=user_info.get("region"),
        )

    async def get_videos(self, username: str, limit: int = 20) -> TikTokVideoList:
        """Fetch recent videos for a TikTok user."""
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[settings.tiktok_ms_token] if settings.tiktok_ms_token else None,
                num_sessions=1,
                sleep_after=3,
                headless=True,
            )
            try:
                user = api.user(username=username)
                videos_raw = []
                async for video in user.videos(count=limit):
                    videos_raw.append(video)
            except TikTokException as exc:
                raise ValueError(f"TikTok error for {username}: {exc}")

        videos = [self._raw_to_video(v, username) for v in videos_raw]
        return TikTokVideoList(username=username, videos=videos, total=len(videos))

    async def get_video(self, video_id: str) -> TikTokVideo:
        """Fetch details for a single TikTok video by ID."""
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[settings.tiktok_ms_token] if settings.tiktok_ms_token else None,
                num_sessions=1,
                sleep_after=3,
                headless=True,
            )
            try:
                video = api.video(id=video_id)
                info = await video.info()
            except TikTokException as exc:
                raise ValueError(f"TikTok video not found: {video_id} — {exc}")

        raw = info if isinstance(info, dict) else {}
        username = raw.get("author", {}).get("uniqueId", "")
        return self._raw_to_video(video, username)

    async def get_comments(self, video_id: str, limit: int = 50) -> TikTokCommentList:
        """Fetch comments for a TikTok video."""
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[settings.tiktok_ms_token] if settings.tiktok_ms_token else None,
                num_sessions=1,
                sleep_after=3,
                headless=True,
            )
            try:
                video = api.video(id=video_id)
                raw_comments = []
                async for comment in video.comments(count=limit):
                    raw_comments.append(comment)
            except TikTokException as exc:
                raise ValueError(f"TikTok comments error for {video_id}: {exc}")

        comments = [self._raw_to_comment(c) for c in raw_comments]
        return TikTokCommentList(video_id=video_id, comments=comments, total=len(comments))

    async def get_trending(self, limit: int = 20) -> TikTokVideoList:
        """Fetch trending videos from TikTok."""
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[settings.tiktok_ms_token] if settings.tiktok_ms_token else None,
                num_sessions=1,
                sleep_after=3,
                headless=True,
            )
            try:
                raw_videos = []
                async for video in api.trending.videos(count=limit):
                    raw_videos.append(video)
            except TikTokException as exc:
                raise ValueError(f"TikTok trending error: {exc}")

        videos = [self._raw_to_video(v, v.author.username if hasattr(v, "author") else "") for v in raw_videos]
        return TikTokVideoList(username="trending", videos=videos, total=len(videos))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _raw_to_video(video, username: str) -> TikTokVideo:
        """Convert a TikTokApi video object to our TikTokVideo model."""
        # TikTokApi video objects expose .as_dict for raw data
        data: dict = video.as_dict if hasattr(video, "as_dict") else {}
        stats = data.get("stats", {})
        music = data.get("music", {})
        desc = data.get("desc", "")

        # Extract hashtags from description
        hashtags = [word[1:] for word in desc.split() if word.startswith("#")]

        created_ts = data.get("createTime", 0)
        created_at = datetime.fromtimestamp(created_ts, tz=timezone.utc) if created_ts else datetime.now(timezone.utc)

        user_data = data.get("author", {})
        user_id = user_data.get("id", getattr(video, "id", ""))

        video_data = data.get("video", {})

        return TikTokVideo(
            video_id=str(data.get("id", getattr(video, "id", ""))),
            url=f"https://www.tiktok.com/@{username}/video/{data.get('id', '')}",
            description=desc,
            created_at=created_at,
            duration=video_data.get("duration", 0),
            view_count=stats.get("playCount", 0),
            like_count=stats.get("diggCount", 0),
            comment_count=stats.get("commentCount", 0),
            share_count=stats.get("shareCount", 0),
            play_count=stats.get("playCount", 0),
            cover_url=video_data.get("cover") or video_data.get("dynamicCover"),
            download_url=video_data.get("downloadAddr"),
            music_title=music.get("title"),
            music_author=music.get("authorName"),
            hashtags=hashtags,
            username=username,
            user_id=str(user_id),
        )

    @staticmethod
    def _raw_to_comment(comment) -> TikTokComment:
        data: dict = comment.as_dict if hasattr(comment, "as_dict") else {}
        user = data.get("user", {})

        created_ts = data.get("createTime", 0)
        created_at = datetime.fromtimestamp(created_ts, tz=timezone.utc) if created_ts else datetime.now(timezone.utc)

        return TikTokComment(
            comment_id=str(data.get("cid", "")),
            text=data.get("text", ""),
            created_at=created_at,
            like_count=data.get("diggCount", 0),
            username=user.get("uniqueId", ""),
            user_id=str(user.get("uid", "")),
            reply_count=data.get("replyCommentTotal", 0),
        )
