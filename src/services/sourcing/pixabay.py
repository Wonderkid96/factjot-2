from dataclasses import dataclass
from typing import Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import Settings


@dataclass
class PixabayVideoCandidate:
    source_url: str
    width: int
    height: int
    duration: int
    license: str = "Pixabay"
    provider: str = "pixabay"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get(params: dict) -> dict[str, Any]:
    r = requests.get("https://pixabay.com/api/videos/", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def search_pixabay_videos(query: str, per_page: int = 15, settings: Settings | None = None) -> list[PixabayVideoCandidate]:
    settings = settings or Settings()
    data = _get({
        "key": settings.pixabay_api_key,
        "q": query,
        "per_page": per_page,
        "video_type": "film",
    })
    out: list[PixabayVideoCandidate] = []
    for hit in data.get("hits", []):
        videos = hit.get("videos", {})
        # Pixabay returns {tiny, small, medium, large} variants
        best = videos.get("large") or videos.get("medium") or videos.get("small")
        if not best:
            continue
        out.append(PixabayVideoCandidate(
            source_url=best["url"],
            width=best.get("width", 0),
            height=best.get("height", 0),
            duration=hit.get("duration", 0),
        ))
    return out
