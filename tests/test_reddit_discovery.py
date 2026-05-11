import time
from unittest.mock import patch
from src.services.discovery.reddit import fetch_reddit_candidates


# Old-enough timestamp so the 2-day age filter doesn't reject the fixture.
_OLD_UTC = time.time() - 86400 * 14  # 14 days ago


def _make_listing(*, title: str = "TIL Apollo 11 carried a fallback rocket",
                  url: str = "https://example.com/source", score: int = 50000,
                  over_18: bool = False, created_utc: float = _OLD_UTC) -> dict:
    return {
        "data": {
            "children": [{
                "data": {
                    "title": title,
                    "url": url,
                    "permalink": f"/r/sub/comments/abc/{title[:10].lower().replace(' ', '_')}",
                    "score": score,
                    "num_comments": 120,
                    "over_18": over_18,
                    "created_utc": created_utc,
                },
            }],
        },
    }


_FAKE_LISTING = _make_listing()


def test_fetch_returns_candidates_per_subreddit():
    """Public .json endpoint — no credentials required."""
    with patch("src.services.discovery.reddit._fetch_subreddit_json", return_value=_FAKE_LISTING):
        candidates = fetch_reddit_candidates(subreddits=[("todayilearned", 1000)], limit=5)
    assert len(candidates) == 1
    assert candidates[0].source == "reddit"
    assert candidates[0].upvotes == 50000
    # TIL prefix stripped
    assert candidates[0].text.startswith("Apollo")


def test_fetch_tolerates_per_subreddit_failure():
    """One subreddit returning an error must not kill the others."""
    def side_effect(name, *args, **kwargs):
        if name == "AskHistorians":
            raise RuntimeError("rate limited")
        return _FAKE_LISTING

    with patch("src.services.discovery.reddit._fetch_subreddit_json", side_effect=side_effect):
        candidates = fetch_reddit_candidates(
            subreddits=[("todayilearned", 1000), ("AskHistorians", 1000), ("history", 1000)],
            limit=5,
        )
    # 2 candidates (TIL + history), AskHistorians failed.
    assert len(candidates) == 2


def test_fetch_skips_below_min_upvotes():
    low = _make_listing(score=500)
    with patch("src.services.discovery.reddit._fetch_subreddit_json", return_value=low):
        candidates = fetch_reddit_candidates(subreddits=[("todayilearned", 12000)], limit=5)
    assert candidates == []


def test_fetch_skips_over_18():
    nsfw = _make_listing(over_18=True)
    with patch("src.services.discovery.reddit._fetch_subreddit_json", return_value=nsfw):
        candidates = fetch_reddit_candidates(subreddits=[("todayilearned", 1000)], limit=5)
    assert candidates == []


def test_fetch_skips_recent_posts():
    fresh = _make_listing(created_utc=time.time() - 3600)  # 1 hour old
    with patch("src.services.discovery.reddit._fetch_subreddit_json", return_value=fresh):
        candidates = fetch_reddit_candidates(subreddits=[("todayilearned", 1000)], limit=5)
    assert candidates == []


def test_fetch_skips_rejected_terms():
    pol = _make_listing(title="TIL about the 2024 election polls")
    with patch("src.services.discovery.reddit._fetch_subreddit_json", return_value=pol):
        candidates = fetch_reddit_candidates(subreddits=[("todayilearned", 1000)], limit=5)
    assert candidates == []


def test_fetch_non_til_requires_external_link():
    """A history-sub post with only a self-link should be skipped — no source to verify against."""
    self_post = _make_listing(url="https://reddit.com/r/history/comments/xyz")
    with patch("src.services.discovery.reddit._fetch_subreddit_json", return_value=self_post):
        candidates = fetch_reddit_candidates(subreddits=[("history", 1000)], limit=5)
    assert candidates == []
