"""Reddit discovery via the public .json endpoint — no app registration needed.

Reddit exposes any subreddit as JSON at `https://www.reddit.com/r/<sub>/<sort>.json`.
This works without OAuth or a registered app, just a polite User-Agent.

We previously used `praw`, which required REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET
from a registered Reddit script app. Toby pointed out the .json approach during
M24 debugging (2026-05-10) — simpler, fewer dependencies, no registration step.

Anti-bot rules to respect:
- Distinctive User-Agent (we read REDDIT_USER_AGENT from .env)
- Rate limit: ~60 req/min unauthenticated; we sleep between subreddits
- 429/403 responses = back off
"""
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import Settings
from src.core.logger import get_logger
from src.services.discovery.models import DiscoveredCandidate


DEFAULT_SUBREDDITS = [
    # Tier 1 (Toby's preferred — top of the pile)
    "UnpopularFacts",
    "todayilearned",
    "Damnthatsinteresting",
    "interestingasfuck",
    "BeAmazed",
    "UnresolvedMysteries",
    "MorbidReality",
    "HistoryPorn",
    "ArtefactPorn",
    "MapPorn",
    # Tier 2 (extended pool)
    "AskHistorians",
    "AskScience",
    "science",
    "DataIsBeautiful",
    "morbidcuriosity",
    "TheDepthsBelow",
    "space",
    "Futurology",
]
REDDIT_BASE = "https://www.reddit.com"
SLEEP_BETWEEN_SUBREDDITS = 1.5  # be polite

log = get_logger("discovery.reddit")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
def _fetch_subreddit_json(name: str, sort: str, limit: int, user_agent: str) -> dict:
    url = f"{REDDIT_BASE}/r/{name}/{sort}.json"
    r = requests.get(
        url,
        headers={"User-Agent": user_agent},
        params={"limit": min(limit, 100)},  # Reddit caps at 100 per page
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def fetch_reddit_candidates(
    subreddits: list[str] | None = None,
    limit: int = 25,
    sort: str = "top",
) -> list[DiscoveredCandidate]:
    """Pull recent / top posts from each subreddit. Returns DiscoveredCandidates.

    `sort` is one of: "hot", "new", "top", "rising". Default "top" matches
    the previous praw behaviour (high-quality posts).
    """
    settings = Settings()
    user_agent = settings.reddit_user_agent or "factjot-v2/0.1"

    out: list[DiscoveredCandidate] = []
    for i, name in enumerate(subreddits or DEFAULT_SUBREDDITS):
        if i > 0:
            time.sleep(SLEEP_BETWEEN_SUBREDDITS)
        try:
            data = _fetch_subreddit_json(name, sort, limit, user_agent)
        except Exception as e:
            log.warning("reddit_fetch_failed", subreddit=name, error=str(e)[:200])
            continue

        children = data.get("data", {}).get("children", [])
        for child in children[:limit]:
            post = child.get("data", {})
            title = post.get("title", "")
            if not title:
                continue
            text = title
            # r/todayilearned posts start with "TIL"; strip for cleaner candidate text
            if text.upper().startswith("TIL "):
                text = text[4:].strip()

            out.append(DiscoveredCandidate(
                text=text,
                source="reddit",
                source_url=REDDIT_BASE + post.get("permalink", ""),
                upvotes=int(post.get("score") or 0),
                raw_metadata={
                    "subreddit": name,
                    "external_url": post.get("url"),
                    "over_18": post.get("over_18", False),
                    "num_comments": post.get("num_comments", 0),
                },
            ))
    return out
