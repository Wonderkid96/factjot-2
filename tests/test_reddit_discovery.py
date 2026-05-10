from unittest.mock import patch, MagicMock
from src.services.discovery.reddit import fetch_reddit_candidates


def test_fetch_returns_candidates_per_subreddit(monkeypatch):
    monkeypatch.setenv("REDDIT_CLIENT_ID", "fake_id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "fake_secret")
    fake_post = MagicMock()
    fake_post.title = "TIL Apollo 11 carried a fallback rocket"
    fake_post.url = "https://example.com/source"
    fake_post.permalink = "/r/todayilearned/comments/abc/til_apollo"
    fake_post.score = 50000
    with patch("src.services.discovery.reddit._reddit") as r:
        r.return_value.subreddit.return_value.top.return_value = [fake_post]
        candidates = fetch_reddit_candidates(subreddits=["todayilearned"], limit=5)
    assert len(candidates) >= 1
    assert candidates[0].source == "reddit"
    assert candidates[0].upvotes == 50000


def test_fetch_returns_empty_when_credentials_missing(monkeypatch):
    """Reddit credentials are optional in v1's .env; fetcher must not crash without them."""
    from src.services.discovery import reddit as reddit_module
    # Reset the module-level singleton so the new credentials take effect
    reddit_module._REDDIT_INSTANCE = None
    monkeypatch.setenv("REDDIT_CLIENT_ID", "")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "")
    candidates = reddit_module.fetch_reddit_candidates(subreddits=["todayilearned"], limit=5)
    assert candidates == []
