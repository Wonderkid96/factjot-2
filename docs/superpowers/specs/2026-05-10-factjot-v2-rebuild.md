---
title: Fact Jot v2 — Rebuild Spec (pluggable pipeline framework, hybrid Python + TS-Remotion)
date: 2026-05-10
status: approved-for-planning
owner: Toby Johnson (TJCreate)
brand: Fact Jot (@factjot)
location: /Users/Music/Developer/Bot-2/
supersedes: 2026-05-10-factjot-v2-design.md (deprecated, see header of that file)
v1_reference: /Users/Music/Developer/Insta-bot/ (READ-ONLY, never modified by v2 work)
---

# Fact Jot v2 — Rebuild Spec

## 1. What this spec is and what changed

This spec defines a clean rebuild of the Fact Jot system in `/Users/Music/Developer/Bot-2/`, designed around a **pluggable pipeline framework** so new post types can be added later as drop-in folders rather than re-architectures. v1 (the existing Insta-bot at `/Users/Music/Developer/Insta-bot/`) is treated as **authoritative reference** during the rebuild — the v2 codebase reads v1's specs, follows v1's hard rules, and inherits v1's audit-driven wisdom, but does not import or modify v1 code.

The previous spec (`2026-05-10-factjot-v2-design.md`) was written before properly reading v1 and is now deprecated. v1 is more mature than that spec assumed; many "improvements" it proposed already exist in v1.

## 2. Why a rebuild (and not Path A or Path B)

Two earlier paths were available:
- **Path A:** add reel-composition variety inside v1
- **Path B:** bolt Remotion onto v1 as a second render backend

Toby chose a third path: clean rebuild in a separate directory, using v1 as reference, with the explicit goal of incorporating all five frontier improvements at once and resetting the architectural debt (hardwired transitions, dual-role pipelines, scattered brand tokens, missing video-pipeline spec).

The constraints that make this safe:
- v1 keeps running production untouched
- v2 runs in dry-run mode only until proven
- v2 reuses v1's `.env` keys (zero credential setup)
- v1 stays the canonical reference for hard rules and gotchas

## 3. Goals

1. Pluggable pipeline framework where new post types are drop-in additions (folder + config + cron entry)
2. Designer-friendly visual templates (Remotion compositions) so reels can evolve visually without rewriting the engine
3. Equal-or-better output quality vs v1 on every dimension (asset relevance, render quality, render time, brand consistency)
4. Incorporate all five frontier improvements identified during v1 audit (see §10)
5. Bug-finding discipline as part of the build, not a separate phase
6. Zero accidental publishing — dry-run is enforced in code, not by convention

## 4. Non-goals (explicit YAGNI)

- Not touching `/Users/Music/Developer/Insta-bot/` (v1 stays untouched)
- Not building carousel, list, manual, or news pipelines in Phase 1 (reel pipeline only — others added later as framework extensions)
- Not implementing TikTok publishing (no API access yet; carry-over from previous spec)
- No web dashboard, no analytics UI (use platform-native + git history)
- No vector-DB topic dedup (file-based ledgers are sufficient at v1's volume)
- No multi-language narration
- No new brand identity (v2 inherits voice ID `3WqHLnw80rOZqJzW9YRB` and v1's `brand_kit.json`)

## 5. Hard constraints (user-imposed, non-negotiable)

| Constraint | Enforcement |
|---|---|
| **Entirely separate codebases** | v2 lives in `/Users/Music/Developer/Bot-2/`. No symlinks, no shared modules, no shared `.env`, no shared `insta-brain/`. v1 and v2 can run independently and one going down never affects the other. |
| **Both systems coexist** | v1 keeps running production until v2 is in a better place. v2 dry-runs alongside v1 publishing for as long as it takes. Phase-out plan in §16.5. |
| **Dry-run only** until explicitly enabled | Publish modules absent in early phases. When added, `--allow-publish` flag with double-confirmation step. Default behaviour is dry-run regardless of flag presence. |
| **Same ENV keys, separate `.env` file** | v2 has its own `.env` at `Bot-2/.env`. It is **populated by one-time copy** from v1's `.env` at build start, then independent. No symlink. v2 changes do not affect v1; v1 changes do not affect v2. If credentials need to diverge later, v2 can have its own. |
| **v1 codebase is read-only** | v2 does not import v1 modules, does not symlink, does not modify v1 files. v1 is reference for design decisions, never a runtime dependency. |
| **Honour v1's hard rules** | Em-dash in YAML banned, audio 48kHz before mux, no force-push to main, plan mode for image pipeline changes, "visual success is success", etc. (see §13) |
| **Library-audit before building from scratch** | For every non-trivial component, the implementation plan must first answer: *is there an established, maintained library or open-source repo that solves this?* If yes, use it (after a quick maturity / licence / activity check). Building from scratch is the fallback, not the default. Goal: a small, neat, readable codebase that leans on the ecosystem rather than reinventing it. See §15.1 for the audit checklist. |

## 6. v1 as authoritative reference

v2 inherits v1's accumulated wisdom by reading these files, in order, before any new design or build decision:

1. `/Users/Music/Developer/Insta-bot/CLAUDE.md` — operating rules, environment specifics, hard rules
2. `/Users/Music/Developer/Insta-bot/SPEC_FACTJOT_SYSTEM.md` — system constitution, lifecycle stages
3. `/Users/Music/Developer/Insta-bot/SPEC_IMAGE_PIPELINE.md` — image sourcing discipline
4. `/Users/Music/Developer/Insta-bot/insta-brain/gotchas.md` — recorded failure modes
5. `/Users/Music/Developer/Insta-bot/insta-brain/CRITICAL_FACTS.md` — project critical facts
6. `/Users/Music/Developer/Insta-bot/ROADMAP.md` — deferred work (some items become Phase 1 here)

**Brand source-of-truth hierarchy (clarified 2026-05-10):**

1. **`brand/style-guide-v2.pdf` is the canonical source of truth.** Authored as a designed document. When the brand changes, the PDF changes first.
2. **`brand/brand_kit.json` is the machine-readable encoding** of what the PDF specifies. Values in the JSON must match the PDF; when the PDF updates, the JSON must be updated to match.
3. Code (Python + TypeScript) reads only the JSON, never the PDF directly. The PDF cannot be reliably parsed by code; treating it as design source and the JSON as the encoding is the right separation.

**Brand reuse:**
- v2 copies `brand/brand_kit.json` from v1 to `/Users/Music/Developer/Bot-2/brand/brand_kit.json` at build start. After copy, v2's brand_kit is independent — changes do not propagate back.
- v2 copies `brand/fonts/` (the actual TTF files) — required by Remotion compositions.
- v2 copies `brand/style-guide-v2.pdf` for **human reference** alongside the JSON. Designers (or Toby) consult the PDF to verify what the brand should look like; the JSON is updated to match the PDF.
- v2 reads v1's voice rules and embeds them into its own `style/voice.py` module.
- **Brand kit consumed by both Python AND TypeScript.** `src/core/brand.py` is the Python loader. `remotion/src/style/tokens.ts` is the TypeScript loader that reads the same JSON file. No drift between the two — both layers read from one canonical source. Renderers consume tokens; never inline values (carries v1 §9 contract).
- **Visual lock.** v2 honours v1's `brand/visual_guidelines.lock.json` — palette must include paper / ink / accent / lime / lilac, layout consistent across renderers, typography system unchanged.

**v2's own knowledge base:**
- `Bot-2/insta-brain/` is a fresh directory seeded from v1's `insta-brain/` at build start. Same one-time copy rule. After that, v2 evolves its own gotchas catalogue.

## 7. Architecture overview

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Actions: dispatcher.yml                                 │
│  Receives `pipeline_name` input from cron schedule.yml          │
│  Loads the named pipeline from src/pipelines/<name>/            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Pipeline lifecycle (matches v1 §5)                             │
│  SOURCE → VERIFY → GENERATE → ACQUIRE_MEDIA → RENDER →          │
│  (APPROVE) → PUBLISH → LEDGER → MEASURE                         │
│  Each step is a method on the Pipeline base class               │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        Shared services  State ledgers  Render backends
        (sourcing,       (append-only   (Remotion for
         verification,    JSONL files)   reels via Node
         publishing                      subprocess; PIL/
         adapters)                       Playwright for
                                         carousels)
```

## 8. Pluggable pipeline contract

Every pipeline lives in its own folder under `src/pipelines/<name>/` and follows a uniform contract:

```python
# src/pipelines/base.py
class Pipeline(ABC):
    name: str                                # unique pipeline identifier
    output_format: Literal["reel", "carousel"]
    target_platforms: list[Platform]         # subset of {INSTAGRAM, YOUTUBE_SHORTS}
    brand_format: str                        # key in brand_kit.json formats block
    remotion_composition: str | None         # null for non-Remotion pipelines

    @abstractmethod
    def source(self) -> Brief: ...
    @abstractmethod
    def verify(self, brief: Brief) -> Verification: ...
    @abstractmethod
    def generate(self, brief: Brief) -> Script: ...
    @abstractmethod
    def acquire_media(self, script: Script) -> MediaSet: ...
    @abstractmethod
    def render(self, script: Script, media: MediaSet) -> Path: ...
    def publish(self, output: Path, brief: Brief) -> PublishResult:
        # default: iterate target_platforms, call shared adapter per platform
        # carousel pipelines automatically skip YouTube (not in target_platforms)
        ...
    def ledger(self, result: PublishResult) -> None:
        # default: append to standard ledgers (posted, used_assets, costs)
        ...
```

A new pipeline is:
1. A folder under `src/pipelines/<new_name>/`
2. A `pipeline.py` implementing the contract
3. A `config.yaml` declaring name/format/targets/composition
4. A new entry in `.github/workflows/schedule.yml` cron block

The dispatcher workflow (`pipeline.yml`) auto-discovers pipelines from `src/pipelines/registry.py`. No workflow file edits needed.

### Per-pipeline config example

```yaml
# src/pipelines/reel_evergreen/config.yaml
name: reel_evergreen
output_format: reel
target_platforms:
  - instagram
  - youtube_shorts
brand_format: reel_overlay
remotion_composition: FactReel
cadence:
  - "0 8 * * *"    # 09:00 BST morning
  - "30 19 * * *"  # 20:30 BST night
```

```yaml
# src/pipelines/list_carousel/config.yaml (FUTURE, not Phase 1)
name: list_carousel
output_format: carousel
target_platforms:
  - instagram   # YouTube auto-excluded — carousels can't post there
brand_format: list_carousel
remotion_composition: null  # static carousel, PIL/Playwright render
cadence:
  - "0 13 * * *"  # 14:00 BST midday
```

## 9. Hybrid stack: Python + TypeScript split

| Layer | Language | Reason |
|---|---|---|
| Pipeline framework, lifecycle, registry | Python 3.11 | Matches v1 idioms, Toby's literacy |
| Sourcing services (Wikimedia, Pexels, etc.) | Python | Reuse v1 patterns directly |
| LLM agent + content generation | Python (Anthropic SDK) | Same as v1 |
| Verification (fact checker, vision) | Python | Same as v1 |
| State ledgers, audit log | Python | Same as v1 |
| Publish adapters (IG Graph, YouTube Data API) | Python | Same as v1 |
| Brand kit loader, voice rules | Python | Same as v1 |
| **Remotion compositions (reels only)** | **TypeScript / React** | Only language Remotion supports |
| Static carousel renderer (future) | Python (PIL or Playwright) | No need for Remotion in static work |

**Boundary:** Python pipeline produces a `video-spec.json` describing the reel (beats, assets, captions, narration timing, transitions). The Python `render` step calls `npx remotion render` as a subprocess, passing the JSON. Remotion reads the JSON, renders the MP4, exits. Python takes the MP4 back.

If Remotion is ever swapped out, the swap is one JSON contract — the rest of the system doesn't care.

## 10. Five frontier improvements (incorporated from day 1)

These are the gaps identified during v1 audit. Each gets explicit treatment in v2:

### 10.1 Vision-model verification of selected images
v1 hard validation reads metadata (title, tags, license). v2 adds a **post-Haiku vision check**: Haiku 4.5 vision model receives the actual selected image bytes and is asked "does this image depict {visual_subject}? Answer yes/no with confidence." Low confidence → reject and try next candidate. Implementation: `src/services/verification/vision.py`.

### 10.2 Video pipeline spec (write SPEC_VIDEO_PIPELINE.md)
v1 has no equivalent of `SPEC_IMAGE_PIPELINE.md` for video sourcing. v2 writes one before building the reel pipeline. Covers: video provider trust order, footage quality gates (min resolution, min duration, watermark detection), per-beat duplicate prevention, fallback strategy, AI-generation tier policy.

### 10.3 Wikidata entity resolution
For named historical events / people / places, v2 resolves the topic to a canonical Wikidata entity ID before generating image queries. Returns: canonical name, date range, location, linked Wikimedia category, Wikipedia URL. Implementation: `src/services/resolution/wikidata.py`. The resolved entity feeds the director's visual queries with structured anchors instead of LLM-guessed aliases.

### 10.4 Wikimedia Commons category traversal
For topics with a resolved Wikidata entity that has a Wikimedia category, v2 retrieves images directly from the category (e.g. `Category:Johnstown Flood`) instead of doing keyword search. Categories are curated; keyword search is noisy. Falls back to keyword search if no category exists.

### 10.5 Era / temporal awareness
The intent contract (visual_subject, aliases, etc.) gains a `period_constraints` block:
```python
period_constraints: {
    min_year: 1850,           # reject candidates known to be from after this
    max_year: 1900,           # reject candidates known to be from before this
    prefer_eras: ["victorian", "early-photography"]
}
```
Hard validation rejects era-mismatched candidates where the metadata supports inference. Haiku selector receives era as context for judgement on ambiguous cases.

### 10.6 Multi-source fact discovery layer

v1 originally had Reddit-discovery and a curated fact bank, both retired in audit Phase G.1 (2026-05-10) on the rationale "let the agent source from knowledge." That decision is reversed in v2: relying on the LLM's general knowledge biases candidate topics toward common-knowledge material. For "shocking, not widely known" content, real-world sources surface obscure material the LLM wouldn't volunteer.

**Architecture: discover candidates → fact-check → score → pick.** Sonnet becomes the editor of real-world candidates rather than the generator of imagined ones.

**Sources (all free, all read-only):**

| Source | Why include | Access |
|---|---|---|
| `r/todayilearned` | Highest fact volume; posts must cite a source; upvote-filtered | Reddit API via `praw` |
| `r/AskHistorians` | Expert-vetted history; comment threads are the real source | Reddit API |
| `r/Damnthatsinteresting` | Visual/shareable bias; useful share_trigger signal | Reddit API |
| Wikipedia "Did You Know" | Hand-curated obscure facts by Wikipedia editors; daily updates | RSS / API |
| Atlas Obscura | Curated weird places/events; pre-filtered for Fact Jot territory | RSS |
| Hacker News (top) | Tech/science weird; surfaces papers and counterintuitive findings | Free public API |
| Wikidata SPARQL patterns | Structured weirdness ("died on stage", "lost ships", "abandoned megaprojects") | SPARQL endpoint |

**Verification floor (non-negotiable):** every Reddit-sourced claim is fact-checked against ≥2 *authoritative* sources (Wikipedia, primary documents, academic papers) at confidence ≥0.65 before being passed to the script writer (carries §10.6 verification rule). Reddit gives us "what's interesting"; primary sources give us "what's true." Cross-validation across multiple discovery sources earns higher initial trust.

**Implementation:** `src/services/discovery/` with one module per source plus `orchestrator.py` aggregating + deduplicating. Output: `list[DiscoveredCandidate]` feeding directly into the topic curator (§10.6) — the curator now scores real candidates rather than generating imagined ones.

**Required new env keys** (add to `.env.example`): `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`. One-time Reddit app registration at https://www.reddit.com/prefs/apps. No new costs — Reddit's free tier is sufficient for daily polling.

**Why this is a frontier improvement:** it directly addresses Toby's stated brand goal ("facts so shocking they NEED to share with a friend"). LLM-only generation was structurally underpowered for that goal. Discovery + curation together (§10.6 + §10.7) form the v2 content-quality engine.

### 10.7 Topic curation with share-trigger scoring

v1's autonomous agent picks topics in a single LLM shot. v2 replaces this with a two-stage process designed to maximise the probability that a chosen topic actually hooks, retains, and triggers a share.

**Stage 1 — Candidate generation.** Sonnet proposes 5 candidate topics. Each scored on:
- `hook_potential` (1–10): would this stop a thumb in 1.5s?
- `counterintuitiveness` (1–10): does this defy a held belief or expectation?
- `share_trigger` (1–10): would the average viewer feel compelled to send this to someone?
- `specificity` (1–10): does it resolve to a canonical entity (improves visual sourcing in §10.3/§10.4)?
- `verifiability` (1–10): can this be sourced from authoritative material (feeds verification floor)?
- `risk_flags`: list of strings — graphic, political, contested, or any other automatic-disqualifier categories.

**Stage 2 — Critique.** Opus 4.7 reviews the candidate list. Rejects any candidate with score <7 on any axis OR any risk_flags present. Picks highest combined-score survivor. Tie-break on `share_trigger`. If all 5 candidates are rejected, the slot is skipped (matches v1's `skip(reason)` discipline).

**Stage 3 — Handoff.** Winning candidate is passed to:
- Topic resolution (§10.3) — Wikidata canonical entity
- Fact verification (existing) — ≥2 sources, 0.65 confidence floor
- Script generation — uses the candidate's `hook_potential` reasoning to inform hook construction

**Implementation:** `src/services/curation/topic_curator.py`. Cost: ~$0.02 extra per video (one extra Opus call). Logged: full candidate list + scores + rejection reasons go into `data/ledgers/topic_curation.jsonl` for post-hoc analysis.

**Why this matters for the brand promise:** Toby's stated goal for v2 is "facts that hook people, keep them, and tell them something so shocking they NEED to share." This step is the structural mechanism for that goal. Without it, content quality depends on whatever single shot the agent takes. With it, the floor is materially higher — and the curation ledger gives a feedback dataset for tuning the rubric over time.

## 11. Bug-finding discipline (as part of the build, not a separate phase)

Three rules:

1. **First commit per module is a "v1 audit note".** A comment block at the top of every new v2 module summarises: what the v1 equivalent is, what it does well, what's brittle, what gotchas to preserve. Before writing v2 code, you read v1's version.

2. **Findings file is real.** `Bot-2/docs/audit-findings.md` captures every v1 bug, gap, or non-obvious decision discovered during the rebuild. Each entry is a short paragraph: file, behaviour, why it matters, v2 status (fixed / changed / preserved with reason / escalated to user).

3. **Side-by-side dry-run comparison at every milestone.** Run v1 dry-run and v2 dry-run on the same brief. Open both outputs. Note differences. Quality regressions block the milestone.

## 12. Phase 1 scope: Reel pipeline only

Phase 1 ships when:

1. The pluggable pipeline framework exists (base class, registry, dispatcher workflow)
2. The Reel pipeline (`src/pipelines/reel_evergreen/`) is fully implemented end to end
3. Dry-runs produce inspectable MP4s in `output/reel_evergreen/<run-id>/`
4. All five frontier improvements are integrated and demonstrably working
5. SPEC_VIDEO_PIPELINE.md is written and approved
6. `audit-findings.md` is populated for every shared service touched
7. Side-by-side dry-run comparison vs v1 shows equal-or-better quality

Future phases (separate spec + plan each):
- Phase 2: List carousel pipeline
- Phase 3: Manual/editorial carousel pipeline (with human approval mode)
- Phase 4: New post types (Toby-defined: e.g. story_reel, news_revival)
- Phase 5: Enable live publishing (remove dry-run-only gate after stability proven)
- Phase 6: v1 phase-out (see §16.5)

## 13. v1 hard rules honoured (carry-over)

These are non-negotiable in v2:

1. Em dashes banned in `.yml`/`.yaml` files (GitHub Go YAML parser silently rejects them, breaks `workflow_dispatch`)
2. Em dashes banned in shipping post copy (Toby voice rule)
3. British English throughout copy and captions
4. Audio resampled to 48kHz before muxing (Meta rejects 44.1kHz)
5. Image-pipeline changes require plan mode
6. "Visual success is success" — open the rendered artefact, don't trust green tests
7. Never force-push to main
8. Append-only ledgers (one named exception: reel_performance.jsonl)
9. No image / footage reuse within rolling windows (used_assets ledgers)
10. No empty image boxes — slide either has a real image or intentional typography-only
11. Reel transitions are designable, not hardwired (departure from v1's `case_file_dynamic` lock — this is a deliberate v2 change to enable variety)
12. Brand tokens consumed from `brand_kit.json`, never inlined in templates

## 14. Repo structure

```
/Users/Music/Developer/Bot-2/
├── .github/
│   └── workflows/
│       ├── dispatcher.yml         # takes pipeline_name input, runs the named pipeline
│       ├── schedule.yml           # cron entries → dispatcher with right pipeline_name
│       ├── housekeeping.yml       # token refresh, ledger pruning
│       └── manual-test.yml        # workflow_dispatch for ad-hoc dry-runs
├── brand/
│   └── brand_kit.json             # copied from v1 at build start, then independent
├── style/
│   ├── voice.py                   # voice rules (banned phrases, hook formulas, etc.)
│   └── style-guide.md             # Toby-owned style document (fed to script LLM)
├── src/
│   ├── pipelines/
│   │   ├── base.py                # Pipeline ABC
│   │   ├── registry.py            # auto-discovers folders under src/pipelines/
│   │   └── reel_evergreen/        # Phase 1 reference implementation
│   │       ├── pipeline.py
│   │       ├── config.yaml
│   │       └── prompts/           # pipeline-specific LLM prompts
│   ├── services/
│   │   ├── sourcing/
│   │   │   ├── wikimedia.py
│   │   │   ├── wikipedia.py
│   │   │   ├── smithsonian.py
│   │   │   ├── nasa.py
│   │   │   ├── inaturalist.py
│   │   │   ├── pixabay.py
│   │   │   ├── pexels.py
│   │   │   ├── openverse.py
│   │   │   ├── tmdb.py
│   │   │   └── orchestrator.py    # round-aware fallback (R1/R2/R3)
│   │   ├── resolution/
│   │   │   ├── wikidata.py        # Frontier improvement #3
│   │   │   └── era.py             # Frontier improvement #5
│   │   ├── verification/
│   │   │   ├── fact_checker.py    # ports v1's verifier with same gates
│   │   │   └── vision.py          # Frontier improvement #1
│   │   ├── selection/
│   │   │   ├── haiku.py           # Haiku selector (image)
│   │   │   └── scoring.py         # deterministic scoring
│   │   ├── narration/
│   │   │   └── elevenlabs.py      # eleven_v3, voice 3WqHLnw80rOZqJzW9YRB, 48kHz
│   │   ├── render/
│   │   │   └── remotion.py        # Python wrapper that calls Node subprocess
│   │   ├── publish/
│   │   │   ├── instagram.py       # gated by --allow-publish
│   │   │   └── youtube.py         # gated by --allow-publish
│   │   └── state/
│   │       ├── ledgers.py
│   │       └── runs.py
│   ├── core/
│   │   ├── brand.py               # typed loader for brand_kit.json
│   │   ├── voice.py
│   │   ├── config.py
│   │   └── paths.py
│   └── runner/
│       └── run_pipeline.py        # entry point invoked by dispatcher.yml
├── remotion/
│   ├── compositions/
│   │   └── FactReel.tsx           # Phase 1 reel composition
│   ├── components/                # reusable JSX (Caption, Asset, Hook, Outro, etc.)
│   ├── style/
│   │   ├── tokens.ts              # imports brand_kit.json values
│   │   └── lut.cube
│   ├── package.json
│   ├── tsconfig.json
│   └── remotion.config.ts
├── insta-brain/                   # seeded from v1, then independent
│   ├── CLAUDE.md
│   ├── CRITICAL_FACTS.md
│   └── gotchas.md
├── data/
│   └── ledgers/                   # used_assets, posted, costs, run_log (jsonl)
├── output/
│   └── <pipeline-name>/<run-id>/  # gitignored, per-run artefacts
├── docs/
│   ├── superpowers/
│   │   ├── specs/
│   │   │   ├── 2026-05-10-factjot-v2-rebuild.md  # this file
│   │   │   └── 2026-05-10-factjot-v2-design.md   # deprecated
│   │   └── plans/                 # implementation plans land here
│   ├── audit-findings.md          # bug-finding output, populated as we build
│   └── SPEC_VIDEO_PIPELINE.md     # to be written before reel pipeline
├── tests/                         # pytest tests
├── .env                           # symlinked or copied from v1 .env (same keys)
├── .env.example                   # documents required keys
├── pyproject.toml
├── requirements.txt
├── README.md
└── .gitignore
```

## 15. Tech stack summary

| Concern | Choice |
|---|---|
| Orchestration language | Python 3.11 |
| Render templates | TypeScript / React (Remotion 5) |
| LLM agent | Claude Sonnet 4.6 (Anthropic SDK, with prompt caching) |
| LLM verification | Claude Opus 4.7 (cross-check) and Haiku 4.5 (vision) |
| TTS | ElevenLabs `eleven_v3`, voice ID `3WqHLnw80rOZqJzW9YRB`, 48kHz resample |
| Image sourcing (9 providers, ported from v1) | Wikimedia, Wikipedia, Smithsonian, NASA, iNaturalist, Pixabay, Pexels, Openverse, TMDB |
| Entity resolution | Wikidata + Wikipedia |
| Render | Remotion (Node subprocess), FFmpeg under the hood |
| Storage | Same approach as v1 (imgbb / S3-style ephemeral; no separate vendor needed for Phase 1 since dry-run only) |
| Posting | Instagram Graph API, YouTube Data API v3 (both gated behind dry-run flag) |
| State | JSON files committed back to repo, append-only ledgers |
| CI | GitHub Actions |
| Tests | pytest (Python), Vitest (TypeScript inside Remotion) |

### 15.1 Library-audit checklist

Before any component is built from scratch, the implementation plan answers these questions in writing:

1. **Does an established library do this already?** Check PyPI, npm, GitHub. Search at minimum two terms.
2. **Is it maintained?** Last commit within ~12 months, open issues triaged, no critical unresolved bugs.
3. **Is the licence compatible?** MIT, Apache 2.0, BSD preferred. GPL needs explicit thought.
4. **Is the API surface what we need, or do we use 5% of a giant package?** Smaller targeted libs preferred over kitchen-sink.
5. **Does it add real complexity?** Sometimes "just write 30 lines" beats pulling in a 50-MB dep tree.
6. **Verdict + reason** captured in `docs/audit-findings.md` so future maintainers see why.

Known wins to bias toward (non-exhaustive — implementation plan confirms each):

| Need | Likely library |
|---|---|
| Anthropic LLM calls + caching | `anthropic` (official SDK) |
| ElevenLabs TTS + alignment | `elevenlabs` (official SDK) |
| Wikidata entity resolution | `qwikidata` or `wikidata` |
| Wikimedia API + categories | `mwclient` or `pywikibot` |
| Wikipedia | `wikipedia-api` |
| YouTube Data API | `google-api-python-client` |
| Meta Graph API | direct `requests` (Meta has no first-party Python SDK) |
| Pexels / Pixabay | direct `requests` (their APIs are simple; no good SDK) |
| FFmpeg wrapper | `ffmpeg-python` if scripting needed; raw subprocess if simple |
| Audio resample to 48kHz | `pydub` or `ffmpeg` directly |
| Word-level forced alignment | ElevenLabs alignment endpoint (no second tool) |
| Vision verification | `anthropic` (Haiku 4.5 vision native) |
| YAML config | `pyyaml` |
| Type-validated config / state | `pydantic` v2 |
| HTTP retries + backoff | `tenacity` |
| Append-only JSONL | stdlib `json` + file lock (no need for a library) |
| Tests | `pytest` (Python), `vitest` (TS) |
| Remotion | `remotion` (official) |
| Date / timezone (BST/UTC) | stdlib `zoneinfo` |

Items NOT in the list above (e.g. brand kit loader, pipeline registry, ledger writers) are intentionally first-party because they're <100 lines each and are core to v2's identity — those we own.

## 16. Acceptance criteria for Phase 1

A "Phase 1 done" verdict requires ALL of the following:

1. Pluggable pipeline framework: a documented contract + auto-registry + dispatcher workflow. Adding a second pipeline takes <1 day of work.
2. Reel pipeline runs end to end in dry-run mode, producing an MP4 in `output/reel_evergreen/<run-id>/`.
3. SPEC_VIDEO_PIPELINE.md exists and is approved.
4. All five frontier improvements are present and demonstrably affect output (audit-findings.md cites at least one example per improvement where v2 outperforms v1).
5. Side-by-side dry-run comparison: same brief inputs, both v1 and v2 dry-run, both MP4s opened. v2 quality is judged equal-or-better on visual inspection.
6. Render time on GitHub Actions runner is ≤ v1's (or, if Remotion Lambda added later, ≤ v1's).
7. v1's hard rules (§13) are all preserved; no v1 gotcha is re-introduced.
8. Publish modules exist but are gated by `--allow-publish` (default off, dry-run on).
9. `audit-findings.md` is populated; each finding has v2 status documented.
10. v2's `insta-brain/` is seeded from v1's and has at least one v2-original gotcha entry.

If any of the above is unverified, Phase 1 is not done.

### 16.5 v1 phase-out plan (Phase 6, deferred)

Both systems coexist for as long as it takes for v2 to demonstrably outperform v1. The phase-out is staged, not abrupt:

1. **Coexistence (Phases 1-4):** v2 dry-runs only. v1 keeps publishing on its current 3-slot cadence. Both systems live in `/Users/Music/Developer/`. They share IG account `@factjot` and YouTube channel `thefactjot@gmail.com` only at the destination — they share no code, no `.env`, no state.

2. **Live trial (Phase 5):** v2 enables publishing for one slot (e.g. `reel_morning`). v1 is paused for that slot only (its cron is commented out for that mode). Other v1 slots keep running. Two-week observation. If v2's slot performs equal-or-better and produces no incidents, the next slot moves to v2.

3. **Full handover (Phase 6):** all slots are running on v2. v1's GH Actions workflows are paused (renamed `*.yml.disabled`) but the codebase is preserved untouched as historical reference for at least 90 days. After 90 days of stable v2 operation, v1 can be archived (moved to `/Users/Music/Archive/Insta-bot-2026-archive/`) but not deleted.

The gate at every step is: "did v2's posts perform equal-or-better than v1's would have?" Measured via the same `reel_performance.jsonl`-style ledger that v1 already uses. v2 inherits this ledger format.

If v2 ever regresses below v1, the affected slot rolls back to v1 within one cron cycle by un-commenting the v1 cron entry and pausing v2's. Rollback is a 30-second YAML edit, not a rebuild.

## 17. Open items (resolve during planning, not now)

1. **Render compute target:** GitHub Actions runners for Phase 1, evaluate Remotion Lambda after we measure runner render times. Decision deferred until we have measurements.
2. **Approval gate:** None for Phase 1 (dry-run only — Toby reviews artefacts manually). When live publishing is enabled (Phase 5), add Telegram preview gate then.
3. **YouTube channel:** v1 already publishes to YouTube as `thefactjot@gmail.com`. v2 reuses the same OAuth refresh token from v1's `.env`. No new channel.
4. **Insta-brain governance:** how v1 and v2 brain drift over time. Currently treating as fork-and-diverge; revisit when both are running.

## 18. Glossary

- **Pipeline:** a self-contained content-production unit (e.g. reel_evergreen, list_carousel) implementing the lifecycle contract.
- **Lifecycle:** SOURCE → VERIFY → GENERATE → ACQUIRE_MEDIA → RENDER → (APPROVE) → PUBLISH → LEDGER → MEASURE. Carry-over from v1 SPEC §5.
- **Frontier improvement:** one of the five gaps in v1 identified in §10. Each is an explicit v2 component.
- **Audit findings:** v1 behaviour discovered during v2 rebuild that's worth recording (bugs, gotchas, design choices).
- **Dispatcher workflow:** the single GH Actions workflow that takes pipeline_name as input and runs the matching pipeline.
- **Frontier improvements registry:** the list of five v2 capabilities that go beyond v1 (vision verification, video spec, Wikidata, Wikimedia categories, era awareness).

### 17.1 Composition library vision (Phase 1.2 — captured here for continuity)

Phase 1 ships with a minimal `FactReel.tsx` to prove the autonomous mechanism. The full vision for "videos that feel handmade" is a **library of small Remotion components + a director step** that picks combinations per video. Captured here so it's not lost between Phase 1 and Phase 1.2 planning:

- **Component library:** hooks (`HookCard`, `HookSplitReveal`, `HookStatBlast`), beats (`BeatVideoOver`, `BeatStatOverlay`, `BeatComparison`, `BeatMapPin`, `BeatTimeline`, `BeatDiagram`), outros (`OutroQuote`, `OutroCTA`), overlays (`LowerThirdCaption`, `CitationChip`, `SegmentNumber`), transitions (`Cut`, `DipToColor`, `Whip`, `ParallaxSlide`).
- **Director output:** the script-writer agent expands its JSON to include a `composition_plan` per beat — which component to use, which props to pass, which transition.
- **Specialist elements:** maps (Mapbox static + animated paths), diagrams (Anthropic SVG → drawn-on animation), animated counters, progressive reveals, all synced to ElevenLabs word-level alignment.
- **Brand-token consumption:** Remotion components import from a TS loader that reads `brand/brand_kit.json`; no inline style values.

Result: same components, different combinations every video. Same architectural style as After Effects motion design, but generated from JSON each run rather than authored manually. Costs no extra compute — Remotion renders one composition per run regardless of how many components it contains internally.

**Sequencing:** Phase 1 builds the engine (the minimal `FactReel.tsx` for video, plus `ReelThumbnail.tsx` and `ReelStory.tsx` for stills — see plan §18.5–§18.8 — all consuming the same brand tokens). Phase 1.2 adds the broader composition library + director step. Phase 1.3 adds the specialist visual elements (maps, diagrams). Each phase is shippable on its own.

**Phase 1 already includes:** one video composition (`FactReel`), one thumbnail composition (`ReelThumbnail` for IG grid covers and YouTube custom thumbnails), one story composition (`ReelStory` for IG story teasers), `Wordmark` and `YearAccent` reusable components, and brand tokens loaded from `brand_kit.json` in both Python and TypeScript. The thumbnail and story use the same React components and brand tokens as the video — one rendering system, no drift.

## 19. Change log

- **2026-05-10** — Initial rebuild spec, supersedes the previous v2 design spec.
- **2026-05-10** — Strengthened separation guarantees in §5 (dedicated `.env`, no symlinks, both systems coexist). Added §16.5 v1 phase-out plan. (User clarification: "keep builds entirely separate, phase out v1 once v2 is in a better place.")
- **2026-05-10** — Added §10.6 Topic curation with share-trigger scoring as the sixth frontier improvement. (User goal: facts that hook, retain, trigger shares.)
- **2026-05-10** — Added "library-audit-first" hard constraint in §5 and §15.1 audit checklist. (User principle: lean on the ecosystem, neat readable codebase, build from scratch only when needed.)
- **2026-05-10** — Approved by Toby for handoff to writing-plans.
- **2026-05-10** — Added §17.1 Composition library vision capturing the "feels handmade" approach (component library + director step + specialist elements) as Phase 1.2/1.3 work. Phase 1 stays minimal to prove the autonomous mechanism first.
- **2026-05-10** — Added §10.6 Multi-source fact discovery layer (Reddit + Wikipedia DYK + Atlas Obscura + Hacker News + Wikidata SPARQL patterns). v1's Reddit-discovery decision (killed in audit Phase G.1) is reversed for v2: Sonnet becomes editor of real-world candidates rather than generator of imagined ones. Renumbered: discovery is now §10.6 (data flows in), curation is §10.7 (consumes from discovery).
- **2026-05-10** — Added narration-locked beat timing to Phase 1's minimal FactReel composition. Beats are sized to their narration windows (start/end frames computed from ElevenLabs alignment). No naive even-split. `calculateMetadata` makes total video duration match actual narration length. Word-by-word kinetic captions still wait for Phase 1.2.
- **2026-05-10** — Clarified brand source-of-truth hierarchy in §3: PDF is canonical, JSON is machine-readable encoding, code reads only the JSON. PDF is copied to `brand/style-guide-v2.pdf` for human reference.
- **2026-05-10** — Added thumbnail + story compositions to Phase 1 (plan milestones 18.5-18.8). Same React components, same brand tokens, single rendering system across video AND stills via Remotion `renderStill`. ReelPipeline.render() now produces three artefacts per run (video.mp4, thumbnail.png, story.png).
