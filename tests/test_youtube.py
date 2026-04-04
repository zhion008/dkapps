"""
Unit tests for the YouTube scraper and API routes.

These tests mock yt-dlp to avoid making real network calls.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.scrapers.youtube import YouTubeScraper

client = TestClient(app)


def _video_info(**overrides) -> dict:
    base = {
        "id": "dQw4w9WgXcQ",
        "title": "Never Gonna Give You Up",
        "description": "Rick Astley's official video",
        "upload_date": "20091025",
        "duration": 212,
        "view_count": 1_400_000_000,
        "like_count": 15_000_000,
        "comment_count": 2_000_000,
        "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
        "channel": "Rick Astley",
        "tags": ["rick", "astley", "pop"],
        "categories": ["Music"],
        "is_live": False,
        "age_limit": 0,
        "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "thumbnails": [{"url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"}],
    }
    base.update(overrides)
    return base


class TestYouTubeScraperHelpers:
    def test_resolve_channel_url_channel_id(self):
        scraper = YouTubeScraper()
        url = scraper._resolve_channel_url("UCuAXFkgsw1L7xaCfnd5JJOw")
        assert url == "https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw"

    def test_resolve_channel_url_handle_with_at(self):
        scraper = YouTubeScraper()
        url = scraper._resolve_channel_url("@rickastley")
        assert url == "https://www.youtube.com/@rickastley"

    def test_resolve_channel_url_handle_without_at(self):
        scraper = YouTubeScraper()
        url = scraper._resolve_channel_url("rickastley")
        assert url == "https://www.youtube.com/@rickastley"

    def test_resolve_channel_url_full_url(self):
        scraper = YouTubeScraper()
        url = scraper._resolve_channel_url("https://www.youtube.com/@rickastley")
        assert url == "https://www.youtube.com/@rickastley"

    def test_info_to_video_parses_upload_date(self):
        scraper = YouTubeScraper()
        video = scraper._info_to_video(_video_info())
        assert video.video_id == "dQw4w9WgXcQ"
        assert video.title == "Never Gonna Give You Up"
        assert video.published_at == datetime(2009, 10, 25, tzinfo=timezone.utc)
        assert video.duration == 212
        assert video.like_count == 15_000_000
        assert video.age_restricted is False

    def test_info_to_video_age_restricted(self):
        scraper = YouTubeScraper()
        video = scraper._info_to_video(_video_info(age_limit=18))
        assert video.age_restricted is True

    def test_best_thumbnail_picks_last(self):
        thumbnails = [
            {"url": "https://example.com/small.jpg"},
            {"url": "https://example.com/large.jpg"},
        ]
        url = YouTubeScraper._best_thumbnail(thumbnails)
        assert url == "https://example.com/large.jpg"

    def test_best_thumbnail_none(self):
        assert YouTubeScraper._best_thumbnail(None) is None
        assert YouTubeScraper._best_thumbnail([]) is None

    def test_raw_to_comment(self):
        scraper = YouTubeScraper()
        raw = {
            "id": "comment123",
            "text": "Great video!",
            "timestamp": 1_700_000_000,
            "like_count": 42,
            "author": "SomeUser",
            "author_id": "UCabc",
            "reply_count": 3,
            "parent": "root",
        }
        comment = scraper._raw_to_comment(raw)
        assert comment.comment_id == "comment123"
        assert comment.text == "Great video!"
        assert comment.like_count == 42
        assert comment.is_reply is False

    def test_raw_to_comment_reply(self):
        scraper = YouTubeScraper()
        raw = {
            "id": "reply456",
            "text": "I agree!",
            "timestamp": 1_700_000_000,
            "like_count": 1,
            "author": "Replier",
            "reply_count": 0,
            "parent": "comment123",
        }
        comment = scraper._raw_to_comment(raw)
        assert comment.is_reply is True
        assert comment.parent_comment_id == "comment123"


class TestYouTubeVideoEndpoint:
    @patch("src.api.routes.youtube._run_sync")
    @patch("src.api.routes.youtube._scraper")
    def test_get_video_success(self, mock_scraper_fn, mock_run_sync):
        from src.models.youtube import YouTubeVideo

        mock_video = YouTubeVideo(
            video_id="dQw4w9WgXcQ",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Never Gonna Give You Up",
            description="Rick Astley",
            channel_id="UCuAXFkgsw1L7xaCfnd5JJOw",
            channel_title="Rick Astley",
        )

        import asyncio
        future = asyncio.Future()
        future.set_result(mock_video)
        mock_run_sync.return_value = future

        response = client.get("/api/v1/youtube/video/dQw4w9WgXcQ")
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == "dQw4w9WgXcQ"
        assert data["title"] == "Never Gonna Give You Up"

    @patch("src.api.routes.youtube._run_sync")
    @patch("src.api.routes.youtube._scraper")
    def test_get_video_not_found(self, mock_scraper_fn, mock_run_sync):
        import asyncio

        async def raise_value_error():
            raise ValueError("YouTube video not found")

        future = asyncio.Future()
        future.set_exception(ValueError("YouTube video not found"))
        mock_run_sync.return_value = future

        response = client.get("/api/v1/youtube/video/INVALID")
        assert response.status_code == 404


class TestYouTubeSearchEndpoint:
    def test_search_requires_query(self):
        response = client.get("/api/v1/youtube/search")
        assert response.status_code == 422

    def test_search_limit_validation(self):
        response = client.get("/api/v1/youtube/search?q=test&limit=0")
        assert response.status_code == 422

        response = client.get("/api/v1/youtube/search?q=test&limit=51")
        assert response.status_code == 422
