import React from "react";
import { z } from "zod";
import { AbsoluteFill, Sequence, useVideoConfig, Audio, Img, OffthreadVideo } from "remotion";

const windowSchema = z.object({ start_frame: z.number(), end_frame: z.number() });

export const factReelSchema = z.object({
  composition: z.string(),
  title: z.string(),
  hook: z.string(),
  cta: z.string(),
  narration_audio: z.string().nullable(),
  intro_overlay: z.string().nullable().optional(),
  alignment: z.array(z.any()),
  // ALL frame values below are ABSOLUTE — relative to start of narration audio.
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

const INTRO_DURATION_S = 1.37;  // matches v1's factjot_intro.mov ProRes

export const FactReel: React.FC<z.infer<typeof factReelSchema>> = ({
  hook, cta, narration_audio, beats, intro_overlay,
  hook_window, cta_window, narration_offset_frames,
}) => {
  const { fps } = useVideoConfig();

  // Hook plays from frame 0 to whenever the narration's hook words end.
  // Fall back to a 1.5s window if the spec didn't supply one.
  const hookEnd = hook_window?.end_frame ?? Math.floor(fps * 1.5);
  // CTA plays at its narration window; fall back to "just after last beat".
  const ctaStart = cta_window?.start_frame ?? (beats.length ? beats[beats.length - 1].end_frame : hookEnd);
  const ctaEnd = cta_window?.end_frame ?? (ctaStart + Math.floor(fps * 1.8));
  const INTRO_FRAMES = Math.floor(fps * INTRO_DURATION_S);
  // Audio is delayed by the title-hold so the hook gets a silent beat first.
  const narrationDelay = narration_offset_frames ?? 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#0A0A0A" }}>
      {narration_audio && (
        <Sequence from={narrationDelay}>
          <Audio src={narration_audio} />
        </Sequence>
      )}

      {/* Hook — plays for the duration of the hook's narration window. */}
      <Sequence from={0} durationInFrames={Math.max(hookEnd, 1)}>
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <h1 style={{
            color: "#F4F1E9",
            fontFamily: "Archivo Black",
            fontSize: 96,
            lineHeight: 1.05,
            textAlign: "center",
            padding: "0 60px",
            textTransform: "uppercase",
            letterSpacing: "-0.01em",
            margin: 0,
          }}>{hook}</h1>
        </AbsoluteFill>
      </Sequence>

      {/* Beat assets — one Sequence per beat at its ABSOLUTE narration window. */}
      {beats.map((beat, i) => {
        const duration = Math.max(beat.end_frame - beat.start_frame, fps);
        return (
          <Sequence key={`asset-${i}`} from={beat.start_frame} durationInFrames={duration}>
            <AbsoluteFill>
              {beat.asset.path?.endsWith(".mp4") ? (
                <OffthreadVideo src={beat.asset.path} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : beat.asset.path ? (
                <Img src={beat.asset.path} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : null}
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* Caption chunks — each at its own ABSOLUTE alignment window. No offset math. */}
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
                // Lower-middle, not lower-third — keeps captions out of the
                // IG UI chrome zone (Like/Comment buttons hug the bottom-right).
                justifyContent: "center",
                paddingTop: 720,    // 720/1920 = 37.5% from top — comfortably lower-middle
                paddingLeft: 60,
                paddingRight: 60,
                pointerEvents: "none",
              }}>
                <p style={{
                  color: "#F4F1E9",
                  background: "rgba(0,0,0,0.72)",
                  padding: "24px 36px",
                  fontFamily: "Space Grotesk",
                  fontWeight: 700,
                  fontSize: 88,
                  lineHeight: 1.15,
                  letterSpacing: "-0.01em",
                  borderRadius: 18,
                  margin: 0,
                  textAlign: "center",
                  textTransform: "uppercase",
                  alignSelf: "center",
                  maxWidth: "100%",
                }}>{chunk.text}</p>
              </AbsoluteFill>
            </Sequence>
          );
        })
      )}

      {/* CTA — plays at its ABSOLUTE narration window. */}
      <Sequence from={ctaStart} durationInFrames={Math.max(ctaEnd - ctaStart, 1)}>
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <p style={{
            color: "#F4F1E9",
            fontFamily: "Archivo Black",
            fontSize: 72,
            lineHeight: 1.1,
            textAlign: "center",
            padding: "0 60px",
            textTransform: "uppercase",
            margin: 0,
          }}>{cta}</p>
        </AbsoluteFill>
      </Sequence>

      {/* Brand intro overlay — ProRes 4444 with alpha. Plays on top of everything
          for the first ~1.37s. v1 used the exact same .mov; carried over verbatim. */}
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
