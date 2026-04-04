"""
Unit tests for the TikTok scraper and API routes.

These tests mock TikTokApi to avoid browser automation during CI.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.scrapers.tiktok import TikTokScraper

client = TestClient(app)


class TestTikTokScraperHelpers:
    def test_raw_to_video_extracts_hashtags(self):
        video = MagicMock()
        video.as_dict = {
            "id": "7123456789",
            "desc": "Check this out #viral #fyp #funny",
            "createTime": 1_700_000_000,
            "stats": {
                "playCount": 1_000_000,
                "diggCount": 50_000,
                "commentCount": 2_000,
                "shareCount": 5_000,
            },
            "video": {"duration": 30, "cover": "https://example.com/cover.jpg"},
            "music": {"title": "Original Sound", "authorName": "Creator"},
            "author": {"id": "user_123", "uniqueId": "testcreator"},
        }

        result = TikTokScraper._raw_to_video(video, "testcreator")
        assert result.video_id == "7123456789"
        assert result.username == "testcreator"
        assert "viral" in result.hashtags
        assert "fyp" in result.hashtags
        assert "funny" in result.hashtags
        assert result.view_count == 1_000_000
        assert result.like_count == 50_000
        assert result.duration == 30
        assert result.music_title == "Original Sound"

    def test_raw_to_video_no_hashtags(self):
        video = MagicMock()
        video.as_dict = {
            "id": "111",
            "desc": "No hashtags here",
            "createTime": 1_700_000_000,
            "stats": {},
            "video": {},
            "music": {},
            "author": {},
        }
        result = TikTokScraper._raw_to_video(video, "user")
        assert result.hashtags == []

    def test_raw_to_comment(self):
        comment = MagicMock()
        comment.as_dict = {
            "cid": "comment_999",
            "text": "Hilarious!",
            "createTime": 1_700_000_000,
            "diggCount": 10,
            "user": {"uniqueId": "commenter", "uid": "uid_456"},
            "replyCommentTotal": 2,
        }

        result = TikTokScraper._raw_to_comment(comment)
        assert result.comment_id == "comment_999"
        assert result.text == "Hilarious!"
        assert result.like_count == 10
        assert result.username == "commenter"
        assert result.reply_count == 2

    def test_raw_to_comment_zero_ts(self):
        comment = MagicMock()
        comment.as_dict = {
            "cid": "c1",
            "text": "hi",
            "createTime": 0,
            "diggCount": 0,
            "user": {},
            "replyCommentTotal": 0,
        }
        result = TikTokScraper._raw_to_comment(comment)
        # Should not raise; timestamp 0 falls back to now
        assert result.comment_id == "c1"


class TestTikTokProfileEndpoint:
    @patch("src.api.routes.tiktok._scraper")
    def test_get_profile_success(self, mock_scraper):
        from src.models.tiktok import TikTokProfile

        mock_scraper.get_profile = AsyncMock(
            return_value=TikTokProfile(
                user_id="user_123",
                username="testcreator",
                nickname="Test Creator",
                biography="Making content",
                follower_count=100_000,
                following_count=500,
                like_count=5_000_000,
                video_count=200,
                is_verified=False,
                is_private=False,
            )
        )

        response = client.get("/api/v1/tiktok/profile/testcreator")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testcreator"
        assert data["follower_count"] == 100_000

    @patch("src.api.routes.tiktok._scraper")
    def test_get_profile_not_found(self, mock_scraper):
        mock_scraper.get_profile = AsyncMock(
            side_effect=ValueError("TikTok user not found: nobody")
        )

        response = client.get("/api/v1/tiktok/profile/nobody")
        assert response.status_code == 404


class TestTikTokVideosEndpoint:
    @patch("src.api.routes.tiktok._scraper")
    def test_get_videos_limit_validation(self, mock_scraper):
        response = client.get("/api/v1/tiktok/videos/testcreator?limit=0")
        assert response.status_code == 422

        response = client.get("/api/v1/tiktok/videos/testcreator?limit=51")
        assert response.status_code == 422

    @patch("src.api.routes.tiktok._scraper")
    def test_get_trending_success(self, mock_scraper):
        from src.models.tiktok import TikTokVideoList

        mock_scraper.get_trending = AsyncMock(
            return_value=TikTokVideoList(username="trending", videos=[], total=0)
        )

        response = client.get("/api/v1/tiktok/trending")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "trending"
