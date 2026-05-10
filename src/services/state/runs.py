from dataclasses import dataclass, field
from pathlib import Path
from src.core.paths import OUTPUT_DIR


@dataclass
class RunContext:
    run_id: str
    base: Path = field(default_factory=lambda: OUTPUT_DIR)

    @property
    def dir(self) -> Path:
        # First segment after run_id derives pipeline name (e.g. reel_evergreen)
        parts = self.run_id.split("_")
        # parts[0]=YYYY-MM-DD, parts[1]=HH-MM, parts[2..]=pipeline_name + slug
        pipeline = "_".join(parts[2:-1]) if len(parts) > 3 else "_".join(parts[2:])
        return self.base / pipeline / self.run_id

    @property
    def audio_path(self) -> Path:
        return self.dir / "narration.mp3"

    @property
    def alignment_path(self) -> Path:
        return self.dir / "narration-alignment.json"

    @property
    def video_spec_path(self) -> Path:
        return self.dir / "video-spec.json"

    @property
    def video_path(self) -> Path:
        return self.dir / "final.mp4"

    @property
    def assets_dir(self) -> Path:
        return self.dir / "assets"

    def ensure(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
