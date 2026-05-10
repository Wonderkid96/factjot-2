# V1 visual constants (extracted)

Source: `/Users/Music/Developer/Insta-bot/src/render/` (reel_composer.py + reel_text_renderer.py).

These are the numeric/style decisions V1 settled on after many iterations.
Bot-2 should match unless we have a written reason to differ.

## Canvas

| Parameter        | V1     | Bot-2          | Match? |
|------------------|--------|----------------|--------|
| Width            | 1080   | 1080           | ✓      |
| Height           | 1920   | 1920           | ✓      |
| FPS              | 30     | 30             | ✓      |

## Typography

| Element          | V1                                | Bot-2                                     | Match? |
|------------------|-----------------------------------|-------------------------------------------|--------|
| Kinetic subtitles| Archivo Bold 700                  | Space Grotesk Bold 700                    | DIFFERS |
| Hook             | Archivo Black                     | Archivo Black                             | ✓      |
| Subtitle size    | 72px (Space Grotesk SemiBold also acceptable) | ~72px lowercase           | ✓      |
| Wordmark         | Instrument Serif                  | Instrument Serif                          | ✓      |

> **Discrepancy:** V1 uses Archivo Bold 700 for subtitles in some templates
> but Space Grotesk SemiBold in `reel_text_renderer.py` (line 70: 
> "Body-scale, Space Grotesk SemiBold reads cleanly"). Bot-2's choice of
> Space Grotesk Bold 700 lands between the two and matches user's stated
> "subtitles use space 700 font, headers 900" rule.

## Encode

| Parameter        | V1                                | Bot-2 (Remotion default) | Action |
|------------------|-----------------------------------|--------------------------|--------|
| Codec            | libx264                           | libx264                  | ✓      |
| Preset           | medium                            | medium                   | ✓      |
| CRF              | 23                                | 18 (Remotion default)    | Consider crf=20 to match V1 quality budget |
| Audio sample rate| 48kHz                             | 48kHz (resampled)        | ✓      |

## Layout

| Element                  | V1                              | Bot-2                                  | Match? |
|--------------------------|---------------------------------|----------------------------------------|--------|
| CTA frame y position     | 28% from top                    | ~52% (subtitle line)                   | Different — V1's CTA is its own composition; Bot-2 has subtitle + CTA window |
| Caption pill / stroke    | None (plain text + drop shadow) | None (drop shadow only)                | ✓      |
| Footage frame            | 65% width (border left/right)   | Full-bleed with chrome overlay         | DIFFERS |

## Intro overlay

| Parameter         | V1                                          | Bot-2                                   | Match? |
|-------------------|---------------------------------------------|-----------------------------------------|--------|
| File              | `brand/intros/factjot_intro.mov`            | `brand/intros/factjot_intro.mov`        | ✓ (same file) |
| Duration          | 1.37s                                       | Matches MOV duration                    | ✓      |
| Format            | ProRes 4444 yuva444p12le (12-bit alpha)     | Same input                              | ✓      |
| Scale filter      | `bilinear` (lanczos is too expensive)       | Remotion handles via Video component    | N/A    |
| `eof_action`      | `pass` (don't hold stream open)             | Remotion's `<Sequence>` handles this    | N/A    |

## Subtitle timing

V1 generates `.ass` subtitle files via `tts_engine.py::generate_ass_file()`
from ElevenLabs word-level beats. Each chunk is rendered as a libass
subtitle window. Bot-2's `FactReel.tsx` does the same chunking in React
(`WORDS_PER_CAPTION_CHUNK = 3`).

| V1 default              | Bot-2 default | Match? |
|-------------------------|---------------|--------|
| Chunk word count        | 3-5 (variable)| 3 (constant) | ✓ (close enough) |
| Sync offset             | -0.2s (mp3 latency comp) | -0.2s | ✓      |

## Open questions to test overnight

1. Does Bot-2's caption Y position (52%) match V1's recent output? — needs
   frame-by-frame comparison against `/tmp/v1-reference/v1-*.png`.
2. Does Remotion's default crf=18 produce a 53MB MP4 for 42s — that's
   ~10Mbps which is higher than V1's crf-23 output. Consider crf=20 to
   trim filesize and roughly match V1 quality budget.
3. V1 uses 65%-width footage with side borders. Bot-2 is full-bleed.
   Toby's v1 reference frames show full-bleed, so this is the right call.
