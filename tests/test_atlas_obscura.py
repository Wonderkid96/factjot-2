from unittest.mock import patch, MagicMock
from src.services.discovery.atlas_obscura import fetch_atlas_obscura_candidates


def test_fetch_atlas_returns_candidates():
    fake_feed = MagicMock()
    fake_feed.entries = [
        MagicMock(title="The forgotten library of Timbuktu", link="https://atlasobscura.com/x", summary="..."),
    ]
    with patch("src.services.discovery.atlas_obscura.feedparser.parse", return_value=fake_feed):
        candidates = fetch_atlas_obscura_candidates()
    assert len(candidates) == 1
    assert candidates[0].source == "atlas_obscura"
