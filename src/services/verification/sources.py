"""Source gathering for fact-check verification.

`fact_checker.verify_claim()` needs ≥2 sources to make a confident call.
For a Reddit-sourced topic, the cheapest two we can reliably fetch are:
  1. The post's external link (`raw_metadata.external_url`) — the source the
     Reddit submitter pointed at. Often a news article, Wikipedia, NASA, etc.
  2. The Wikipedia REST summary for the strongest noun-phrase in the topic.
     Free, fast, no auth, and Wikipedia's coverage is broad.

If we can't find ≥2 sources the topic is rejected outright — better to skip
the run than ship a hallucinated story.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import requests

from src.core.logger import get_logger


log = get_logger("verification.sources")

WIKIPEDIA_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
USER_AGENT = "factjot-v2/0.1 (https://factjot.com; tobyjohnsonemail@gmail.com)"


@dataclass
class GatheredSource:
    url: str
    snippet: str  # 1-3 sentence extract, shown to the LLM judge


def _wiki_summary(query: str) -> GatheredSource | None:
    """Fetch a Wikipedia REST summary for the best-guess title. Returns None
    on miss / disambiguation / rate-limit."""
    title = query.strip().replace(" ", "_")
    if not title:
        return None
    try:
        resp = requests.get(
            WIKIPEDIA_SUMMARY.format(title=requests.utils.quote(title, safe="")),
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            extract = data.get("extract") or ""
            if extract and len(extract) > 80:
                return GatheredSource(
                    url=data.get("content_urls", {}).get("desktop", {}).get("page")
                        or f"https://en.wikipedia.org/wiki/{title}",
                    snippet=extract[:600],
                )
    except Exception as exc:
        log.warning("wikipedia_summary_failed", query=query, error=str(exc)[:200])
    return None


# Crude noun-phrase candidate extractor. Picks the longest run of
# Capitalised tokens (likely a proper noun) followed by the longest noun-
# looking word. Good enough for "Solarpunk", "Tsutomu Yamaguchi", "Apollo 11".
_PROPER_RE = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3})\b")


def _candidate_titles(topic_text: str) -> list[str]:
    candidates: list[str] = []
    for m in _PROPER_RE.finditer(topic_text):
        c = m.group(1).strip()
        if c.lower() not in {"the", "a", "an", "til"} and c not in candidates:
            candidates.append(c)
    return candidates[:4]  # bound the Wikipedia calls


def gather_sources_for_topic(
    topic_text: str,
    external_url: str | None = None,
    reddit_url: str | None = None,
) -> list[GatheredSource]:
    """Build the source list for a topic.

    Strategy:
    - If the Reddit post has an external link, include it (snippet = the
      topic title as a stand-in; the judge already sees the URL).
    - Try Wikipedia summaries on the topic's proper-noun candidates.
    - Include the Reddit thread itself only as a last-resort 2nd source
      (lower trust — it's the claim's origin, not a corroboration).
    """
    out: list[GatheredSource] = []
    if external_url and "reddit.com" not in (external_url or "").lower():
        out.append(GatheredSource(url=external_url, snippet=f"external link cited by submitter: {topic_text[:200]}"))

    for title in _candidate_titles(topic_text):
        src = _wiki_summary(title)
        if src and src.url not in {s.url for s in out}:
            out.append(src)
            if len(out) >= 3:
                break

    if len(out) < 2 and reddit_url:
        out.append(GatheredSource(
            url=reddit_url,
            snippet=f"reddit thread (source of original claim, lower trust): {topic_text[:200]}",
        ))
    return out
