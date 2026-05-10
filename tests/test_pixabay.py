from unittest.mock import patch
from src.services.sourcing.pixabay import search_pixabay_videos


def test_search_returns_candidates():
    fake = {"hits": [{
        "videos": {"large": {"url": "https://x/v.mp4", "width": 1920, "height": 1080}},
        "duration": 10,
    }]}
    with patch("src.services.sourcing.pixabay._get", return_value=fake):
        results = search_pixabay_videos("apollo")
    assert len(results) >= 1
