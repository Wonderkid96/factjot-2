from pathlib import Path
from src.pipelines.base import Pipeline
from src.pipelines.models import Brief, Script, MediaSet, Verification, Platform


class _DummyPipeline(Pipeline):
    name = "dummy"
    output_format = "reel"
    target_platforms = [Platform.INSTAGRAM]
    brand_format = "reel_overlay"
    remotion_composition = None

    def source(self) -> Brief:
        return Brief(topic="t", angle="a")

    def verify(self, brief): return Verification(verified=True)
    def generate(self, brief): return Script(title="t", hook="h", beats=[], cta="c", citations=[])
    def acquire_media(self, script): return MediaSet()
    def render(self, script, media): return Path("/tmp/dummy.mp4")


def test_pipeline_subclass_runs():
    p = _DummyPipeline()
    assert p.name == "dummy"
    assert Platform.INSTAGRAM in p.target_platforms
