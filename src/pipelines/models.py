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


SceneTreatment = Literal[
    "polaroid",        # photo wrapped in white border + tape, slid onto desk
    "evidence_slide",  # document slides in from off-canvas, settles in frame
    "redacted_doc",    # typewriter paragraph with sweeping black bars
    "stamp_reveal",    # asset already on screen, big stamp slams in over it
    "index_card",      # typed monospaced fact on a manila card
    "newsprint_clip",  # halftone-filtered image inside a yellowed newspaper crop
    "archive_film",    # black-and-white film-strip frame around moving asset
    "map_pin",         # asset on a map fragment with a pin drop
    "red_thread",      # connects this beat's pinned asset to the prior one
    "ken_burns",       # the v1 fallback — full-bleed asset with slow zoom
]


class Beat(BaseModel):
    text: str
    visual_brief: VisualBrief | dict = Field(default_factory=dict)
    # Directorial choice the script writer picks for this beat. Drives which
    # CaseFileReel scene component renders the asset. Falls back to the
    # full-bleed Ken Burns treatment when the writer omits or the renderer
    # can't satisfy the chosen treatment (e.g. red_thread on beat 0).
    scene_treatment: SceneTreatment = "ken_burns"


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
    # Top-level entity anchor for the whole reel. Used to propagate Wikimedia
    # category sourcing to every beat — a JFK reel pulls from
    # Category:John F. Kennedy across all 6 beats, not just the one whose
    # visual_brief happens to mention him. None for abstract topics with no
    # specific person/place/event/object at the centre.
    topic_entity: str | None = None


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
