import React from "react";
import { CinematicFrame } from "./CinematicFrame";

// "Archive film" — was sprocket-hole film-strip border. Now: full-bleed
// B&W with heavier grain (handled by the screen-blended grit.mov overlay
// applied at composition level). Reads as archival without the literal
// film-strip mat.

interface ArchiveFilmProps {
  src: string;
  isVideo?: boolean;
  durationFrames?: number;
  beatIndex?: number;
}

export function ArchiveFilm({ src, isVideo = false, durationFrames, beatIndex }: ArchiveFilmProps) {
  return <CinematicFrame src={src} isVideo={isVideo} grade="bw_grain" durationFrames={durationFrames} beatIndex={beatIndex} />;
}
