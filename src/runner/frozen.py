"""Frozen-mode rendering — replay a captured fixture through Remotion only.

Bypasses Anthropic (script generation), ElevenLabs (narration), and the
sourcing orchestrators (Wikimedia/Pexels/Pixabay). Each frozen render
costs $0 in product API spend, which makes visual iteration genuinely cheap.

The fixture format is what tests/fixtures/<name>/ ships:
    spec.json                   ← the full final.spec.json from the source run
    narration.mp3               ← ElevenLabs output at the original speed
    narration-alignment.json    ← word-level alignment
    assets/beat-{0..3}.{jpg,mp4,...}

Run with:
    uv run python -m src.runner.run_pipeline --pipeline reel_evergreen --frozen yamaguchi
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from src.core.logger import get_logger
from src.core.paths import REPO_ROOT
from src.pipelines.models import Script, Beat, VisualBrief, MediaSet, MediaAsset
from src.pipelines.registry import get_pipeline


log = get_logger("runner.frozen")

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
ASSET_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov", ".webm")


def render_from_fixture(fixture_name: str, pipeline_name: str) -> Path:
    """Render a frozen fixture through the given pipeline's render stage.

    Returns the path to final.mp4.
    """
    fixture = FIXTURES_DIR / fixture_name
    if not fixture.is_dir():
        raise FileNotFoundError(
            f"fixture not found: {fixture}. Known fixtures: "
            f"{[p.name for p in FIXTURES_DIR.iterdir() if p.is_dir()] if FIXTURES_DIR.exists() else []}"
        )

    spec_path = fixture / "spec.json"
    align_path = fixture / "narration-alignment.json"
    audio_path = fixture / "narration.mp3"
    assets_src = fixture / "assets"

    for p in (spec_path, align_path, audio_path, assets_src):
        if not p.exists():
            raise FileNotFoundError(f"fixture missing required artefact: {p}")

    spec = json.loads(spec_path.read_text())
    alignment = json.loads(align_path.read_text())

    pipeline = get_pipeline(pipeline_name)()

    # Stamp a fresh run_id so each frozen render lands in its own output dir
    # without clobbering prior runs. Format must match new_run_id() so RunContext
    # parses the pipeline name correctly.
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    run_id = f"{ts}_{pipeline_name}_frozen-{fixture_name}"
    pipeline.run_id = run_id  # type: ignore[attr-defined]
    rc = pipeline._run_context()  # type: ignore[attr-defined]

    # Stage fixture inputs into the run dir
    shutil.copy2(audio_path, rc.audio_path)
    rc.alignment_path.write_text(json.dumps(alignment))
    for f in assets_src.iterdir():
        if f.suffix.lower() in ASSET_EXTS:
            shutil.copy2(f, rc.assets_dir / f.name)

    # Brand intro overlay + music if available (pipeline normally stages these).
    from src.core.paths import BRAND_DIR
    intro_brand = BRAND_DIR / "intros" / "factjot_intro.mov"
    if intro_brand.exists():
        shutil.copy2(intro_brand, rc.dir / "intro.mov")
    music_fixture = fixture / "music.mp3"
    music_brand = BRAND_DIR / "music" / "default.mp3"
    if music_fixture.exists():
        shutil.copy2(music_fixture, rc.dir / "music.mp3")
    elif music_brand.exists():
        shutil.copy2(music_brand, rc.dir / "music.mp3")
    # V1 film-grain overlay
    grit_brand = BRAND_DIR / "grit" / "film-grain.mov"
    if grit_brand.exists():
        shutil.copy2(grit_brand, rc.dir / "grit.mov")

    # Reconstruct the typed objects the render step expects. visual_brief and
    # citations carry no information at render time, so we synthesise minimal
    # placeholders rather than persisting them in the fixture.
    script = Script(
        title=spec["title"],
        hook=spec["hook"],
        cta=spec["cta"],
        beats=[
            Beat(
                text=b["text"],
                visual_brief=VisualBrief(
                    subject="frozen",
                    queries=["frozen"],
                    preferred_source="image",
                ),
                # Honour the spec's scene_treatment if present, falls back to
                # ken_burns for legacy fixtures. Lets fixtures hand-author
                # treatments without round-tripping through the script writer.
                scene_treatment=b.get("scene_treatment", "ken_burns"),
            )
            for b in spec["beats"]
        ],
        citations=[],
        topic_entity=None,
    )

    assets: list[MediaAsset] = []
    for i in range(len(spec["beats"])):
        for ext in ("jpg", "jpeg", "png", "webp", "gif", "mp4", "mov", "webm"):
            p = rc.assets_dir / f"beat-{i}.{ext}"
            if p.exists():
                assets.append(MediaAsset(
                    beat_index=i, local_path=p,
                    source_url="frozen://fixture", provider="fixture",
                    license="frozen", width=1920, height=1080,
                ))
                break
    if len(assets) != len(spec["beats"]):
        log.warning("frozen_asset_mismatch",
                    beats=len(spec["beats"]), assets=len(assets))

    media = MediaSet(
        assets=assets,
        narration_audio=rc.audio_path,
        narration_alignment=alignment,
    )

    log.info("frozen_render_start", fixture=fixture_name, run_id=run_id)
    output = pipeline.render(script, media)
    log.info("frozen_render_done", path=str(output))
    return output
