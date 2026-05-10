from dataclasses import dataclass
from src.pipelines.models import VisualBrief
from src.services.sourcing.wikimedia import search_commons, traverse_category, WikimediaCandidate
from src.services.sourcing.pexels import search_pexels_videos, PexelsVideoCandidate
from src.services.sourcing.pixabay import search_pixabay_videos, PixabayVideoCandidate


@dataclass
class SourcedAsset:
    source_url: str
    width: int
    height: int
    provider: str
    license: str
    media_type: str  # "video" or "image"


def _from_wm(c: WikimediaCandidate) -> SourcedAsset:
    return SourcedAsset(c.source_url, c.width, c.height, "wikimedia", c.license, "image")


def _from_pex(c: PexelsVideoCandidate) -> SourcedAsset:
    return SourcedAsset(c.source_url, c.width, c.height, "pexels", c.license, "video")


def _from_pix(c: PixabayVideoCandidate) -> SourcedAsset:
    return SourcedAsset(c.source_url, c.width, c.height, "pixabay", c.license, "video")


def _quality_ok(asset: SourcedAsset) -> bool:
    """Carry-over from v1: minimum quality gate."""
    return asset.width >= 1080 or asset.height >= 1080


def source_for_beat(brief: VisualBrief, wikimedia_category: str | None = None) -> SourcedAsset | None:
    """Cascading sourcing per spec §10.4 + frontier #4 priority."""

    # R0 (frontier #4): Wikimedia category traversal if entity is named
    if wikimedia_category:
        for c in traverse_category(wikimedia_category):
            asset = _from_wm(c)
            if _quality_ok(asset):
                return asset

    # R1: Wikimedia search
    for q in brief.queries[:2]:
        for c in search_commons(q):
            asset = _from_wm(c)
            if _quality_ok(asset):
                return asset

    # R2: Pexels (video preferred for motion)
    if brief.preferred_source == "video":
        for q in brief.queries[:2]:
            for c in search_pexels_videos(q):
                asset = _from_pex(c)
                if _quality_ok(asset):
                    return asset

    # R3: Pixabay
    for q in brief.queries[:2]:
        for c in search_pixabay_videos(q):
            asset = _from_pix(c)
            if _quality_ok(asset):
                return asset

    return None
