from src.services.resolution.wikidata import _sparql
from src.services.discovery.models import DiscoveredCandidate


PATTERNS = {
    "lost_ships": """
        SELECT DISTINCT ?item ?itemLabel ?description WHERE {
          ?item wdt:P31/wdt:P279* wd:Q11446.
          ?item wdt:P5008 wd:Q3884.
          ?item schema:description ?description.
          FILTER(LANG(?description) = "en").
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 20
    """,
    "abandoned_megaprojects": """
        SELECT DISTINCT ?item ?itemLabel ?description WHERE {
          ?item wdt:P31/wdt:P279* wd:Q4830453.
          ?item wdt:P576 ?date.
          ?item schema:description ?description.
          FILTER(LANG(?description) = "en").
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 20
    """,
}


def fetch_pattern_candidates(pattern_key: str = "lost_ships") -> list[DiscoveredCandidate]:
    if pattern_key not in PATTERNS:
        return []
    data = _sparql(PATTERNS[pattern_key])
    out: list[DiscoveredCandidate] = []
    for b in data.get("results", {}).get("bindings", []):
        label = b.get("itemLabel", {}).get("value", "")
        desc = b.get("description", {}).get("value", "")
        item_url = b["item"]["value"]
        out.append(DiscoveredCandidate(
            text=f"{label}: {desc}",
            source="wikidata",
            source_url=item_url,
            raw_metadata={"pattern": pattern_key},
        ))
    return out
