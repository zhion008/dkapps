"""
Google Sheets exporter for scraped social media data.

Authentication uses a Google Cloud service account.

Setup (one-time):
  1. Go to https://console.cloud.google.com/
  2. Create a project (or use an existing one)
  3. Enable the Google Sheets API and Google Drive API
  4. Create a Service Account: IAM & Admin → Service Accounts → Create
  5. Download the JSON key file → save it as credentials.json in this project root
  6. Open your Google Sheet → Share → paste the service account email → Editor role
  7. Copy the Sheet ID from the URL and set GOOGLE_SHEET_ID in .env

The exporter writes each data type to a dedicated worksheet tab:
  - Profile      → one row per scrape run (with timestamp)
  - Posts        → one row per post
  - Comments     → one row per comment (with parent post ID)
"""

import logging
from datetime import datetime, timezone
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from src.config import settings
from src.models.instagram import (
    InstagramComment,
    InstagramCommentList,
    InstagramPost,
    InstagramPostList,
    InstagramProfile,
)

logger = logging.getLogger(__name__)

# Scopes required for reading and writing Sheets + Drive metadata
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Column headers for each worksheet tab
_PROFILE_HEADERS = [
    "scraped_at",
    "username",
    "full_name",
    "biography",
    "follower_count",
    "following_count",
    "media_count",
    "is_verified",
    "is_private",
    "profile_pic_url",
    "external_url",
    "category",
]

_POST_HEADERS = [
    "scraped_at",
    "media_id",
    "shortcode",
    "url",
    "media_type",
    "caption",
    "like_count",
    "comment_count",
    "taken_at",
    "thumbnail_url",
    "video_url",
    "video_duration",
    "location",
    "username",
]

_COMMENT_HEADERS = [
    "scraped_at",
    "comment_id",
    "post_media_id",
    "text",
    "created_at",
    "like_count",
    "username",
    "user_id",
    "replied_to_comment_id",
]


class GoogleSheetsExporter:
    """Writes scraped Instagram data to a Google Sheet."""

    def __init__(self) -> None:
        if not settings.google_sheet_id:
            raise RuntimeError(
                "GOOGLE_SHEET_ID is not set in .env. "
                "Copy the sheet ID from the URL: /spreadsheets/d/{ID}/"
            )
        creds = Credentials.from_service_account_file(
            settings.google_service_account_file, scopes=_SCOPES
        )
        self._gc = gspread.authorize(creds)
        self._sh = self._gc.open_by_key(settings.google_sheet_id)
        logger.info("Google Sheets connected: %s", self._sh.title)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_profile(self, profile: InstagramProfile) -> None:
        """Append a profile snapshot row to the 'Profile' tab."""
        ws = self._get_or_create_worksheet("Profile", _PROFILE_HEADERS)
        now = _now()
        row = [
            now,
            profile.username,
            profile.full_name,
            profile.biography,
            profile.follower_count,
            profile.following_count,
            profile.media_count,
            profile.is_verified,
            profile.is_private,
            profile.profile_pic_url or "",
            profile.external_url or "",
            profile.category or "",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Exported profile: @%s", profile.username)

    def export_posts(self, post_list: InstagramPostList) -> None:
        """Append rows to the 'Posts' tab — one row per post."""
        ws = self._get_or_create_worksheet("Posts", _POST_HEADERS)
        now = _now()
        rows = [_post_to_row(now, post) for post in post_list.posts]
        if rows:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
        logger.info("Exported %d posts for @%s", len(rows), post_list.username)

    def export_comments(self, comment_list: InstagramCommentList) -> None:
        """Append rows to the 'Comments' tab — one row per comment."""
        ws = self._get_or_create_worksheet("Comments", _COMMENT_HEADERS)
        now = _now()
        rows = [_comment_to_row(now, comment_list.media_id, c) for c in comment_list.comments]
        if rows:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
        logger.info(
            "Exported %d comments for post %s", len(rows), comment_list.media_id
        )

    def export_all(
        self,
        profile: InstagramProfile,
        post_list: InstagramPostList,
        comment_lists: list[InstagramCommentList],
    ) -> None:
        """Export profile + posts + all comment lists in one call."""
        self.export_profile(profile)
        self.export_posts(post_list)
        for cl in comment_lists:
            self.export_comments(cl)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_create_worksheet(self, title: str, headers: list[str]) -> gspread.Worksheet:
        """Return the worksheet with ``title``, creating it with headers if missing."""
        try:
            ws = self._sh.worksheet(title)
        except gspread.WorksheetNotFound:
            ws = self._sh.add_worksheet(title=title, rows=1000, cols=len(headers))
            ws.append_row(headers, value_input_option="USER_ENTERED")
            # Bold the header row
            ws.format("1:1", {"textFormat": {"bold": True}})
            logger.info("Created worksheet: %s", title)
        return ws


# ------------------------------------------------------------------
# Row builders
# ------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _post_to_row(scraped_at: str, post: InstagramPost) -> list[Any]:
    return [
        scraped_at,
        post.media_id,
        post.shortcode,
        post.url,
        post.media_type,
        post.caption or "",
        post.like_count,
        post.comment_count,
        post.taken_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        post.thumbnail_url or "",
        post.video_url or "",
        post.video_duration or "",
        post.location or "",
        post.username,
    ]


def _comment_to_row(scraped_at: str, media_id: str, comment: InstagramComment) -> list[Any]:
    return [
        scraped_at,
        comment.comment_id,
        media_id,
        comment.text,
        comment.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        comment.like_count,
        comment.username,
        comment.user_id,
        comment.replied_to_comment_id or "",
    ]
