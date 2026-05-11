import React from "react";
import { CinematicFrame } from "./CinematicFrame";

// "Polaroid" treatment is now Netflix-style: full-bleed colour footage with
// slow Ken Burns, vignette, and edge dim. Name kept for SceneRenderer
// dispatch back-compat.

interface PolaroidProps {
  src: string;
  isVideo?: boolean;
}

export function Polaroid({ src, isVideo = false }: PolaroidProps) {
  return <CinematicFrame src={src} isVideo={isVideo} grade="color" />;
}
