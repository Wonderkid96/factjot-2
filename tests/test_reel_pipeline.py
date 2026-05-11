from src.pipelines.reel_evergreen.pipeline import ReelEvergreenPipeline
from src.pipelines.models import Platform


def test_pipeline_metadata():
    p = ReelEvergreenPipeline()
    assert p.name == "reel_evergreen"
    assert Platform.INSTAGRAM in p.target_platforms
    assert Platform.YOUTUBE_SHORTS in p.target_platforms
    assert p.remotion_composition == "CaseFileReel"


def test_pipeline_run_id_stable_across_stages():
    """Bug guard: acquire_media and render must use the same run_id."""
    p = ReelEvergreenPipeline()
    # source() seeds run_id; subsequent stages reuse it.
    rid1 = p._ensure_run_id("test slug")
    rid2 = p._ensure_run_id("test slug 2")  # second call ignored -- already seeded
    assert rid1 == rid2
