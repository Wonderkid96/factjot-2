import React from "react";
import { CinematicFrame } from "./CinematicFrame";

// "Evidence slide" — was paper-bordered document. Now: full-bleed asset
// graded warm-sepia so it reads as "archival document" without the literal
// paper frame.

interface EvidenceSlideProps {
  src: string;
  isVideo?: boolean;
}

export function EvidenceSlide({ src, isVideo = false }: EvidenceSlideProps) {
  return <CinematicFrame src={src} isVideo={isVideo} grade="sepia" />;
}
