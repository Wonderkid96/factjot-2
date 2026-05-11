import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing, spring } from "remotion";

// Counter — big bold number ticking from `from` to `to` over ~2 seconds with
// an ease-out curve so it slows as it lands. Reaches the target value, then
// pulses once (a quick 1.0 → 1.08 → 1.0 scale) so the eye registers the
// arrival. Optional `unit` text appears underneath in smaller weight.
//
// Layout: sits on top of whatever the base scene renders (asset or black).
// The asset behind is dimmed via a translucent black overlay so the number
// has the eye. Designed to be the dominant element while it's playing.

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
  // Round to int when the tick is mid-stream (avoid 1234.5678 garbage).
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

  // Tick value: 0 → 1 progress through the duration, applied to (from..to).
  const local = Math.max(0, frame - delayFrames);
  const progress = interpolate(local, [0, durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    // ease-out cubic — fast then slow, classic counter feel
    easing: Easing.out(Easing.cubic),
  });
  const value = from + (to - from) * progress;
  const landed = progress >= 1;

  // Landing pulse — runs once when the count reaches its target.
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

  // Entry fade for the whole counter block.
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      pointerEvents: "none",
      opacity,
    }}>
      {/* Backdrop dim so the number reads on busy footage */}
      <AbsoluteFill style={{ backgroundColor: "rgba(0,0,0,0.55)" }} />

      <div style={{
        position: "relative",
        color: "#FFFFFF",
        fontFamily: "Archivo Black",
        fontSize: 220,
        lineHeight: 0.95,
        letterSpacing: "-0.02em",
        textShadow: "6px 6px 0 rgba(0,0,0,0.9)",
        transform: `scale(${pulseScale})`,
        // Tabular numerals keep digit widths constant so the number doesn't
        // jitter as it counts up.
        fontVariantNumeric: "tabular-nums",
      }}>
        {formatNumber(value)}
      </div>
      {unit && (
        <div style={{
          position: "relative",
          marginTop: 24,
          color: "rgba(255,255,255,0.92)",
          fontFamily: "Space Grotesk",
          fontWeight: 700,
          fontSize: 48,
          letterSpacing: "0.16em",
          textTransform: "uppercase",
          textShadow: "3px 3px 0 rgba(0,0,0,0.85)",
        }}>
          {unit}
        </div>
      )}
    </AbsoluteFill>
  );
}
