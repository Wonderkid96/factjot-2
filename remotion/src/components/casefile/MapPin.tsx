import React from "react";
import { LowerThird } from "./LowerThird";

// "Map pin" — was a paper panel with a literal red push-pin. Now: full-bleed
// asset with a Netflix-doc-style lower-third label naming the location.

interface MapPinProps {
  src: string;
  isVideo?: boolean;
  /** Location name to surface in the lower-third. */
  locationLabel?: string;
  durationFrames?: number;
}

export function MapPin({ src, isVideo = false, locationLabel, durationFrames }: MapPinProps) {
  return (
    <LowerThird
      src={src}
      isVideo={isVideo}
      eyebrow="Location"
      label={locationLabel ?? "Unknown"}
      durationFrames={durationFrames}
    />
  );
}
