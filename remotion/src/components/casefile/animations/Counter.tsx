import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing, spring } from "remotion";

// Counter — big bold number ticking from `from` to `to` over ~2 seconds.
// Positioned in the upper-centre of the frame (~38% from top) so the bottom
// third stays clear for TikTok-style captions, and the scene asset below
// reads through the gaps. A vignette-style radial dim around the number's
// area sells the focus without blanketing the whole frame.
//
// Designed to coexist with captions, not replace them — the number tells
// the story visually, the caption confirms it verbally.

interface CounterProps {
  from: number;
  to: number;
  unit?: string | null;
  /** Frames the count takes to land at `to`. Default 60 = 2.0s at 30fps. */
  durationFrames?: number;
  /** Frames before the counter starts (lets the asset breathe first). */
  delayFrames?: number;
}

function formatNumber(n: number): string {
  return Math.round(n).toLocaleString("en-GB");
}

export function Counter({
  from,
  to,
  unit,
  durationFrames = 60,
  delayFrames = 6,
}: CounterProps) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const local = Math.max(0, frame - delayFrames);
  const progress = interpolate(local, [0, durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const value = from + (to - from) * progress;
  const landed = progress >= 1;

  const pulseStart = delayFrames + durationFrames;
  const pulse = spring({
    frame: Math.max(0, frame - pulseStart),
    fps,
    config: { damping: 7, stiffness: 200, mass: 0.8 },
    durationInFrames: 18,
  });
  const pulseScale = landed
    ? interpolate(pulse, [0, 0.4, 1], [1.0, 1.08, 1.0], { extrapolateRight: "clamp" })
    : 1.0;

  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      {/* Local radial vignette behind the number — darkens just the upper
          centre so the digits read, leaves the bottom (captions) and edges
          (asset) untouched. */}
      <AbsoluteFill style={{
        background:
          "radial-gradient(38% 28% at 50% 38%, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 70%)",
      }} />

      <div style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        // Anchor at ~38% from top so the number sits in the upper-centre
        // and the lower 30%+ of the frame stays clear for captions.
        height: `${0.55 * 1920}px`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-end",
      }}>
        <div style={{
          color: "#FFFFFF",
          fontFamily: "Archivo Black",
          fontSize: 200,
          lineHeight: 0.95,
          letterSpacing: "-0.02em",
          textShadow: "6px 6px 0 rgba(0,0,0,0.9), 0 4px 20px rgba(0,0,0,0.6)",
          transform: `scale(${pulseScale})`,
          fontVariantNumeric: "tabular-nums",
        }}>
          {formatNumber(value)}
        </div>
        {unit && (
          <div style={{
            marginTop: 16,
            color: "rgba(255,255,255,0.92)",
            fontFamily: "Space Grotesk",
            fontWeight: 700,
            fontSize: 40,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            textShadow: "3px 3px 0 rgba(0,0,0,0.85)",
          }}>
            {unit}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
}
