"""
YouTube scraper using yt-dlp.

yt-dlp works entirely without an API key and handles:
  - Video metadata (title, description, stats, duration, tags, etc.)
  - Channel metadata and video listings
  - Comments (via --write-comments / writecomments option)
  - Search results (ytsearch: prefix)

All methods are synchronous because yt-dlp's core is blocking.
Run them in a thread pool executor if you need async behaviour.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

import yt_dlp

from src.models.youtube import (
    YouTubeChannel,
    YouTubeComment,
    YouTubeCommentList,
    YouTubeSearchResult,
    YouTubeVideo,
    YouTubeVideoList,
)

logger = logging.getLogger(__name__)

# Shared quiet options to suppress yt-dlp output
_BASE_OPTS: dict = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
}


class YouTubeScraper:
    """Wraps yt-dlp with typed return values."""

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_channel(self, channel: str) -> YouTubeChannel:
        """
        Fetch channel metadata.

        ``channel`` can be:
          - A channel ID:  UCxxxxxxxxxxxxxxxxxxxxxx
          - A handle:      @channelhandle
          - A full URL:    https://www.youtube.com/@handle
        """
        url = self._resolve_channel_url(channel)
        opts = {
            **_BASE_OPTS,
            "extract_flat": "in_playlist",
            "playlistend": 1,  # We only need channel metadata, not all videos
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.DownloadError as exc:
                raise ValueError(f"YouTube channel not found: {channel} — {exc}")

        if not info:
            raise ValueError(f"No data returned for channel: {channel}")

        return self._info_to_channel(info, url)

    def get_channel_videos(self, channel: str, limit: int = 20) -> YouTubeVideoList:
        """Fetch recent videos from a channel."""
        url = self._resolve_channel_url(channel)
        opts = {
            **_BASE_OPTS,
            "extract_flat": True,
            "playlistend": limit,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.DownloadError as exc:
                raise ValueError(f"YouTube channel not found: {channel} — {exc}")

        entries = info.get("entries", []) if info else []
        channel_id = info.get("channel_id", info.get("id", "")) if info else ""
        channel_title = info.get("channel", info.get("title", "")) if info else ""

        # extract_flat returns stubs; enrich each with full metadata
        videos = []
        for entry in entries[:limit]:
            if not entry:
                continue
            video_id = entry.get("id", "")
            if not video_id:
                continue
            try:
                video = self.get_video(video_id)
                videos.append(video)
            except ValueError:
                # Skip unavailable/private videos
                continue

        return YouTubeVideoList(
            channel_id=channel_id,
            channel_title=channel_title,
            videos=videos,
            total=len(videos),
        )

    def get_video(self, video_id: str) -> YouTubeVideo:
        """Fetch full metadata for a single YouTube video."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        opts = {**_BASE_OPTS, "extract_flat": False}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.DownloadError as exc:
                raise ValueError(f"YouTube video not found: {video_id} — {exc}")

        if not info:
            raise ValueError(f"No data returned for video: {video_id}")

        return self._info_to_video(info)

    def get_comments(self, video_id: str, limit: int = 100) -> YouTubeCommentList:
        """
        Fetch comments for a YouTube video.

        yt-dlp's comment extraction can be slow for videos with many comments.
        Use ``limit`` to cap the number returned.
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        opts = {
            **_BASE_OPTS,
            "getcomments": True,
            "extractor_args": {"youtube": {"max_comments": [str(limit), "0", "0", "0"]}},
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.DownloadError as exc:
                raise ValueError(f"YouTube video not found: {video_id} — {exc}")

        raw_comments = (info or {}).get("comments", []) or []
        comments = [self._raw_to_comment(c) for c in raw_comments[:limit] if c]

        return YouTubeCommentList(video_id=video_id, comments=comments, total=len(comments))

    def search(self, query: str, limit: int = 20) -> YouTubeSearchResult:
        """Search YouTube videos."""
        search_url = f"ytsearch{limit}:{query}"
        opts = {**_BASE_OPTS, "extract_flat": False}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(search_url, download=False)
            except yt_dlp.utils.DownloadError as exc:
                raise ValueError(f"YouTube search failed for '{query}': {exc}")

        entries = (info or {}).get("entries", [])
        videos = [self._info_to_video(e) for e in entries if e]

        return YouTubeSearchResult(query=query, videos=videos, total=len(videos))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_channel_url(channel: str) -> str:
        """Normalise various channel identifier formats to a URL."""
        if channel.startswith("http"):
            return channel
        if channel.startswith("UC") and len(channel) == 24:
            return f"https://www.youtube.com/channel/{channel}"
        if channel.startswith("@"):
            return f"https://www.youtube.com/{channel}"
        # Assume it's a handle without @
        return f"https://www.youtube.com/@{channel}"

    @staticmethod
    def _info_to_channel(info: dict, url: str) -> YouTubeChannel:
        joined_ts = info.get("channel_follower_count")  # not the join date, but it's often in upload_date
        # yt-dlp doesn't reliably expose channel join date; skip it
        return YouTubeChannel(
            channel_id=info.get("channel_id", info.get("id", "")),
            handle=info.get("uploader_id"),
            title=info.get("channel", info.get("title", "")),
            description=info.get("description", ""),
            subscriber_count=info.get("channel_follower_count"),
            video_count=info.get("playlist_count"),
            view_count=info.get("view_count"),
            thumbnail_url=YouTubeScraper._best_thumbnail(info.get("thumbnails")),
            country=info.get("channel_location"),
            url=info.get("webpage_url", url),
        )

    @staticmethod
    def _info_to_video(info: dict) -> YouTubeVideo:
        upload_date = info.get("upload_date")  # "YYYYMMDD"
        published_at: Optional[datetime] = None
        if upload_date and len(upload_date) == 8:
            try:
                published_at = datetime(
                    int(upload_date[:4]),
                    int(upload_date[4:6]),
                    int(upload_date[6:]),
                    tzinfo=timezone.utc,
                )
            except ValueError:
                pass

        categories = info.get("categories") or []
        tags = info.get("tags") or []

        return YouTubeVideo(
            video_id=info.get("id", ""),
            url=info.get("webpage_url", f"https://www.youtube.com/watch?v={info.get('id', '')}"),
            title=info.get("title", ""),
            description=info.get("description", ""),
            published_at=published_at,
            duration=info.get("duration"),
            view_count=info.get("view_count"),
            like_count=info.get("like_count"),
            comment_count=info.get("comment_count"),
            thumbnail_url=YouTubeScraper._best_thumbnail(info.get("thumbnails")),
            channel_id=info.get("channel_id", ""),
            channel_title=info.get("channel", info.get("uploader", "")),
            tags=tags,
            categories=categories,
            is_live=info.get("is_live", False) or False,
            age_restricted=info.get("age_limit", 0) >= 18,
        )

    @staticmethod
    def _raw_to_comment(c: dict) -> YouTubeComment:
        ts = c.get("timestamp") or 0
        published_at = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(timezone.utc)

        parent = c.get("parent")
        is_reply = parent is not None and parent != "root"

        return YouTubeComment(
            comment_id=c.get("id", ""),
            text=c.get("text", ""),
            published_at=published_at,
            like_count=c.get("like_count", 0),
            author_name=c.get("author", ""),
            author_channel_id=c.get("author_id"),
            reply_count=c.get("reply_count", 0),
            is_reply=is_reply,
            parent_comment_id=parent if is_reply else None,
        )

    @staticmethod
    def _best_thumbnail(thumbnails: Optional[list]) -> Optional[str]:
        """Pick the highest-resolution thumbnail URL."""
        if not thumbnails:
            return None
        # yt-dlp returns thumbnails sorted by resolution ascending; take the last
        for t in reversed(thumbnails):
            if isinstance(t, dict) and t.get("url"):
                return t["url"]
        return None
