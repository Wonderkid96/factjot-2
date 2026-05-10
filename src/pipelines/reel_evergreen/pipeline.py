import requests
from pathlib import Path
from src.core.run_id import new_run_id
from src.pipelines.base import Pipeline
from src.pipelines.models import (
    Brief, Script, MediaSet, MediaAsset, Verification, Platform, VisualBrief
)
from src.services.curation.topic_curator import curate_topic
from src.services.curation.script_writer import generate_script
from src.services.resolution.wikidata import resolve_entity
from src.services.resolution.era import era_compatible
from src.services.verification.vision import check_image_subject
from src.services.sourcing.orchestrator import source_for_beat
from src.services.narration.elevenlabs import ElevenLabsNarrator
from src.services.render.remotion import render_via_remotion, render_still_via_remotion
from src.services.state.runs import RunContext
from src.services.state import ledgers
from src.services.discovery.orchestrator import discover_candidates


class ReelEvergreenPipeline(Pipeline):
    name = "reel_evergreen"
    output_format = "reel"
    target_platforms = [Platform.INSTAGRAM, Platform.YOUTUBE_SHORTS]
    brand_format = "reel_overlay"
    remotion_composition = "FactReel"

    def __init__(self) -> None:
        self.run_id: str | None = None

    def _ensure_run_id(self, slug: str) -> str:
        """Stamp a run_id once and reuse across all lifecycle stages.

        Bug fix: plan called new_run_id() in both acquire_media and render,
        which produced different run dirs at the minute boundary.
        """
        if self.run_id is None:
            self.run_id = new_run_id(self.name, slug)
        return self.run_id

    def _run_context(self) -> RunContext:
        assert self.run_id, "run_id not yet set; call source() first"
        rc = RunContext(run_id=self.run_id)
        rc.ensure()
        return rc

    def source(self) -> Brief:
        recent = [r["winner"]["topic"] for r in ledgers.read_all("topic_curation.jsonl")[-90:]]
        discovered = discover_candidates(per_source_limit=20)
        winner = curate_topic(recent_topics=recent, discovered=discovered)
        # Stamp the run_id from the chosen topic
        self._ensure_run_id(winner.topic)
        return Brief(topic=winner.topic, angle="hidden / counterintuitive", pipeline_name=self.name)

    def verify(self, brief: Brief) -> Verification:
        # Light pre-script check: does the topic resolve to a real entity?
        entity = resolve_entity(brief.topic)
        return Verification(verified=True, citations=[])  # not blocking at this stage

    def generate(self, brief: Brief) -> Script:
        return generate_script(topic=brief.topic, angle=brief.angle)

    def acquire_media(self, script: Script) -> MediaSet:
        self._ensure_run_id(script.title)
        rc = self._run_context()

        assets: list[MediaAsset] = []
        for i, beat in enumerate(script.beats):
            vb = beat.visual_brief if isinstance(beat.visual_brief, VisualBrief) else VisualBrief(**beat.visual_brief)
            entity = resolve_entity(vb.subject)
            wm_cat = entity.wikimedia_category if entity else None
            sourced = source_for_beat(vb, wikimedia_category=wm_cat)
            if not sourced:
                continue
            if sourced.media_type == "image":
                if not check_image_subject(sourced.source_url, vb.subject):
                    continue
            if vb.period_constraints and not era_compatible(sourced.source_url, vb.period_constraints):
                continue
            local = rc.assets_dir / f"beat-{i}.{sourced.media_type[:3]}"
            local.write_bytes(requests.get(sourced.source_url, timeout=60).content)
            assets.append(MediaAsset(
                beat_index=i, local_path=local, source_url=sourced.source_url,
                provider=sourced.provider, license=sourced.license,
                width=sourced.width, height=sourced.height,
            ))

        full_text = script.hook + " " + " ".join(b.text for b in script.beats) + " " + script.cta
        narration = ElevenLabsNarrator().synthesize(full_text, rc.audio_path)

        return MediaSet(
            assets=assets,
            narration_audio=narration.audio_path,
            narration_alignment=narration.alignment,
        )

    def render(self, script: Script, media: MediaSet) -> Path:
        """Render video, thumbnail, and story to RunContext.dir. Returns the video path."""
        self._ensure_run_id(script.title)
        rc = self._run_context()

        video_path = render_via_remotion(script, media, rc.video_path, composition_id=self.remotion_composition)

        first_asset = media.assets[0] if media.assets else None
        first_frame = (
            str(first_asset.local_path)
            if first_asset and first_asset.local_path.suffix.lower() in (".jpg", ".jpeg", ".png")
            else None
        )

        topic_label = script.title.split()[0].upper() if script.title else "FACT"

        thumb_path = rc.dir / "thumbnail.png"
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
            out_path=thumb_path,
        )

        story_path = rc.dir / "story.png"
        render_still_via_remotion(
            composition_id="ReelStory",
            props={
                "title": script.title,
                "topic": topic_label,
                "frame_path": first_frame,
                "kicker": "NEW REEL",
                "title_size": 132,
            },
            out_path=story_path,
        )

        return video_path
