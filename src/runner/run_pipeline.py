import argparse
import sys
from src.core.logger import get_logger
from src.pipelines.registry import get_pipeline


log = get_logger("runner")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", required=True, help="pipeline name (e.g. reel_evergreen)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="dry-run (default and only mode in Phase 1)")
    parser.add_argument(
        "--topic",
        default=None,
        help="Override discovery: skip topic picking and write a script for THIS topic. "
             "Useful for visual iteration where the content shouldn't change.",
    )
    parser.add_argument(
        "--reuse-narration-from",
        default=None,
        metavar="RUN_ID",
        help="Copy narration.mp3 + alignment from a prior run dir instead of calling ElevenLabs. "
             "Cuts ~$0.10 from the per-run cost when iterating on visuals only.",
    )
    args = parser.parse_args()

    log.info("pipeline_start", pipeline=args.pipeline, dry_run=args.dry_run,
             topic_override=bool(args.topic), reuse_narration=bool(args.reuse_narration_from))

    pipeline_cls = get_pipeline(args.pipeline)
    pipeline = pipeline_cls()
    # Forward CLI overrides to the pipeline instance. Pipelines that don't
    # support these attrs simply ignore them.
    if hasattr(pipeline, "topic_override"):
        pipeline.topic_override = args.topic
    if hasattr(pipeline, "reuse_narration_from"):
        pipeline.reuse_narration_from = args.reuse_narration_from

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
