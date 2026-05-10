from dataclasses import dataclass
from typing import Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


@dataclass
class WikidataEntity:
    entity_id: str
    label: str
    date: str | None
    location: str | None
    wikimedia_category: str | None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _sparql(query: str) -> dict[str, Any]:
    r = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": "FactJotV2/0.1 (https://github.com/factjot)"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def resolve_entity(topic: str) -> WikidataEntity | None:
    """Best-effort label match for an event/person/place. Returns None on no hit."""
    safe = topic.replace('"', '\\"')
    q = f"""
    SELECT ?item ?itemLabel ?date ?coords ?category WHERE {{
      ?item rdfs:label "{safe}"@en.
      OPTIONAL {{ ?item wdt:P585 ?date. }}
      OPTIONAL {{ ?item wdt:P625 ?coords. }}
      OPTIONAL {{ ?item wdt:P373 ?category. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} LIMIT 1
    """
    data = _sparql(q)
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return None
    b = bindings[0]
    return WikidataEntity(
        entity_id=b["item"]["value"].rsplit("/", 1)[-1],
        label=b.get("itemLabel", {}).get("value", topic),
        date=b.get("date", {}).get("value"),
        location=b.get("coords", {}).get("value"),
        wikimedia_category="Category:" + b["category"]["value"] if "category" in b else None,
    )
