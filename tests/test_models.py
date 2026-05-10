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
