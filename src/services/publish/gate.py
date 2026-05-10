import os


def require_publish_allowed() -> None:
    """Raises if publishing is not explicitly enabled. Phase 1 default: dry-run only."""
    if os.environ.get("DRY_RUN", "true").lower() in ("true", "1", "yes"):
        raise RuntimeError("Publishing blocked: DRY_RUN is set. Phase 1 is dry-run only.")
    if os.environ.get("ALLOW_PUBLISH", "").lower() != "yes_i_am_sure":
        raise RuntimeError("Publishing not allowed: ALLOW_PUBLISH must equal 'yes_i_am_sure'.")
