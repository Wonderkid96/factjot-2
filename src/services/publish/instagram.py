from pathlib import Path
from src.pipelines.models import PublishResult, Platform
from src.services.publish.gate import require_publish_allowed


def publish_to_instagram(video_path: Path, caption: str) -> PublishResult:
    try:
        require_publish_allowed()
    except RuntimeError as e:
        return PublishResult(platform=Platform.INSTAGRAM, posted=False, error=str(e))
    # Real implementation lands in Phase 5. Until then we never reach here in dry-run.
    raise NotImplementedError("Instagram publishing not implemented until Phase 5")
