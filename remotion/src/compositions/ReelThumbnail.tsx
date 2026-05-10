import React from "react";
import { z } from "zod";
import { AbsoluteFill, Img } from "remotion";
import { palette, fonts, dimensions } from "../style/tokens";
import { Wordmark } from "../components/Wordmark";
import { YearAccent } from "../components/YearAccent";

export const reelThumbnailSchema = z.object({
  title: z.string(),
  topic: z.string(),
  frame_path: z.string().nullable(),
  kicker: z.string().nullable(),
  fact_number: z.string().nullable(),
  title_size: z.number().default(132),
});

export const ReelThumbnail: React.FC<z.infer<typeof reelThumbnailSchema>> = ({
  title, topic, frame_path, kicker, fact_number, title_size,
}) => (
  <AbsoluteFill style={{ backgroundColor: palette.ink }}>
    {frame_path && (
      <Img src={frame_path} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.6 }} />
    )}

    <div style={{ position: "absolute", top: 56, left: 72 }}>
      <Wordmark size={48} />
    </div>

    {kicker && (
      <div style={{
        position: "absolute", top: 56, right: 72,
        fontFamily: fonts.label, fontSize: 22, fontWeight: 700,
        color: palette.accent, letterSpacing: "0.14em", textTransform: "uppercase",
      }}>{kicker}</div>
    )}

    <div style={{
      position: "absolute",
      left: 72, right: 72,
      top: dimensions.reelH * 0.45,
      transform: "translateY(-50%)",
    }}>
      <h1 style={{
        fontFamily: fonts.caption, fontSize: title_size,
        color: palette.off_white, lineHeight: 0.95,
        letterSpacing: "-0.01em", margin: 0,
        textTransform: "lowercase",
      }}>
        <YearAccent text={title.replace(/\.$/, "")} />
        <span style={{ color: palette.accent }}>.</span>
      </h1>
    </div>

    <div style={{
      position: "absolute", bottom: 80, left: 72,
      fontFamily: fonts.label, fontSize: 22, fontWeight: 700,
      color: palette.paper, letterSpacing: "0.14em", textTransform: "uppercase",
      padding: "8px 16px", border: `1px solid ${palette.paper}`,
    }}>{topic}</div>

    {fact_number && (
      <div style={{
        position: "absolute", bottom: 80, right: 72,
        fontFamily: fonts.label, fontSize: 22, fontWeight: 700,
        color: palette.muted, letterSpacing: "0.14em",
      }}>[ No {fact_number} ]</div>
    )}
  </AbsoluteFill>
);
