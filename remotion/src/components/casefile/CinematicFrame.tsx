import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, useCurrentFrame, interpolate, Easing } from "remotion";

// The Netflix-doc workhorse: takes an asset and frames it full-bleed with
// optional grade, slow Ken Burns, vignette, and top/bottom dim so chrome +
// captions stay legible. Every "image/video" scene treatment routes through
// this — variation comes from the `grade` and overlay props.

export type CinematicGrade =
  | "color"          // modern colour footage, no filter
  | "bw"             // pure black-and-white
  | "bw_grain"       // black-and-white + heavier grain (archival film feel)
  | "sepia"          // warm-tinted desaturate (very old archival)
  | "halftone";      // B&W with halftone dot overlay (newspaper / print)

interface CinematicFrameProps {
  src: string;
  isVideo?: boolean;
  grade?: CinematicGrade;
  /** Optional overlay rendered on top of the asset (text labels, stamps). */
  overlay?: React.ReactNode;
  /** Skip the slow Ken Burns scale-in if the asset is already in motion. */
  staticFraming?: boolean;
}

function gradeFilter(grade: CinematicGrade): string | undefined {
  switch (grade) {
    case "bw":         return "grayscale(1) contrast(1.05)";
    case "bw_grain":   return "grayscale(1) contrast(1.12) brightness(0.92)";
    case "sepia":      return "sepia(0.55) saturate(0.9) contrast(1.05) brightness(0.96)";
    case "halftone":   return "grayscale(1) contrast(1.35) brightness(0.92)";
    case "color":      return undefined;
  }
}

export function CinematicFrame({
  src,
  isVideo = false,
  grade = "color",
  overlay,
  staticFraming = false,
}: CinematicFrameProps) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 22], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const scale = staticFraming
    ? 1.0
    : interpolate(frame, [0, 240], [1.0, 1.06], {
        extrapolateRight: "clamp",
        easing: Easing.linear,
      });
  const filter = gradeFilter(grade);

  const assetStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    transform: `scale(${scale})`,
    transformOrigin: "center center",
    ...(filter ? { filter } : {}),
  };

  return (
    <AbsoluteFill style={{ opacity, backgroundColor: "#000000" }}>
      {isVideo ? (
        <OffthreadVideo src={src} style={assetStyle} />
      ) : (
        <Img src={src} style={assetStyle} />
      )}

      {/* Halftone-specific dot overlay for the "newsprint" treatment */}
      {grade === "halftone" && (
        <AbsoluteFill style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(0,0,0,0.55) 1px, transparent 1.3px)",
          backgroundSize: "4px 4px",
          mixBlendMode: "multiply",
          opacity: 0.5,
          pointerEvents: "none",
        }} />
      )}

      {/* Cinematic vignette — edges fall off so the centre carries weight */}
      <AbsoluteFill style={{
        background:
          "radial-gradient(120% 90% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.6) 100%)",
        pointerEvents: "none",
      }} />

      {/* Top + bottom dim for chrome + caption legibility. Heavier at the
          bottom because captions live there; gentler at top so the wordmark
          doesn't sit on a sharp gradient line. */}
      <AbsoluteFill style={{
        background:
          "linear-gradient(to bottom, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 20%, rgba(0,0,0,0) 58%, rgba(0,0,0,0.7) 100%)",
        pointerEvents: "none",
      }} />

      {overlay}
    </AbsoluteFill>
  );
}
