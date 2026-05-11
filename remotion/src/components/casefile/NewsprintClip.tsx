import React from "react";
import { AbsoluteFill, Img, OffthreadVideo } from "remotion";
import { Tape, useSettleSpring, useImpactBounce, PAPER_SHADOW } from "./primitives";

// NewsprintClip: a halftone-filtered asset cropped inside a yellowed
// newspaper frame, with a headline above and a column-rules pattern below.
// Use for historical events covered in press — crimes, disasters, scandals.

interface NewsprintClipProps {
  src: string;
  isVideo?: boolean;
  headline?: string;
  /** Width of the clipping. */
  width?: number;
  finalRotation?: number;
}

export function NewsprintClip({
  src,
  isVideo = false,
  headline = "Late Edition",
  width = 820,
  finalRotation = -2,
}: NewsprintClipProps) {
  const settle = useSettleSpring(0);
  const bounce = useImpactBounce(0);
  const x = (1 - settle) * 1200;
  const y = (1 - settle) * -180;
  const rot = (1 - settle) * 9 + finalRotation;

  const IMAGE_H = (width - 40) * 0.62; // wider than tall, news-photo aspect

  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          position: "relative",
          width,
          backgroundColor: "#f0e7c8",
          boxShadow: PAPER_SHADOW,
          transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scaleY(${bounce})`,
          padding: 20,
          // Slight foxing — brownish tint at edges
          backgroundImage:
            "radial-gradient(120% 120% at 50% 50%, rgba(255,255,255,0) 60%, rgba(120,90,40,0.18) 100%)",
        }}
      >
        {/* Masthead */}
        <div
          style={{
            borderTop: "4px double #2a1c10",
            borderBottom: "1.5px solid #2a1c10",
            color: "#2a1c10",
            fontFamily: "Instrument Serif, serif",
            fontSize: 56,
            textAlign: "center",
            padding: "6px 0 10px",
            letterSpacing: "0.04em",
          }}
        >
          {headline}
        </div>

        {/* Photo with halftone duotone */}
        <div style={{ position: "relative", width: width - 40, height: IMAGE_H, overflow: "hidden", marginTop: 14 }}>
          {isVideo ? (
            <OffthreadVideo
              src={src}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                filter: "grayscale(1) contrast(1.4) brightness(0.9)",
              }}
            />
          ) : (
            <Img
              src={src}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                filter: "grayscale(1) contrast(1.4) brightness(0.9)",
              }}
            />
          )}
          {/* Halftone dot pattern overlay */}
          <AbsoluteFill
            style={{
              backgroundImage:
                "radial-gradient(circle at 1px 1px, rgba(0,0,0,0.65) 1.2px, transparent 1.4px)",
              backgroundSize: "5px 5px",
              mixBlendMode: "multiply",
              opacity: 0.55,
              pointerEvents: "none",
            }}
          />
          {/* Sepia wash */}
          <AbsoluteFill style={{ background: "rgba(120, 80, 30, 0.18)", mixBlendMode: "multiply" }} />
        </div>

        {/* Caption + column rules */}
        <div
          style={{
            color: "#2a1c10",
            fontFamily: "Instrument Serif, serif",
            fontStyle: "italic",
            fontSize: 22,
            marginTop: 12,
            textAlign: "center",
            letterSpacing: "0.02em",
          }}
        >
          archival photo · public record
        </div>
        <div
          style={{
            marginTop: 18,
            height: 86,
            backgroundImage:
              "repeating-linear-gradient(0deg, #2a1c10 0px, #2a1c10 1.2px, transparent 1.2px, transparent 7px)",
            opacity: 0.4,
            columnCount: 3,
            columnGap: 18,
          }}
        />

        <Tape side="top-left" rotation={-18} width={110} />
        <Tape side="top-right" rotation={18} width={110} />
      </div>
    </AbsoluteFill>
  );
}
