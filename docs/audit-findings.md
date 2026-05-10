# Audit Findings

This file captures observations made while reading the v1 codebase during v2 rebuild. Each entry: file/area, observation, v2 status (preserved / changed / fixed / escalated).

---

## 2026-05-10: v1 .env keys catalogued

**Source:** `/Users/Music/Developer/Insta-bot/.env`

**Keys observed (names only, never values):**
- TIMEZONE
- IMAGE_HOST
- MUSIC_CREDIT
- INSTAGRAM_ACCOUNT_ID
- FACEBOOK_PAGE_ID
- META_ACCESS_TOKEN
- META_GRAPH_VERSION
- META_GRAPH_HOST
- META_LOGIN_FLOW
- META_APP_ID
- META_APP_SECRET
- ANTHROPIC_API_KEY
- ELEVENLABS_API_KEY
- ELEVENLABS_VOICE
- PEXELS_API_KEY
- COVERR_API_KEY
- PIXABAY_API_KEY
- IMGBB_API_KEY
- TMDB_API_KEY
- TMDB_READ_TOKEN
- OMDB_API_KEY
- CLOUDINARY_CLOUD_NAME
- CLOUDINARY_UPLOAD_PRESET
- CLOUDINARY_API_KEY
- CLOUDINARY_API_SECRET
- GUARDIAN_API_KEY
- REEL_TRANSITIONS_MODE
- TIKTOK_CLIENT_KEY
- TIKTOK_CLIENT_SECRET

**v2 status:** v2 will copy this `.env` once at Task 1.2. Same keys; v2 has its own file from then on.

---

## 2026-05-10: ELEVENLABS_VOICE drift between docs and live env

**Source:** `/Users/Music/Developer/Insta-bot/.env` line 17.

**Observation:** v1's live `.env` has `ELEVENLABS_VOICE=zNsotODqUhvbJ5wMG7Ei` (the voice currently producing every Fact Jot reel), but the v2 spec, plan, `.env.example` comment, `src/core/config.py` default, `tests/test_env_validation.py` assertion, and Brain note `wiki/motion/factjot.md` all hardcoded a different ID `3WqHLnw80rOZqJzW9YRB`. The hardcoded ID was never set in any `.env` and is not referenced anywhere v1's runtime reads — so the docs described a voice that was never live.

**v2 status:** fixed + new policy. Toby confirmed the live `zNsotODqUhvbJ5wMG7Ei` is canonical. Resolution:

1. `src/core/config.py` — `elevenlabs_voice` is now `Field(..., alias="ELEVENLABS_VOICE")` (required, no default literal).
2. `.env.example` — value blanked, comment notes live value lives in `.env`.
3. `tests/test_env_validation.py` — asserts the var is set, no longer asserts a literal.
4. Brain `wiki/motion/factjot.md` — voice line now reads "voice from `.env` `ELEVENLABS_VOICE`".
5. Spec and plan files — hardcoded ID references replaced with env-var references (see commit message).

**New policy (carry into every milestone):** documentation must reference env-var names, never literal env values. This applies to voice IDs, account IDs, API endpoints, host names, and any other configurable that lives in `.env`. Code defaults likewise — `Field(...)` (required) or `Field(default=None)` rather than the literal env value as a default. The single exception is *behaviour* defaults that are part of the contract (e.g. `dry_run: bool = True`).

---

## 2026-05-10: YOUTUBE_* keys absent from v1 .env

**Source:** `/Users/Music/Developer/Insta-bot/.env` (no YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN).

**Observation:** plan Task 1.4 declares all three YouTube fields as required (`Field(...)`). With v1's `.env` lacking them, `Settings()` raises ValidationError before any test runs.

**v2 status:** changed (Phase 1 deviation from plan). The three YouTube fields are now `str | None = Field(default=None, ...)`. Phase 1 is dry-run only, YouTube publishing is gated to Phase 5 per spec §16.5. When Phase 5 wires YouTube, Toby adds the three keys to `.env` and the fields can be tightened to required.
