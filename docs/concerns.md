# Fact Jot v2 — open concerns & adjustments

Living tracker. Tick off in order as we address each item. New concerns added at the bottom; resolved items kept (struck through and dated) for traceability.

---

## P0 — must land before next strong test

- [ ] **#1 Topic-level entity propagation actually fires.** Code is committed; first M24 with this code is M24 #12. Verify `topic_entity_resolved` log line appears and pool sizes go up vs M24 #11.
- [ ] **#2 Subtitle chunks render correctly.** Big-text (88px), 3-5 word chunks, lower-third position, timed via alignment. Defensive `?? []` to tolerate old specs.
- [ ] **#3 Hook quality.** Sonnet must produce counterintuitive declarative claims, not passive descriptions. Em/en dashes and ellipses banned (with post-generation scrub as final defence). Hook examples added to prompt.
- [ ] **#4 Length cap.** Total script 80-100 words, exactly 4 beats, 30-40s when narrated. Anything longer drags.
- [ ] **#5 Subtitle sync.** Beat windows offset by hook duration so captions align with audio.
- [ ] **#6 Captions at lower third (not top).** Explicit `flexDirection: column, justifyContent: flex-end`.
- [ ] **#7 Brand intro overlay.** v1's `factjot_intro.mov` plays as alpha-channel top overlay for first 1.37s. Pipeline copies it into each run dir.
- [ ] **#8 Empty slots prevented.** Orchestrator always returns the highest-scored asset when the pool is non-empty, even if vision rejects it.
- [ ] **#9 Tighter sourcing queries.** 1-3 word progressive queries, no scene descriptions.

## P1 — visual quality, before we publish

- [ ] **#10 Asset-level dedup ledger.** `data/ledgers/used_assets.jsonl` records every URL used; orchestrator skips recently-used (30-day window). Stops the same Wikimedia photo turning up across reels.
- [ ] **#11 Vision-check on archive matches.** Already wired in pool-then-rank. Confirm it actually runs in M24 #12 logs.
- [ ] **#12 Script writer should pre-validate length.** If output exceeds 110 words, ask Sonnet to tighten before passing to TTS.
- [ ] **#13 Better topic quality without curator.** Currently top-upvote pick. Consider:
  - Higher minimum upvote threshold (10k Reddit / always for DYK)
  - Filter out non-fact noise (image-only Reddit posts that are visual not factual)
  - Source weighting (UnpopularFacts > generic todayilearned)

## P1 — extra polish

- [ ] **#14 Noise / film grain overlay.** v1 had a temporal film grain (luma noise) baked in via FFmpeg. Adds production feel. Implement as Remotion overlay or post-render FFmpeg pass.
- [ ] **#15 More fact sources.** Damn Interesting (RSS), Smithsonian Magazine (RSS), Public Domain Review (RSS), Wikipedia "Selected anniversaries" (daily). All free, all RSS, ~30 lines each.

## P0 — Remotion is being underused (Toby flagged 2026-05-10)

Honest read: we've been treating Remotion as a video compositor and not using ANY of its motion-design power. Every Remotion benefit (interpolate, spring, Easing, Transitions, composition library) is currently absent. The output looks like iMovie because it IS like iMovie. This is the single biggest brand-quality lever remaining.

- [ ] **#16 Hook entry animation.** Hook text should animate IN — e.g. mask reveal, scale spring, letter stagger. Currently appears static.
- [ ] **#17 Caption chunk pop-in.** Each chunk should fade/spring in with a snap (15-20 frames), not just appear. TikTok-standard.
- [ ] **#18 Asset transitions between beats.** Currently hard-cuts. Cross-dissolves, whip pans, dip-to-color, parallax slide — pick a small set, vary per beat for rhythm.
- [ ] **#19 Image parallax (Ken Burns).** Static images should slow-pan / slow-zoom. Trivial in Remotion via `useCurrentFrame` + interpolate.
- [ ] **#20 CTA animation.** CTA needs presence — slide-up + fade-in, or word-by-word reveal. Currently static.
- [ ] **#21 Wordmark presence.** factjot wordmark should appear somewhere in every frame after the intro (corner watermark? lower-right pill?). Currently absent from FactReel composition.
- [ ] **#22 Component library + templates.** Spec §17.1 Phase 1.2: build `HookCard`, `BeatVideoOver`, `BeatStatOverlay`, `BeatComparison`, `OutroCTA`, transition library. Script writer's composition_plan picks per beat. Different combinations = "feels handmade".

Once these land, the strong test result will look like a real brand reel, not a slideshow.

## P2 — overnight iteration enablers (already shipped, sanity-check)

- [x] **USE_LOCAL_AGENT=true** routes Anthropic calls to `claude -p` (free via subscription). Committed.
- [x] **--reuse-narration-from <run-id>** copies narration + alignment from prior run, skips ElevenLabs. Committed.
- [x] **--topic "X"** flag bypasses discovery + picking. Committed.

## P3 — Phase 1.2+ (deferred per spec §17.1)

- [ ] **Composition library + director step.** `HookStatBlast`, `BeatMapPin`, `BeatTimeline` etc. Sonnet picks per beat.
- [ ] **Word-by-word kinetic captions.** Currently chunk-level (3-5 words); upgrade to word-by-word sync.
- [ ] **Specialist visuals.** Mapbox maps, animated SVG diagrams, counters synced to alignment.
- [ ] **Update elevenlabs voice ID to be https://elevenlabs.io/app/voice-library?voiceId=Bj9UqZbhQsanLzgalpEG - Bj9UqZbhQsanLzgalpEG

---

## Resolved

- [x] ~~`Remotion 5` doesn't exist; v2 plan was wrong.~~ Pinned to `^4.0.0`. (2026-05-10)
- [x] ~~zod must be 4.3.6 for Remotion 4.~~ Pinned. (2026-05-10)
- [x] ~~Fonts not loading in Remotion.~~ `@remotion/google-fonts` wires Archivo Black / Instrument Serif / Space Grotesk. (2026-05-10)
- [x] ~~`--public-dir` flag was unreliable for serving run-dir assets.~~ Switched to in-process HTTP server bridge. (2026-05-10)
- [x] ~~ElevenLabs alignment was returning char-list, MediaSet expects list[dict].~~ Group chars to words in `_fetch_alignment`. (2026-05-10)
- [x] ~~Topic curator was costing $0.17/run for over-engineering.~~ Removed; replaced with deterministic top-upvote pick. (2026-05-10)
- [x] ~~Wikidata SPARQL timeouts were 30s × 3 retries (90s/call).~~ Cut to 10s × 2 retries (20s). (2026-05-10)
- [x] ~~Reddit fetcher required app registration.~~ Switched to public `.json` endpoint, no auth. (2026-05-10)
- [x] ~~Voice ID drift between docs and live env.~~ Docs reference `.env` only; voice now `3WqHLnw80rOZqJzW9YRB`. (2026-05-10)
