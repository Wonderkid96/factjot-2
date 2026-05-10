import React from "react";
import { z } from "zod";
import {
  AbsoluteFill, Sequence, useVideoConfig, useCurrentFrame,
  interpolate, spring, Easing, Audio, Img, OffthreadVideo,
} from "remotion";
import { Wordmark } from "../components/Wordmark";
import { YearAccent } from "../components/YearAccent";
import { palette } from "../style/tokens";


const windowSchema = z.object({ start_frame: z.number(), end_frame: z.number() });

export const factReelSchema = z.object({
  composition: z.string(),
  title: z.string(),
  hook: z.string(),
  cta: z.string(),
  narration_audio: z.string().nullable(),
  intro_overlay: z.string().nullable().optional(),
  alignment: z.array(z.any()),
  // ALL frame values are ABSOLUTE — relative to start of the video (frame 0).
  hook_window: windowSchema.optional(),
  cta_window: windowSchema.optional(),
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
function ChunkCaption({ text }: { text: string }) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 4], [0, 1], { extrapolateRight: "clamp" });
  const translateY = interpolate(frame, [0, 6], [12, 0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <p style={{
      color: "#FFFFFF",
      fontFamily: "Space Grotesk",
      fontWeight: 700,
      fontSize: 72,
      lineHeight: 1.15,
      letterSpacing: "-0.005em",
      margin: 0,
      textAlign: "center",
      textShadow: "0 4px 18px rgba(0,0,0,0.85), 0 0 8px rgba(0,0,0,0.6)",
      opacity,
      transform: `translateY(${translateY}px)`,
    }}>{text}</p>
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
      <AbsoluteFill style={{
        background: "linear-gradient(to bottom, rgba(0,0,0,0) 35%, rgba(0,0,0,0.55) 90%)",
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
      <AbsoluteFill style={{
        background: "linear-gradient(to bottom, rgba(0,0,0,0) 35%, rgba(0,0,0,0.55) 90%)",
        pointerEvents: "none",
      }} />
    </AbsoluteFill>
  );
}

// Hook title — spring scale + opacity on entry. Lives on a dark background
// during the 2.5s title hold before narration starts.
function Hook({ text }: { text: string }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entry = spring({ frame, fps, config: { damping: 14, stiffness: 110 } });
  const scale = interpolate(entry, [0, 1], [0.85, 1]);
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

// Persistent chrome — factjot wordmark top-left across the whole reel
// AFTER the intro overlay finishes. v1 uses this on every frame.
function ChromeOverlay() {
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", top: 56, left: 56 }}>
        <Wordmark size={36} />
      </div>
    </AbsoluteFill>
  );
}


// ---------- Composition ----------

export const FactReel: React.FC<z.infer<typeof factReelSchema>> = ({
  hook, cta, narration_audio, beats, intro_overlay,
  hook_window, cta_window, narration_offset_frames,
}) => {
  const { fps } = useVideoConfig();

  const hookEnd = hook_window?.end_frame ?? Math.floor(fps * 1.5);
  const ctaStart = cta_window?.start_frame ?? (beats.length ? beats[beats.length - 1].end_frame : hookEnd);
  const ctaEnd = cta_window?.end_frame ?? (ctaStart + Math.floor(fps * 1.8));
  const INTRO_FRAMES = Math.floor(fps * INTRO_DURATION_S);
  const narrationDelay = narration_offset_frames ?? 0;

  return (
    <AbsoluteFill style={{ backgroundColor: palette.ink }}>
      {narration_audio && (
        <Sequence from={narrationDelay}>
          <Audio src={narration_audio} />
        </Sequence>
      )}

      {/* Hook — silent title hold, then narration kicks in during the same window */}
      <Sequence from={0} durationInFrames={Math.max(hookEnd, 1)}>
        <Hook text={hook} />
      </Sequence>

      {/* Beat assets — Ken Burns + cross-dissolve. */}
      {beats.map((beat, i) => {
        const duration = Math.max(beat.end_frame - beat.start_frame, fps);
        const path = beat.asset.path;
        if (!path) return null;
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
          positioned ~52% from top. */}
      {beats.flatMap((beat, i) =>
        ((beat.chunks ?? []).length > 0 ? (beat.chunks ?? []) : [{
          text: beat.text,
          start_frame: beat.start_frame,
          end_frame: beat.end_frame,
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
      )}

      {/* CTA — fade + rise. */}
      <Sequence from={ctaStart} durationInFrames={Math.max(ctaEnd - ctaStart, 1)}>
        <CTA text={cta} />
      </Sequence>

      {/* Persistent factjot wordmark — appears after the intro overlay completes. */}
      <Sequence from={INTRO_FRAMES}>
        <ChromeOverlay />
      </Sequence>

      {/* Brand intro overlay — alpha-channel video on top for the first 1.37s. */}
      {intro_overlay && (
        <Sequence from={0} durationInFrames={INTRO_FRAMES}>
          <AbsoluteFill style={{ pointerEvents: "none" }}>
            <OffthreadVideo
              src={intro_overlay}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              muted
            />
          </AbsoluteFill>
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
