import React from "react";
import { AbsoluteFill, Img, OffthreadVideo } from "remotion";
import { Tape, useSettleSpring, useImpactBounce, useHandJitter, STIFF_SHADOW } from "./primitives";

// Polaroid frame: thick white border, narrow top/sides, fat bottom strip,
// tape strip at the top centre. Enters from off-canvas top-right with a
// rotation and lands with an impact bounce. Lives slightly off-centre and
// off-vertical so it feels like it was hand-placed.

interface PolaroidProps {
  src: string;
  isVideo?: boolean;
  /** Rotation when settled, in degrees. Default −4° = leftward lean. */
  finalRotation?: number;
  /** Horizontal offset from centre in pixels. Negative = left. */
  offsetX?: number;
  /** Vertical offset from centre in pixels. Negative = up. */
  offsetY?: number;
  /** Image area aspect, e.g. 1 (square), 4/5 (portrait crop). */
  aspect?: number;
}

export function Polaroid({
  src,
  isVideo = false,
  finalRotation = -4,
  offsetX = -20,
  offsetY = -80,
  aspect = 4 / 5,
}: PolaroidProps) {
  const settle = useSettleSpring(0);
  const bounceY = useImpactBounce(0);
  const jitter = useHandJitter(0.6, 0.03);

  // Travel: from off-canvas top-right, rotated steeply, into final pose.
  const startX = 700;
  const startY = -1200;
  const startRot = 18;
  const x = (1 - settle) * startX + offsetX + jitter.x;
  const y = (1 - settle) * startY + offsetY + jitter.y;
  const rot = (1 - settle) * startRot + finalRotation + jitter.r;

  // Polaroid dimensions (the frame, not the image inside)
  const FRAME_W = 720;
  const IMAGE_W = FRAME_W - 60; // 30px white border each side
  const IMAGE_H = IMAGE_W / aspect;
  const FRAME_H = IMAGE_H + 60 + 110; // top 60, bottom 110 (signature strip)

  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          position: "relative",
          width: FRAME_W,
          height: FRAME_H,
          backgroundColor: "#fdfaf2",
          // The polaroid edge has a faint warm tint
          boxShadow: STIFF_SHADOW,
          transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scaleY(${bounceY})`,
          transformOrigin: "center 30%",
        }}
      >
        {/* Image well */}
        <div
          style={{
            position: "absolute",
            top: 30,
            left: 30,
            width: IMAGE_W,
            height: IMAGE_H,
            overflow: "hidden",
            backgroundColor: "#0a0a0a",
          }}
        >
          {isVideo ? (
            <OffthreadVideo src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          )}
          {/* Slight inner darken for old-photograph feel */}
          <AbsoluteFill
            style={{
              background:
                "radial-gradient(120% 120% at 50% 40%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.32) 100%)",
              pointerEvents: "none",
            }}
          />
        </div>
        {/* Tape strip top-centre */}
        <Tape side="top-center" rotation={-3} width={180} />
      </div>
    </AbsoluteFill>
  );
}
