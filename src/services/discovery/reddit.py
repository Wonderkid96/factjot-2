import praw
from src.core.config import Settings
from src.services.discovery.models import DiscoveredCandidate


DEFAULT_SUBREDDITS = ["todayilearned", "AskHistorians", "Damnthatsinteresting"]

_REDDIT_INSTANCE: praw.Reddit | None = None


def _reddit() -> praw.Reddit:
    global _REDDIT_INSTANCE
    if _REDDIT_INSTANCE is None:
        s = Settings()
        _REDDIT_INSTANCE = praw.Reddit(
            client_id=s.reddit_client_id,
            client_secret=s.reddit_client_secret,
            user_agent=s.reddit_user_agent,
        )
    return _REDDIT_INSTANCE


def fetch_reddit_candidates(subreddits: list[str] | None = None, limit: int = 25, time_filter: str = "week") -> list[DiscoveredCandidate]:
    s = Settings()
    if not s.reddit_client_id or not s.reddit_client_secret:
        # v1's .env has these as commented placeholders. Phase 1 dry-runs without Reddit
        # if credentials aren't set. Other discovery sources continue to work.
        import logging
        logging.getLogger(__name__).warning("REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET not set; skipping Reddit discovery.")
        return []
    out: list[DiscoveredCandidate] = []
    r = _reddit()
    for name in subreddits or DEFAULT_SUBREDDITS:
        for post in r.subreddit(name).top(time_filter=time_filter, limit=limit):
            text = post.title
            # r/todayilearned posts start with "TIL"; strip for cleaner candidate text
            if text.upper().startswith("TIL "):
                text = text[4:].strip()
            out.append(DiscoveredCandidate(
                text=text,
                source="reddit",
                source_url=f"https://reddit.com{post.permalink}",
                upvotes=int(post.score or 0),
                raw_metadata={"subreddit": name, "external_url": post.url},
            ))
    return out
