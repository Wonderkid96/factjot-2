from src.services.state.runs import RunContext


def test_run_context_creates_dir(tmp_path):
    rc = RunContext(run_id="2026-05-10_07-30_reel_evergreen_apollo-11", base=tmp_path)
    rc.ensure()
    assert rc.dir.exists()
    assert rc.audio_path.parent == rc.dir
    assert rc.video_path.parent == rc.dir
