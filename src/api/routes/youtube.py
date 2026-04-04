import asyncio
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from src.scrapers.youtube import YouTubeScraper
from src.models.youtube import (
    YouTubeChannel,
    YouTubeVideo,
    YouTubeVideoList,
    YouTubeCommentList,
    YouTubeSearchResult,
)

router = APIRouter(prefix="/youtube", tags=["YouTube"])


@lru_cache(maxsize=1)
def _scraper() -> YouTubeScraper:
    return YouTubeScraper()


def _run_sync(fn, *args, **kwargs):
    """Run a blocking yt-dlp call in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, lambda: fn(*args, **kwargs))


@router.get("/channel/{channel}", response_model=YouTubeChannel, summary="Get YouTube channel info")
async def get_channel(channel: str):
    """
    Fetch metadata for a YouTube channel.

    ``channel`` accepts:
    - Channel ID: ``UCxxxxxxxxxxxxxxxxxxxxxx``
    - Handle: ``@channelhandle`` or ``channelhandle``
    - Full URL: ``https://www.youtube.com/@handle``

    No API key required.
    """
    try:
        return await _run_sync(_scraper().get_channel, channel)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/videos/{channel}", response_model=YouTubeVideoList, summary="Get channel videos")
async def get_channel_videos(
    channel: str,
    limit: int = Query(default=20, ge=1, le=50, description="Number of videos to fetch"),
):
    """
    Fetch recent videos from a YouTube channel.

    Each video is fully enriched with title, description, stats, tags, and thumbnails.
    Maximum 50 videos per request.
    """
    try:
        return await _run_sync(_scraper().get_channel_videos, channel, limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/video/{video_id}", response_model=YouTubeVideo, summary="Get video details")
async def get_video(video_id: str):
    """
    Fetch full metadata for a single YouTube video.

    Returns title, description, view/like/comment counts, tags, categories,
    thumbnail, duration, and channel info.
    """
    try:
        return await _run_sync(_scraper().get_video, video_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/comments/{video_id}", response_model=YouTubeCommentList, summary="Get video comments")
async def get_comments(
    video_id: str,
    limit: int = Query(default=100, ge=1, le=500, description="Number of comments to fetch"),
):
    """
    Fetch comments for a YouTube video.

    Includes top-level comments and replies. Comment extraction can be slow
    for videos with large comment sections. Maximum 500 per request.
    """
    try:
        return await _run_sync(_scraper().get_comments, video_id, limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/search", response_model=YouTubeSearchResult, summary="Search YouTube videos")
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=20, ge=1, le=50, description="Number of results to return"),
):
    """
    Search YouTube for videos matching a query.

    Returns full video metadata for each result. Maximum 50 results per request.
    No API key required.
    """
    try:
        return await _run_sync(_scraper().search, q, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
