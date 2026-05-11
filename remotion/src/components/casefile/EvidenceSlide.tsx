import React from "react";
import { AbsoluteFill, Img, OffthreadVideo } from "remotion";
import { Tape, useSettleSpring, useImpactBounce, PAPER_SHADOW } from "./primitives";

// EvidenceSlide: a sourced document/asset slides in from off-canvas, lands on
// the desk with an impact bounce, settles at a slight angle. Two strips of
// tape pin its top corners. Use for archival material — letters, charters,
// blueprints, paintings — anything that should read as "documented evidence".

interface EvidenceSlideProps {
  src: string;
  isVideo?: boolean;
  /** Direction of entry — "left", "right", or "bottom". Default "left". */
  from?: "left" | "right" | "bottom";
  /** Final rotation in degrees. */
  finalRotation?: number;
  /** Width of the paper (image area). */
  width?: number;
  aspect?: number;
}

export function EvidenceSlide({
  src,
  isVideo = false,
  from = "left",
  finalRotation = 2,
  width = 820,
  aspect = 3 / 4,
}: EvidenceSlideProps) {
  const settle = useSettleSpring(0);
  const bounce = useImpactBounce(0);

  const offCanvas = { left: { x: -1300, y: 80 }, right: { x: 1300, y: 80 }, bottom: { x: 60, y: 1400 } };
  const startRotByDir = { left: -8, right: 8, bottom: -3 };
  const startX = offCanvas[from].x;
  const startY = offCanvas[from].y;
  const startRot = startRotByDir[from];

  const x = (1 - settle) * startX;
  const y = (1 - settle) * startY;
  const rot = (1 - settle) * startRot + finalRotation;

  const height = width / aspect;

  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          position: "relative",
          width,
          height,
          backgroundColor: "#f6efde",
          boxShadow: PAPER_SHADOW,
          transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scaleY(${bounce})`,
          overflow: "hidden",
        }}
      >
        {/* Image fills the paper, but with a thin paper margin so the asset
            reads as something "stuck" to the paper, not the paper itself. */}
        <div style={{ position: "absolute", inset: 22, overflow: "hidden", backgroundColor: "#0a0a0a" }}>
          {isVideo ? (
            <OffthreadVideo src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          )}
          {/* Aged-paper duotone wash to unify the asset with the file */}
          <AbsoluteFill
            style={{
              background:
                "linear-gradient(180deg, rgba(80,55,28,0.18) 0%, rgba(40,28,14,0.28) 100%)",
              mixBlendMode: "multiply",
              pointerEvents: "none",
            }}
          />
        </div>
        <Tape side="top-left" rotation={-12} width={130} />
        <Tape side="top-right" rotation={12} width={130} />
      </div>
    </AbsoluteFill>
  );
}
