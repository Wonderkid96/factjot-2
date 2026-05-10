"""Pool-then-rank sourcing orchestrator.

v1 lesson (Toby's audit): returning the first passing candidate gives "the same
boring image five times" because the cascade always converges on the same source
ordering. Better: pool 20-40 candidates across providers, score, vision-check the
top survivors, return the highest-scoring candidate that passes.

Hard validation (resolution gate) runs BEFORE scoring so junk never enters the pool.
Vision verification runs AFTER scoring on the top N — keeps Haiku calls bounded
even when the pool is large.
"""
from dataclasses import dataclass

from src.core.logger import get_logger
from src.pipelines.models import VisualBrief
from src.services.sourcing.wikimedia import (
    search_commons,
    traverse_category,
    WikimediaCandidate,
)
from src.services.sourcing.pexels import search_pexels_videos, PexelsVideoCandidate
from src.services.sourcing.pixabay import search_pixabay_videos, PixabayVideoCandidate
from src.services.verification.vision import check_image_subject


log = get_logger("sourcing.orchestrator")


# Provider tier — higher = more trusted. Wikimedia is curated; Pexels/Pixabay are stock.
PROVIDER_SCORE = {"wikimedia": 6, "pexels": 3, "pixabay": 2}

# How many top-ranked candidates to vision-verify before giving up. Bounds Haiku calls.
VISION_BUDGET = 3

# Quality floor: candidates below this resolution never enter the pool.
MIN_DIMENSION = 1080


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


def _passes_quality(asset: SourcedAsset) -> bool:
    """Hard gate: minimum resolution. Reject below 1080p before scoring."""
    return asset.width >= MIN_DIMENSION or asset.height >= MIN_DIMENSION


def _score(asset: SourcedAsset, brief: VisualBrief) -> int:
    """Deterministic score — higher is better.

    Components:
    - provider tier (Wikimedia > Pexels > Pixabay)
    - resolution bonus (≥2000px gets +2, ≥1500px gets +1)
    - media-type match with preferred_source (+2 if matches)
    """
    score = PROVIDER_SCORE.get(asset.provider, 0)
    longest = max(asset.width, asset.height)
    if longest >= 2000:
        score += 2
    elif longest >= 1500:
        score += 1
    if (brief.preferred_source == "video") == (asset.media_type == "video"):
        score += 2
    return score


def _safe(label: str, fn, *args, **kwargs):
    """Per-source error tolerance — one provider's timeout doesn't kill the pool."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log.warning("source_failed", source=label, error=str(e)[:200])
        return []


def _gather_pool(brief: VisualBrief, wikimedia_category: str | None) -> list[SourcedAsset]:
    """Collect candidates across all providers without picking yet.

    Wikimedia category (if available) goes first because it's the most curated.
    Then Wikimedia keyword search across the brief's queries. Then Pexels +
    Pixabay video search if the beat prefers motion.
    """
    pool: list[SourcedAsset] = []

    if wikimedia_category:
        for c in _safe("wikimedia_category", traverse_category, wikimedia_category):
            pool.append(_from_wm(c))

    for q in brief.queries[:3]:
        for c in _safe("wikimedia_search", search_commons, q):
            pool.append(_from_wm(c))

    if brief.preferred_source == "video":
        for q in brief.queries[:3]:
            for c in _safe("pexels", search_pexels_videos, q):
                pool.append(_from_pex(c))
            for c in _safe("pixabay", search_pixabay_videos, q):
                pool.append(_from_pix(c))
    else:
        # Even for image-preferred beats, fall back to Pexels stills if Wikimedia is dry
        for q in brief.queries[:2]:
            for c in _safe("pexels_fallback", search_pexels_videos, q):
                pool.append(_from_pex(c))

    return [a for a in pool if _passes_quality(a)]


def source_for_beat(brief: VisualBrief, wikimedia_category: str | None = None) -> SourcedAsset | None:
    """Pool-then-rank with best-effort fallback: gather → score → vision-check top N → pick.

    A non-empty pool ALWAYS returns an asset — beats with empty visuals look broken,
    so we'd rather use a Haiku-rejected candidate than nothing. Vision check is a
    quality preference, not a hard gate. Returns None only when the pool is truly
    empty (every provider returned zero or failed).
    """
    pool = _gather_pool(brief, wikimedia_category)
    if not pool:
        log.info("source_pool_empty", subject=brief.subject)
        return None

    pool.sort(key=lambda a: _score(a, brief), reverse=True)
    log.info("source_pool", subject=brief.subject, pool_size=len(pool), top_provider=pool[0].provider)

    # Vision verification only on images, budget-capped. Track the best image we saw
    # in case nothing passes — beats can't have empty slots.
    checked = 0
    for asset in pool:
        if asset.media_type != "image":
            # Videos skip vision check (frames vary too much for a single-frame test)
            return asset
        if checked >= VISION_BUDGET:
            log.info("source_picked_unverified", url=asset.source_url, provider=asset.provider, reason="vision_budget_spent")
            return asset
        if check_image_subject(asset.source_url, brief.subject):
            return asset
        checked += 1

    # Vision rejected every image we could afford to check. Return the highest-scored
    # candidate anyway — empty slots are worse than imperfect ones.
    log.info("source_picked_vision_rejected", url=pool[0].source_url, provider=pool[0].provider, checked=checked)
    return pool[0]
