import React from "react";
import { z } from "zod";
import { AbsoluteFill, Sequence, useVideoConfig, Audio, Img, OffthreadVideo } from "remotion";

export const factReelSchema = z.object({
  composition: z.string(),
  title: z.string(),
  hook: z.string(),
  cta: z.string(),
  narration_audio: z.string().nullable(),
  intro_overlay: z.string().nullable().optional(),
  alignment: z.array(z.any()),
  beats: z.array(z.object({
    text: z.string(),
    start_frame: z.number(),
    end_frame: z.number(),
    asset: z.object({
      path: z.string().nullable(),
      source: z.string().nullable(),
    }),
  })),
});

const INTRO_DURATION_S = 1.37;  // matches v1's factjot_intro.mov ProRes

export const FactReel: React.FC<z.infer<typeof factReelSchema>> = ({
  hook, cta, narration_audio, beats, intro_overlay,
}) => {
  const { fps } = useVideoConfig();

  const HOOK_FRAMES = Math.floor(fps * 1.5);
  const lastBeatEnd = beats.length ? beats[beats.length - 1].end_frame : HOOK_FRAMES;
  const CTA_FRAMES = Math.floor(fps * 1.8);
  const INTRO_FRAMES = Math.floor(fps * INTRO_DURATION_S);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0A0A0A" }}>
      {narration_audio && <Audio src={narration_audio} />}

      <Sequence from={0} durationInFrames={HOOK_FRAMES}>
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <h1 style={{
            color: "#F4F1E9",
            fontFamily: "Archivo Black",
            fontSize: 72,
            textAlign: "center",
            padding: "0 40px",
          }}>{hook}</h1>
        </AbsoluteFill>
      </Sequence>

      {beats.map((beat, i) => {
        const offsetStart = HOOK_FRAMES + beat.start_frame;
        const duration = Math.max(beat.end_frame - beat.start_frame, fps);
        return (
          <Sequence key={i} from={offsetStart} durationInFrames={duration}>
            <AbsoluteFill>
              {beat.asset.path?.endsWith(".mp4") ? (
                <OffthreadVideo src={beat.asset.path} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : beat.asset.path ? (
                <Img src={beat.asset.path} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : null}
              <AbsoluteFill style={{
                display: "flex",
                flexDirection: "column",
                justifyContent: "flex-end",
                padding: "0 60px 200px 60px",
              }}>
                <p style={{
                  color: "#F4F1E9",
                  background: "rgba(0,0,0,0.65)",
                  padding: "20px 28px",
                  fontFamily: "Space Grotesk",
                  fontWeight: 700,
                  fontSize: 44,
                  lineHeight: 1.25,
                  borderRadius: 14,
                  margin: 0,
                  textAlign: "center",
                }}>{beat.text}</p>
              </AbsoluteFill>
            </AbsoluteFill>
          </Sequence>
        );
      })}

      <Sequence from={HOOK_FRAMES + lastBeatEnd} durationInFrames={CTA_FRAMES}>
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <p style={{
            color: "#F4F1E9", fontFamily: "Archivo Black", fontSize: 56,
            textAlign: "center", padding: "0 60px",
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
