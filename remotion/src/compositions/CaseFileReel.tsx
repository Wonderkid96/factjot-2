import React from "react";
import { z } from "zod";
import {
  AbsoluteFill, Sequence, useVideoConfig, useCurrentFrame,
  interpolate, spring, Easing, Audio, OffthreadVideo, Loop,
} from "remotion";
import { Wordmark } from "../components/Wordmark";
import { YearAccent } from "../components/YearAccent";
import { palette } from "../style/tokens";
import { Desk } from "../components/casefile/Desk";
import { SceneRenderer, SceneTreatment } from "../components/casefile/SceneRenderer";
import { Counter } from "../components/casefile/animations/Counter";

// CaseFileReel — case-file aesthetic variant of FactReel. Same audio,
// captions, chrome. Every beat renders via SceneRenderer instead of
// flat-bleed Ken Burns. A persistent EvidenceStack accumulates prior beats
// in the bottom-right corner.

const chunkSchema = z.object({
  text: z.string(),
  start_frame: z.number(),
  end_frame: z.number(),
  words: z.array(z.object({
    text: z.string(),
    start_frame: z.number(),
    end_frame: z.number(),
    emphasis: z.boolean().default(false),
  })).default([]),
});

const windowSchema = z.object({
  start_frame: z.number(),
  end_frame: z.number(),
  chunks: z.array(chunkSchema).default([]),
});

const treatmentEnum = z.enum([
  "polaroid", "evidence_slide", "redacted_doc", "stamp_reveal",
  "index_card", "newsprint_clip", "archive_film", "map_pin",
  "red_thread", "ken_burns",
]);

export const caseFileReelSchema = z.object({
  composition: z.string(),
  title: z.string(),
  hook: z.string(),
  cta: z.string(),
  kicker: z.string().default("FACT"),
  narration_audio: z.string().nullable(),
  music_audio: z.string().nullable().optional(),
  grit_overlay: z.string().nullable().optional(),
  ambient_overlay: z.string().nullable().optional(),
  intro_overlay: z.string().nullable().optional(),
  alignment: z.array(z.any()),
  hook_window: windowSchema.optional(),
  cta_window: windowSchema.optional(),
  outro_window: windowSchema.optional(),
  outro_text: z.string().optional(),
  total_frames: z.number().optional(),
  narration_offset_frames: z.number().optional(),
  beats: z.array(z.object({
    text: z.string(),
    start_frame: z.number(),
    end_frame: z.number(),
    scene_treatment: treatmentEnum.default("ken_burns"),
    chunks: z.array(chunkSchema).default([]),
    asset: z.object({
      path: z.string().nullable(),
      source: z.string().nullable(),
    }),
    // Optional rich-animation overlay — see src/pipelines/models.py.
    // Validated upstream so we only need to support known shapes here.
    animation: z.discriminatedUnion("type", [
      z.object({
        type: z.literal("counter"),
        from: z.number(),
        to: z.number(),
        unit: z.string().nullable().optional(),
      }),
    ]).nullable().optional(),
  })),
});

const INTRO_DURATION_S = 1.37;
// TikTok-style caption position — anchored to the bottom third with the
// font sized so the line wraps to ~2 lines max. The CENTRE of the frame
// is reserved for animations + scene visuals.
const CAPTION_TOP_FRACTION = 0.72;
const FRAME_H = 1920;

function isVideoUrl(p: string | null): boolean {
  if (!p) return false;
  return p.endsWith(".mp4") || p.endsWith(".webm") || p.endsWith(".mov");
}

// ---------- Caption (TikTok-style bold block) ----------

// TikTok caption convention: bottom-anchored, large bold sans, heavy stroke
// AND drop-shadow so the text reads on any background. Each chunk does a
// 4-frame fade-in + a 1-2px upward translate so the swap reads as a soft
// pop rather than a hard cut. Chunks are already chain-extended upstream
// (in render.remotion.py), so there's no gap between consecutive chunks —
// only the entry animation is local.
function ChunkCaption({ text }: { text: string }) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const tx = interpolate(frame, [0, 6], [6, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <p style={{
      color: "#FFFFFF",
      fontFamily: "Archivo Black",
      fontWeight: 900,
      fontSize: 76,
      lineHeight: 1.1,
      letterSpacing: "-0.01em",
      margin: 0,
      textAlign: "center",
      textTransform: "lowercase",
      // Heavy black stroke for TikTok-style legibility on any background,
      // plus a soft drop shadow for depth on dark scenes.
      WebkitTextStroke: "4px #000000",
      paintOrder: "stroke fill",
      textShadow: "0 6px 18px rgba(0,0,0,0.85)",
      opacity,
      transform: `translateY(${tx}px)`,
    }}>
      {text}
    </p>
  );
}

// ---------- Hook + CTA (slightly lighter than FactReel — case-file is editorial, not loud) ----------

function Hook({ text }: { text: string }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const introFrames = Math.floor(fps * INTRO_DURATION_S);
  const revealStart = Math.floor(introFrames * 0.4);
  const entry = spring({
    frame: Math.max(0, frame - revealStart),
    fps,
    config: { damping: 14, stiffness: 110 },
  });
  const scale = interpolate(entry, [0, 1], [0.92, 1]);
  const opacity = interpolate(entry, [0, 1], [0, 1]);
  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <h1 style={{
        color: palette.off_white,
        fontFamily: "Archivo Black",
        fontSize: 80,
        lineHeight: 1.05,
        textAlign: "center",
        padding: "0 70px",
        textTransform: "lowercase",
        letterSpacing: "-0.01em",
        margin: 0,
        textShadow: "0 6px 24px rgba(0,0,0,0.7)",
        transform: `scale(${scale})`,
        opacity,
      }}>
        <YearAccent text={text.replace(/\.$/, "")} />
        <span style={{ color: palette.accent }}>.</span>
      </h1>
    </AbsoluteFill>
  );
}

function ChromeOverlay({ kicker }: { kicker: string }) {
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{
        position: "absolute",
        top: 60,
        left: 56,
        filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.7))",
      }}>
        <Wordmark size={44} />
      </div>
      <div style={{
        position: "absolute",
        top: 76,
        right: 56,
        filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.7))",
        color: palette.off_white,
        fontFamily: "Space Grotesk",
        fontWeight: 600,
        fontSize: 22,
        letterSpacing: "0.22em",
        textTransform: "uppercase",
      }}>
        {kicker}
      </div>
    </AbsoluteFill>
  );
}

function OutroWordmark() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const letters = ["f", "a", "c", "t", "j", "o", "t"];
  const italicFrom = 4;
  return (
    <div style={{
      fontFamily: "Instrument Serif",
      fontSize: 144,
      color: palette.off_white,
      letterSpacing: "-0.04em",
      textShadow: "0 6px 24px rgba(0,0,0,0.6)",
    }}>
      {letters.map((ch, i) => {
        const enter = spring({
          frame: Math.max(0, frame - i * 3),
          fps,
          config: { damping: 12, stiffness: 140 },
        });
        const scale = interpolate(enter, [0, 1], [0.6, 1]);
        const opacity = interpolate(enter, [0, 1], [0, 1]);
        return (
          <span key={`l-${i}`} style={{
            display: "inline-block",
            transform: `scale(${scale})`,
            opacity,
            fontStyle: i >= italicFrom ? "italic" : "normal",
            transformOrigin: "center bottom",
          }}>
            {ch}
          </span>
        );
      })}
      <span style={{
        color: palette.accent,
        opacity: interpolate(frame, [21, 27], [0, 1], { extrapolateRight: "clamp" }),
        marginLeft: 6,
      }}>.</span>
    </div>
  );
}

// Outro plate — rapid fade to solid black (10 frames ≈ 333ms), then the
// wordmark dead-centred over it. The previous version held the last beat's
// asset at 0.55 opacity behind the wordmark, which read as cluttered;
// Netflix-doc closes are a clean cut to black + the brand mark.
function OutroPlate() {
  const frame = useCurrentFrame();
  const bgOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <>
      <AbsoluteFill style={{
        backgroundColor: "#000000",
        opacity: bgOpacity,
      }} />
      <AbsoluteFill style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}>
        <OutroWordmark />
      </AbsoluteFill>
    </>
  );
}

function GrainOverlay({ src, durationInFrames }: { src?: string | null; durationInFrames: number }) {
  if (!src) {
    return null;
  }
  return (
    <AbsoluteFill style={{
      pointerEvents: "none",
      mixBlendMode: "screen",
      opacity: 0.45,
    }}>
      <Loop durationInFrames={Math.max(durationInFrames, 1)}>
        <OffthreadVideo
          src={src}
          muted
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </Loop>
    </AbsoluteFill>
  );
}

// Ambient backdrop — slow, low-opacity loop that lives between the Desk base
// and the case-file scenes. Subtle texture (dust, paper fibres, light shift)
// without competing for attention. Falls through silently when no src.
function AmbientLayer({ src, durationInFrames }: { src?: string | null; durationInFrames: number }) {
  if (!src) {
    return null;
  }
  return (
    <AbsoluteFill style={{
      pointerEvents: "none",
      opacity: 0.18,
    }}>
      <Loop durationInFrames={Math.max(durationInFrames, 1)}>
        <OffthreadVideo
          src={src}
          muted
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </Loop>
    </AbsoluteFill>
  );
}

// (scrappy stage code removed — scenes now render one-at-a-time at their
//  natural centred position, and prior beats accumulate as a corner thumbnail
//  stack via EvidenceStack at full opacity.)

// ---------- Composition ----------

export const CaseFileReel: React.FC<z.infer<typeof caseFileReelSchema>> = ({
  hook, cta, narration_audio, music_audio, grit_overlay, ambient_overlay, beats, intro_overlay,
  hook_window, cta_window, outro_window,
  narration_offset_frames, kicker,
}) => {
  const { fps } = useVideoConfig();

  const hookEnd = hook_window?.end_frame ?? Math.floor(fps * 1.5);
  const ctaStart = cta_window?.start_frame ?? (beats.length ? beats[beats.length - 1].end_frame : hookEnd);
  const ctaEnd = cta_window?.end_frame ?? (ctaStart + Math.floor(fps * 1.8));
  const outroStart = outro_window?.start_frame ?? ctaEnd;
  const outroEnd = outro_window?.end_frame ?? (outroStart + Math.floor(fps * 2.0));
  const INTRO_FRAMES = Math.floor(fps * INTRO_DURATION_S);
  const narrationDelay = narration_offset_frames ?? 0;

  // Music gets a 2-second fade in/out so the bed doesn't slam in or cut out.
  // Narration plays at full volume the whole time — fading the voice itself
  // sounds like a dead mic at the start of the hook.
  const FADE_FRAMES = Math.floor(fps * 2);
  const MUSIC_PEAK = 0.07;
  const musicVolume = (f: number) => {
    const fadeIn = Math.min(1, f / FADE_FRAMES);
    const fadeOut = Math.min(1, Math.max(0, (outroEnd - f) / FADE_FRAMES));
    return MUSIC_PEAK * Math.min(fadeIn, fadeOut);
  };

  return (
    <AbsoluteFill style={{ backgroundColor: palette.ink }}>
      {/* Persistent desk background — case-file foundation */}
      <Desk />

      {/* Ambient backdrop — sits between desk and scenes at 0.18 opacity */}
      <AmbientLayer src={ambient_overlay} durationInFrames={Math.max(outroEnd, 60)} />

      {narration_audio && (
        <Sequence from={narrationDelay}>
          <Audio src={narration_audio} />
        </Sequence>
      )}
      {music_audio && (
        <Audio src={music_audio} volume={musicVolume} loop />
      )}

      {/* Hook — sits over the desk during the title hold */}
      <Sequence from={0} durationInFrames={Math.max(hookEnd, 1)}>
        <Hook text={hook} />
      </Sequence>

      {/* Per-beat scenes — each beat's Sequence extends BEAT_OVERLAP_FRAMES
          past its end so it cross-fades into the next beat's fade-in. The
          15-frame fade-out lives inside CinematicFrame's opacity envelope. */}
      {beats.map((beat, i) => {
        const BEAT_OVERLAP_FRAMES = 15;
        const path = beat.asset?.path ?? null;
        const isVideo = isVideoUrl(path);
        const isLast = i === beats.length - 1;
        const naturalDuration = Math.max(beat.end_frame - beat.start_frame, fps);
        // Last beat extends through CTA + outro so we don't cut to bare desk.
        const extendedEnd = isLast ? Math.max(outroEnd, beat.end_frame) : beat.end_frame;
        // Add overlap so the next beat is rendered on top during this beat's
        // last 15 frames — both scenes alpha-blend during the handoff.
        const duration = Math.max(extendedEnd - beat.start_frame, naturalDuration) + BEAT_OVERLAP_FRAMES;

        const priorBeat = i > 0 ? beats[i - 1] : null;
        const priorSrc = priorBeat?.asset?.path ?? null;
        const priorIsVideo = isVideoUrl(priorSrc);

        return (
          <Sequence key={`scene-${i}`} from={beat.start_frame} durationInFrames={duration}>
            <SceneRenderer
              treatment={beat.scene_treatment as SceneTreatment}
              src={path}
              isVideo={isVideo}
              beatText={beat.text}
              durationFrames={duration}
              priorSrc={priorSrc}
              priorIsVideo={priorIsVideo}
            />
            {/* Rich-animation overlay (optional). Sits on top of the scene
                treatment with its own dim backdrop — designed to be the
                dominant element while playing. */}
            {beat.animation?.type === "counter" && (
              <Counter
                from={beat.animation.from}
                to={beat.animation.to}
                unit={beat.animation.unit ?? null}
              />
            )}
          </Sequence>
        );
      })}

      {/* (No corner stack in the Netflix-doc layout. Each beat owns the
           full frame; prior beats are remembered by the narration alone.) */}

      {/* Caption chunks — plain white block, no karaoke. Text-only scene
          treatments (index_card, redacted_doc) already render the beat text
          full-screen, so suppressing captions on those beats avoids reading
          the same words twice. */}
      {beats.flatMap((beat, i) => {
        const TEXT_ONLY = new Set(["index_card", "redacted_doc"]);
        if (TEXT_ONLY.has(beat.scene_treatment)) {
          return [];
        }
        return (
        ((beat.chunks ?? []).length > 0 ? (beat.chunks ?? []) : [{
          text: beat.text,
          start_frame: beat.start_frame,
          end_frame: beat.end_frame,
          words: [],
        }]).map((chunk, ci) => {
          const chunkDuration = Math.max(chunk.end_frame - chunk.start_frame, Math.floor(fps / 3));
          return (
            <Sequence key={`chunk-${i}-${ci}`} from={chunk.start_frame} durationInFrames={chunkDuration}>
              <AbsoluteFill style={{
                display: "flex",
                flexDirection: "column",
                justifyContent: "flex-start",
                paddingTop: Math.floor(FRAME_H * CAPTION_TOP_FRACTION),
                paddingLeft: 80,
                paddingRight: 80,
                pointerEvents: "none",
              }}>
                <ChunkCaption text={chunk.text} />
              </AbsoluteFill>
            </Sequence>
          );
        })
        );
      })}

      {(cta_window?.chunks ?? []).map((chunk, ci) => {
        const dur = Math.max(chunk.end_frame - chunk.start_frame, Math.floor(fps / 3));
        return (
          <Sequence key={`cta-chunk-${ci}`} from={chunk.start_frame} durationInFrames={dur}>
            <AbsoluteFill style={{
              display: "flex", flexDirection: "column", justifyContent: "flex-start",
              paddingTop: Math.floor(FRAME_H * CAPTION_TOP_FRACTION),
              paddingLeft: 80, paddingRight: 80, pointerEvents: "none",
            }}>
              <ChunkCaption text={chunk.text} />
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {(outro_window?.chunks ?? []).map((chunk, ci) => {
        const dur = Math.max(chunk.end_frame - chunk.start_frame, Math.floor(fps / 3));
        return (
          <Sequence key={`outro-chunk-${ci}`} from={chunk.start_frame} durationInFrames={dur}>
            <AbsoluteFill style={{
              display: "flex", flexDirection: "column", justifyContent: "flex-start",
              paddingTop: Math.floor(FRAME_H * CAPTION_TOP_FRACTION),
              paddingLeft: 80, paddingRight: 80, pointerEvents: "none",
            }}>
              <ChunkCaption text={chunk.text} />
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* Outro — background fades to near-solid black in ~10 frames so the
          last beat's asset clears out, then the wordmark holds dead-centre
          (no paddingBottom offset). */}
      <Sequence from={outroStart}>
        <OutroPlate />
      </Sequence>

      {/* Chrome (wordmark + kicker) appears after intro overlay, hidden during outro */}
      <Sequence from={INTRO_FRAMES} durationInFrames={Math.max(outroStart - INTRO_FRAMES, 1)}>
        <ChromeOverlay kicker={kicker} />
      </Sequence>

      <GrainOverlay src={grit_overlay} durationInFrames={Math.max(outroEnd, 60)} />

      {intro_overlay && (
        <Sequence from={0} durationInFrames={INTRO_FRAMES}>
          <AbsoluteFill style={{ pointerEvents: "none" }}>
            <OffthreadVideo
              src={intro_overlay}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              muted
              transparent
            />
          </AbsoluteFill>
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
