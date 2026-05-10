from src.services.discovery.models import DiscoveredCandidate
from src.services.discovery.reddit import fetch_reddit_candidates
from src.services.discovery.wikipedia_dyk import fetch_dyk_candidates
from src.services.discovery.atlas_obscura import fetch_atlas_obscura_candidates
from src.services.discovery.hacker_news import fetch_hn_candidates
from src.services.discovery.wikidata_patterns import fetch_pattern_candidates


def discover_candidates(per_source_limit: int = 25) -> list[DiscoveredCandidate]:
    """Aggregate candidates from all enabled sources, dedupe by normalised text."""
    pool: list[DiscoveredCandidate] = []
    pool.extend(fetch_reddit_candidates(limit=per_source_limit))
    pool.extend(fetch_dyk_candidates(limit=per_source_limit))
    pool.extend(fetch_atlas_obscura_candidates(limit=per_source_limit))
    pool.extend(fetch_hn_candidates(limit=per_source_limit))
    pool.extend(fetch_pattern_candidates("lost_ships"))
    pool.extend(fetch_pattern_candidates("abandoned_megaprojects"))

    # Dedupe by normalised text; track which sources saw the same fact
    seen: dict[str, DiscoveredCandidate] = {}
    for c in pool:
        key = c.dedupe_key
        if key in seen:
            existing = seen[key]
            seen_in = existing.raw_metadata.setdefault("seen_in", [existing.source])
            if c.source not in seen_in:
                seen_in.append(c.source)
            existing.upvotes = max(existing.upvotes, c.upvotes)
        else:
            c.raw_metadata.setdefault("seen_in", [c.source])
            seen[key] = c
    return list(seen.values())
