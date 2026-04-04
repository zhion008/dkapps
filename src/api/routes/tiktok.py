from fastapi import APIRouter, HTTPException, Query

from src.scrapers.tiktok import TikTokScraper
from src.models.tiktok import (
    TikTokProfile,
    TikTokVideo,
    TikTokVideoList,
    TikTokCommentList,
)

router = APIRouter(prefix="/tiktok", tags=["TikTok"])

# Single shared scraper instance (sessions are created per-request inside the class)
_scraper = TikTokScraper()


@router.get("/profile/{username}", response_model=TikTokProfile, summary="Get TikTok profile")
async def get_profile(username: str):
    """
    Fetch public profile info for a TikTok user.

    Returns follower/following counts, bio, like count, and account metadata.
    Set TIKTOK_MS_TOKEN in .env for better reliability.
    """
    try:
        return await _scraper.get_profile(username)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TikTok scraper error: {exc}")


@router.get("/videos/{username}", response_model=TikTokVideoList, summary="Get user videos")
async def get_videos(
    username: str,
    limit: int = Query(default=20, ge=1, le=50, description="Number of videos to fetch"),
):
    """
    Fetch recent videos for a TikTok user.

    Returns video metadata including view/like/comment/share counts, description,
    hashtags, music info, and cover image URLs. Maximum 50 per request.
    """
    try:
        return await _scraper.get_videos(username, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TikTok scraper error: {exc}")


@router.get("/video/{video_id}", response_model=TikTokVideo, summary="Get single video")
async def get_video(video_id: str):
    """
    Fetch details for a single TikTok video by its numeric ID.
    """
    try:
        return await _scraper.get_video(video_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TikTok scraper error: {exc}")


@router.get("/comments/{video_id}", response_model=TikTokCommentList, summary="Get video comments")
async def get_comments(
    video_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Number of comments to fetch"),
):
    """
    Fetch comments for a TikTok video. Maximum 200 per request.
    """
    try:
        return await _scraper.get_comments(video_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TikTok scraper error: {exc}")


@router.get("/trending", response_model=TikTokVideoList, summary="Get trending videos")
async def get_trending(
    limit: int = Query(default=20, ge=1, le=50, description="Number of trending videos to fetch"),
):
    """
    Fetch currently trending TikTok videos. Maximum 50 per request.
    """
    try:
        return await _scraper.get_trending(limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TikTok scraper error: {exc}")
