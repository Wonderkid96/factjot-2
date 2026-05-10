# Video Pipeline Spec

**Status:** Draft, 2026-05-10
**Parent spec:** `docs/superpowers/specs/2026-05-10-factjot-v2-rebuild.md`
**Replaces:** v1 had no equivalent; video sourcing lived implicitly in `narrative_beats.py` + `video_finder.py`. v2 makes it explicit.

## 1. Product goal
A reel that uses videos and images sourced specifically for the narrated claim. No generic b-roll. No anachronisms. No watermarks.

## 2. Provider trust order
1. Wikimedia Commons (search + category traversal when entity has Wikimedia category)
2. Pexels (video preferred for motion)
3. Pixabay (video then photo)
4. AI generation (last resort, behind PREMIUM_VISUALS=true flag -- Phase 1: disabled)

## 3. Footage quality gates (carry-over + new)
- Minimum 1080p resolution
- No watermarks (Wikimedia heuristic + Pexels/Pixabay are watermark-free)
- Min duration 3s, max 30s per clip
- Vision verification on images (frontier #1; videos skip -- frames vary)
- Era compatibility (frontier #5)

## 4. Per-beat duplicate prevention
`data/ledgers/used_assets.jsonl` records every asset URL used. 30-day rolling window enforces no reuse.

## 5. Visual brief contract
Every beat carries a `VisualBrief` (see `src/pipelines/models.py`):
- `subject`: canonical entity preferred (Wikidata-resolved when possible)
- `shot_type`, `mood`, `queries[]`, `preferred_source`, `ai_fallback_prompt`, `period_constraints?`

## 6. Failure modes
- All sources empty for a beat after cascade: pipeline aborts (matches v1 reel quality gate). Better to skip a slot than ship a beat-missing reel.
- Vision check rejects all candidates: try next query, then next provider, then abort.

## 7. Out of scope (Phase 1)
- AI image / video generation
- Internet Archive fallback
- Semantic embedding search
- TMDB poster seeding (deferred to Phase 2 if list/film content needed)

## 8. Acceptance
A change to video sourcing is "done" only after running a dry-run, opening the rendered MP4, and confirming each beat's visual matches the narrated claim. Tests passing is not enough.
