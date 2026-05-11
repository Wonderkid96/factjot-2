import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, spring, useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
import { PAPER_SHADOW } from "./primitives";

// StampReveal: the asset rides full-frame underneath while a giant rubber
// stamp slams in from above, rotates with overshoot, and leaves a slightly
// uneven ink impression. Use for verdicts, dates, labels — anywhere the
// punchline needs to LAND.

interface StampRevealProps {
  src: string;
  isVideo?: boolean;
  /** Big stamp text. Forced uppercase. */
  text: string;
  /** Stamp ink colour. Defaults to a slightly dusty red. */
  color?: string;
  /** Frame to start the stamp animation. Lets you delay until after the asset enters. */
  stampDelay?: number;
}

export function StampReveal({
  src,
  isVideo = false,
  text,
  color = "#b3201a",
  stampDelay = 14,
}: StampRevealProps) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Asset entry — gentle fade + slight zoom
  const assetOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const assetScale = interpolate(frame, [0, 30], [1.04, 1.0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Stamp spring — punchy, overshoot heavy
  const stamp = spring({
    frame: Math.max(0, frame - stampDelay),
    fps,
    config: { damping: 8, stiffness: 220, mass: 1.0 },
  });
  const stampScale = interpolate(stamp, [0, 1], [2.6, 1.0]);
  const stampRot = interpolate(stamp, [0, 1], [-18, -5]);
  const stampOpacity = interpolate(stamp, [0, 0.35, 1], [0, 0.95, 0.88]);

  // After landing, a slight ink "soak" — opacity drops a touch as if the ink
  // has bled into the paper.
  const localSettled = Math.max(0, frame - stampDelay - 10);
  const inkSoak = interpolate(localSettled, [0, 20], [0, 0.05], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {/* Asset — full-bleed beneath the stamp, slightly desaturated so the stamp pops */}
      <AbsoluteFill style={{ opacity: assetOpacity, transform: `scale(${assetScale})` }}>
        {isVideo ? (
          <OffthreadVideo src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "saturate(0.7) brightness(0.78)" }} />
        ) : (
          <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "saturate(0.7) brightness(0.78)" }} />
        )}
        {/* Sepia wash on top */}
        <AbsoluteFill style={{ background: "rgba(40, 24, 12, 0.18)" }} />
      </AbsoluteFill>

      {/* Stamp — centred-ish, rotated, with the classic rubber-stamp texture */}
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            transform: `scale(${stampScale}) rotate(${stampRot}deg)`,
            opacity: stampOpacity - inkSoak,
            border: `8px solid ${color}`,
            padding: "22px 56px",
            borderRadius: 6,
            color,
            fontFamily: "Archivo Black, sans-serif",
            fontSize: 132,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            backgroundColor: "transparent",
            boxShadow: PAPER_SHADOW,
            // Texture: a subtle inset that mimics uneven ink
            filter: "url(#stamp-noise)",
            WebkitTextStroke: "1px transparent",
          }}
        >
          {text.toUpperCase()}
        </div>
      </AbsoluteFill>

      {/* SVG noise filter for the stamp texture. Defined inline so we don't
          need an external asset. */}
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          <filter id="stamp-noise">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" />
            <feColorMatrix
              values="0 0 0 0 0
                      0 0 0 0 0
                      0 0 0 0 0
                      0 0 0 -1.2 1.1"
            />
            <feComposite in="SourceGraphic" in2="noise" operator="in" />
          </filter>
        </defs>
      </svg>
    </AbsoluteFill>
  );
}
