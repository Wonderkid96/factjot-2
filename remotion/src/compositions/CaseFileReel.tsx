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
  })),
});

const INTRO_DURATION_S = 1.37;
// Case-file scenes leave ~25% of vertical space empty below the scene element
// (polaroid, document, card all centre-anchored ~510-1410). Captions land in
// that desk negative space at 0.78 of frame height = ~1500px from top.
// Stays clear of the Instagram bottom safe zone (~1680+).
const CAPTION_TOP_FRACTION = 0.78;
const FRAME_H = 1920;

function isVideoUrl(p: string | null): boolean {
  if (!p) return false;
  return p.endsWith(".mp4") || p.endsWith(".webm") || p.endsWith(".mov");
}

// ---------- Caption (identical to FactReel) ----------

interface ChunkWord {
  text: string;
  start_frame: number;
  end_frame: number;
  emphasis?: boolean;
}

function ChunkCaption({
  text, words, chunkStart,
}: {
  text: string;
  words?: ChunkWord[];
  chunkStart: number;
}) {
  const frame = useCurrentFrame();
  const baseStyle: React.CSSProperties = {
    color: "#FFFFFF",
    fontFamily: "Space Grotesk",
    fontWeight: 700,
    fontSize: 64,
    lineHeight: 1.15,
    letterSpacing: "-0.005em",
    margin: 0,
    textAlign: "center",
    textShadow: "0 4px 18px rgba(0,0,0,0.85), 0 0 8px rgba(0,0,0,0.6)",
  };

  if (!words || words.length === 0) {
    return <p style={baseStyle}>{text}</p>;
  }

  return (
    <p style={baseStyle}>
      {words.map((w, i) => {
        const localStart = w.start_frame - chunkStart;
        const localEnd = w.end_frame - chunkStart;
        const isActive = frame >= localStart && frame < localEnd;
        const emphasisScale = w.emphasis
          ? interpolate(
              frame,
              [localStart - 4, localStart + 2, Math.min(localEnd, localStart + 14)],
              [1.0, 1.14, 1.0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            )
          : 1.0;
        const color = isActive ? palette.accent : "#FFFFFF";
        return (
          <span key={`w-${i}`} style={{
            color,
            display: "inline-block",
            transform: `scale(${emphasisScale})`,
            transformOrigin: "center center",
            transition: "color 80ms linear",
            marginRight: i < words.length - 1 ? (w.emphasis ? "0.38em" : "0.26em") : 0,
            marginLeft: w.emphasis ? "0.06em" : 0,
          }}>
            {w.text}
          </span>
        );
      })}
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

// ---------- Scrappy mission-brief stage ----------

// Per-beat stage offsets — each scene sits in a deliberately slightly-off
// position so as the four beats accumulate they read as a *stack* of related
// items on a desk rather than four identical centred renders. The offsets
// alternate left/right and creep down the frame so each new beat covers
// part of the previous ones, but enough of each prior beat peeks out to be
// recognisable. Indices wrap mod-4 so beat counts >4 still get variety.
const STAGE_OFFSETS: Array<{ x: number; y: number; rotation: number }> = [
  { x: -70, y: -180, rotation: -3.0 },
  { x:  80, y: -110, rotation:  2.4 },
  { x: -50, y:  -30, rotation: -1.8 },
  { x:  60, y:  -90, rotation:  1.6 },
];

// Whole-stage zoom — the "camera leaning in" feel for the mission-brief look.
// 1.06 is enough to feel intimate without clipping critical scene content.
const STAGE_SCALE = 1.06;

// Opacity of a prior beat after the next one has taken over. Visible enough
// to read as a stacked layer, dim enough that the eye lands on the current
// beat. 14-frame crossfade so the handoff is felt, not seen.
const FROZEN_OPACITY = 0.42;
const FADE_FRAMES = 14;

interface StageProps {
  offset: { x: number; y: number; rotation: number };
  /** How many frames this scene is the ACTIVE one. After that it freezes at FROZEN_OPACITY. */
  activeFrames: number;
  children: React.ReactNode;
}

function Stage({ offset, activeFrames, children }: StageProps) {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [activeFrames - FADE_FRAMES, activeFrames],
    [1.0, FROZEN_OPACITY],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  return (
    <AbsoluteFill style={{
      transform: `translate(${offset.x}px, ${offset.y}px) rotate(${offset.rotation}deg)`,
      opacity,
    }}>
      {children}
    </AbsoluteFill>
  );
}

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
        <Audio src={music_audio} volume={0.18} loop />
      )}

      {/* Hook — sits over the desk during the title hold */}
      <Sequence from={0} durationInFrames={Math.max(hookEnd, 1)}>
        <Hook text={hook} />
      </Sequence>

      {/* Stage container — scale-zoomed for the "leaned-in mission brief" feel.
          Each beat's Sequence persists from its start through outroStart so
          prior beats remain visible (faded) behind the current one, giving
          the scrappy stacked-evidence look. */}
      <AbsoluteFill style={{
        transform: `scale(${STAGE_SCALE})`,
        transformOrigin: "center 42%",
      }}>
        {beats.map((beat, i) => {
          const path = beat.asset?.path ?? null;
          const isVideo = isVideoUrl(path);
          const nextStart = i + 1 < beats.length ? beats[i + 1].start_frame : outroStart;
          // Length of THIS beat as "active" before the next one takes over.
          const activeFrames = Math.max(nextStart - beat.start_frame, fps);
          // Sequence runs all the way to outroStart so prior beats stay on
          // screen (at FROZEN_OPACITY) until the outro begins.
          const sequenceLength = Math.max(outroStart - beat.start_frame, fps);
          const priorBeat = i > 0 ? beats[i - 1] : null;
          const priorSrc = priorBeat?.asset?.path ?? null;
          const priorIsVideo = isVideoUrl(priorSrc);
          const offset = STAGE_OFFSETS[i % STAGE_OFFSETS.length];

          return (
            <Sequence key={`scene-${i}`} from={beat.start_frame} durationInFrames={sequenceLength}>
              <Stage offset={offset} activeFrames={activeFrames}>
                <SceneRenderer
                  treatment={beat.scene_treatment as SceneTreatment}
                  src={path}
                  isVideo={isVideo}
                  beatText={beat.text}
                  durationFrames={activeFrames}
                  priorSrc={priorSrc}
                  priorIsVideo={priorIsVideo}
                />
              </Stage>
            </Sequence>
          );
        })}
      </AbsoluteFill>

      {/* Caption chunks — same karaoke treatment as FactReel */}
      {beats.flatMap((beat, i) =>
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
                <ChunkCaption
                  text={chunk.text}
                  words={chunk.words}
                  chunkStart={chunk.start_frame}
                />
              </AbsoluteFill>
            </Sequence>
          );
        })
      )}

      {(cta_window?.chunks ?? []).map((chunk, ci) => {
        const dur = Math.max(chunk.end_frame - chunk.start_frame, Math.floor(fps / 3));
        return (
          <Sequence key={`cta-chunk-${ci}`} from={chunk.start_frame} durationInFrames={dur}>
            <AbsoluteFill style={{
              display: "flex", flexDirection: "column", justifyContent: "flex-start",
              paddingTop: Math.floor(FRAME_H * CAPTION_TOP_FRACTION),
              paddingLeft: 80, paddingRight: 80, pointerEvents: "none",
            }}>
              <ChunkCaption text={chunk.text} words={chunk.words} chunkStart={chunk.start_frame} />
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
              <ChunkCaption text={chunk.text} words={chunk.words} chunkStart={chunk.start_frame} />
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* Outro wordmark — runs from outroStart through the tail buffer so the
          final ~1.2s isn't an empty desk. The wordmark letter-pop-in finishes
          well before the end; it then holds steady while the audio fades out. */}
      <Sequence from={outroStart}>
        <AbsoluteFill style={{
          display: "flex", alignItems: "center", justifyContent: "center",
          paddingBottom: 320,
          backgroundColor: "rgba(0,0,0,0.55)",
        }}>
          <OutroWordmark />
        </AbsoluteFill>
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
