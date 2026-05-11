import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, useCurrentFrame, interpolate, Easing } from "remotion";

// ArchiveFilm: a black-and-white film-strip frame around the asset. Two
// vertical sprocket-hole strips left and right; the asset sits in the middle
// gate with a subtle grain wash and very slight vertical jitter (like an
// old projector wobble). Restrained — no scratches, no burn marks.

interface ArchiveFilmProps {
  src: string;
  isVideo?: boolean;
}

export function ArchiveFilm({ src, isVideo = false }: ArchiveFilmProps) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const wobbleY = Math.sin(frame * 0.18) * 1.2;
  const zoom = interpolate(frame, [0, 240], [1.02, 1.06], { extrapolateRight: "clamp", easing: Easing.linear });

  // Sprocket holes — drawn as a repeating linear-gradient so we don't ship an asset.
  const sprocket =
    "repeating-linear-gradient(0deg, #f4ead0 0px, #f4ead0 18px, #0a0a0a 18px, #0a0a0a 56px)";

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Wood/desk shows through edges via Desk underneath; this fills the centre */}
      <AbsoluteFill style={{ backgroundColor: "#0a0a0a" }} />

      {/* Left sprocket strip */}
      <div
        style={{
          position: "absolute",
          top: 60,
          bottom: 60,
          left: 40,
          width: 70,
          backgroundImage: sprocket,
          backgroundSize: "100% 74px",
          backgroundColor: "#0a0a0a",
          opacity: 0.92,
        }}
      />
      {/* Right sprocket strip */}
      <div
        style={{
          position: "absolute",
          top: 60,
          bottom: 60,
          right: 40,
          width: 70,
          backgroundImage: sprocket,
          backgroundSize: "100% 74px",
          backgroundColor: "#0a0a0a",
          opacity: 0.92,
        }}
      />

      {/* Film gate — the asset */}
      <div
        style={{
          position: "absolute",
          top: 110,
          bottom: 110,
          left: 130,
          right: 130,
          overflow: "hidden",
          backgroundColor: "#0a0a0a",
          transform: `translateY(${wobbleY}px) scale(${zoom})`,
          transformOrigin: "center center",
        }}
      >
        {isVideo ? (
          <OffthreadVideo
            src={src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              filter: "grayscale(1) contrast(1.15) brightness(0.88)",
            }}
          />
        ) : (
          <Img
            src={src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              filter: "grayscale(1) contrast(1.15) brightness(0.88)",
            }}
          />
        )}
        {/* Mild vignette */}
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(120% 120% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.5) 100%)",
            pointerEvents: "none",
          }}
        />
      </div>
    </AbsoluteFill>
  );
}
