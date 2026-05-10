from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Literal
from src.pipelines.models import (
    Brief, Script, MediaSet, Verification, PublishResult, Platform
)


class Pipeline(ABC):
    """Base contract every Fact Jot v2 pipeline implements.

    Lifecycle (from spec §7, matches v1 SPEC §5):
      SOURCE -> VERIFY -> GENERATE -> ACQUIRE_MEDIA -> RENDER -> (APPROVE) -> PUBLISH -> LEDGER -> MEASURE
    """

    name: ClassVar[str]
    output_format: ClassVar[Literal["reel", "carousel"]]
    target_platforms: ClassVar[list[Platform]]
    brand_format: ClassVar[str]
    remotion_composition: ClassVar[str | None]  # null for non-Remotion pipelines

    @abstractmethod
    def source(self) -> Brief: ...

    @abstractmethod
    def verify(self, brief: Brief) -> Verification: ...

    @abstractmethod
    def generate(self, brief: Brief) -> Script: ...

    @abstractmethod
    def acquire_media(self, script: Script) -> MediaSet: ...

    @abstractmethod
    def render(self, script: Script, media: MediaSet) -> Path: ...

    def publish(self, output: Path, brief: Brief) -> list[PublishResult]:
        """Default: dry-run no-op. Real publishing wired in Milestone 19, gated by --allow-publish."""
        return [
            PublishResult(platform=p, posted=False, error="dry-run")
            for p in self.target_platforms
        ]

    def ledger(self, results: list[PublishResult]) -> None:
        """Default: append to standard ledgers. Implementations may override for pipeline-specific state."""
        from src.services.state.ledgers import append_run_record
        append_run_record(self.name, results)
