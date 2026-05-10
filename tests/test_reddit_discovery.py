from unittest.mock import patch
from src.services.discovery.reddit import fetch_reddit_candidates


_FAKE_LISTING = {
    "data": {
        "children": [
            {
                "data": {
                    "title": "TIL Apollo 11 carried a fallback rocket",
                    "url": "https://example.com/source",
                    "permalink": "/r/todayilearned/comments/abc/til_apollo",
                    "score": 50000,
                    "num_comments": 120,
                    "over_18": False,
                }
            }
        ]
    }
}


def test_fetch_returns_candidates_per_subreddit():
    """Public .json endpoint — no credentials required."""
    with patch("src.services.discovery.reddit._fetch_subreddit_json", return_value=_FAKE_LISTING):
        candidates = fetch_reddit_candidates(subreddits=["todayilearned"], limit=5)
    assert len(candidates) == 1
    assert candidates[0].source == "reddit"
    assert candidates[0].upvotes == 50000
    # TIL prefix stripped
    assert candidates[0].text.startswith("Apollo")
    assert candidates[0].source_url == "https://www.reddit.com/r/todayilearned/comments/abc/til_apollo"


def test_fetch_tolerates_per_subreddit_failure():
    """One subreddit returning an error must not kill the others."""
    def side_effect(name, *args, **kwargs):
        if name == "AskHistorians":
            raise RuntimeError("rate limited")
        return _FAKE_LISTING

    with patch("src.services.discovery.reddit._fetch_subreddit_json", side_effect=side_effect):
        candidates = fetch_reddit_candidates(
            subreddits=["todayilearned", "AskHistorians", "Damnthatsinteresting"], limit=5
        )
    # 1 candidate from todayilearned, 0 from AskHistorians (failed), 1 from Damnthatsinteresting
    assert len(candidates) == 2
