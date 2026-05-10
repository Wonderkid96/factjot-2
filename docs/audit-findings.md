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
