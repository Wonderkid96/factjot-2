# Eval — reel pipeline

The objective quality rubric for a Fact Jot reel. Each grader runs against
a single run directory (`output/reel_evergreen/<run_id>/`) and emits a
PASS/FAIL plus, where useful, a numeric score.

Run via `python scripts/run_evals.py <run_dir>`. Output lands at
`<run_dir>/eval-report.json` and a console summary.

## Why this exists

Before this rubric, every change was scored by Toby's eye — expensive
cognitively and lossy between runs. With graders we can:

- Catch regressions automatically (every GH Actions run)
- Track quality trends across runs
- Halt overnight visual iterations when something gets worse instead of better

This is the prerequisite for any autonomous loop. Without measurement, an
autonomous loop iterates blind.

## Grader types

1. **Code graders** — deterministic shell / Python checks against artefacts
2. **Rule graders** — parse spec.json / alignment.json and assert constraints
3. **Model graders** — vision LLM judges (DEFERRED — costs money, Toby's call)
4. **Human grader** — Toby's final brand approval (no automation)

## Capability evals (must pass on every render)

### CE-1 — Render completes
- **Type:** code
- **Check:** GH Actions step exited 0, `final.mp4` exists and is > 1 MB
- **Why:** the AttributeError I shipped earlier would have failed this at pass@1

### CE-2 — Duration in target range
- **Type:** code (ffprobe)
- **Check:** 25.0 ≤ duration_seconds ≤ 50.0
- **Why:** v1's brand spec calls for 30-45s. Allowing 25-50s as a soft band;
  outside this is a script-writer or timeline-math regression.

### CE-3 — Frame count matches spec
- **Type:** rule
- **Check:** `final.spec.json#total_frames == ffprobe.frame_count`
- **Why:** mismatch = Remotion truncated the composition or audio outran the timeline

### CE-4 — All beat assets valid
- **Type:** code
- **Check:** every `assets/beat-N.{jpg,mp4,...}` exists, > 4 KB, magic-byte sniff passes
- **Why:** 126-byte Wikimedia rate-limit HTML masquerading as JPEG was a bug

### CE-5 — Outro present in alignment
- **Type:** rule
- **Check:** last 6 alignment words concatenated contain "follow fact jot" (case-insensitive)
- **Why:** brand outro must always close the reel

### CE-6 — No em-dash in script
- **Type:** rule
- **Check:** none of `final.spec.json#hook`, `cta`, beats' text, or `title` contains `—` or `–`
- **Why:** banned in Toby's voice. The post-gen scrub catches it but a gate closes the loop.

### CE-7 — Hook word count 6-10
- **Type:** rule
- **Check:** `len(script.hook.split())` in `[6, 10]`
- **Why:** hook formula spec; too short = no payload, too long = lost the scroll

### CE-8 — Script length 80-100 words
- **Type:** rule
- **Check:** `len(hook + beats + cta).split()` in `[80, 110]`
- **Why:** ElevenLabs reads at ~150wpm; out-of-band = wrong duration

### CE-9 — Beat count == 4
- **Type:** rule
- **Check:** `len(script.beats) == 4`
- **Why:** spec hard constraint; downstream timeline math assumes 4

### CE-10 — Topic entity resolved
- **Type:** rule
- **Check:** `script.topic_entity` is non-null OR explicitly null (not missing)
- **Why:** missing key = old model bypassing the new schema

## Visual evals (model grader, deferred)

These need a vision LLM to score. Skipped until Toby green-lights the cost
(estimated $0.01/frame, 5 frames = $0.05/run).

### VE-1 — Caption Y position matches v1 reference
- **Type:** model (vision)
- **Check:** caption baseline at ~52% from top, within ±5% band
- **Reference:** `/tmp/v1-reference/v1-*.png`

### VE-2 — Caption typography matches v1
- **Type:** model (vision)
- **Check:** lowercase, Space Grotesk Bold, no pill / no heavy stroke

### VE-3 — Persistent wordmark visible
- **Type:** model (vision)
- **Check:** `factjot` wordmark top-left for ≥ 90% of frames

### VE-4 — Asset matches subject
- **Type:** model (vision)
- **Check:** rendered frame's asset is on-topic for the beat's text

## Human evals

### HE-1 — Final brand approval
- **Type:** human (Toby)
- **Check:** ship-worthy? Y/N

## Pass@k thresholds

| Eval class       | Target |
|------------------|--------|
| Capability evals | pass^3 = 100% (release-critical) |
| Visual evals     | pass@1 ≥ 80% per dimension (when wired) |
| Human eval       | pass@1 = 100% (no waivers) |

## Score storage

Each run produces `<run_dir>/eval-report.json`:

```json
{
  "run_id": "2026-05-11_00-07_...",
  "timestamp": "2026-05-11T00:07:00Z",
  "capability": {
    "CE-1_render_completes":   {"status": "PASS"},
    "CE-2_duration_in_range":  {"status": "PASS", "actual": 45.5, "min": 25, "max": 50},
    "CE-3_frame_count_match":  {"status": "PASS", "spec": 1365, "actual": 1365},
    "...":                      "..."
  },
  "summary": {"passed": 10, "failed": 0, "skipped": 0},
  "verdict": "PASS"
}
```

A rolling history is appended to `.claude/evals/reel-pipeline.log`.

## When this rubric should change

- New brand constraint added → add a capability eval
- A regression slipped past existing graders → add a grader for the class
- A grader is consistently flaky → tighten it or demote to human
- Model graders prove cheap+reliable → promote to capability

Treat this file as code. Version with commits. Don't loosen thresholds to make a
failing change pass.
