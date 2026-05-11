import argparse
import os
import sys

# Load .env into os.environ FIRST, before anything else imports. This is what
# makes the FACTJOT_FROZEN lock real: pydantic-settings reads .env into the
# Settings() object but does NOT populate os.environ, so the
# os.getenv("FACTJOT_FROZEN") guards in script_writer + elevenlabs never saw
# the .env value before this. With load_dotenv() here, .env behaves the way
# it reads — set FACTJOT_FROZEN=1 and the paid APIs actually refuse to fire.
from dotenv import load_dotenv
load_dotenv()

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
    parser.add_argument(
        "--frozen",
        default=None,
        metavar="FIXTURE",
        help="Replay a frozen fixture (tests/fixtures/<FIXTURE>/) through Remotion only. "
             "Skips Anthropic + ElevenLabs + asset sourcing entirely. $0 in product API spend.",
    )
    args = parser.parse_args()

    # --frozen short-circuits the entire normal pipeline. Set the env guard
    # FIRST so any accidental import path that touches ElevenLabs / Anthropic
    # raises rather than silently hitting a paid endpoint.
    if args.frozen:
        os.environ["FACTJOT_FROZEN"] = "1"
        from src.runner.frozen import render_from_fixture
        output = render_from_fixture(args.frozen, args.pipeline)
        log.info("frozen_done", output=str(output))
        return 0

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
