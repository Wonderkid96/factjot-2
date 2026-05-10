from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

    # Narration
    elevenlabs_api_key: str = Field(..., alias="ELEVENLABS_API_KEY")
    elevenlabs_voice: str = Field(default="3WqHLnw80rOZqJzW9YRB", alias="ELEVENLABS_VOICE")

    # Sourcing
    pexels_api_key: str = Field(..., alias="PEXELS_API_KEY")
    pixabay_api_key: str = Field(..., alias="PIXABAY_API_KEY")
    smithsonian_api_key: str = Field(default="DEMO_KEY", alias="SMITHSONIAN_API_KEY")
    tmdb_api_key: str | None = Field(default=None, alias="TMDB_API_KEY")

    # Instagram
    meta_access_token: str = Field(..., alias="META_ACCESS_TOKEN")
    instagram_account_id: str = Field(..., alias="INSTAGRAM_ACCOUNT_ID")
    facebook_page_id: str = Field(..., alias="FACEBOOK_PAGE_ID")
    imgbb_api_key: str = Field(..., alias="IMGBB_API_KEY")

    # YouTube (not present in v1 .env; required once YouTube pipeline is wired)
    youtube_client_id: str | None = Field(default=None, alias="YOUTUBE_CLIENT_ID")
    youtube_client_secret: str | None = Field(default=None, alias="YOUTUBE_CLIENT_SECRET")
    youtube_refresh_token: str | None = Field(default=None, alias="YOUTUBE_REFRESH_TOKEN")

    # Phase 1 mode
    dry_run: bool = Field(default=True, alias="DRY_RUN")
