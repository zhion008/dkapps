"""
Instagram scraper using instagrapi (unofficial Instagram API).

Requirements:
  - Instagram account credentials (username + password) set in .env
  - OR a session ID from an active Instagram login

Rate limits: Instagram enforces rate limits. Keep requests under 30/min
and add delays between bulk operations to avoid account restrictions.
"""

import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    MediaNotFound,
    UserNotFound,
    ClientError,
)

from src.config import settings
from src.models.instagram import (
    InstagramComment,
    InstagramCommentList,
    InstagramPost,
    InstagramPostList,
    InstagramProfile,
)

logger = logging.getLogger(__name__)

MEDIA_TYPE_MAP = {1: "photo", 2: "video", 8: "album"}


class InstagramScraper:
    """Wraps instagrapi.Client with typed return values and error handling."""

    def __init__(self) -> None:
        self._client: Optional[Client] = None

    def _get_client(self) -> Client:
        """Return an authenticated instagrapi Client, creating one if needed."""
        if self._client is not None:
            return self._client

        cl = Client()

        if settings.instagram_session_id:
            # Faster than full login; avoids triggering 2FA
            cl.login_by_sessionid(settings.instagram_session_id)
            logger.info("Instagram: logged in via session ID")
        elif settings.instagram_username and settings.instagram_password:
            cl.login(settings.instagram_username, settings.instagram_password)
            logger.info("Instagram: logged in as %s", settings.instagram_username)
        else:
            raise RuntimeError(
                "Instagram credentials not configured. "
                "Set INSTAGRAM_USERNAME + INSTAGRAM_PASSWORD or INSTAGRAM_SESSION_ID in .env"
            )

        self._client = cl
        return cl

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_profile(self, username: str) -> InstagramProfile:
        """Fetch public profile info for a given username."""
        cl = self._get_client()
        try:
            user = cl.user_info_by_username(username)
        except UserNotFound:
            raise ValueError(f"Instagram user not found: {username}")
        except LoginRequired:
            self._client = None
            raise RuntimeError("Instagram session expired; please re-authenticate")

        return InstagramProfile(
            user_id=str(user.pk),
            username=user.username,
            full_name=user.full_name or "",
            biography=user.biography or "",
            follower_count=user.follower_count,
            following_count=user.following_count,
            media_count=user.media_count,
            profile_pic_url=str(user.profile_pic_url) if user.profile_pic_url else None,
            is_private=user.is_private,
            is_verified=user.is_verified,
            external_url=str(user.external_url) if user.external_url else None,
            category=user.category,
        )

    def get_posts(self, username: str, limit: int = 20) -> InstagramPostList:
        """Fetch recent posts for a given username."""
        cl = self._get_client()
        try:
            user_id = cl.user_id_from_username(username)
            medias = cl.user_medias(user_id, amount=limit)
        except UserNotFound:
            raise ValueError(f"Instagram user not found: {username}")

        posts = [self._media_to_post(m, username, str(user_id)) for m in medias]
        return InstagramPostList(username=username, posts=posts, total=len(posts))

    def get_post(self, media_id: str) -> InstagramPost:
        """Fetch details for a single post by its media ID or shortcode."""
        cl = self._get_client()
        try:
            # Accept both numeric media_id and shortcode (e.g. "CxYz123")
            if media_id.isdigit():
                media = cl.media_info(int(media_id))
            else:
                media = cl.media_info(cl.media_id(media_id))
        except MediaNotFound:
            raise ValueError(f"Instagram post not found: {media_id}")

        username = media.user.username if media.user else ""
        user_id = str(media.user.pk) if media.user else ""
        return self._media_to_post(media, username, user_id)

    def get_comments(self, media_id: str, limit: int = 50) -> InstagramCommentList:
        """Fetch comments for a post."""
        cl = self._get_client()
        try:
            numeric_id = int(media_id) if media_id.isdigit() else cl.media_id(media_id)
            raw_comments = cl.media_comments(numeric_id, amount=limit)
        except (MediaNotFound, ClientError) as exc:
            raise ValueError(f"Could not fetch comments for {media_id}: {exc}")

        comments = [
            InstagramComment(
                comment_id=str(c.pk),
                text=c.text,
                created_at=c.created_at_utc or datetime.now(timezone.utc),
                like_count=c.like_count,
                username=c.user.username if c.user else "",
                user_id=str(c.user.pk) if c.user else "",
            )
            for c in raw_comments
        ]
        return InstagramCommentList(
            media_id=str(numeric_id), comments=comments, total=len(comments)
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _media_to_post(media, username: str, user_id: str) -> InstagramPost:
        media_type = MEDIA_TYPE_MAP.get(media.media_type, "photo")

        thumbnail_url = None
        if media.thumbnail_url:
            thumbnail_url = str(media.thumbnail_url)
        elif media.resources:
            thumbnail_url = str(media.resources[0].thumbnail_url) if media.resources[0].thumbnail_url else None

        video_url = str(media.video_url) if media.video_url else None

        taken_at = media.taken_at or datetime.now(timezone.utc)
        if taken_at.tzinfo is None:
            taken_at = taken_at.replace(tzinfo=timezone.utc)

        location_name = None
        if media.location:
            location_name = media.location.name

        return InstagramPost(
            media_id=str(media.pk),
            shortcode=media.code,
            url=f"https://www.instagram.com/p/{media.code}/",
            media_type=media_type,
            caption=media.caption_text,
            like_count=media.like_count,
            comment_count=media.comment_count,
            taken_at=taken_at,
            thumbnail_url=thumbnail_url,
            video_url=video_url,
            video_duration=media.video_duration,
            location=location_name,
            username=username,
            user_id=user_id,
        )
