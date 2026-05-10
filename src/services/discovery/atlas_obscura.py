import feedparser
from src.services.discovery.models import DiscoveredCandidate

ATLAS_FEED = "https://www.atlasobscura.com/feeds/latest"


def fetch_atlas_obscura_candidates(limit: int = 20) -> list[DiscoveredCandidate]:
    feed = feedparser.parse(ATLAS_FEED)
    out: list[DiscoveredCandidate] = []
    for entry in feed.entries[:limit]:
        out.append(DiscoveredCandidate(
            text=entry.title,
            source="atlas_obscura",
            source_url=entry.link,
            raw_metadata={"summary": getattr(entry, "summary", "")},
        ))
    return out
