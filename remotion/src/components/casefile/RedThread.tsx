import React from "react";
import { CinematicFrame } from "./CinematicFrame";

// "Red thread" — was a conspiracy-board with two pinned photos connected by
// string. Netflix-doc rebuild: the literal corkboard metaphor is gone (too
// kitsch for the new aesthetic). Falls back to a clean cinematic full-bleed
// of the current beat's asset; the "connection" reads through the spoken
// narration rather than a visual string.

interface RedThreadProps {
  src: string;
  isVideo?: boolean;
  /** Unused now — kept so SceneRenderer call sites don't have to change. */
  priorSrc?: string | null;
  priorIsVideo?: boolean;
}

export function RedThread({ src, isVideo = false }: RedThreadProps) {
  return <CinematicFrame src={src} isVideo={isVideo} grade="color" />;
}
