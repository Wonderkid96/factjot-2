import pytest
from pydantic import ValidationError
from src.pipelines.models import Brief, Citation, Beat, Script, MediaAsset, MediaSet, Platform


def test_brief_minimum():
    b = Brief(topic="Apollo 11", angle="moon landing weirdness")
    assert b.topic == "Apollo 11"


def test_script_has_beats():
    s = Script(title="x", hook="y", beats=[Beat(text="t", visual_brief={})], cta="z", citations=[])
    assert len(s.beats) == 1


def test_platform_enum():
    assert Platform.INSTAGRAM.value == "instagram"
    assert Platform.YOUTUBE_SHORTS.value == "youtube_shorts"


def test_beat_defaults_to_ken_burns():
    """Back-compat: existing scripts without scene_treatment fall through to ken_burns."""
    b = Beat(text="t", visual_brief={})
    assert b.scene_treatment == "ken_burns"


def test_beat_accepts_valid_treatment():
    b = Beat(text="t", visual_brief={}, scene_treatment="polaroid")
    assert b.scene_treatment == "polaroid"


def test_beat_rejects_invalid_treatment():
    """Closed enum — LLM can't hallucinate a treatment the renderer doesn't know."""
    with pytest.raises(ValidationError):
        Beat(text="t", visual_brief={}, scene_treatment="bogus_scene")
