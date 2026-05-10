import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from src.services.discovery.models import DiscoveredCandidate

DYK_URL = "https://en.wikipedia.org/wiki/Wikipedia:Recent_additions"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get_html(url: str = DYK_URL) -> str:
    r = requests.get(url, headers={"User-Agent": "FactJotV2/0.1"}, timeout=30)
    r.raise_for_status()
    return r.text


def fetch_dyk_candidates(limit: int = 30) -> list[DiscoveredCandidate]:
    soup = BeautifulSoup(_get_html(), "html.parser")
    out: list[DiscoveredCandidate] = []
    for li in soup.find_all("li"):
        text = li.get_text().strip()
        if not text.startswith("...") and not text.lower().startswith("that "):
            continue
        # Strip leading "..." and "that "
        cleaned = text.lstrip(".").strip()
        if cleaned.lower().startswith("that "):
            cleaned = cleaned[5:].strip()
        if cleaned.endswith("?"):
            cleaned = cleaned[:-1].strip()
        # Find a link if any to use as source
        link = li.find("a", href=True)
        source_url = "https://en.wikipedia.org" + link["href"] if link else "https://en.wikipedia.org/wiki/Wikipedia:Recent_additions"
        out.append(DiscoveredCandidate(
            text=cleaned,
            source="wikipedia_dyk",
            source_url=source_url,
        ))
        if len(out) >= limit:
            break
    return out
