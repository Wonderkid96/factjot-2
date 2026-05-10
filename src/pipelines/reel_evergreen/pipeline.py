"""Evergreen reel pipeline.

Discovery → cheap topic pick → script gen → per-beat sourcing →
narration → render. Topic curator (Sonnet+Opus) was removed 2026-05-10
to cut $0.17/run; we just take the highest-upvote candidate that
hasn't been used recently.
"""
import json
import shutil
from pathlib import Path

import requests

from src.core.logger import get_logger
from src.core.paths import BRAND_DIR, OUTPUT_DIR
from src.core.run_id import new_run_id
from src.pipelines.base import Pipeline
from src.pipelines.models import (
    Brief, Script, MediaSet, MediaAsset, Verification, Platform, VisualBrief
)
from src.services.curation.script_writer import generate_script
from src.services.discovery.models import DiscoveredCandidate
from src.services.discovery.orchestrator import discover_candidates
from src.services.narration.elevenlabs import ElevenLabsNarrator, NarrationResult
from src.services.render.remotion import render_via_remotion, render_still_via_remotion
from src.services.resolution.era import era_compatible
from src.services.resolution.wikidata import resolve_entity
from src.services.sourcing.orchestrator import source_for_beat
from src.services.state import ledgers
from src.services.state.runs import RunContext
from src.services.verification.vision import check_image_subject


log = get_logger("pipelines.reel_evergreen")

POSTED_LEDGER = "posted.jsonl"
RECENT_TOPIC_WINDOW = 90  # last N entries treated as "recent" for dedup
INTRO_OVERLAY_PATH = BRAND_DIR / "intros" / "factjot_intro.mov"


class ReelEvergreenPipeline(Pipeline):
    name = "reel_evergreen"
    output_format = "reel"
    target_platforms = [Platform.INSTAGRAM, Platform.YOUTUBE_SHORTS]
    brand_format = "reel_overlay"
    remotion_composition = "FactReel"

    def __init__(self) -> None:
        self.run_id: str | None = None
        # Set by the runner from CLI flags. Both default to None.
        self.topic_override: str | None = None
        self.reuse_narration_from: str | None = None

    # --- run-context plumbing ----------------------------------------

    def _ensure_run_id(self, slug: str) -> str:
        """Stamp a run_id once and reuse across all lifecycle stages."""
        if self.run_id is None:
            self.run_id = new_run_id(self.name, slug)
        return self.run_id

    def _run_context(self) -> RunContext:
        assert self.run_id, "run_id not yet set; call source() first"
        rc = RunContext(run_id=self.run_id)
        rc.ensure()
        return rc

    # --- topic selection (no curator) --------------------------------

    @staticmethod
    def _recent_dedupe_keys() -> set[str]:
        """Pull the last N posted entries' dedupe keys for filtering."""
        recent = ledgers.read_all(POSTED_LEDGER)[-RECENT_TOPIC_WINDOW:]
        return {r["dedupe_key"] for r in recent if "dedupe_key" in r}

    def _pick_topic(self, candidates: list[DiscoveredCandidate]) -> DiscoveredCandidate | None:
        """Cheapest viable pick: highest upvotes among non-recent candidates.

        No LLM. Topic-level dedup uses the normalised text key (DiscoveredCandidate.dedupe_key).
        """
        recent = self._recent_dedupe_keys()
        fresh = [c for c in candidates if c.dedupe_key not in recent]
        if not fresh:
            return None
        return max(fresh, key=lambda c: c.upvotes)

    # --- lifecycle stages --------------------------------------------

    def source(self) -> Brief:
        if self.topic_override:
            log.info("topic_override", topic=self.topic_override)
            self._ensure_run_id(self.topic_override)
            return Brief(topic=self.topic_override, angle="hidden / counterintuitive", pipeline_name=self.name)

        discovered = discover_candidates(per_source_limit=20)
        log.info("discovered", count=len(discovered))
        winner = self._pick_topic(discovered)
        if winner is None:
            raise RuntimeError("Discovery returned no fresh candidates after dedup")

        # Record the pick before we run anything expensive — the dedup ledger
        # works even if the run later fails.
        ledgers.append(POSTED_LEDGER, {
            "topic": winner.text,
            "dedupe_key": winner.dedupe_key,
            "source": winner.source,
            "source_url": winner.source_url,
            "upvotes": winner.upvotes,
        })

        self._ensure_run_id(winner.text)
        log.info("topic_picked", topic=winner.text[:80], upvotes=winner.upvotes, source=winner.source)
        return Brief(topic=winner.text, angle="hidden / counterintuitive", pipeline_name=self.name)

    def verify(self, brief: Brief) -> Verification:
        # Phase 1: non-blocking. Wikidata + multi-source fact verification land in Phase 1.1.
        return Verification(verified=True, citations=[])

    def generate(self, brief: Brief) -> Script:
        return generate_script(topic=brief.topic, angle=brief.angle)

    def acquire_media(self, script: Script) -> MediaSet:
        self._ensure_run_id(script.title)
        rc = self._run_context()

        # Resolve the topic-level entity ONCE — anchors all beats. A JFK reel
        # pulls from Category:John F. Kennedy across every beat, not just the
        # one whose visual_brief happened to mention him.
        topic_wm_cat: str | None = None
        if script.topic_entity:
            topic_entity = resolve_entity(script.topic_entity)
            if topic_entity:
                topic_wm_cat = topic_entity.wikimedia_category
            log.info("topic_entity_resolved",
                     entity=script.topic_entity,
                     wikimedia_category=topic_wm_cat)

        assets: list[MediaAsset] = []
        for i, beat in enumerate(script.beats):
            vb = beat.visual_brief if isinstance(beat.visual_brief, VisualBrief) else VisualBrief(**beat.visual_brief)
            entity = resolve_entity(vb.subject)
            beat_wm_cat = entity.wikimedia_category if entity else None
            sourced = source_for_beat(
                vb,
                wikimedia_category=beat_wm_cat,
                topic_wikimedia_category=topic_wm_cat,
            )
            if not sourced:
                continue
            if vb.period_constraints and not era_compatible(sourced.source_url, vb.period_constraints):
                continue
            # Pick a sane extension from the source URL or fall back by media type.
            url_suffix = Path(sourced.source_url.split("?")[0]).suffix.lower()
            if url_suffix in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov", ".webm"):
                ext = url_suffix.lstrip(".")
            else:
                ext = "mp4" if sourced.media_type == "video" else "jpg"
            local = rc.assets_dir / f"beat-{i}.{ext}"

            # Download with proper error handling. Wikimedia returns 429 with a
            # short HTML body when rate-limited; we used to write that body as
            # if it were a JPEG and Remotion choked on the 126-byte ASCII file.
            # User-Agent is REQUIRED — upload.wikimedia.org returns 403 to
            # default Python requests UA (their published bot policy).
            try:
                resp = requests.get(
                    sourced.source_url,
                    timeout=60,
                    headers={"User-Agent": "FactJotV2/0.1 (https://factjot.com; tobyjohnsonemail@gmail.com)"},
                )
                resp.raise_for_status()
                content = resp.content
                if len(content) < 4096:
                    log.warning("asset_download_too_small",
                                url=sourced.source_url, bytes=len(content))
                    continue
                # Magic-byte sniff for images so we don't write HTML/PDF as .jpg
                if sourced.media_type == "image":
                    head = content[:8]
                    if not (head.startswith(b"\xff\xd8")           # JPEG
                            or head.startswith(b"\x89PNG")          # PNG
                            or head[:4] == b"RIFF"                  # WEBP container
                            or head[:6] in (b"GIF87a", b"GIF89a")):  # GIF
                        log.warning("asset_not_an_image",
                                    url=sourced.source_url,
                                    head=head.hex())
                        continue
                local.write_bytes(content)
            except Exception as e:
                log.warning("asset_download_failed",
                            url=sourced.source_url, error=str(e)[:200])
                continue
            assets.append(MediaAsset(
                beat_index=i, local_path=local, source_url=sourced.source_url,
                provider=sourced.provider, license=sourced.license,
                width=sourced.width, height=sourced.height,
            ))

        narration = self._narration_for(script, rc)
        return MediaSet(
            assets=assets,
            narration_audio=narration.audio_path,
            narration_alignment=narration.alignment,
        )

    def _narration_for(self, script: Script, rc: RunContext) -> NarrationResult:
        """Synthesise narration via ElevenLabs — OR copy from a prior run if reuse is enabled.

        Visual-only iterations are common; the narration doesn't need to change between
        them and ElevenLabs is the dominant per-run cost. `reuse_narration_from` is the
        prior run-id whose audio + alignment we copy into this run.
        """
        if self.reuse_narration_from:
            return self._copy_prior_narration(rc)

        # Append the brand outro so the voice says "Follow fact jot for more facts"
        # at the end of every reel. _compute_timeline extracts its window.
        full_text = (
            script.hook + " "
            + " ".join(b.text for b in script.beats) + " "
            + script.cta + " "
            + OUTRO_TEXT
        )
        return ElevenLabsNarrator().synthesize(full_text, rc.audio_path)

    def _copy_prior_narration(self, rc: RunContext) -> NarrationResult:
        prior_id = self.reuse_narration_from
        prior_dir = OUTPUT_DIR / self.name / prior_id
        prior_audio = prior_dir / "narration.mp3"
        prior_alignment = prior_dir / "narration-alignment.json"
        if not prior_audio.exists():
            raise FileNotFoundError(f"No narration to reuse at {prior_audio}")

        shutil.copy2(prior_audio, rc.audio_path)
        alignment: list[dict] = []
        if prior_alignment.exists():
            alignment = json.loads(prior_alignment.read_text())
        log.info("narration_reused", source_run=prior_id, words=len(alignment))
        return NarrationResult(audio_path=rc.audio_path, alignment=alignment)

    def render(self, script: Script, media: MediaSet) -> Path:
        """Render video, thumbnail, and story to the run dir. Returns the video path."""
        self._ensure_run_id(script.title)
        rc = self._run_context()

        # Persist the alignment alongside the audio so future --reuse-narration-from runs
        # have everything they need without rerunning the full pipeline.
        if media.narration_alignment:
            rc.alignment_path.write_text(json.dumps(media.narration_alignment))

        # Stage the brand intro overlay into the run dir so the HTTP server bridge
        # serves it. FactReel.tsx falls back gracefully if the file is missing.
        if INTRO_OVERLAY_PATH.exists():
            shutil.copy2(INTRO_OVERLAY_PATH, rc.dir / "intro.mov")

        video_path = render_via_remotion(script, media, rc.video_path, composition_id=self.remotion_composition)

        first_asset = media.assets[0] if media.assets else None
        first_frame = (
            str(first_asset.local_path)
            if first_asset and first_asset.local_path.suffix.lower() in (".jpg", ".jpeg", ".png")
            else None
        )

        topic_label = script.title.split()[0].upper() if script.title else "FACT"

        render_still_via_remotion(
            composition_id="ReelThumbnail",
            props={
                "title": script.title,
                "topic": topic_label,
                "frame_path": first_frame,
                "kicker": "DID YOU KNOW",
                "fact_number": None,
                "title_size": 132,
            },
            out_path=rc.dir / "thumbnail.png",
        )

        render_still_via_remotion(
            composition_id="ReelStory",
            props={
                "title": script.title,
                "topic": topic_label,
                "frame_path": first_frame,
                "kicker": "NEW REEL",
                "title_size": 132,
            },
            out_path=rc.dir / "story.png",
        )

        return video_path
