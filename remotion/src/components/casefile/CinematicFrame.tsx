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
  /** Total frames this scene plays for. Enables a clean fade-out in the last
      ~15 frames, so the beat handoff cross-fades into the next scene instead
      of cutting. Falls back to 240 if not provided. */
  durationFrames?: number;
  /** Beat index 0..N. Used to alternate the Ken Burns variant so consecutive
      beats don't all zoom in the same way — beat 0 zooms in, beat 1 pans
      left, beat 2 zooms out, beat 3 pans right (and cycles). */
  beatIndex?: number;
}

type KenBurnsVariant =
  | "zoom_in"     // scale 1.0 → 1.10, no pan
  | "zoom_out"    // scale 1.10 → 1.0, no pan
  | "pan_left"    // scale 1.06, translateX -40 → 0
  | "pan_right"   // scale 1.06, translateX 40 → 0
  | "pan_up";     // scale 1.06, translateY 30 → 0

const KEN_BURNS_CYCLE: KenBurnsVariant[] = ["zoom_in", "pan_left", "zoom_out", "pan_right", "pan_up"];

function gradeFilter(grade: CinematicGrade): string | undefined {
  switch (grade) {
    case "bw":         return "grayscale(1) contrast(1.05)";
    case "bw_grain":   return "grayscale(1) contrast(1.12) brightness(0.92)";
    case "sepia":      return "sepia(0.55) saturate(0.9) contrast(1.05) brightness(0.96)";
    case "halftone":   return "grayscale(1) contrast(1.35) brightness(0.92)";
    case "color":      return undefined;
  }
}

const FADE_OUT_FRAMES = 15;

function kenBurnsMotion(variant: KenBurnsVariant, p: number): { scale: number; tx: number; ty: number } {
  // p is 0..1 progress through the scene window.
  switch (variant) {
    case "zoom_in":   return { scale: 1.0 + 0.10 * p, tx: 0, ty: 0 };
    case "zoom_out":  return { scale: 1.10 - 0.10 * p, tx: 0, ty: 0 };
    case "pan_left":  return { scale: 1.06, tx: -40 * (1 - p), ty: 0 };  // start left, end centered
    case "pan_right": return { scale: 1.06, tx:  40 * (1 - p), ty: 0 };
    case "pan_up":    return { scale: 1.06, tx: 0, ty: -30 * (1 - p) };
  }
}

export function CinematicFrame({
  src,
  isVideo = false,
  grade = "color",
  overlay,
  staticFraming = false,
  durationFrames = 240,
  beatIndex = 0,
}: CinematicFrameProps) {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, 22], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const fadeOut = interpolate(
    frame,
    [durationFrames - FADE_OUT_FRAMES, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) },
  );
  const opacity = Math.min(fadeIn, fadeOut);

  // Ken Burns — variant cycles per beat so consecutive scenes don't all
  // zoom in the same direction. Progress runs across the scene's full
  // visible window (NOT a fixed 240 frames) so the motion lands.
  const variant: KenBurnsVariant = staticFraming
    ? "zoom_in"
    : KEN_BURNS_CYCLE[beatIndex % KEN_BURNS_CYCLE.length];
  const progress = interpolate(frame, [0, durationFrames], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });
  const motion = staticFraming ? { scale: 1, tx: 0, ty: 0 } : kenBurnsMotion(variant, progress);
  const filter = gradeFilter(grade);

  const assetStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    transform: `translate(${motion.tx}px, ${motion.ty}px) scale(${motion.scale})`,
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
