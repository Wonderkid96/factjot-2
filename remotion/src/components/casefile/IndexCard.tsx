import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";
import { useSettleSpring, useImpactBounce, useHandJitter, STIFF_SHADOW } from "./primitives";

// IndexCard: typed monospaced fact on a manila card. The card slides in from
// below with a settle bounce. Card has ruled horizontal lines and a red
// margin line on the left, like a real recipe / library index card. Use when
// the beat IS the fact and an accompanying asset would be redundant.

interface IndexCardProps {
  text: string;
  /** Frames to take typing. */
  typeDurationFrames?: number;
}

export function IndexCard({ text, typeDurationFrames = 30 }: IndexCardProps) {
  const frame = useCurrentFrame();
  const settle = useSettleSpring(0);
  const bounce = useImpactBounce(0);
  const jitter = useHandJitter(0.5, 0.025);

  const startX = -120;
  const startY = 1400;
  const startRot = 6;
  const x = (1 - settle) * startX + jitter.x;
  const y = (1 - settle) * startY + jitter.y;
  const rot = (1 - settle) * startRot - 2.5 + jitter.r;

  const typeProgress = interpolate(frame, [4, 4 + typeDurationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });
  const chars = Math.floor(typeProgress * text.length);
  const visible = text.slice(0, chars);

  // Blinking cursor — visible 30 frames in, blinks until typing finishes
  const showCursor = chars > 0 && chars < text.length;
  const cursorAlpha = Math.floor(frame / 8) % 2 === 0 ? 1 : 0;

  const CARD_W = 940;
  const CARD_H = 560;

  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          position: "relative",
          width: CARD_W,
          height: CARD_H,
          backgroundColor: "#f0d99a",
          boxShadow: STIFF_SHADOW,
          transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scaleY(${bounce})`,
          overflow: "hidden",
          // Ruled horizontal lines + red margin line
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent 0px, transparent 67px, rgba(60, 90, 120, 0.32) 67px, rgba(60, 90, 120, 0.32) 68px), linear-gradient(90deg, transparent 0px, transparent 84px, rgba(180, 28, 24, 0.55) 84px, rgba(180, 28, 24, 0.55) 86px, transparent 86px)",
          backgroundPosition: "0 70px, 0 0",
          padding: "80px 60px 60px 110px",
        }}
      >
        <p
          style={{
            color: "#2a1c10",
            fontFamily: "IBM Plex Mono, Courier New, monospace",
            fontSize: 52,
            lineHeight: "68px",
            margin: 0,
            letterSpacing: "-0.005em",
          }}
        >
          {visible}
          {showCursor && (
            <span
              style={{
                display: "inline-block",
                width: "0.55em",
                height: "1em",
                marginLeft: 2,
                verticalAlign: "text-top",
                background: "#2a1c10",
                opacity: cursorAlpha,
              }}
            />
          )}
        </p>
      </div>
    </AbsoluteFill>
  );
}
