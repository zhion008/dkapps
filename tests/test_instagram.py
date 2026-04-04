"""
Unit tests for the Instagram scraper and API routes.

These tests mock instagrapi to avoid needing real credentials.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def _make_mock_user(**overrides):
    user = MagicMock()
    user.pk = 123456
    user.username = "testuser"
    user.full_name = "Test User"
    user.biography = "Bio text"
    user.follower_count = 1000
    user.following_count = 500
    user.media_count = 42
    user.profile_pic_url = "https://example.com/pic.jpg"
    user.is_private = False
    user.is_verified = False
    user.external_url = None
    user.category = None
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


def _make_mock_media(**overrides):
    media = MagicMock()
    media.pk = 987654
    media.code = "AbCdEf"
    media.media_type = 1
    media.caption_text = "A caption #test"
    media.like_count = 200
    media.comment_count = 15
    media.taken_at = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    media.thumbnail_url = "https://example.com/thumb.jpg"
    media.video_url = None
    media.video_duration = None
    media.location = None
    media.resources = []
    media.user = MagicMock()
    media.user.username = "testuser"
    media.user.pk = 123456
    for k, v in overrides.items():
        setattr(media, k, v)
    return media


class TestInstagramProfileEndpoint:
    @patch("src.api.routes.instagram._scraper")
    def test_get_profile_success(self, mock_scraper_fn):
        from src.models.instagram import InstagramProfile

        mock_scraper = MagicMock()
        mock_scraper_fn.return_value = mock_scraper
        mock_scraper.get_profile.return_value = InstagramProfile(
            user_id="123456",
            username="testuser",
            full_name="Test User",
            biography="Bio text",
            follower_count=1000,
            following_count=500,
            media_count=42,
            is_private=False,
            is_verified=False,
        )

        response = client.get("/api/v1/instagram/profile/testuser")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["follower_count"] == 1000

    @patch("src.api.routes.instagram._scraper")
    def test_get_profile_not_found(self, mock_scraper_fn):
        mock_scraper = MagicMock()
        mock_scraper_fn.return_value = mock_scraper
        mock_scraper.get_profile.side_effect = ValueError("Instagram user not found: nobody")

        response = client.get("/api/v1/instagram/profile/nobody")
        assert response.status_code == 404

    @patch("src.api.routes.instagram._scraper")
    def test_get_profile_auth_error(self, mock_scraper_fn):
        mock_scraper = MagicMock()
        mock_scraper_fn.return_value = mock_scraper
        mock_scraper.get_profile.side_effect = RuntimeError("Instagram session expired")

        response = client.get("/api/v1/instagram/profile/testuser")
        assert response.status_code == 503


class TestInstagramPostsEndpoint:
    @patch("src.api.routes.instagram._scraper")
    def test_get_posts_success(self, mock_scraper_fn):
        from src.models.instagram import InstagramPost, InstagramPostList

        mock_scraper = MagicMock()
        mock_scraper_fn.return_value = mock_scraper
        mock_scraper.get_posts.return_value = InstagramPostList(
            username="testuser",
            posts=[
                InstagramPost(
                    media_id="987654",
                    shortcode="AbCdEf",
                    url="https://www.instagram.com/p/AbCdEf/",
                    media_type="photo",
                    caption="A caption",
                    like_count=200,
                    comment_count=15,
                    taken_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                    username="testuser",
                    user_id="123456",
                )
            ],
            total=1,
        )

        response = client.get("/api/v1/instagram/posts/testuser")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert len(data["posts"]) == 1
        assert data["posts"][0]["shortcode"] == "AbCdEf"

    @patch("src.api.routes.instagram._scraper")
    def test_get_posts_limit_validation(self, mock_scraper_fn):
        response = client.get("/api/v1/instagram/posts/testuser?limit=0")
        assert response.status_code == 422

        response = client.get("/api/v1/instagram/posts/testuser?limit=51")
        assert response.status_code == 422


class TestInstagramCommentsEndpoint:
    @patch("src.api.routes.instagram._scraper")
    def test_get_comments_success(self, mock_scraper_fn):
        from src.models.instagram import InstagramComment, InstagramCommentList

        mock_scraper = MagicMock()
        mock_scraper_fn.return_value = mock_scraper
        mock_scraper.get_comments.return_value = InstagramCommentList(
            media_id="987654",
            comments=[
                InstagramComment(
                    comment_id="111",
                    text="Great post!",
                    created_at=datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc),
                    like_count=5,
                    username="commenter",
                    user_id="999",
                )
            ],
            total=1,
        )

        response = client.get("/api/v1/instagram/comments/987654")
        assert response.status_code == 200
        data = response.json()
        assert data["media_id"] == "987654"
        assert len(data["comments"]) == 1
        assert data["comments"][0]["text"] == "Great post!"
