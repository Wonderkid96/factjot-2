import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

// Netflix-doc base — pure black backdrop with an optional fade-in. The
// previous warm-leather desk was distracting against full-bleed footage;
// black puts the asset front and centre. Kept the component name + signature
// so CaseFileReel doesn't need to know about the swap.

interface DeskProps {
  fadeIn?: boolean;
}

export function Desk({ fadeIn = false }: DeskProps) {
  const frame = useCurrentFrame();
  const opacity = fadeIn
    ? interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" })
    : 1;
  return (
    <AbsoluteFill style={{
      pointerEvents: "none",
      opacity,
      backgroundColor: "#000000",
    }} />
  );
}
