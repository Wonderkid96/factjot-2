from unittest.mock import patch
from src.services.sourcing.orchestrator import source_for_beat
from src.pipelines.models import VisualBrief


def test_orchestrator_prefers_wikimedia_category_when_present():
    vb = VisualBrief(subject="Johnstown Flood", queries=["johnstown flood"], preferred_source="image")
    fake_wm = type("C", (), {
        "source_url": "https://wm/cat.jpg",
        "width": 2000,
        "height": 3000,
        "license": "PD",
        "provider": "wikimedia",
    })()
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[fake_wm]):
        result = source_for_beat(vb, wikimedia_category="Category:Johnstown Flood")
    assert result.provider == "wikimedia"
    assert "wm/cat" in result.source_url


def test_orchestrator_falls_through_to_pexels_for_motion():
    vb = VisualBrief(subject="ocean waves", queries=["ocean waves"], preferred_source="video")
    fake_pex = type("V", (), {
        "source_url": "https://pex/v.mp4",
        "width": 1920,
        "height": 1080,
        "duration": 10,
        "license": "Pexels",
        "provider": "pexels",
    })()
    with patch("src.services.sourcing.orchestrator.search_commons", return_value=[]):
        with patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[fake_pex]):
            result = source_for_beat(vb)
    assert result.provider == "pexels"
