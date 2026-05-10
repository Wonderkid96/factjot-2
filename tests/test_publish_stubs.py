from src.services.publish.instagram import publish_to_instagram
from src.services.publish.youtube import publish_to_youtube


def test_instagram_returns_dry_run_in_phase1(monkeypatch, tmp_path):
    monkeypatch.setenv("DRY_RUN", "true")
    f = tmp_path / "v.mp4"; f.write_bytes(b"")
    result = publish_to_instagram(f, caption="hi")
    assert not result.posted
    assert "dry-run" in (result.error or "").lower()


def test_youtube_returns_dry_run_in_phase1(monkeypatch, tmp_path):
    monkeypatch.setenv("DRY_RUN", "true")
    f = tmp_path / "v.mp4"; f.write_bytes(b"")
    result = publish_to_youtube(f, title="t", description="d")
    assert not result.posted
