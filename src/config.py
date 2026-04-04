from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Instagram
    instagram_username: str = ""
    instagram_password: str = ""
    instagram_session_id: str = ""

    # YouTube
    youtube_api_key: str = ""

    # TikTok
    tiktok_ms_token: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Cache TTL (seconds)
    cache_ttl: int = 300

    # Rate limits (requests per minute)
    instagram_rate_limit: int = 30
    tiktok_rate_limit: int = 60
    youtube_rate_limit: int = 100


settings = Settings()
