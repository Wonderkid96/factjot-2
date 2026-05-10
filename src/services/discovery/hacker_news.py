import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from src.services.discovery.models import DiscoveredCandidate

API = "https://hacker-news.firebaseio.com/v0"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get_top_ids() -> list[int]:
    return requests.get(f"{API}/topstories.json", timeout=15).json()


def _get_item(item_id: int) -> dict:
    return requests.get(f"{API}/item/{item_id}.json", timeout=15).json()


def fetch_hn_candidates(limit: int = 30, min_score: int = 200) -> list[DiscoveredCandidate]:
    ids = _get_top_ids()[:limit * 2]  # over-fetch since we filter
    out: list[DiscoveredCandidate] = []
    for item_id in ids:
        item = _get_item(item_id)
        if not item or not item.get("url") or item.get("score", 0) < min_score:
            continue
        out.append(DiscoveredCandidate(
            text=item["title"],
            source="hacker_news",
            source_url=item["url"],
            upvotes=item.get("score", 0),
        ))
        if len(out) >= limit:
            break
    return out
