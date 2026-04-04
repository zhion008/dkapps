#!/usr/bin/env python3
"""
Scrape @omareltakrori's Instagram profile, posts, and comments,
then write all data to Google Sheets.

Usage:
    python scripts/scrape_instagram_to_sheets.py

    # Scrape more posts:
    python scripts/scrape_instagram_to_sheets.py --posts 50

    # Scrape posts + fetch comments for each:
    python scripts/scrape_instagram_to_sheets.py --posts 20 --comments 30

    # Dry run (scrape only, no Sheets write):
    python scripts/scrape_instagram_to_sheets.py --dry-run

Requires .env with:
    INSTAGRAM_USERNAME=iamdkhammonds
    INSTAGRAM_PASSWORD=...
    GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
    GOOGLE_SHEET_ID=...
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Allow running from the project root without installing as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.scrapers.instagram import InstagramScraper
from src.exporters.google_sheets import GoogleSheetsExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

TARGET_USERNAME = "omareltakrori"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape @omareltakrori → Google Sheets")
    p.add_argument(
        "--posts",
        type=int,
        default=20,
        metavar="N",
        help="Number of recent posts to scrape (default: 20, max: 50)",
    )
    p.add_argument(
        "--comments",
        type=int,
        default=0,
        metavar="N",
        help="Comments to fetch per post (0 = skip comments, default: 0)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape but do NOT write to Google Sheets",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    logger.info("Target: @%s", TARGET_USERNAME)
    logger.info("Posts to scrape: %d", args.posts)
    logger.info("Comments per post: %d", args.comments)
    logger.info("Dry run: %s", args.dry_run)

    scraper = InstagramScraper()

    # --- Profile ---------------------------------------------------------
    logger.info("Fetching profile @%s …", TARGET_USERNAME)
    profile = scraper.get_profile(TARGET_USERNAME)
    logger.info(
        "  %s | %s followers | %s posts",
        profile.full_name,
        f"{profile.follower_count:,}",
        profile.media_count,
    )

    # --- Posts -----------------------------------------------------------
    logger.info("Fetching %d posts …", args.posts)
    post_list = scraper.get_posts(TARGET_USERNAME, limit=args.posts)
    logger.info("  Retrieved %d posts", len(post_list.posts))

    # --- Comments (optional) --------------------------------------------
    comment_lists = []
    if args.comments > 0:
        logger.info("Fetching comments for each post (up to %d each) …", args.comments)
        for i, post in enumerate(post_list.posts, 1):
            logger.info(
                "  [%d/%d] post %s (%d comments available) …",
                i,
                len(post_list.posts),
                post.shortcode,
                post.comment_count,
            )
            try:
                cl = scraper.get_comments(post.media_id, limit=args.comments)
                comment_lists.append(cl)
                logger.info("    → fetched %d comments", len(cl.comments))
            except ValueError as exc:
                logger.warning("    → skipped: %s", exc)

            # Be polite to Instagram's rate limiter
            if i < len(post_list.posts):
                time.sleep(1.5)

    # --- Export ----------------------------------------------------------
    if args.dry_run:
        logger.info("Dry run complete — skipping Google Sheets export")
        _print_summary(profile, post_list, comment_lists)
        return

    logger.info("Connecting to Google Sheets …")
    exporter = GoogleSheetsExporter()
    exporter.export_all(profile, post_list, comment_lists)

    logger.info("Done! Data written to Google Sheets.")
    _print_summary(profile, post_list, comment_lists)


def _print_summary(profile, post_list, comment_lists) -> None:
    total_comments = sum(len(cl.comments) for cl in comment_lists)
    print("\n" + "=" * 50)
    print(f"  Profile:   @{profile.username} ({profile.full_name})")
    print(f"  Followers: {profile.follower_count:,}")
    print(f"  Posts:     {len(post_list.posts)} scraped")
    print(f"  Comments:  {total_comments} scraped across {len(comment_lists)} posts")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
