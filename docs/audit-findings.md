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

---

## 2026-05-10: brand_kit.json copied from v1

**Source:** `/Users/Music/Developer/Insta-bot/brand/brand_kit.json`
**Destination:** `brand/brand_kit.json`
**v2 status:** preserved as-is. Independent from v1 from this point. Per spec §6, edits do not propagate either direction.

**Top-level shape (recorded so future tests don't drift):** `name`, `handle`, `version`, `version_note`, `voice`, `colors`, `colors_v2`, `surfaces`, `gradient`, `typography`, `type_scale_v2`, `type_rules_v2`, `layout`, `highlights`, `wordmark`, `templates`, `visual_guidelines`, `content_schema`. Note: plan example used `palette`/`fonts` keys that v1 doesn't have; v2 brand loader and test align with `colors` and `typography` instead.

---

## 2026-05-10: logging library audit

**Need:** structured logging with JSON output for CI, human-readable for dev.

**Candidates:** `loguru` (popular, simple), `structlog` (composable), stdlib `logging` (zero deps).

**Decision:** `structlog`. Composable, supports both JSON and console renderer, mature, used widely. Cost: 1 dep.

**Verdict:** add `structlog>=24.0.0` to pyproject.toml.

---

## 2026-05-10: Anthropic SDK audit

**Need:** Claude API calls with prompt caching, structured output (JSON), vision (Haiku), tool use later.

**Library:** `anthropic` (official SDK, already in pyproject). Native support for caching via `cache_control` blocks. Native vision. Battle-tested.

**Verdict:** use as-is. v2's `core/anthropic_client.py` is a thin wrapper providing: model defaults, retry policy (tenacity), prompt caching helpers, structured-output helper using `response_model` pattern.

---

## 2026-05-10: ElevenLabs SDK audit

**Need:** TTS with the voice ID from `.env` `ELEVENLABS_VOICE`, `eleven_v3` model, word-level alignment, output 48kHz (Meta requires).

**Library:** `elevenlabs` (official SDK, already in pyproject). Supports `text_to_speech.convert()` (audio bytes) and a separate alignment endpoint. Audio output defaults to 44.1kHz; we'll resample.

**Resample tool:** ffmpeg (already a system requirement for Remotion). `subprocess.run(["ffmpeg", "-i", in, "-ar", "48000", out])`.

**Verdict:** use SDK for TTS, raw HTTP `requests` to alignment endpoint (the SDK alignment helper is partial), ffmpeg subprocess for resample.

---

## 2026-05-10: Wikidata library audit

**Need:** Resolve a topic string ("Johnstown Flood") to canonical Wikidata entity ID (Q261221), with linked Wikimedia category, dates, location.

**Candidates:** `qwikidata` (official Wikidata helpers, well-maintained), `wikidata` (older, simpler), raw SPARQL via `requests` (zero-dep).

**Decision:** raw SPARQL via `requests`. Wikidata's SPARQL endpoint is stable, well-documented, and we only need 1-2 queries. `qwikidata` adds 50MB for very little gain over a 30-line wrapper.

**Verdict:** first-party, ~50 lines, uses stdlib `requests` + `tenacity` retry.

---

## 2026-05-10: Wikimedia client audit

**Need:** Wikimedia Commons API access -- both keyword search AND category traversal (frontier #4).

**Candidates:** `mwclient` (mature, supports both), `pywikibot` (heavy, more aimed at editing), raw API via `requests`.

**Decision:** `mwclient`. ~5MB, well-maintained, supports `Site.categories()` and `Site.images()`. Cleanly handles auth-free reads.

**Verdict:** add `mwclient>=0.10.0` to deps. Use it for both R1 (search) and R2 (category) paths.

---

## 2026-05-10: Pexels SDK audit

**Need:** Search Pexels for video clips (preferred) and photos by query.

**Candidates:** `pexels-api`, `pypexels` (both unmaintained), raw `requests`.

**Decision:** raw `requests`. Pexels API is 2 endpoints, ~30 lines total. No SDK needed.

**Verdict:** first-party.

---

## 2026-05-10: Reddit / discovery library audit

**Need:** Read-only Reddit access (subreddit listings, top posts, post metadata + URLs).

**Library:** `praw` (Python Reddit API Wrapper). Mature, official-style, handles OAuth, well-documented. Adds ~5MB.

**Wikipedia DYK:** scrape from https://en.wikipedia.org/wiki/Wikipedia:Recent_additions via stdlib `requests` + `beautifulsoup4`.

**Atlas Obscura:** RSS feed via `feedparser`.

**Hacker News:** free public API (no auth) via `requests`.

**Wikidata SPARQL:** already wired in §10.3, reuse `_sparql()`.

**Verdict:** add `praw`, `beautifulsoup4`, `feedparser`. ~3 deps total.
