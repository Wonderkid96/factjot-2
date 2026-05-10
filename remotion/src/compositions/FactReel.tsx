import React from "react";
import { z } from "zod";
import { AbsoluteFill, Sequence, useVideoConfig, Audio, Img, OffthreadVideo } from "remotion";

export const factReelSchema = z.object({
  composition: z.string(),
  title: z.string(),
  hook: z.string(),
  cta: z.string(),
  narration_audio: z.string().nullable(),
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

export const FactReel: React.FC<z.infer<typeof factReelSchema>> = ({
  hook, cta, narration_audio, beats,
}) => {
  const { fps } = useVideoConfig();

  const HOOK_FRAMES = Math.floor(fps * 1.5);
  const lastBeatEnd = beats.length ? beats[beats.length - 1].end_frame : HOOK_FRAMES;
  const CTA_FRAMES = Math.floor(fps * 1.8);

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
              <AbsoluteFill style={{ display: "flex", alignItems: "flex-end", padding: 40 }}>
                <p style={{
                  color: "#F4F1E9", background: "rgba(0,0,0,0.6)", padding: 20,
                  fontFamily: "Space Grotesk", fontSize: 36, lineHeight: 1.2,
                  borderRadius: 12, maxWidth: "100%",
                }}>{beat.text}</p>
              </AbsoluteFill>
            </AbsoluteFill>
          </Sequence>
        );
      })}

      <Sequence from={HOOK_FRAMES + lastBeatEnd} durationInFrames={CTA_FRAMES}>
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <p style={{
            color: "#F4F1E9", fontFamily: "Instrument Serif", fontSize: 56, fontStyle: "italic",
            textAlign: "center", padding: "0 60px",
          }}>{cta}</p>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
