from fastapi import APIRouter, HTTPException, Query
from functools import lru_cache

from src.scrapers.instagram import InstagramScraper
from src.models.instagram import (
    InstagramProfile,
    InstagramPost,
    InstagramPostList,
    InstagramCommentList,
)

router = APIRouter(prefix="/instagram", tags=["Instagram"])


@lru_cache(maxsize=1)
def _scraper() -> InstagramScraper:
    return InstagramScraper()


@router.get("/profile/{username}", response_model=InstagramProfile, summary="Get Instagram profile")
async def get_profile(username: str):
    """
    Fetch public profile information for an Instagram user.

    Returns follower/following counts, bio, post count, and account metadata.
    Requires valid Instagram credentials in .env.
    """
    try:
        return _scraper().get_profile(username)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/posts/{username}", response_model=InstagramPostList, summary="Get user posts")
async def get_posts(
    username: str,
    limit: int = Query(default=20, ge=1, le=50, description="Number of posts to fetch"),
):
    """
    Fetch recent posts for an Instagram user.

    Returns post metadata including captions, like/comment counts, media URLs,
    and timestamps. Maximum 50 posts per request.
    """
    try:
        return _scraper().get_posts(username, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/post/{media_id}", response_model=InstagramPost, summary="Get single post")
async def get_post(media_id: str):
    """
    Fetch details for a single Instagram post.

    ``media_id`` can be a numeric media ID or a shortcode (e.g. ``CxYz123``).
    """
    try:
        return _scraper().get_post(media_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/comments/{media_id}", response_model=InstagramCommentList, summary="Get post comments")
async def get_comments(
    media_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Number of comments to fetch"),
):
    """
    Fetch comments on an Instagram post.

    ``media_id`` can be a numeric media ID or a shortcode. Maximum 200 per request.
    """
    try:
        return _scraper().get_comments(media_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
