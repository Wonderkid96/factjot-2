from enum import Enum
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    YOUTUBE_SHORTS = "youtube_shorts"


class Brief(BaseModel):
    topic: str
    angle: str
    format: Literal["fact", "list"] = "fact"
    pipeline_name: str = "reel_evergreen"


class Citation(BaseModel):
    claim: str
    source_url: str
    source_quote: str = ""


class VisualBrief(BaseModel):
    subject: str
    shot_type: Literal["wide", "close", "macro", "aerial", "static", "motion"] = "wide"
    mood: str = ""
    queries: list[str] = Field(default_factory=list)
    preferred_source: Literal["video", "image"] = "video"
    ai_fallback_prompt: str = ""
    period_constraints: dict[str, int | list[str]] | None = None


class Beat(BaseModel):
    text: str
    visual_brief: VisualBrief | dict = Field(default_factory=dict)


class PostMetadata(BaseModel):
    title: str
    description: str = ""
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    youtube_tags: list[str] = Field(default_factory=list)


class Script(BaseModel):
    title: str
    hook: str
    beats: list[Beat]
    cta: str
    citations: list[Citation]
    post_metadata: PostMetadata | None = None


class MediaAsset(BaseModel):
    beat_index: int
    local_path: Path
    source_url: str
    provider: str
    license: str = "unknown"
    width: int = 0
    height: int = 0


class MediaSet(BaseModel):
    assets: list[MediaAsset] = Field(default_factory=list)
    narration_audio: Path | None = None
    narration_alignment: list[dict] = Field(default_factory=list)


class Verification(BaseModel):
    verified: bool
    failures: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class PublishResult(BaseModel):
    platform: Platform
    posted: bool
    remote_id: str | None = None
    error: str | None = None
