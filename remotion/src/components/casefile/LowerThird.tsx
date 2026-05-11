import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";
import { CinematicFrame, CinematicGrade } from "./CinematicFrame";

// Netflix-doc lower-third: full-bleed asset + a small bottom-left label bar
// (location, person's name, year). Slides in from the left a beat after the
// asset, holds briefly, slides out. Used for treatments that introduce a
// specific place or person (map_pin, occasionally polaroid).

interface LowerThirdProps {
  src: string;
  isVideo?: boolean;
  /** Primary label — usually a place or person. Lowercased styling matches the kicker. */
  label: string;
  /** Optional smaller line above the primary (e.g. "LOCATION" / "ARCHIVE"). */
  eyebrow?: string;
  grade?: CinematicGrade;
  durationFrames?: number;
  beatIndex?: number;
}

export function LowerThird({
  src,
  isVideo = false,
  label,
  eyebrow,
  grade = "color",
  durationFrames,
  beatIndex,
}: LowerThirdProps) {
  const frame = useCurrentFrame();
  // Label entry: starts ~14 frames after the asset's fade-in completes.
  const ENTRY_DELAY = 30;
  const ENTRY = 14;
  const entry = interpolate(frame, [ENTRY_DELAY, ENTRY_DELAY + ENTRY], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const tx = interpolate(entry, [0, 1], [-60, 0]);

  return (
    <CinematicFrame
      src={src}
      isVideo={isVideo}
      grade={grade}
      durationFrames={durationFrames}
      beatIndex={beatIndex}
      overlay={
        <AbsoluteFill style={{ pointerEvents: "none" }}>
          <div style={{
            position: "absolute",
            left: 80,
            bottom: 460,
            transform: `translateX(${tx}px)`,
            opacity: entry,
          }}>
            {eyebrow && (
              <div style={{
                color: "rgba(255,255,255,0.78)",
                fontFamily: "Space Grotesk",
                fontWeight: 600,
                fontSize: 22,
                letterSpacing: "0.22em",
                textTransform: "uppercase",
                marginBottom: 10,
              }}>
                {eyebrow}
              </div>
            )}
            <div style={{
              color: "#FFFFFF",
              fontFamily: "Archivo Black",
              fontSize: 56,
              lineHeight: 1.05,
              letterSpacing: "-0.005em",
              textShadow: "0 4px 18px rgba(0,0,0,0.65)",
              paddingLeft: 18,
              borderLeft: "4px solid #FFFFFF",
            }}>
              {label}
            </div>
          </div>
        </AbsoluteFill>
      }
    />
  );
}
