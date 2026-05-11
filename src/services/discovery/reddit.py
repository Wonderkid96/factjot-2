"""Reddit discovery via the public .json endpoint — no app registration needed.

Reddit exposes any subreddit as JSON at `https://www.reddit.com/r/<sub>/<sort>.json`.
This works without OAuth or a registered app, just a polite User-Agent.

V1 lesson (Insta-bot/src/research/story_scout.py): a flat "highest-upvote
wins" pick floods the pipeline with viral-but-fabricated stories from subs
like r/interestingasfuck. V1 mitigated this with per-sub upvote thresholds,
REJECT_TERMS, a 2-day age minimum, and multi-factor scoring. This module
ports + tightens that approach: drops the three highest-volume but lowest-
truth subs, requires NSFW=False, demands external sources outside TIL.
"""
import re
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import Settings
from src.core.logger import get_logger
from src.services.discovery.models import DiscoveredCandidate


REDDIT_BASE = "https://www.reddit.com"
SLEEP_BETWEEN_SUBREDDITS = 1.5
USER_AGENT_FALLBACK = "factjot-v2/0.1"

# Subreddit curation — (name, min_upvotes). Sources are ordered by truth
# rigor, NOT by engagement. r/todayilearned mandates every post link to a
# verifiable source — that's the gold standard. The high-engagement
# offenders (interestingasfuck, Damnthatsinteresting, BeAmazed) are dropped
# because their feed is dominated by staged/fabricated content.
CURATED_SUBREDDITS: list[tuple[str, int]] = [
    # Tier 1 — strict moderation, mandatory sourcing
    ("todayilearned",        12000),
    ("AskHistorians",         1500),
    ("AskScience",            1500),
    ("science",               2000),
    # Tier 2 — photo-anchored, harder to fake
    ("HistoryPorn",           3000),
    ("ArtefactPorn",          2000),
    ("MapPorn",               2000),
    ("space",                 3000),
    # Tier 3 — quality-variable but useful breadth
    ("DataIsBeautiful",       3000),
    ("UnresolvedMysteries",   1500),
    ("UnpopularFacts",        1500),
    ("TheDepthsBelow",        1500),
    ("history",               3000),
]

# Reject any title containing these tokens (case-insensitive substring match).
# Political/election content is divisive and ages poorly; nsfw/graphic/gore
# fail Meta upload policy; rumour/leak/opinion aren't fact-shaped.
REJECT_TERMS = (
    "politics", "election", "biden", "trump", "putin", "rally",
    "rumour", "rumor", "leak", "leaked", "opinion",
    "nsfw", "graphic", "gore", "nude", "porn",
    "[serious]",
)

# Skip posts younger than this many days. Reddit's first-48-hour cycle is
# dominated by viral-but-unverified posts; mature posts have had time to be
# debunked in comments.
MIN_AGE_DAYS = 2

log = get_logger("discovery.reddit")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
def _fetch_subreddit_json(name: str, sort: str, t: str, limit: int, user_agent: str) -> dict:
    url = f"{REDDIT_BASE}/r/{name}/{sort}.json"
    r = requests.get(
        url,
        headers={"User-Agent": user_agent},
        params={"limit": min(limit, 100), "t": t},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def _is_external(post: dict) -> bool:
    """True if the post links to a non-Reddit URL (the typical TIL pattern)."""
    url = (post.get("url") or "").lower()
    if not url:
        return False
    if "reddit.com" in url or url.startswith("/r/") or "redd.it" in url:
        return False
    return True


def _passes_reject_filter(text: str) -> bool:
    tl = text.lower()
    return not any(bad in tl for bad in REJECT_TERMS)


def fetch_reddit_candidates(
    subreddits: list[tuple[str, int]] | None = None,
    limit: int = 25,
    sort: str = "top",
    timeframe: str = "month",
) -> list[DiscoveredCandidate]:
    """Pull top posts from each curated subreddit. Returns DiscoveredCandidates.

    Args:
        subreddits: list of (name, min_upvotes) tuples. Defaults to CURATED_SUBREDDITS.
        limit: per-subreddit fetch limit.
        sort: "top" (proven), "hot" (currently-popular), "new", "rising".
        timeframe: when sort="top", which window — "day", "week", "month", "year", "all".

    Filters applied per candidate:
    - upvotes >= sub's min_upvotes
    - age >= MIN_AGE_DAYS
    - over_18 != True
    - title does not contain any REJECT_TERMS
    - non-TIL subs require an external link (TIL posts have sources in comments)
    """
    settings = Settings()
    user_agent = settings.reddit_user_agent or USER_AGENT_FALLBACK
    out: list[DiscoveredCandidate] = []
    now = time.time()
    subs = subreddits or CURATED_SUBREDDITS

    for i, (name, min_upvotes) in enumerate(subs):
        if i > 0:
            time.sleep(SLEEP_BETWEEN_SUBREDDITS)
        try:
            data = _fetch_subreddit_json(name, sort, timeframe, limit, user_agent)
        except Exception as e:
            log.warning("reddit_fetch_failed", subreddit=name, error=str(e)[:200])
            continue

        children = data.get("data", {}).get("children", [])
        for child in children[:limit]:
            post = child.get("data", {})
            title = post.get("title", "")
            if not title:
                continue

            ups = int(post.get("score") or 0)
            if ups < min_upvotes:
                continue
            if post.get("over_18"):
                continue
            age_days = (now - float(post.get("created_utc", now) or now)) / 86400
            if age_days < MIN_AGE_DAYS:
                continue
            if not _passes_reject_filter(title):
                continue
            # Non-TIL: require an external link so the topic has a referenceable source.
            if name.lower() != "todayilearned" and not _is_external(post):
                continue

            text = title
            if text.upper().startswith("TIL "):
                text = text[4:].strip()
            # TIL titles often start with "that " — clean for readability
            if text.lower().startswith("that "):
                text = text[5:].strip()
            # TIL titles often end with a parenthesised note — keep but flag
            text = re.sub(r"\s+", " ", text).strip()

            out.append(DiscoveredCandidate(
                text=text,
                source="reddit",
                source_url=REDDIT_BASE + post.get("permalink", ""),
                upvotes=ups,
                raw_metadata={
                    "subreddit": name,
                    "external_url": post.get("url"),
                    "is_external": _is_external(post),
                    "over_18": bool(post.get("over_18")),
                    "num_comments": post.get("num_comments", 0),
                    "age_days": round(age_days, 2),
                },
            ))
    return out


# Back-compat: callers passing list[str] still work, mapped to default threshold of 1500.
def fetch_reddit_candidates_str(subreddits: list[str], **kwargs) -> list[DiscoveredCandidate]:
    return fetch_reddit_candidates(
        subreddits=[(s, 1500) for s in subreddits],
        **kwargs,
    )
