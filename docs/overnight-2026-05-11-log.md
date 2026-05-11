# Overnight log — 2026-05-11

Branch: `bot-2/overnight-2026-05-11`
Working from: HEAD `cd27a0d` (main, Yamaguchi run committed)

## Scope and constraints

- ElevenLabs locked after the Yamaguchi run dispatched at 23:05 UTC
- Anthropic locked after that same run's script generation
- Pexels / Pixabay calls deferred (free APIs, but cross the "no API" line; Toby's call in the morning)
- All overnight rendering is via the local `--frozen yamaguchi` flag → $0 product API spend
- All work on `bot-2/overnight-2026-05-11`; main untouched

## Cost summary

| Item                                            | Cost     |
|-------------------------------------------------|----------|
| Yamaguchi paid run (Anthropic + ElevenLabs)     | ~$0.10   |
| All overnight visual iteration (5 frozen renders) | $0.00  |
| **Total overnight product API spend**           | **$0.10** |

(Anthropic session tokens via Claude Code subscription are excluded — that
is harness budget, not product cost.)

## Milestones landed

| #   | Title                                      | Commit    | Eval verdict |
|-----|--------------------------------------------|-----------|--------------|
| M26 | Eval-harness scaffold + Yamaguchi fixture  | `d9acd17` | 8/1/1 baseline |
| M27 | --frozen flag for zero-cost iteration      | `1652fe6` | 8/1/1 (unchanged) |
| M28 | V1 gotchas-transfer + visual-constants     | `78cb2e1` | docs only |
| M29.1 | Per-word karaoke captions + intro reveal | `9a48d3e` | 8/1/1 (unchanged) |
| M29.2 | Wordmark legibility (top grad + shadow)  | `1620853` | 8/1/1 (unchanged) |
| M29.3 | Topic kicker chip (HISTORY/SCIENCE/etc.) | `d181055` | 8/1/1 (unchanged) |

Eval scores held at 8 PASS / 1 FAIL / 1 SKIP across every iteration. The
only FAIL is CE-8 script word count (74 vs target 80-110) — a known soft
fail of the Sonnet writer occasionally underdelivering on the Yamaguchi
topic. Not introduced by overnight changes.

## What you'll see in the morning

Open the latest render:
```
open "$(ls -dt /Users/Music/Developer/Bot-2/output/reel_evergreen/*frozen-yamaguchi | head -1)/final.mp4"
```

### Comparison against the original GH Actions Yamaguchi run

| Frame | Before                          | After                                       |
|-------|---------------------------------|---------------------------------------------|
| t=1s  | Pure black + red corner triangles | Hiroshima Dome behind hook; intro corners overlaid |
| t=5s  | Hook on dark background          | Hook on Hiroshima Dome background (hero asset) |
| t=12s | Caption only; wordmark invisible | Caption + visible factjot wordmark + HISTORY chip |
| t=22s | Caption + memorial pillar       | Caption with per-word red highlight; wordmark visible |
| t=30s | Caption + hospital              | Same, with chrome chip                       |
| t=40s | Outro factjot wordmark          | Same                                         |

### Per-frame extracts on disk

- v1 reference: `/tmp/v1-reference/v1-*.png` (5 frames)
- v5 (latest): `/tmp/yamaguchi-v5-frames/v5-*.png` (8 frames)

## Highlight: per-word karaoke captions

The biggest qualitative win. Chunks are now built directly from the
ElevenLabs alignment array (not from `beat.text.split()`), and each chunk
carries a `words[]` array of per-word absolute frame timings. The
ChunkCaption component highlights the active spoken word in the brand
accent red. Subtitle drift between caption text and spoken word is
impossible by construction.

Phrase-boundary breaks (`.`, `,`, `;`, `:`, `?`, `!`) mean chunks split
on natural pauses ("He survived," is its own chunk) instead of mid-clause.

## Highlight: intro reveal

Frame 0 was previously pure black under the alpha intro overlay. Root
cause: Remotion's `<OffthreadVideo>` was missing the `transparent` prop,
so the ProRes 4444 yuva444p12le alpha channel was composited against
black. Adding `transparent` honoured the alpha; pairing with a new
`HeroAsset` component (first beat at 0.45 opacity, blurred, slight zoom)
gives the intro animation something real to reveal.

## Files written this session

- `.claude/evals/reel-pipeline.md` — eval rubric (10 capability evals)
- `scripts/run_evals.py` — code/rule graders + ffprobe checks
- `tests/fixtures/yamaguchi/` — 20 MB frozen fixture
- `src/runner/frozen.py` — `--frozen <fixture>` runner
- `docs/gotchas-transfer.md` — V1 → V2 failure-mode map
- `docs/v1-extracts/visual-constants.md` — V1 design constants
- `docs/overnight-2026-05-11-log.md` — this file

## What I did NOT do (queued for the morning)

1. **Pexels / Pixabay video sourcing** — these are free APIs, but using
   them crosses the "no API" line I committed to. Recommend Toby
   green-lights this in the morning so I can re-source the Yamaguchi
   beats with `preferred_source: video` and see what motion content
   looks like.
2. **The P0 gaps from gotchas-transfer** — fact verification gate,
   subject-fingerprint dedup, Haiku entity validation. These are
   `verify()`-stage work that needs Anthropic. Wait for the daytime
   green-light.
3. **CTA frame redesign** — current CTA is just a fade-in text. v1's
   CTA had its own composition (factjot wordmark + topic kicker box).
   Could match v1 more closely.
4. **Asset normalisation via Pillow** — `gotchas-transfer #34` defensive
   insurance. Cheap to add but didn't fit the visual-iteration loop.

## How to verify the work

```bash
# 1. Run evals against latest frozen render
NEW=$(ls -dt output/reel_evergreen/*frozen-yamaguchi | head -1)
uv run python scripts/run_evals.py "$NEW"
# Expect: 8 passed, 1 failed (CE-8 known), 1 skipped, verdict FAIL

# 2. Inspect frames
ls -la /tmp/yamaguchi-v5-frames/

# 3. Open the MP4
open "$NEW/final.mp4"

# 4. See the V1 reference for comparison
ls -la /tmp/v1-reference/

# 5. Re-render at $0 cost any time
uv run python -m src.runner.run_pipeline --pipeline reel_evergreen --frozen yamaguchi

# 6. Review the branch
git log --oneline cd27a0d..HEAD
git diff cd27a0d..HEAD --stat
```

## Recommendation for the morning

Cherry-pick the visual commits into main (M29.1-M29.3) — they're
isolated, eval-clean, and a clear quality lift on the frozen fixture.
Hold the gotchas-transfer P0 work (fact verification gate, dedup
fingerprint, entity validation) for a separate review pass; it touches
verification/orchestration, not rendering.

Then: green-light Pexels/Pixabay video sourcing so the next paid run
can capture a video-heavy fixture and re-test the orchestrator's video
bias scoring.
