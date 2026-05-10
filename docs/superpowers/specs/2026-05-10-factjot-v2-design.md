---
title: Fact Jot v2 — Autonomous Short-Form Video Pipeline (DEPRECATED)
date: 2026-05-10
status: DEPRECATED — superseded by 2026-05-10-factjot-v2-rebuild.md
owner: Toby Johnson (TJCreate)
brand: Fact Jot (@factjot)
deprecation_reason: Written before reading v1 (Insta-bot) properly. v1 is far more mature than this spec assumed; most "improvements" proposed here are already in v1, often more rigorously. Direction pivoted to a pluggable-pipeline rebuild in Bot-2 that uses v1 as authoritative reference. See new spec.
---

# Fact Jot v2 — Design Spec

## 1. Executive summary

Fact Jot v2 is a fully automated short-form video pipeline that publishes three videos per day (two "did you know" facts and one "5 of X" list) to YouTube Shorts and Instagram Reels under the existing **@factjot** brand.

The system runs entirely on GitHub Actions (cron-driven), uses Claude for scripting and verification, ElevenLabs for narration, a cascading multi-source visual pipeline (Wikimedia → Pexels → Pixabay → AI fallback), Remotion for templated rendering, and a Telegram bot for one-tap human approval before any post goes live.

The end state is: Toby wakes up, gets a Telegram notification with a rendered preview, taps Approve, and the video posts to both platforms. No code touched, no manual editing, no copy-paste. If Toby does nothing, nothing posts.

## 2. Goals and non-goals

### Goals
- Three videos per day, every day, with consistent quality and brand identity.
- Single human action per video (Approve / Reject / Regenerate via Telegram).
- Publish to YouTube Shorts **and** Instagram Reels from one source render.
- Verifiable facts only — every claim is cross-checked against a source before narration.
- Designer-friendly templates (React/Remotion) so visual style can evolve without rewriting the engine.
- Run cost under £60/month all-in.
- Idempotent, resumable pipeline — any single step failure can be retried without re-running the whole chain.

### Non-goals (v1)
- TikTok publishing (their Content Posting API requires app review + business verification — separate project).
- Web dashboard for analytics or queue management (use git history + native platform analytics).
- Multi-narrator voices, multi-language output, or A/B-tested hook variants.
- Live news / time-sensitive content (the topic discovery is general-knowledge, not trending).
- Database. State lives as JSON files committed back to the repo.
- Anything that touches `/Users/Music/Documents/Insta-bot/`.

## 3. Brand identity and continuity

| Item | Value | Source |
|---|---|---|
| Brand name | Fact Jot | existing |
| Instagram handle | @factjot | existing |
| YouTube channel | TBD — to be created or confirmed before launch | new |
| Narrator voice | ElevenLabs voice ID `3WqHLnw80rOZqJzW9YRB` | continuity from v1 |
| ElevenLabs model | `eleven_v3` for production; `eleven_flash_v2_5` for dev/test | new |
| Visual style | Defined in Remotion templates — single LUT, consistent grain, vignette, brand-mark watermark | new |
| Voice/tone of script | Defined in `style/style-guide.md` (Toby provides) | new |

**Reused credentials from v1 (Toby supplies via GH Actions secrets):**
- `META_ACCESS_TOKEN` (Instagram publish, refresh before ~2026-06-29)
- `ELEVENLABS_API_KEY` (paid plan, no expiry)
- `PEXELS_API_KEY`, `PIXABAY_API_KEY` (no expiry)

**New credentials needed:**
- `YOUTUBE_OAUTH_REFRESH_TOKEN` and `YOUTUBE_CLIENT_ID/SECRET` (one-time OAuth setup)
- `ANTHROPIC_API_KEY`
- `REPLICATE_API_TOKEN` (for Flux fallback image gen)
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- `BLOB_READ_WRITE_TOKEN` (Vercel Blob)
- `GITHUB_DISPATCH_TOKEN` (PAT with `repo` scope, used by Telegram webhook to trigger publish workflow)

## 4. Architecture overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  PRODUCTION WORKFLOW (.github/workflows/produce.yml)                │
│  Trigger: cron 09:00, 13:00, 18:00 UK (3 jobs/day)                  │
│           workflow_dispatch (manual test)                           │
│                                                                     │
│  Inputs: schedule slot → format (fact|list) lookup                  │
│  Steps:                                                             │
│    1. topic.select       → state/topics-used.json (read)            │
│    2. script.generate    → uses style/style-guide.md                │
│    3. fact.verify        → dual-LLM cross-check + citation          │
│    4. director.plan      → script → beats with visual queries       │
│    5. narration.synth    → ElevenLabs (audio + word timestamps)     │
│    6. visuals.source     → cascade per beat                         │
│    7. visuals.normalize  → download, crop 9:16, apply LUT           │
│    8. render.compose     → Remotion → MP4 1080×1920                 │
│    9. upload.publish     → Vercel Blob (public URL)                 │
│   10. notify.preview     → Telegram bot (Approve/Reject/Regenerate) │
│   11. state.commit       → git commit state/*.json back to repo     │
│                                                                     │
│  Output artifact: runs/<run-id>/ folder with all intermediate files │
└─────────────────────────────────────────────────────────────────────┘
                                │
                  Telegram callback hits webhook
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PUBLISH WORKFLOW (.github/workflows/publish.yml)                   │
│  Trigger: repository_dispatch (event: factjot.approve)              │
│           with payload { run_id, action: approve|reject|regenerate }│
│                                                                     │
│  Steps:                                                             │
│    1. Fetch run artifact (MP4 + metadata)                           │
│    2. publishers.youtube.upload  → YouTube Data API v3              │
│    3. publishers.instagram.post  → Meta Graph API (Reels)           │
│    4. state.markPosted           → state/runs.jsonl update          │
│    5. notify.success             → Telegram confirmation            │
│                                                                     │
│  On reject: mark topic burned, no post.                             │
│  On regenerate: dispatch produce.yml with same brief.               │
└─────────────────────────────────────────────────────────────────────┘
```

## 5. Pipeline — detailed step contracts

Each step takes a typed input, writes its output to `runs/<run-id>/<step>.json` (or binary for media), and is idempotent. A retry of step N does not require steps 1..N-1 to re-run.

### 5.1 `topic.select`
- **Input**: `{ format: "fact" | "list", recentTopics: Topic[] }` (last 90 days from `state/topics-used.json`).
- **Output**: `{ topic: string, angle: string, novelty_check: "pass" }`
- **Logic**: Claude Sonnet 4.6 chooses one topic that doesn't overlap with `recentTopics`. For `format: "list"`, also returns a 5-item shortlist.
- **Failure modes**: novelty collision (rare) → regenerate up to 3 times.

### 5.2 `script.generate`
- **Input**: `{ topic, angle, format, styleGuide: string }` (style-guide.md loaded fresh each run).
- **Output**:
  ```ts
  {
    title: string;
    hook: string;            // first 1.5s, ≤12 words
    beats: Beat[];           // one per narrated line
    cta: string;             // outro line
    citations: Citation[];   // {claim, source_url, source_quote}
  }
  ```
- **Logic**: Claude Sonnet 4.6 with style-guide.md pinned in system prompt (cached). Output strictly typed via JSON schema.
- **Failure modes**: schema invalid → 1 retry; persistent failure → escalate to Telegram.

### 5.3 `fact.verify`
- **Input**: script output (specifically `citations` and `beats`).
- **Output**: `{ verified: true } | { verified: false, failures: VerificationFailure[] }`
- **Logic**: Claude Opus 4.7 receives the citations and is asked: "For each claim, does the cited source actually support it? Quote the supporting passage." Uses web fetch tool to retrieve the source.
- **Failure modes**: any claim unverifiable → regenerate the script with the failing claim flagged; up to 2 regen attempts; then escalate to Telegram (do not narrate unverified facts).

### 5.4 `director.plan`
- **Input**: verified script.
- **Output**: each beat enriched with `visualBrief`, plus a top-level `postMetadata` object:
  ```ts
  // per-beat
  {
    visualBrief: {
      subject: string;
      shot_type: "wide" | "close" | "macro" | "aerial" | "static" | "motion";
      mood: string;
      queries: string[];          // 3-5 fallback search strings
      preferred_source: "video" | "image";
      ai_fallback_prompt: string; // used only if all stock fails
    }
  }

  // run-level
  postMetadata: {
    title: string;                // ≤95 chars (YouTube limit is 100)
    description: string;          // long-form for YouTube
    caption: string;              // short-form for Instagram
    hashtags: string[];           // 5-10 items, no leading '#'
    youtube_tags: string[];       // 10-15 items
  }
  ```
- **Logic**: Claude Opus 4.7. Anchors visual queries to the *image* of the claim, not the text of the claim (matches v1 lesson: "All footage queries anchored to image_hint. Never drift to generic topic b-roll").

### 5.5 `narration.synth`
- **Input**: full script (hook + beats + cta concatenated as one VO).
- **Output**: `narration.mp3` + `narration-alignment.json` (word-level timestamps).
- **Logic**: ElevenLabs `eleven_v3`, voice ID `3WqHLnw80rOZqJzW9YRB`, with the alignment endpoint.
- **Failure modes**: API timeout → 3 retries with exponential backoff.

### 5.6 `visuals.source`
- **Input**: each beat's `visualBrief`.
- **Output**: `assets/<beat-id>.{mp4|jpg}` for each beat plus `assets/manifest.json` (provenance: source, license, original URL).
- **Logic** — per-beat cascade, stop at first success:
  1. **Wikimedia Commons**: API search for queries[0]; if a freely-licensed video or high-res image matches, use it.
  2. **Pexels**: video search first (preferred for motion), then photo search.
  3. **Pixabay**: video, then photo.
  4. **AI fallback**: Flux 1.1 Pro via Replicate using `ai_fallback_prompt`. Only triggered if `PREMIUM_VISUALS=true` *or* all stock sources returned nothing.
- **Quality filter**: minimum 1080p, no watermarks, file size > 800KB (carry-over rule from v1 — reject thumbnail-quality assets).
- **Duplicate prevention**: `state/used-asset-urls.json` set; reject any URL used in the last 30 days.
- **Failure modes**: if zero sources return for a beat after AI fallback, the whole pipeline fails and Telegram notifies — do not ship a video with a missing beat.

### 5.7 `visuals.normalize`
- **Input**: `assets/*` from previous step.
- **Output**: `assets-normalized/<beat-id>.mp4` — every asset standardised to 1080×1920, 30fps, with brand LUT applied, slight Ken Burns on stills, vignette + grain.
- **Logic**: FFmpeg pre-processing pass before Remotion compositing (faster than doing it inside Remotion).

### 5.8 `render.compose`
- **Input**: normalized assets + narration + alignment + script metadata.
- **Output**: `final.mp4`, 1080×1920, H.264 high profile, AAC audio, ≤60s.
- **Logic**: Remotion CLI invokes `FactShort` or `ListShort` composition. Renders with Chromium in headless mode on the GH runner.
- **Captions**: word-by-word burn-in driven by `narration-alignment.json`, brand-coloured highlight on active word.
- **BGM**: muted background bed (Pexels Music or Storyblocks free tier), sidechain-ducked under VO.

### 5.9 `upload.publish` (preview, not social)
- **Input**: `final.mp4`.
- **Output**: `{ blobUrl: string }` — Vercel Blob public URL with 30-day TTL.
- **Logic**: this URL is what Meta Graph API will fetch when publishing. Also embedded in Telegram message for preview.

### 5.10 `notify.preview`
- **Input**: `final.mp4` URL + run metadata + script + citations.
- **Output**: Telegram message in approval chat with:
  - Video preview (Telegram inlines MP4)
  - Caption with title, hook, citations
  - Inline keyboard: `✅ Approve`  `🔄 Regenerate`  `❌ Reject`
- **Logic**: Telegram Bot API `sendVideo` with `reply_markup`. Callback data encodes `{ run_id, action }`.

### 5.11 `state.commit`
- **Input**: run metadata.
- **Output**: commits to `state/topics-used.json`, `state/runs.jsonl`, `state/used-asset-urls.json` and pushes back to repo.
- **Logic**: uses `GITHUB_TOKEN` of the workflow. Single-author commits, message format `chore(state): run <run-id>`.
- **Concurrency**: workflows run sequentially (`concurrency.group: produce`) to avoid commit conflicts.

## 6. Publish workflow

### 6.1 YouTube Shorts
- **API**: YouTube Data API v3 `videos.insert`.
- **Auth**: OAuth 2.0 refresh token (one-time setup).
- **Body**:
  - `snippet.title`: `postMetadata.title`
  - `snippet.description`: `postMetadata.description` + `\n\n#Shorts`
  - `snippet.tags`: `postMetadata.youtube_tags`
  - `status.privacyStatus`: `public`
  - `status.madeForKids`: `false`
- **Quota cost**: ~1600 units per upload; daily quota 10000 → comfortably room for 3 uploads.

### 6.2 Instagram Reels
- **API**: Meta Graph API (existing token).
- **Two-step**:
  1. `POST /{ig-user-id}/media` with `media_type=REELS`, `video_url={blobUrl}`, `caption=...`, `share_to_feed=true`.
  2. Poll `GET /{container-id}` until `status_code=FINISHED`, then `POST /{ig-user-id}/media_publish` with `creation_id`.
- **Caption**: title + hook + 5–10 hashtags (director-supplied; see §5.4).
- **Failure modes**: container stays `IN_PROGRESS` >10min → fail; `ERROR` → fail with error message → Telegram notify, manual retry path.

### 6.3 Cross-platform metadata mapping
A single `PostMetadata` object per run produces both platform payloads via adapter functions. No duplicate metadata authoring.

## 7. Visual sourcing strategy — full detail

### 7.1 Why a cascade, not a single source
- Free sources (Wikimedia/Pexels/Pixabay) cover ~70% of beats with high quality.
- AI generation is the safety net: ensures we never ship a video with a missing or wrong-feeling visual, but isn't the default (cost + "AI look" risk).
- Wikimedia first because it covers historical/factual subjects best — exactly Fact Jot's terrain.

### 7.2 Asset rules (non-negotiable)
- **Minimum 1080p resolution** (or upscale rejected).
- **Minimum file size 800KB** (rejects thumbnail-quality misclassified assets).
- **No watermarked assets** (Wikimedia heuristic check; Pexels/Pixabay are watermark-free by API).
- **License logged**: every asset's license + source URL stored in `assets/manifest.json` per run; auditable.
- **No reuse within 30 days** (`state/used-asset-urls.json`).
- **Anchored to visual brief subject**, not the literal claim text. Fact: "the first photograph took 8 hours to expose" → query: "1820s daguerreotype process" not "Niépce photograph". This is the single most-broken thing in cheap content bots.

### 7.3 AI fallback specifics
- Model: Flux 1.1 Pro on Replicate (~$0.04/image).
- Prompt template includes negative prompts: `no text, no watermark, no logos, photorealistic, cinematic`.
- Output 1024×1820, upscaled to 1080×1920.
- One Veo 3 hero shot per **list** video allowed if `PREMIUM_VISUALS=true` (env-gated, default off; estimated ~$1.50 per hero shot).

## 8. Approval workflow

### 8.1 Telegram bot
- One bot, one private chat (Toby's user ID).
- After production: bot sends video preview + inline keyboard.
- Bot's webhook is hosted on a tiny Vercel Function (Node, ~30 lines) that:
  1. Validates Telegram update signature.
  2. Reads callback data `{ run_id, action }`.
  3. Calls GitHub repository_dispatch API with event `factjot.approve` (or `.reject`/`.regenerate`).
  4. Acknowledges callback (Telegram requires <3s ack).
- The Vercel Function holds only the bot token + dispatch PAT, nothing else.

### 8.2 Timeout policy
- `APPROVAL_TIMEOUT_HOURS=6` (env, configurable).
- Reminder ping at +2h.
- At +6h with no action: archive run (Blob retains 7 more days for manual recovery), state marked `expired`, no post.

### 8.3 Manual override
- `gh workflow run publish.yml -f run_id=<id> -f action=approve` works at any time within the Blob retention window.
- Same for `produce.yml -f resume_from=<step> -f run_id=<id>` for retrying mid-pipeline failures.

## 9. State management

All state is JSON files committed back to the repo. No database.

### 9.1 Files

- **`state/topics-used.json`** — append-only log of last 90 days of topics, with format and run-id. Read by `topic.select` for novelty.
- **`state/used-asset-urls.json`** — set of asset URLs used in the last 30 days. Read by `visuals.source`.
- **`state/runs.jsonl`** — one line per run, full lifecycle: `{ run_id, started_at, format, topic, status, citations, error?, posted_to[], blob_url, expires_at }`.
- **`state/last-published.json`** — convenience file with `{ youtube: {...}, instagram: {...} }` for the most recent successful post per platform.

### 9.2 Concurrency
- `produce.yml` and `publish.yml` share `concurrency.group: factjot-state` to serialise commits.
- A run-in-progress lock file (`state/.lock`) prevents double-trigger.

### 9.3 Pruning
- Weekly housekeeping workflow trims `topics-used.json` to last 90 days, prunes Blob URLs older than 30 days, vacuums `used-asset-urls.json` to last 30 days.

## 10. Style guide contract

The file `style/style-guide.md` is the single source of truth for narration tone, hook formulas, banned words/phrases, CTA conventions, and any brand-voice rules. Toby owns and edits it.

The pipeline contract:
- `script.generate` reads `style/style-guide.md` at run-time and pins it in the system prompt (Anthropic prompt caching applies).
- Edits to the style guide take effect on the next run.
- The spec does not duplicate the style-guide content — the file is canonical.

Required sections in style-guide.md (template provided in repo):
1. **Voice and tone**
2. **Hook formula** (what the first 1.5s must achieve)
3. **Banned words and phrases**
4. **CTA convention** (how every video ends)
5. **Pacing rules** (words per second target, max sentence length)

## 11. Repo structure

```
/Users/Music/Developer/Bot-2/
├── .github/
│   └── workflows/
│       ├── produce.yml          # cron 3x daily
│       ├── publish.yml          # repository_dispatch from Telegram
│       ├── manual-test.yml      # workflow_dispatch
│       └── housekeeping.yml     # weekly state pruning
├── style/
│   └── style-guide.md           # OWNED BY TOBY
├── src/
│   ├── pipeline/
│   │   ├── topic.ts
│   │   ├── script.ts
│   │   ├── verify.ts
│   │   ├── director.ts
│   │   ├── narration.ts
│   │   ├── normalize.ts
│   │   ├── render.ts
│   │   └── upload.ts
│   ├── visuals/
│   │   ├── orchestrator.ts
│   │   ├── wikimedia.ts
│   │   ├── pexels.ts
│   │   ├── pixabay.ts
│   │   └── ai-image.ts
│   ├── publishers/
│   │   ├── youtube.ts
│   │   └── instagram.ts
│   ├── notify/
│   │   └── telegram.ts
│   ├── state/
│   │   ├── topics.ts
│   │   ├── runs.ts
│   │   └── assets.ts
│   ├── lib/
│   │   ├── anthropic.ts        # client + caching helpers
│   │   ├── ffmpeg.ts
│   │   └── retry.ts
│   └── runner/
│       ├── produce.ts          # entry point for produce.yml
│       └── publish.ts          # entry point for publish.yml
├── remotion/
│   ├── compositions/
│   │   ├── FactShort.tsx
│   │   └── ListShort.tsx
│   ├── components/
│   │   ├── Caption.tsx
│   │   ├── Asset.tsx           # Ken Burns, loops, blends
│   │   ├── Logo.tsx
│   │   ├── ListNumber.tsx
│   │   └── BackgroundBed.tsx
│   ├── style/
│   │   ├── tokens.ts           # colour, type, spacing tokens
│   │   └── lut.cube
│   └── index.ts                # registers compositions
├── webhook/                    # SEPARATE Vercel project, deployed independently of the GH Actions pipeline
│   ├── api/telegram.ts         # validates Telegram sig → calls GH repository_dispatch
│   ├── package.json            # has its own deps (no Remotion, no FFmpeg)
│   └── vercel.json
├── state/
│   ├── topics-used.json
│   ├── used-asset-urls.json
│   ├── runs.jsonl
│   └── last-published.json
├── runs/                       # gitignored; per-run intermediate artifacts
├── docs/superpowers/specs/
├── package.json
├── tsconfig.json
├── remotion.config.ts
└── README.md
```

## 12. Tech stack summary

| Concern | Choice |
|---|---|
| Language | TypeScript, Node 24 LTS |
| LLM (script, topic) | Claude Sonnet 4.6 with prompt caching |
| LLM (verify, director) | Claude Opus 4.7 |
| TTS | ElevenLabs `eleven_v3` + alignment endpoint |
| Visuals | Wikimedia Commons → Pexels → Pixabay → Flux 1.1 Pro (Replicate) |
| Rendering | Remotion 5 (React templates, Chromium-based renderer) |
| Pre/post media | FFmpeg (normalize step + final mux) |
| Storage | Vercel Blob (public bucket, 30-day TTL on renders) |
| Posting | YouTube Data API v3, Meta Graph API |
| Approval | Telegram Bot API + tiny Vercel Function webhook |
| Orchestration | GitHub Actions (cron + repository_dispatch) |
| State | JSON files in repo |

## 13. Schedule and cadence

| Slot | UK local time | Format |
|---|---|---|
| Morning | 09:00 | Fact #1 |
| Afternoon | 13:00 | Fact #2 |
| Evening | 18:00 | List of 5 |

- **Cron is UTC.** Workflows convert via DST-aware logic: in BST (Mar–Oct) cron runs an hour earlier UTC than the UK local intent. Implementation handles this by either (a) using two cron entries gated by month, or (b) running every hour and skipping unless local time matches. Decision deferred to plan stage; recommendation is (a) for simplicity.
- Production runs at slot − 90 minutes (e.g. 07:30 UK for the 09:00 slot) so Toby has time to approve. Approval window is 6 hours, so a missed morning approval can still publish before midday.
- Publish workflow only fires when approved via Telegram (or auto-approved if `AUTO_APPROVE=true`, default off — never recommended).
- Cadence is configurable in `.github/workflows/produce.yml` cron block.

## 14. Cost envelope (monthly, 3 videos/day = ~90/month)

| Line item | Estimate |
|---|---|
| ElevenLabs Creator | $22 |
| Anthropic API (with caching) | $5–10 |
| Replicate (Flux fallback ~30% of beats) | $5 |
| Vercel Blob (30-day TTL renders) | free tier likely |
| GitHub Actions (private repo) | free tier likely (~9 hrs/month vs 2000 free) |
| Pexels / Pixabay / Wikimedia / Telegram | free |
| YouTube / Meta APIs | free |
| Optional: Veo 3 hero shots (list videos) | +$15–30 |
| **Total baseline** | **$32–47** |
| **Total with premium hero shots** | **$47–77** |

Hard cap: keep under £60 (~$75) — premium toggle gates the only meaningful variable cost.

## 15. Failure handling and resilience

### Per-step
- Every step writes its output to `runs/<run-id>/<step>.json` or `<step>.{mp3,mp4,jpg}`.
- Steps detect existing output and skip (idempotency).
- Retries with exponential backoff at the step level: `{network: 3, llm: 2, render: 1}`.

### Per-run
- Run-level error → Telegram notify with `run_id` + step + error message + suggested resume command.
- Failed run state recorded in `state/runs.jsonl` with status `failed`. Never silently dropped.

### Cross-cutting
- Concurrency lock prevents two runs from racing.
- All secrets validated at workflow start; missing key fails fast with a clear error.
- Dry-run mode: `gh workflow run produce.yml -f dry_run=true` skips publish + Telegram, writes to `runs/dry-run-<ts>/`.

## 16. Security and credentials

- Secrets stored in GitHub Actions repository secrets, **not in `.env` files**.
- Telegram webhook validates Telegram's `X-Telegram-Bot-Api-Secret-Token` header against a secret set during webhook registration.
- Vercel webhook function has no other capability beyond calling `repository_dispatch` — its PAT is scoped to one repo.
- META and YouTube refresh tokens are rotated/refreshed on a calendar reminder; the Telegram bot pings Toby 7 days before token expiry.

## 17. Out of scope (explicit YAGNI)

- **TikTok**: separate project, requires app review.
- **Web dashboard**: git log + Telegram is enough for v1.
- **Database**: JSON files + commit history.
- **Multi-tenancy**: single brand only.
- **A/B hook testing**: defer until baseline engagement is measured.
- **Multi-language narration**: English only.
- **Cloning Toby's voice**: keeping v1 narrator voice.
- **Vector-DB topic deduplication**: simple text/normalised-string match against `topics-used.json` is sufficient for 90-day window.
- **Touching `/Users/Music/Documents/Insta-bot/`**: read-only until v2 supersedes.

## 18. Open items to resolve before implementation

1. **YouTube channel** — does @factjot have a YouTube channel yet? If not, create one and complete OAuth consent screen setup before workflow can publish.
2. **Style guide content** — Toby to provide `style/style-guide.md`. Implementation can begin without it (placeholder) but cannot ship without it.
3. **Telegram chat ID** — Toby creates the bot via @BotFather, gets `TELEGRAM_BOT_TOKEN`, sends a message, retrieves their chat ID via `getUpdates`.
4. **Vercel Blob bucket** — create bucket in Vercel dashboard, generate `BLOB_READ_WRITE_TOKEN`.
5. **GitHub PAT for Telegram → repository_dispatch** — Toby generates PAT with `repo` scope.

These are checklist items for the first implementation step, not design questions.

## 19. Glossary

- **Beat**: a single line of narration with its own visual asset. Typical fact video has 4–6 beats; list video has 8–10 (intro + 5 items + payoff + cta).
- **Director plan**: structured per-beat metadata that turns the script into a shot list.
- **Cascade**: ordered fallback strategy for visual sourcing (Wikimedia → Pexels → Pixabay → AI).
- **Run**: one end-to-end attempt to produce one video, identified by `run_id` (UTC timestamp + slug).
- **Approval gate**: Telegram preview + Approve/Reject/Regenerate before publish.
- **Premium visuals**: env-gated AI hero shot for list videos (Veo 3).

## 20. Change log

- **2026-05-10**: Initial design, approved by Toby for handoff to writing-plans.
