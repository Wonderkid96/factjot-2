import React from "react";
import { z } from "zod";
import { AbsoluteFill, Img } from "remotion";
import { palette, fonts } from "../style/tokens";
import { Wordmark } from "../components/Wordmark";
import { YearAccent } from "../components/YearAccent";

export const reelStorySchema = z.object({
  title: z.string(),
  topic: z.string(),
  frame_path: z.string().nullable(),
  kicker: z.string().nullable(),
  title_size: z.number().default(132),
});

export const ReelStory: React.FC<z.infer<typeof reelStorySchema>> = ({
  title, topic, frame_path, kicker, title_size,
}) => (
  <AbsoluteFill style={{ backgroundColor: palette.ink }}>
    {frame_path && (
      <Img src={frame_path} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.5 }} />
    )}

    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "0 80px" }}>
      <div>
        <div style={{
          fontFamily: fonts.label, fontSize: 22, fontWeight: 700,
          color: palette.accent, letterSpacing: "0.14em", textTransform: "uppercase",
          textAlign: "center", marginBottom: 32,
        }}>{kicker || "NEW REEL"}</div>

        <h1 style={{
          fontFamily: fonts.caption, fontSize: title_size,
          color: palette.off_white, lineHeight: 0.95,
          letterSpacing: "-0.01em", margin: 0,
          textTransform: "lowercase", textAlign: "center",
        }}>
          <YearAccent text={title.replace(/\.$/, "")} />
          <span style={{ color: palette.accent }}>.</span>
        </h1>
      </div>
    </AbsoluteFill>

    <div style={{
      position: "absolute", bottom: 80, left: 0, right: 0,
      display: "flex", justifyContent: "center",
    }}>
      <Wordmark size={40} />
    </div>
  </AbsoluteFill>
);
