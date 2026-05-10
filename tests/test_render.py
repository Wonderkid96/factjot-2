from unittest.mock import patch, MagicMock
from pathlib import Path
from src.services.render.remotion import build_video_spec, render_via_remotion
from src.pipelines.models import Script, Beat, VisualBrief, MediaSet, MediaAsset


def test_build_video_spec_produces_json_serialisable_dict():
    script = Script(
        title="t", hook="h",
        beats=[Beat(text="t1", visual_brief=VisualBrief(subject="x", queries=["x"]))],
        cta="c", citations=[]
    )
    media = MediaSet(
        assets=[MediaAsset(beat_index=0, local_path=Path("/tmp/a.jpg"), source_url="https://x", provider="wikimedia")],
        narration_audio=Path("/tmp/n.mp3"),
        narration_alignment=[{"word": "h", "start": 0, "end": 0.3}],
    )
    spec = build_video_spec(script, media, composition_id="FactReel")
    assert spec["composition"] == "FactReel"
    assert len(spec["beats"]) == 1
    assert spec["beats"][0]["asset"]["path"].endswith("a.jpg")
    assert "start_frame" in spec["beats"][0]
    assert "end_frame" in spec["beats"][0]


def test_render_invokes_subprocess(tmp_path):
    script = Script(title="t", hook="h", beats=[], cta="c", citations=[])
    media = MediaSet(narration_audio=Path("/tmp/n.mp3"))
    out = tmp_path / "v.mp4"
    with patch("src.services.render.remotion.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0)
        out.write_bytes(b"")  # Remotion would create this
        render_via_remotion(script, media, out, composition_id="FactReel")
    assert run.called


def test_render_still_invokes_subprocess(tmp_path):
    from unittest.mock import patch, MagicMock
    from src.services.render.remotion import render_still_via_remotion
    out = tmp_path / "thumb.png"
    with patch("src.services.render.remotion.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0)
        out.write_bytes(b"")
        render_still_via_remotion(
            composition_id="ReelThumbnail",
            props={"title": "test", "topic": "TEST", "frame_path": None, "kicker": None, "fact_number": None, "title_size": 132},
            out_path=out,
        )
    assert run.called
    args = run.call_args[0][0]
    assert "still" in args
    assert "ReelThumbnail" in args
