from unittest.mock import patch
from src.services.sourcing.pexels import search_pexels_videos


def test_search_videos_returns_candidates():
    fake = {"videos": [{
        "id": 1, "url": "https://example", "duration": 12,
        "video_files": [{"link": "https://example/v.mp4", "width": 1920, "height": 1080}]
    }]}
    with patch("src.services.sourcing.pexels._get", return_value=fake):
        results = search_pexels_videos("apollo")
    assert len(results) == 1
    assert results[0].source_url.endswith(".mp4")
