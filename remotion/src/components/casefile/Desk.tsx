import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

// The desk is the persistent surface every case-file beat sits on. It carries
// three layers, painted in CSS so we don't pay an asset cost:
//   1. Base leather + paper grain (deep coffee tone with a warm centre)
//   2. Two soft pinpoint highlights, mimicking a lamp glow off-frame
//   3. Inner vignette so the corners darken and the eye lands on the centre
//
// The base palette intentionally avoids pure black so foreground paper still
// reads against it. Paper whites (#fffaf0) feel detective-noir against this
// rather than the surgical-white-on-black of v1's FactReel.

interface DeskProps {
  /** When true the desk fades in over the first ~0.4s instead of being instant. */
  fadeIn?: boolean;
}

export function Desk({ fadeIn = false }: DeskProps) {
  const frame = useCurrentFrame();
  const opacity = fadeIn
    ? interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" })
    : 1;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      {/* Base leather + paper grain — radial coffee tone */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(120% 80% at 50% 45%, #3a2a1c 0%, #28190f 55%, #150b06 100%)",
        }}
      />
      {/* Warm lamp glow, top-left */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(28% 22% at 22% 18%, rgba(255, 196, 120, 0.18) 0%, rgba(255, 196, 120, 0) 70%)",
          mixBlendMode: "screen",
        }}
      />
      {/* Cooler highlight, bottom-right — fakes a second light source */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(30% 22% at 82% 84%, rgba(110, 140, 180, 0.10) 0%, rgba(0, 0, 0, 0) 70%)",
          mixBlendMode: "screen",
        }}
      />
      {/* Wood-grain noise via repeated linear gradient — very subtle */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(92deg, rgba(255,255,255,0.012) 0px, rgba(255,255,255,0.012) 2px, rgba(0,0,0,0) 2px, rgba(0,0,0,0) 6px)",
          mixBlendMode: "overlay",
        }}
      />
      {/* Corner vignette to keep the eye centred */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(80% 60% at 50% 50%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.45) 100%)",
        }}
      />
    </AbsoluteFill>
  );
}
