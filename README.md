# Fact Jot v2

Autonomous Instagram + YouTube Shorts publishing system, rebuilt with a pluggable pipeline framework.

**Status:** Phase 1 build, dry-run only.

**v1 reference (read-only):** `/Users/Music/Developer/Insta-bot/`. See `V1_REFERENCE.md`.

## Quick links
- Spec: [docs/superpowers/specs/2026-05-10-factjot-v2-rebuild.md](docs/superpowers/specs/2026-05-10-factjot-v2-rebuild.md)
- Plan: [docs/superpowers/plans/2026-05-10-factjot-v2-rebuild.md](docs/superpowers/plans/2026-05-10-factjot-v2-rebuild.md)
- Audit findings: [docs/audit-findings.md](docs/audit-findings.md)

## Hard rules (carried over from v1)
1. Em dashes banned in `.yml` / `.yaml` (GitHub Go YAML parser silently rejects)
2. Audio resampled to 48kHz before muxing (Meta rejects 44.1kHz)
3. Never force-push to main
4. "Visual success is success" — open the rendered artefact, don't trust green tests
5. Append-only ledgers (one named exception: `reel_performance.jsonl`)
6. Library-audit before building from scratch (see spec §15.1)
7. Dry-run by default; publish requires explicit `--allow-publish`

## Setup (Phase 1)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp /Users/Music/Developer/Insta-bot/.env .env
```

Then read the plan and start at Milestone 1.

## Compositions

Two Remotion compositions are registered:

- **CaseFileReel** (default) — case-file aesthetic. Each beat carries a `scene_treatment` chosen by the script writer from a closed set: `polaroid`, `evidence_slide`, `redacted_doc`, `stamp_reveal`, `index_card`, `newsprint_clip`, `archive_film`, `map_pin`, `red_thread`, `ken_burns`. Beats render onto a persistent desk; prior beats file into an accumulating evidence stack in the bottom-right corner.
- **FactReel** (fallback) — original v1-style full-bleed Ken Burns over a stock asset. Keep around for content that doesn't suit the case-file treatment.

Pick the composition via the pipeline config (`src/pipelines/reel_evergreen/config.yaml:remotion_composition`) or the `composition_id` arg to `render_via_remotion()`.

## Frozen mode

`FACTJOT_FROZEN=1` in `.env` (default ON) blocks every paid-API call (`script_writer.generate_script`, `ElevenLabsNarrator.synthesize`) — they raise `FrozenModeViolation`. Render against a fixture instead:

```bash
uv run python -m src.runner.run_pipeline --pipeline reel_evergreen --frozen yamaguchi
```

Fixtures live in `tests/fixtures/<name>/` with a `spec.json` (Remotion props), `narration.mp3`, `narration-alignment.json`, and `assets/beat-{0..3}.{jpg,mp4,...}`. Fixture beats can hand-author `scene_treatment` per beat. Unset / set `FACTJOT_FROZEN=0` only when you genuinely want fresh generation.
