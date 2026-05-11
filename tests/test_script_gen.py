import json
from unittest.mock import patch
from src.services.curation.script_writer import generate_script, _scrub_script


def _beat(text: str, treatment: str | None = None) -> dict:
    b = {"text": text, "visual_brief": {"subject": "x", "queries": ["x"], "preferred_source": "image"}}
    if treatment is not None:
        b["scene_treatment"] = treatment
    return b


def test_generate_script_returns_typed_object():
    fake = json.dumps({
        "title": "Apollo 11's Hidden Gold",
        "hook": "There's gold on the moon, and we put it there.",
        "beats": [_beat("In 1969, NASA bolted gold-coated kapton to the Eagle.", "polaroid")],
        "cta": "Every moon mission since has carried the same metal.",
        "citations": [{"claim": "Eagle had gold-coated kapton", "source_url": "https://en.wikipedia.org/wiki/Apollo_Lunar_Module", "source_quote": "..."}]
    })
    with patch("src.services.curation.script_writer._call_writer", return_value=fake):
        script = generate_script(topic="Apollo 11 leftover gold", angle="hidden engineering")
    assert script.title.startswith("Apollo")
    assert len(script.beats) >= 1
    assert script.beats[0].scene_treatment == "polaroid"


def test_scrub_script_backfills_missing_treatment():
    data = {"hook": "h", "cta": "c", "title": "t", "beats": [_beat("b")]}
    out = _scrub_script(data)
    assert out["beats"][0]["scene_treatment"] == "ken_burns"


def test_scrub_script_repairs_invalid_treatment():
    data = {"hook": "h", "cta": "c", "title": "t", "beats": [_beat("b", "made_up_treatment")]}
    out = _scrub_script(data)
    assert out["beats"][0]["scene_treatment"] == "ken_burns"


def test_scrub_script_rewrites_red_thread_on_beat_zero():
    """red_thread on beat 0 has no prior beat to connect to — promote to polaroid."""
    data = {"hook": "h", "cta": "c", "title": "t", "beats": [_beat("b", "red_thread")]}
    out = _scrub_script(data)
    assert out["beats"][0]["scene_treatment"] == "polaroid"


def test_scrub_script_preserves_valid_treatments():
    data = {
        "hook": "h", "cta": "c", "title": "t",
        "beats": [
            _beat("b0", "polaroid"),
            _beat("b1", "redacted_doc"),
            _beat("b2", "stamp_reveal"),
            _beat("b3", "red_thread"),
        ],
    }
    out = _scrub_script(data)
    assert [b["scene_treatment"] for b in out["beats"]] == [
        "polaroid", "redacted_doc", "stamp_reveal", "red_thread",
    ]
