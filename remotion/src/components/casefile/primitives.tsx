import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";

// Shared low-level building blocks for the case-file scene kit. Treatments
// import these so we get a consistent feel across the deck: every paper has
// the same shadow stack, every entry settles with the same spring, every
// tape strip looks like the same roll.

// ---------- Shadow + paper ----------

// Realistic stacked-paper shadow. Three layered shadows — soft ambient,
// medium contact, sharp under-edge — give the impression the paper is
// physically sitting on the desk, not floating.
export const PAPER_SHADOW =
  "0 1px 2px rgba(0,0,0,0.18), 0 8px 18px rgba(0,0,0,0.28), 0 22px 36px rgba(0,0,0,0.22)";

// Heavier shadow for polaroids and index cards (thicker stock).
export const STIFF_SHADOW =
  "0 2px 3px rgba(0,0,0,0.22), 0 12px 24px rgba(0,0,0,0.32), 0 28px 48px rgba(0,0,0,0.26)";

// ---------- Tape strip ----------

interface TapeProps {
  side: "top-left" | "top-right" | "top-center" | "bottom-left" | "bottom-right";
  rotation?: number;
  width?: number;
}

export function Tape({ side, rotation = -6, width = 110 }: TapeProps) {
  const positions: Record<TapeProps["side"], React.CSSProperties> = {
    "top-left": { top: -22, left: -24 },
    "top-right": { top: -22, right: -24 },
    "top-center": { top: -22, left: "50%", marginLeft: -width / 2 },
    "bottom-left": { bottom: -22, left: -24 },
    "bottom-right": { bottom: -22, right: -24 },
  };
  return (
    <div
      style={{
        position: "absolute",
        width,
        height: 38,
        background:
          "linear-gradient(180deg, rgba(255,247,196,0.78) 0%, rgba(248,228,140,0.62) 50%, rgba(255,247,196,0.78) 100%)",
        boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
        transform: `rotate(${rotation}deg)`,
        transformOrigin: "center center",
        pointerEvents: "none",
        ...positions[side],
      }}
    />
  );
}

// ---------- Slide settle ----------

// Returns 0..1 across SETTLE_FRAMES with a strong ease-out, NO overshoot.
// Models a paper sliding across a table and decelerating to rest under
// friction — not a spring. Used as `progress` by scenes to interpolate
// position/rotation from "off-canvas" to "settled".
//
// Friction curve: cubic-bezier(0.18, 0.9, 0.22, 1.0) — front-loaded velocity
// that ramps down to zero. Matches the way real paper behaves: most of the
// travel happens in the first third of the animation, the last third is the
// slow glide-to-stop.
export const SETTLE_FRAMES = 22;
const SLIDE_EASE = Easing.bezier(0.18, 0.9, 0.22, 1.0);

export function useSettleProgress(delay = 0): number {
  const frame = useCurrentFrame();
  return interpolate(
    Math.max(0, frame - delay),
    [0, SETTLE_FRAMES],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: SLIDE_EASE },
  );
}

// Back-compat alias — older scenes import useSettleSpring expecting the
// 0..1 progress shape (they don't care about the spring overshoot, they
// just used it as a 0→1 driver). Mapping the old name to the new function
// removes the overshoot everywhere in one swap.
export const useSettleSpring = useSettleProgress;

// No-op impact bounce — kept exported so existing scene files don't break.
// Returns a constant 1 (no squash). Real paper sliding to a stop doesn't
// squash; older scenes called this for a small Y-scale bounce that read as
// cartoony rather than natural.
export function useImpactBounce(_delay = 0): number {
  return 1;
}

// ---------- Subtle hand wobble ----------

// Tiny per-frame jitter to simulate a hand-held element. Use sparingly —
// only on items that should feel alive (index cards, stamps post-landing).
export function useHandJitter(amplitude = 1.2, speed = 0.04): { x: number; y: number; r: number } {
  const frame = useCurrentFrame();
  return {
    x: Math.sin(frame * speed) * amplitude,
    y: Math.cos(frame * speed * 1.3) * (amplitude * 0.7),
    r: Math.sin(frame * speed * 0.7) * (amplitude * 0.18),
  };
}
