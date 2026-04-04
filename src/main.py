"""
Social Media Scraping API
=========================
FastAPI application that exposes scraping endpoints for Instagram, TikTok,
and YouTube.

Run locally:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

Interactive docs:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import instagram, tiktok, youtube
from src.config import settings

app = FastAPI(
    title="Social Media Scraping API",
    description=(
        "Scrape public data from Instagram, TikTok, and YouTube. "
        "Provides profiles, posts/videos, comments, and engagement metrics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Register platform routers under /api/v1
app.include_router(instagram.router, prefix="/api/v1")
app.include_router(tiktok.router, prefix="/api/v1")
app.include_router(youtube.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    """Health check / API info."""
    return {
        "name": "Social Media Scraping API",
        "version": "1.0.0",
        "platforms": ["instagram", "tiktok", "youtube"],
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
