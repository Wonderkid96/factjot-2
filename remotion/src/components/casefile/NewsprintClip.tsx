import React from "react";
import { CinematicFrame } from "./CinematicFrame";

// "Newsprint" — was halftone-filtered image inside a yellowed paper frame.
// Now: full-bleed B&W with a halftone dot overlay. Reads as press archival
// without the literal newspaper border.

interface NewsprintClipProps {
  src: string;
  isVideo?: boolean;
  /** Unused now — kept so SceneRenderer call sites don't have to change. */
  headline?: string;
  durationFrames?: number;
  beatIndex?: number;
}

export function NewsprintClip({ src, isVideo = false, durationFrames, beatIndex }: NewsprintClipProps) {
  return <CinematicFrame src={src} isVideo={isVideo} grade="halftone" durationFrames={durationFrames} beatIndex={beatIndex} />;
}
