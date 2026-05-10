# V1 → V2 gotchas transfer

A line-by-line mapping of V1's 293-line `insta-brain/gotchas.md` (the
catalogue of production failures Insta-bot has burned through) against
Bot-2's architecture. Each row is one of:

- **N/A** — Bot-2's Remotion path doesn't exercise this code branch
- **HANDLED** — Bot-2 already addresses it
- **GAP** — equivalent risk exists; mitigation needed
- **PUBLISH** — future-relevant once Bot-2 leaves dry-run mode

> Draft generated 2026-05-11 from V1 gotchas + Bot-2 codebase. Toby
> reviews and signs off before any production promotion.

---

## CI / GitHub Actions

| # | V1 gotcha                                          | Status   | Bot-2 action                                                                 |
|---|----------------------------------------------------|----------|------------------------------------------------------------------------------|
| 1 | Em dashes in workflow comments → 422 silent reject | GAP      | Add `grep -r "—" .github/` to a pre-commit hook or CI lint                  |
| 2 | Multiline Python heredocs in `run: \|` blocks      | HANDLED  | Bot-2 workflow uses `python -m src.runner...` directly, no heredocs          |
| 3 | GitHub cron unreliable on free tier                | N/A      | Bot-2 has no cron; only workflow_dispatch                                    |

## Meta / Instagram publishing (DEFERRED — Phase 2 only)

| #  | V1 gotcha                                                                  | Status   | Bot-2 action                                                                 |
|----|----------------------------------------------------------------------------|----------|------------------------------------------------------------------------------|
| 4  | Meta video URL fetcher rejects >5MB                                        | PUBLISH  | When wiring publish: compress to <4.7MB via crf 30→33→35 fallback ladder     |
| 5  | Meta requires 48kHz audio (44.1 and 96 both rejected)                      | HANDLED  | `_resample_to_48khz` in `elevenlabs.py` enforces this                        |
| 6  | Meta access tokens expire every 60 days                                    | PUBLISH  | Build refresh-token script when wiring publish                               |
| 7  | Cloudinary URLs rejected by Meta fetcher; use tmpfiles                     | PUBLISH  | Use tmpfiles for IG video upload host                                        |
| 17 | IG carousel cap 20 (raised from 10)                                        | PUBLISH  | Set publisher cap to 20 when wiring carousels                                |
| 45 | IG Reel `cover_url` accepts JPEG only, <500KB; silent drop if non-conforming | PUBLISH  | When wiring publish: emit thumbnail.jpg at <=450KB via q=85→75→65 fallback   |

## Audio / narration

| # | V1 gotcha                                       | Status   | Bot-2 action                                                                  |
|---|-------------------------------------------------|----------|-------------------------------------------------------------------------------|
| 8 | "factjot" rendered as two tokens; CTA-sync fallback | N/A   | Bot-2 has no CTA-sync code — outro is appended to narration as its own phrase |

## Footage / clip handling

| #  | V1 gotcha                                                       | Status   | Bot-2 action                                                                  |
|----|-----------------------------------------------------------------|----------|-------------------------------------------------------------------------------|
| 9  | Short clips loop visibly (`stream_loop -1` minimum 2MB/4s)      | GAP      | When Pexels/Pixabay video returns short clips, Remotion may show a hard cut. Verify with a synthetic 2s-clip-in-7s-window test or enforce a minimum length |
| 10 | Same clip in intro + main is correct (alpha overlay)            | N/A      | Bot-2 has dedicated `factjot_intro.mov` overlay; no clip overlap              |
| 11 | Footage dedup ledger must be git-tracked                        | GAP      | When sourcing wired for production, track `data/ledgers/used_footage.jsonl`  |
| 12 | Image dedup ledger must be git-tracked                          | GAP      | Same as #11 for `used_images.jsonl`                                          |

## Topic discovery / fact quality

| #  | V1 gotcha                                                       | Status   | Bot-2 action                                                                  |
|----|-----------------------------------------------------------------|----------|-------------------------------------------------------------------------------|
| 18 | News cover queries over-constrained by aliases                  | N/A      | Bot-2 has no carousel cover concept                                           |
| 19 | Entity search must use named person from claim, not `image_hint`| HANDLED  | `resolve_entity()` reads `script.topic_entity`, anchors sourcing on it       |
| 20 | Tier-0 Wikipedia/Wikimedia/Archive before Pexels                | HANDLED  | Orchestrator scores `wikimedia=6` vs `pexels=3` (`sourcing/orchestrator.py`)  |
| 21 | Wikimedia 2-step API call (search → imageinfo)                  | HANDLED  | `mwclient` handles this                                                       |
| 33 | Wikimedia JPEG stills deadlock FFmpeg on macOS                  | N/A      | Remotion path doesn't exercise FFmpeg `image2`+`stream_loop`                  |
| 34 | Wikimedia PNGs in palette/RGBA/16-bit modes crash FFmpeg PNG dec | GAP-LITE | Remotion-via-Chromium should handle any mode, but adding a Pillow normalise pass would be cheap insurance |
| 41 | Wrong-subject thumbnails from `footage_clips[0]` (entity-vs-beat)| GAP      | Bot-2's thumbnail picks first beat asset — same risk. Add Haiku-validated entity check, like V1's `validate_entity_image()` |
| 43 | Subject-fingerprint dedup beats text-key dedup                  | GAP      | Bot-2 dedups by `normalise(text)` only. Add Jaccard token-set fingerprint with 0.6 threshold over last 14 days |
| 44 | Fact verification gate (Haiku consistency + Wikipedia anchoring)| GAP      | Bot-2's `verify()` returns `Verification(verified=True)` unconditionally. Implement the V1 Phase D.1 two-layer gate before publishing |

## FFmpeg / encoding (mostly N/A — we use Remotion)

| #  | V1 gotcha                                                       | Status   | Bot-2 action                                                                  |
|----|-----------------------------------------------------------------|----------|-------------------------------------------------------------------------------|
| 23 | `-nostdin` + `stdin=DEVNULL` to prevent CI hang                 | GAP-LITE | `_resample_to_48khz` calls ffmpeg directly. Add `-nostdin` to be safe in CI   |
| 24 | 20+ PNG overlay stages are wrong approach for subtitles         | N/A      | Remotion does subtitles as React layers, not FFmpeg overlays                  |
| 25 | `ass` filter deadlock at frame ~275 on macOS                    | N/A      | Remotion doesn't use `ass`                                                    |
| 26 | Primary encode crf 23 preset medium                             | INFO     | Remotion default is crf 18; consider explicit crf=20 for closer match to V1   |
| 27 | stderr pipe backpressure from `-progress pipe:2`                | N/A      | Remotion handles its own stderr                                               |
| 28 | GH Actions empty log mid-encode is normal                       | INFO     | Same applies to Remotion — quiet ≠ stuck                                      |
| 29 | ProRes 4444 12-bit alpha overlay `bilinear` not `lanczos`       | INFO     | Bot-2 uses the same ProRes intro; Remotion <Img>/Video should handle 12-bit  |
| 31 | Tier-0 stills stuck on frame 0 with image2/25fps                | N/A      | Remotion renders as React, no `image2` demuxer                                |
| 32 | macOS subtitles use PNG overlays not `ass`                      | N/A      | Remotion handles via React text layers                                        |

## macOS local environment

| #  | V1 gotcha                                                       | Status   | Bot-2 action                                                                  |
|----|-----------------------------------------------------------------|----------|-------------------------------------------------------------------------------|
| 35 | Homebrew `ffmpeg 8.0.1_2` broken after libvpx upgrade           | GAP-LITE | Add a startup probe; auto-fallback to `ffmpeg-full` if default `ffmpeg -version` fails |
| 36 | iCloud intercepts FFmpeg output in `~/Documents/`               | HANDLED  | Bot-2 lives at `/Users/Music/Developer/Bot-2/` (outside iCloud)               |
| 37 | Only one local pipeline at a time via `fcntl` lock              | GAP-LITE | Bot-2 uses timestamped run dirs; collision only if two runs start in the same minute. Add `fcntl.flock` on a lock file for paranoia |
| 38 | FFmpeg exit 255 — read stderr log, not "slow init"              | N/A      | Remotion-specific failure modes are different                                 |

## Git / repo discipline

| #  | V1 gotcha                                                       | Status   | Bot-2 action                                                                  |
|----|-----------------------------------------------------------------|----------|-------------------------------------------------------------------------------|
| 14 | Scout cache reset must not touch publish or dedup ledgers       | INFO     | Adopt the V1 split (`PUBLISH_AND_DEDUP` vs `SCOUT_INVENTORY_CACHE`) before publishing |
| 15 | `assert_no_duplicate()` called immediately before publish        | PUBLISH  | When wiring publish: fresh disk read of ledger right before IG API call       |
| 39 | Force-push to main → triple-post incident                       | HANDLED  | Toby's CLAUDE.md already prohibits this                                       |
| 42 | `git add <list>` aborts on first missing ledger                 | PUBLISH  | When wiring publish: stage each ledger separately with `if [ -e ]` guard      |

## Thumbnail design

| #  | V1 gotcha                                                       | Status   | Bot-2 action                                                                  |
|----|-----------------------------------------------------------------|----------|-------------------------------------------------------------------------------|
| 22 | `factjot.` top-left, `TOPIC` top-right, title centred, corner brackets, no logo divider, no bottom strip, no flanking lines | PARTIAL | Bot-2's ReelThumbnail composition has factjot top-left and title centred. Verify no extra elements snuck back in. Compare against `/Users/Music/Developer/Insta-bot/src/render/templates/reel_thumbnail.html.j2` |

## Fix philosophy

V1's final line: *"Every fix must be a long-term structural fix, not a
temporary patch."* Bot-2 inherits this as policy. No symptom suppression.

---

## Bot-2 actions queued from this audit (P0–P2)

### P0 — block-publishing gates (must land before Phase 2)
- **GAP-44**: implement Haiku consistency + Wikipedia anchoring fact-verification gate. Replace the hardcoded `Verification(verified=True)`.
- **GAP-43**: subject-fingerprint dedup (token-set Jaccard ≥ 0.6 over 14 days) in addition to current normalised-text key.
- **GAP-41**: Haiku-validated entity check on the thumbnail source asset.

### P1 — quality of life (do before any unattended runs)
- **GAP-9**: minimum-clip-length guard on Pexels/Pixabay video assets (>= 4s, >= 2MB).
- **GAP-1**: pre-push hook that fails on em dashes in `.github/`.

### P2 — defensive insurance
- **GAP-LITE-34**: Pillow normalise pass on Wikimedia images.
- **GAP-LITE-23**: `-nostdin` on the `_resample_to_48khz` ffmpeg call.
- **GAP-LITE-35**: ffmpeg version probe + auto-fallback to `ffmpeg-full`.
- **GAP-LITE-37**: `fcntl.flock` on a lock file to prevent concurrent local runs.

### Future (Phase 2 — publishing)
- **PUBLISH-4 / 45**: video <4.7MB ladder, JPEG thumbnail <=450KB.
- **PUBLISH-6 / 7**: Meta token refresh, tmpfiles for upload host.
- **PUBLISH-11 / 12 / 15 / 42**: footage + image dedup ledgers, pre-publish disk-read of posted ledger, robust `git add` per ledger.

---

## What this confirms

The debate's conclusion was right: Bot-2's architecture is already
correct (Remotion renders, Python orchestrates). The `ass`-filter macOS
deadlock and ~30% of V1's gotchas list are structurally absent from
Bot-2's code path. The other ~30% (publishing) is future work; the
remaining ~40% mostly maps to existing Bot-2 behaviour or queued P0/P1
gaps. There's no architectural drift, just a normal sourcing/verification
backlog plus a publishing-phase backlog.
