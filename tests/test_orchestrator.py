from unittest.mock import patch
from src.services.sourcing.orchestrator import source_for_beat
from src.pipelines.models import VisualBrief


def _wm(url, w=2000, h=3000):
    return type("WM", (), {
        "source_url": url,
        "width": w,
        "height": h,
        "license": "PD",
        "provider": "wikimedia",
    })()


def _pex(url, w=1920, h=1080):
    return type("PEX", (), {
        "source_url": url,
        "width": w,
        "height": h,
        "duration": 10,
        "license": "Pexels",
        "provider": "pexels",
    })()


def _pix(url, w=1920, h=1080):
    return type("PIX", (), {
        "source_url": url,
        "width": w,
        "height": h,
        "duration": 10,
        "license": "Pixabay",
        "provider": "pixabay",
    })()


def _all_mocks():
    """Patch every external source to return [] by default — tests opt in by overriding."""
    return (
        patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]),
        patch("src.services.sourcing.orchestrator.search_commons", return_value=[]),
        patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[]),
        patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]),
        patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True),
    )


def test_orchestrator_prefers_wikimedia_category_when_present():
    vb = VisualBrief(subject="Johnstown Flood", queries=["johnstown flood"], preferred_source="image")
    cat_hit = _wm("https://wm/cat.jpg", w=2000, h=3000)
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[cat_hit]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        result = source_for_beat(vb, wikimedia_category="Category:Johnstown Flood")
    assert result is not None
    assert result.provider == "wikimedia"
    assert "wm/cat" in result.source_url


def test_orchestrator_picks_pexels_for_motion_when_wikimedia_empty():
    vb = VisualBrief(subject="ocean waves", queries=["ocean waves"], preferred_source="video")
    pex_hit = _pex("https://pex/v.mp4")
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[pex_hit]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        result = source_for_beat(vb)
    assert result is not None
    assert result.provider == "pexels"


def test_orchestrator_ranks_pool_picks_highest_score():
    """When multiple candidates pass quality, the one with the highest score wins."""
    vb = VisualBrief(subject="Apollo 11", queries=["apollo 11"], preferred_source="image")
    low_res_wm = _wm("https://wm/low.jpg", w=1100, h=1100)  # passes quality, low score
    hi_res_wm = _wm("https://wm/hi.jpg", w=4000, h=6000)    # passes quality, higher score
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[low_res_wm, hi_res_wm]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        result = source_for_beat(vb)
    assert result is not None
    assert result.source_url == "https://wm/hi.jpg"  # higher resolution → higher score


def test_orchestrator_drops_below_quality_floor():
    """720p candidate must be filtered out before the pool ever ranks."""
    vb = VisualBrief(subject="x", queries=["x"], preferred_source="image")
    sub_hd = _wm("https://wm/720.jpg", w=1280, h=720)
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[sub_hd]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        # 1280x720 has longest=1280 which IS >= MIN_DIMENSION (1080), so it actually passes
        result = source_for_beat(vb)
    assert result is not None
    # But a true sub-1080p candidate would be rejected:
    sub_min = _wm("https://wm/small.jpg", w=800, h=900)
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[sub_min]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        result = source_for_beat(vb)
    assert result is None  # nothing passed quality, pool empty


def test_orchestrator_runs_vision_check_on_archive_images():
    """Images must pass Haiku vision verification, even Wikimedia ones."""
    vb = VisualBrief(subject="Apollo 11", queries=["apollo 11"], preferred_source="image")
    wrong_subject = _wm("https://wm/wrong.jpg", w=2000, h=3000)
    right_subject = _wm("https://wm/right.jpg", w=1500, h=2000)
    # Vision rejects the first, accepts the second
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[wrong_subject, right_subject]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject",
               side_effect=lambda url, subj: "right" in url):
        result = source_for_beat(vb)
    assert result is not None
    assert "right" in result.source_url


def test_orchestrator_returns_none_when_pool_empty():
    vb = VisualBrief(subject="x", queries=["x"], preferred_source="video")
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        result = source_for_beat(vb)
    assert result is None


def test_orchestrator_video_preference_beats_high_res_wikimedia_still():
    """When preferred_source='video', a Pexels video must outrank a Wikimedia
    still even if the still has a higher provider tier and higher resolution.
    Regression guard: the previous scoring used +2 for type-match which was
    swallowed by the +3 Wikimedia tier gap, so videos silently lost.
    """
    vb = VisualBrief(subject="ocean", queries=["ocean waves"], preferred_source="video")
    wm_image = _wm("https://wm/big.jpg", w=4000, h=6000)   # tier 6 + max res
    pex_video = _pex("https://pex/wave.mp4", w=1920, h=1080)  # tier 3 + 1080p
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[wm_image]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[pex_video]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        result = source_for_beat(vb)
    assert result is not None
    assert result.provider == "pexels", "video preference must win when LLM asks for video"
    assert result.media_type == "video"


def test_orchestrator_image_preference_still_picks_wikimedia():
    """Inverse of the above — when preferred_source='image', the Wikimedia
    still must win even with a Pexels video also in the pool."""
    vb = VisualBrief(subject="JFK", queries=["jfk"], preferred_source="image")
    wm_image = _wm("https://wm/jfk.jpg", w=2000, h=3000)
    pex_video = _pex("https://pex/clip.mp4", w=3840, h=2160)  # higher res but wrong type
    with patch("src.services.sourcing.orchestrator.traverse_category", return_value=[]), \
         patch("src.services.sourcing.orchestrator.search_commons", return_value=[wm_image]), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[pex_video]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        result = source_for_beat(vb)
    assert result is not None
    assert result.provider == "wikimedia"
    assert result.media_type == "image"


def test_orchestrator_tolerates_provider_failure():
    """One provider raising an exception must not kill the pool — the rest continue."""
    vb = VisualBrief(subject="x", queries=["x"], preferred_source="video")
    pex_hit = _pex("https://pex/ok.mp4")
    with patch("src.services.sourcing.orchestrator.traverse_category", side_effect=RuntimeError("boom")), \
         patch("src.services.sourcing.orchestrator.search_commons", side_effect=TimeoutError("slow")), \
         patch("src.services.sourcing.orchestrator.search_pexels_videos", return_value=[pex_hit]), \
         patch("src.services.sourcing.orchestrator.search_pixabay_videos", return_value=[]), \
         patch("src.services.sourcing.orchestrator.check_image_subject", return_value=True):
        result = source_for_beat(vb, wikimedia_category="Category:X")
    assert result is not None
    assert result.provider == "pexels"
