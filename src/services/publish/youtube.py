from pathlib import Path
from src.pipelines.models import PublishResult, Platform
from src.services.publish.gate import require_publish_allowed


def publish_to_youtube(video_path: Path, title: str, description: str) -> PublishResult:
    try:
        require_publish_allowed()
    except RuntimeError as e:
        return PublishResult(platform=Platform.YOUTUBE_SHORTS, posted=False, error=str(e))
    raise NotImplementedError("YouTube publishing not implemented until Phase 5")
