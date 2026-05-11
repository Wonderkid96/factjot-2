import React from "react";
import { z } from "zod";
import {
  AbsoluteFill, Sequence, useVideoConfig, useCurrentFrame,
  interpolate, spring, Easing, Audio, Img, OffthreadVideo,
} from "remotion";
import { Wordmark } from "../components/Wordmark";
import { YearAccent } from "../components/YearAccent";
import { palette } from "../style/tokens";


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

export const factReelSchema = z.object({
  composition: z.string(),
  title: z.string(),
  hook: z.string(),
  cta: z.string(),
  // Short uppercase label rendered top-right alongside the wordmark.
  // Matches v1's "SCIENCE" / "HISTORY" / "NATURE" category chips. Defaults
  // to "FACT" if the pipeline can't derive a more specific category.
  kicker: z.string().default("FACT"),
  narration_audio: z.string().nullable(),
  // Background music — V1's default.mp3 at 20% volume with 1s fade-in.
  music_audio: z.string().nullable().optional(),
  // V1's film-grain overlay — screen-blended on top at ~65% opacity.
  grit_overlay: z.string().nullable().optional(),
  intro_overlay: z.string().nullable().optional(),
  alignment: z.array(z.any()),
  // ALL frame values are ABSOLUTE — relative to start of the video (frame 0).
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
    chunks: z.array(z.object({
      text: z.string(),
      start_frame: z.number(),
      end_frame: z.number(),
      // Per-word timing so the chunk can highlight the spoken word.
      // Built from the same ElevenLabs alignment that drove chunk timing,
      // so word boundaries are exact.
      words: z.array(z.object({
        text: z.string(),
        start_frame: z.number(),
        end_frame: z.number(),
        // True if the word contains a digit — renderer pulses + scales it
        // so years, percentages, and stats land with visual emphasis.
        emphasis: z.boolean().default(false),
      })).default([]),
    })).default([]),
    asset: z.object({
      path: z.string().nullable(),
      source: z.string().nullable(),
    }),
  })),
});

const INTRO_DURATION_S = 1.37;
// v1's caption position: roughly mid-screen, slightly above the centre.
// 1920 * 0.52 = ~998px from top.
const CAPTION_TOP_FRACTION = 0.52;
const FRAME_H = 1920;


// ---------- Sub-components ----------

// Caption chunk: lowercase, clean white, no stroke / no pill,
// soft drop shadow. v1 style verbatim.
//
// When `words[]` is present (built from ElevenLabs alignment), the chunk
// highlights the currently-spoken word with the brand accent. When it's
// not (legacy or fallback chunks), the chunk renders as one static block.
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
  // NO entry fade-in or translate — every chunk swap created a perceptible
  // flicker because the new chunk would animate from opacity 0. The karaoke
  // word colour change inside the chunk provides all the motion needed;
  // text appears instantly with the chunk's start frame.
  const baseStyle: React.CSSProperties = {
    color: "#FFFFFF",
    fontFamily: "Space Grotesk",
    fontWeight: 700,
    fontSize: 72,
    lineHeight: 1.15,
    letterSpacing: "-0.005em",
    margin: 0,
    textAlign: "center",
    textShadow: "0 4px 18px rgba(0,0,0,0.85), 0 0 8px rgba(0,0,0,0.6)",
  };

  // Without word-level timing, render the whole chunk as one block.
  if (!words || words.length === 0) {
    return <p style={baseStyle}>{text}</p>;
  }

  // With word-level timing, render each word inline. Active word goes to
  // accent red; words flagged `emphasis` (digits, years, stats) get a brief
  // pulse + scale around their spoken window.
  return (
    <p style={baseStyle}>
      {words.map((w, i) => {
        const localStart = w.start_frame - chunkStart;
        const localEnd = w.end_frame - chunkStart;
        const isActive = frame >= localStart && frame < localEnd;
        // Emphasis pulse: word scales 1.0 → 1.18 → 1.0 across its window.
        const emphasisScale = w.emphasis
          ? interpolate(
              frame,
              [localStart - 4, localStart + 2, Math.min(localEnd, localStart + 14)],
              [1.0, 1.18, 1.0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            )
          : 1.0;
        const color = w.emphasis && isActive ? palette.accent : (isActive ? palette.accent : "#FFFFFF");
        return (
          <span key={`w-${i}`} style={{
            color,
            display: "inline-block",
            transform: `scale(${emphasisScale})`,
            transformOrigin: "center center",
            transition: "color 80ms linear",
            // Explicit horizontal margin guarantees the trailing space survives
            // the inline-block layout; emphasis words get a bit more breathing room.
            marginRight: i < words.length - 1 ? (w.emphasis ? "0.4em" : "0.28em") : 0,
            marginLeft: w.emphasis ? "0.06em" : 0,
          }}>
            {w.text}
          </span>
        );
      })}
    </p>
  );
}

// Ken Burns slow-zoom for stills. Static images get subtle motion.
// Scale 1.0 -> 1.08 across the beat.
function useKenBurnsScale(durationFrames: number): number {
  const frame = useCurrentFrame();
  return interpolate(frame, [0, durationFrames], [1.0, 1.08], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });
}

function BeatStill({ path, durationFrames }: { path: string; durationFrames: number }) {
  const frame = useCurrentFrame();
  const scale = useKenBurnsScale(durationFrames);
  // Cross-dissolve in over first 12 frames so the cut between beats reads as a fade.
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        src={path}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      />
      {/* Dark gradient at the bottom half so captions stay legible */}
      {/* Top + bottom gradients: top keeps the factjot wordmark legible
          against light assets; bottom keeps captions legible. */}
      <AbsoluteFill style={{
        background:
          "linear-gradient(to bottom, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 35%, rgba(0,0,0,0.55) 90%)",
        pointerEvents: "none",
      }} />
    </AbsoluteFill>
  );
}

function BeatVideo({ path }: { path: string }) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity }}>
      <OffthreadVideo
        src={path}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
      {/* Top + bottom gradients: top keeps the factjot wordmark legible
          against light assets; bottom keeps captions legible. */}
      <AbsoluteFill style={{
        background:
          "linear-gradient(to bottom, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 35%, rgba(0,0,0,0.55) 90%)",
        pointerEvents: "none",
      }} />
    </AbsoluteFill>
  );
}

// Hook title — spring scale + opacity on entry, coordinated with the intro
// overlay's reveal animation. The intro plays for INTRO_DURATION_S frames;
// during that window the title is fading in BENEATH the intro alpha, so as
// the overlay clears the title is already in position.
function Hook({ text }: { text: string }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Delay the spring entry slightly past the intro start so the title
  // "appears" with the intro animation rather than before it.
  const introFrames = Math.floor(fps * INTRO_DURATION_S);
  const revealStart = Math.floor(introFrames * 0.4); // 40% through the intro
  const entry = spring({
    frame: Math.max(0, frame - revealStart),
    fps,
    config: { damping: 14, stiffness: 110 },
  });
  const scale = interpolate(entry, [0, 1], [0.88, 1]);
  const opacity = interpolate(entry, [0, 1], [0, 1]);
  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <h1 style={{
        color: palette.off_white,
        fontFamily: "Archivo Black",
        fontSize: 88,
        lineHeight: 1.05,
        textAlign: "center",
        padding: "0 60px",
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

// HeroAsset — first-beat image at low opacity during the title hold, so
// the intro animation reveals a real background instead of pure ink.
// Fades from 0 → 0.45 over the first 0.8s, then holds until beat 0 starts
// (where the full-opacity BeatStill takes over).
function HeroAsset({ path, holdFrames }: { path: string; holdFrames: number }) {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, 24], [0, 0.45], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  // Gentle zoom from 1.04 → 1.0 so the asset feels alive without distracting
  const scale = interpolate(frame, [0, holdFrames], [1.04, 1.0], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });
  return (
    <AbsoluteFill style={{ opacity: fadeIn }}>
      <Img src={path} style={{
        width: "100%", height: "100%", objectFit: "cover",
        transform: `scale(${scale})`,
        transformOrigin: "center center",
        filter: "blur(2px) brightness(0.78)",
      }} />
      <AbsoluteFill style={{
        background: "linear-gradient(to bottom, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.55) 100%)",
        pointerEvents: "none",
      }} />
    </AbsoluteFill>
  );
}

// CTA — fade + slight upward rise.
function CTA({ text }: { text: string }) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const translateY = interpolate(frame, [0, 12], [24, 0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <p style={{
        color: palette.off_white,
        fontFamily: "Archivo Black",
        fontSize: 64,
        lineHeight: 1.1,
        textAlign: "center",
        padding: "0 60px",
        textTransform: "lowercase",
        margin: 0,
        textShadow: "0 6px 24px rgba(0,0,0,0.7)",
        opacity,
        transform: `translateY(${translateY}px)`,
      }}>
        <YearAccent text={text.replace(/\.$/, "")} />
        <span style={{ color: palette.accent }}>.</span>
      </p>
    </AbsoluteFill>
  );
}

// Persistent chrome — factjot wordmark top-left + topic kicker top-right.
// Both carry drop shadows so they read against any beat asset. Matches v1's
// frame chrome verbatim.
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
        letterSpacing: "0.18em",
        textTransform: "uppercase",
      }}>
        {kicker}
      </div>
    </AbsoluteFill>
  );
}

// Outro wordmark — letter-by-letter pop-in. Used over the last beat asset
// (which continues from the previous beat) so the outro feels like part of
// the reel, not a separate text card. The follow-fact-jot text rides the
// normal karaoke caption flow further down the frame.
function OutroWordmark() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const letters = ["f", "a", "c", "t", "j", "o", "t"]; // matches brand_kit
  const italicFrom = 4; // "jot" is italic — index 4..6
  // Each letter pops in 3 frames apart, with a tiny spring scale.
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

// V1 film-grain overlay — the same .mov V1 uses, screen-blended at ~65%
// opacity. Loops (the video is ~58s, sufficient for any reel length).
// Replaces the SVG fractalNoise approach so we match V1's aesthetic byte-for-byte.
function GrainOverlay({ src }: { src?: string | null }) {
  if (!src) {
    return null;
  }
  return (
    <AbsoluteFill style={{
      pointerEvents: "none",
      mixBlendMode: "screen",
      opacity: 0.55,
    }}>
      <OffthreadVideo
        src={src}
        loop
        muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    </AbsoluteFill>
  );
}

// Subtle weave — sin-based ±1.5px translate so everything wiggles ever so slightly.
// Apply as a wrapper around the entire video tree.
function Weave({ children }: { children: React.ReactNode }) {
  const frame = useCurrentFrame();
  const x = Math.sin(frame * 0.045) * 1.5;
  const y = Math.cos(frame * 0.038) * 1.2;
  return (
    <AbsoluteFill style={{ transform: `translate(${x}px, ${y}px)` }}>
      {children}
    </AbsoluteFill>
  );
}


// ---------- Composition ----------

export const FactReel: React.FC<z.infer<typeof factReelSchema>> = ({
  hook, cta, narration_audio, music_audio, grit_overlay, beats, intro_overlay,
  hook_window, cta_window, outro_window, outro_text,
  narration_offset_frames, kicker, alignment,
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
      {narration_audio && (
        <Sequence from={narrationDelay}>
          <Audio src={narration_audio} />
        </Sequence>
      )}

      {/* Background music — V1 settings: 20% volume, 1s fade-in, looped. */}
      {music_audio && (
        <Audio src={music_audio} volume={0.20} loop />
      )}

      {/* Subtle weave wraps every visual layer so the whole frame wiggles slightly. */}
      <Weave>

      {/* Hero asset — first beat's image at low opacity from frame 0, so the
          intro animation reveals a real background, not pure ink. Continues
          until beat 0's full-opacity BeatStill takes over. */}
      {beats[0]?.asset?.path && (
        <Sequence from={0} durationInFrames={Math.max(beats[0].start_frame, 1)}>
          <HeroAsset path={beats[0].asset.path} holdFrames={beats[0].start_frame} />
        </Sequence>
      )}

      {/* Hook — silent title hold, then narration kicks in during the same window */}
      <Sequence from={0} durationInFrames={Math.max(hookEnd, 1)}>
        <Hook text={hook} />
      </Sequence>

      {/* Beat assets — Ken Burns + cross-dissolve. The LAST beat extends through
          the CTA + outro window so we never cut to black; the outro lives on
          top of that continuing asset. */}
      {beats.map((beat, i) => {
        const path = beat.asset.path;
        if (!path) return null;
        const isLast = i === beats.length - 1;
        // Last beat holds through cta + outro so the outro wordmark plays over
        // real content, not pure ink.
        const naturalDuration = Math.max(beat.end_frame - beat.start_frame, fps);
        const extendedEnd = isLast ? Math.max(outroEnd, beat.end_frame) : beat.end_frame;
        const duration = Math.max(extendedEnd - beat.start_frame, naturalDuration);
        const isVideo = path.endsWith(".mp4") || path.endsWith(".webm") || path.endsWith(".mov");
        return (
          <Sequence key={`asset-${i}`} from={beat.start_frame} durationInFrames={duration}>
            {isVideo
              ? <BeatVideo path={path} />
              : <BeatStill path={path} durationFrames={duration} />}
          </Sequence>
        );
      })}

      {/* Caption chunks — v1 style: lowercase, 72px, no pill, no stroke,
          positioned ~52% from top. Per-word highlight pulls the spoken word
          to the brand accent so subtitles read as karaoke-style. */}
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

      {/* CTA + Outro captions — same karaoke treatment as the beat chunks.
          The standalone "outro text card" is gone; instead the spoken outro
          flows as captions while the OutroWordmark letter-animates above. */}
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

      {/* Letter-animated factjot wordmark over the outro — sits above the
          continuing last-beat asset so the reel never goes to black. */}
      <Sequence from={outroStart} durationInFrames={Math.max(outroEnd - outroStart, 1)}>
        <AbsoluteFill style={{
          display: "flex", alignItems: "center", justifyContent: "center",
          paddingBottom: 320,
          backgroundColor: "rgba(0,0,0,0.45)",
        }}>
          <OutroWordmark />
        </AbsoluteFill>
      </Sequence>

      {/* Persistent factjot wordmark + topic kicker — appears after the intro
          overlay completes. Hidden during the outro (which has its own big
          wordmark centred). */}
      <Sequence from={INTRO_FRAMES} durationInFrames={Math.max(outroStart - INTRO_FRAMES, 1)}>
        <ChromeOverlay kicker={kicker} />
      </Sequence>

      </Weave>

      {/* V1 film-grain overlay — screen-blended on top. Sits OUTSIDE the weave
          wrapper so it stays pinned to the frame, not shifted with the asset. */}
      <GrainOverlay src={grit_overlay} />

      {/* Brand intro overlay — alpha-channel video on top for the first 1.37s.
          ProRes 4444 yuva444p12le source carries a real alpha channel; Remotion
          needs `transparent` to honour it instead of compositing against black.
          Sits OUTSIDE the weave so it's perfectly aligned with the frame edge. */}
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
