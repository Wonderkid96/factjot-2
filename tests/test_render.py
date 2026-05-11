from unittest.mock import patch, MagicMock
from pathlib import Path
from src.services.render.remotion import (
    build_video_spec, render_via_remotion, _strip_suppressed_from_chunks, _is_suppressed,
)
from src.pipelines.models import Script, Beat, VisualBrief, MediaSet, MediaAsset


def test_is_suppressed_matches_brand_words_with_punctuation():
    assert _is_suppressed("fact")
    assert _is_suppressed("Fact")
    assert _is_suppressed("jot")
    assert _is_suppressed("jot.")
    assert _is_suppressed("FACTJOT")
    assert not _is_suppressed("follow")
    assert not _is_suppressed("facts")
    assert not _is_suppressed("for")


def test_strip_suppressed_removes_brand_words_from_outro_chunk():
    """Outro chunk for 'Follow fact jot for more facts.' must read
    'Follow for more facts.' in the caption while the audio stays untouched."""
    chunk = {
        "text": "Follow fact jot for more facts.",
        "start_frame": 100, "end_frame": 200,
        "words": [
            {"text": "Follow",  "start_frame": 100, "end_frame": 120, "emphasis": False},
            {"text": "fact",    "start_frame": 121, "end_frame": 140, "emphasis": False},
            {"text": "jot",     "start_frame": 141, "end_frame": 155, "emphasis": False},
            {"text": "for",     "start_frame": 156, "end_frame": 170, "emphasis": False},
            {"text": "more",    "start_frame": 171, "end_frame": 185, "emphasis": False},
            {"text": "facts.",  "start_frame": 186, "end_frame": 200, "emphasis": False},
        ],
    }
    out = _strip_suppressed_from_chunks([chunk])
    assert len(out) == 1
    assert "fact" not in out[0]["text"].lower().split()
    assert "jot" not in out[0]["text"].lower()
    assert out[0]["text"] == "Follow for more facts."
    assert [w["text"] for w in out[0]["words"]] == ["Follow", "for", "more", "facts."]


def test_strip_suppressed_drops_chunks_that_become_empty():
    """A chunk containing only brand words should be dropped entirely
    (otherwise it would render as a blank caption window)."""
    chunk = {
        "text": "fact jot.",
        "start_frame": 100, "end_frame": 150,
        "words": [
            {"text": "fact", "start_frame": 100, "end_frame": 125, "emphasis": False},
            {"text": "jot.", "start_frame": 126, "end_frame": 150, "emphasis": False},
        ],
    }
    assert _strip_suppressed_from_chunks([chunk]) == []


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
