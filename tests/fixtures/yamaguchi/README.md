# Yamaguchi fixture

A frozen end-to-end run captured 2026-05-11 to enable visual iteration
without spending ElevenLabs or Anthropic credits.

## What's here

| File                       | Purpose                                                 |
|----------------------------|---------------------------------------------------------|
| `spec.json`                | Full Remotion props (hook/beats/cta/alignment/timeline) |
| `narration.mp3`            | ElevenLabs voice at 48kHz, atempo'd to 1.1x             |
| `narration-alignment.json` | Word-level alignment used by FactReel chunk captions    |
| `assets/beat-0..3.jpg`     | Wikimedia + Pexels stills resolved for each beat        |

## How to use

Run the pipeline in frozen mode:

```bash
uv run python -m src.runner.run_pipeline --pipeline reel_evergreen --frozen yamaguchi
```

This bypasses discovery, script generation, narration, and asset sourcing
entirely. Only Remotion's render step runs.

Cost: **$0** in product API spend.

## Source

GH Actions run [25642281208](https://github.com/Wonderkid96/factjot-2/actions/runs/25642281208).

Topic override: "Tsutomu Yamaguchi survived both the Hiroshima and
Nagasaki atomic bombings, three days apart."

Eval baseline at capture time:

| Eval                       | Result                  |
|----------------------------|-------------------------|
| CE-1 render completes      | PASS (53.5 MB)          |
| CE-2 duration in range     | PASS (42.52s)           |
| CE-3 frame count match     | PASS (1275 == 1275)     |
| CE-4 beat assets valid     | PASS (4 valid)          |
| CE-5 outro present         | PASS                    |
| CE-6 no em-dash            | PASS                    |
| CE-7 hook word count       | PASS (7)                |
| CE-8 script word count     | **FAIL (74, want 80+)** |
| CE-9 beat count            | PASS (4)                |
| CE-10 topic entity         | SKIP                    |

The CE-8 fail is a known soft fail of the Sonnet writer occasionally
under-delivering. Tracked, not blocking.
