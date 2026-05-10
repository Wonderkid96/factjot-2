from unittest.mock import patch
from src.services.discovery.hacker_news import fetch_hn_candidates


def test_fetch_hn_returns_candidates():
    with patch("src.services.discovery.hacker_news._get_top_ids", return_value=[1, 2]):
        with patch("src.services.discovery.hacker_news._get_item", side_effect=[
            {"title": "A surprising study about cats", "url": "https://example.com/cats", "score": 500},
            {"title": "Ask HN: thoughts?", "url": None, "score": 50},  # filtered: no url + low score
        ]):
            candidates = fetch_hn_candidates(limit=2)
    assert len(candidates) == 1
    assert "cats" in candidates[0].text.lower()
