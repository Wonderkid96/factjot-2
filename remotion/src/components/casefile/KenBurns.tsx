import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, useCurrentFrame, interpolate, Easing } from "remotion";

// KenBurns: the v1 full-bleed Ken Burns treatment, extracted for use as a
// case-file fallback. The only case-file scene that covers the desk —
// reserved for assets striking enough to warrant the full frame.

interface KenBurnsProps {
  src: string;
  isVideo?: boolean;
  durationFrames: number;
}

export function KenBurns({ src, isVideo = false, durationFrames }: KenBurnsProps) {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, durationFrames], [1.0, 1.08], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ opacity }}>
      {isVideo ? (
        <OffthreadVideo src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <Img
          src={src}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale})`,
            transformOrigin: "center center",
          }}
        />
      )}
      {/* Top + bottom gradient for chrome legibility */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 35%, rgba(0,0,0,0.55) 90%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
}
