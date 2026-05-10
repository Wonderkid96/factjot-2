from dataclasses import dataclass
from typing import Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import Settings


@dataclass
class PexelsVideoCandidate:
    source_url: str
    width: int
    height: int
    duration: int
    license: str = "Pexels"
    provider: str = "pexels"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get(url: str, params: dict, settings: Settings) -> dict[str, Any]:
    r = requests.get(
        url,
        params=params,
        headers={"Authorization": settings.pexels_api_key},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def search_pexels_videos(query: str, per_page: int = 15, settings: Settings | None = None) -> list[PexelsVideoCandidate]:
    settings = settings or Settings()
    data = _get(
        "https://api.pexels.com/videos/search",
        {"query": query, "per_page": per_page, "orientation": "portrait"},
        settings,
    )
    out: list[PexelsVideoCandidate] = []
    for v in data.get("videos", []):
        # Pick the highest-resolution portrait MP4
        best = max(
            v.get("video_files", []),
            key=lambda f: f.get("width", 0) * f.get("height", 0),
            default=None,
        )
        if not best:
            continue
        out.append(PexelsVideoCandidate(
            source_url=best["link"],
            width=best.get("width", 0),
            height=best.get("height", 0),
            duration=v.get("duration", 0),
        ))
    return out
