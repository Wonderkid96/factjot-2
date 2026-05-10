import argparse
import sys
from src.core.logger import get_logger
from src.pipelines.registry import get_pipeline


log = get_logger("runner")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", required=True, help="pipeline name (e.g. reel_evergreen)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="dry-run (default and only mode in Phase 1)")
    args = parser.parse_args()

    log.info("pipeline_start", pipeline=args.pipeline, dry_run=args.dry_run)

    pipeline_cls = get_pipeline(args.pipeline)
    pipeline = pipeline_cls()

    brief = pipeline.source()
    log.info("brief_ready", topic=brief.topic)

    verification = pipeline.verify(brief)
    if not verification.verified:
        log.warning("verification_failed", failures=verification.failures)
        return 2

    script = pipeline.generate(brief)
    log.info("script_ready", title=script.title, beats=len(script.beats))

    media = pipeline.acquire_media(script)
    log.info("media_ready", assets=len(media.assets))

    output = pipeline.render(script, media)
    log.info("render_complete", path=str(output))

    if args.dry_run:
        log.info("dry_run_done", output=str(output))
        return 0

    log.info("publish_skipped_phase1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
