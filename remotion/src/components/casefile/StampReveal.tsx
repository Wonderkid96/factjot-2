import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";
import { CinematicFrame } from "./CinematicFrame";

// "Stamp reveal" — was a rubber-stamp slammed over the asset. Netflix-doc
// rebuild: the asset rides full-bleed in colour, then a bold text card
// slides up from the bottom and holds (year, verdict, key number). No rubber
// stamp, no rotation overshoot — just a clean lower-third hero text plate.

interface StampRevealProps {
  src: string;
  isVideo?: boolean;
  text: string;
  /** Delay before the text plate enters, in frames. */
  delay?: number;
  /** Frames after `delay` to hold the text plate fully visible. After this
      it fades out, so when the beat is extended through the outro the plate
      doesn't clash with the factjot wordmark. */
  holdFrames?: number;
}

export function StampReveal({ src, isVideo = false, text, delay = 18, holdFrames = 90 }: StampRevealProps) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entry = spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: { damping: 16, stiffness: 110, mass: 1.0 },
  });
  const ty = interpolate(entry, [0, 1], [80, 0]);
  const entryOpacity = interpolate(entry, [0, 0.6], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  // Fade out after the hold so the plate clears for the outro wordmark.
  const fadeStart = delay + holdFrames;
  const exitOpacity = interpolate(frame, [fadeStart, fadeStart + 18], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.cubic),
  });
  const opacity = Math.min(entryOpacity, exitOpacity);

  return (
    <CinematicFrame
      src={src}
      isVideo={isVideo}
      grade="color"
      overlay={
        <AbsoluteFill style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          paddingBottom: 540,
          pointerEvents: "none",
        }}>
          <div style={{
            transform: `translateY(${ty}px)`,
            opacity,
            color: "#FFFFFF",
            fontFamily: "Archivo Black",
            fontSize: 156,
            lineHeight: 1.0,
            letterSpacing: "-0.02em",
            textShadow: "0 8px 32px rgba(0,0,0,0.85)",
            textAlign: "center",
          }}>
            {text.toUpperCase()}
          </div>
        </AbsoluteFill>
      }
    />
  );
}
