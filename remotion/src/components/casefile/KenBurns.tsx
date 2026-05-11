import React from "react";
import { CinematicFrame } from "./CinematicFrame";

// Ken Burns — same as the new Polaroid (full-bleed colour with slow scale)
// but kept as a distinct dispatch target so SceneRenderer doesn't have to
// rewrite. Identical to Polaroid in behaviour now; both delegate.

interface KenBurnsProps {
  src: string;
  isVideo?: boolean;
  durationFrames?: number;
}

export function KenBurns({ src, isVideo = false, durationFrames }: KenBurnsProps) {
  return <CinematicFrame src={src} isVideo={isVideo} grade="color" durationFrames={durationFrames} />;
}
