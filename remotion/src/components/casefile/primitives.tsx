import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";

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

// ---------- Settle spring ----------

// Springs that simulate a paper landing on the desk: overshoots its target
// then settles. `delay` is in frames; lets you stagger entry across stacked
// items (used in EvidenceStack).
export function useSettleSpring(delay = 0): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: { damping: 11, stiffness: 95, mass: 1.1 },
  });
}

// A short scale jolt that runs in the first ~6 frames, simulating the paper
// hitting the desk surface (slight squash). Returns a multiplier on Y-scale.
export function useImpactBounce(delay = 0): number {
  const frame = useCurrentFrame();
  const local = frame - delay;
  if (local < 0 || local > 12) {
    return 1;
  }
  // 1.0 → 0.93 → 1.04 → 1.0 across 12 frames
  return interpolate(local, [0, 3, 7, 12], [1.0, 0.93, 1.04, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.4, 0, 0.2, 1),
  });
}

// ---------- Slide-in helper ----------

// Returns an entry transform string: translate from `(fromX, fromY)` to (0, 0)
// with a small rotation drift and an opacity fade across `durationFrames`.
export function useSlideIn(
  fromX: number,
  fromY: number,
  fromRotate: number,
  durationFrames = 18,
  delay = 0,
): { transform: string; opacity: number } {
  const frame = useCurrentFrame();
  const local = Math.max(0, frame - delay);
  const eased = interpolate(local, [0, durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const x = interpolate(eased, [0, 1], [fromX, 0]);
  const y = interpolate(eased, [0, 1], [fromY, 0]);
  const rot = interpolate(eased, [0, 1], [fromRotate, 0]);
  const opacity = interpolate(eased, [0, 0.6], [0, 1], {
    extrapolateRight: "clamp",
  });
  return {
    transform: `translate(${x}px, ${y}px) rotate(${rot}deg)`,
    opacity,
  };
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
