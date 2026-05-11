import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { useSettleSpring, useImpactBounce, PAPER_SHADOW } from "./primitives";

// MapPin: the asset displays inside an off-white panel sitting atop a paper
// "map" texture. A red push-pin drops in and pierces the panel's top edge.
// Restrained — the map is a subtle line texture, not a literal map image.

interface MapPinProps {
  src: string;
  isVideo?: boolean;
  /** Caption for the pin — usually a location. Lowercase, single line. */
  locationLabel?: string;
}

export function MapPin({ src, isVideo = false, locationLabel }: MapPinProps) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const settle = useSettleSpring(0);
  const bounce = useImpactBounce(0);

  // Pin drops in slightly after the panel lands
  const pin = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: { damping: 9, stiffness: 200, mass: 1 },
  });
  const pinY = interpolate(pin, [0, 1], [-260, 0]);
  const pinScale = interpolate(pin, [0, 0.6, 1], [1.4, 1.0, 1.0]);

  const x = (1 - settle) * 30;
  const y = (1 - settle) * 60;
  const rot = (1 - settle) * 2 - 1;

  const PANEL_W = 800;
  const IMAGE_H = PANEL_W * 0.62;

  return (
    <AbsoluteFill>
      {/* Map texture — concentric topographic-style lines, very subtle */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "radial-gradient(circle at 30% 40%, rgba(180,140,90,0.18) 0px, rgba(180,140,90,0.18) 1px, transparent 1px, transparent 22px), radial-gradient(circle at 75% 70%, rgba(180,140,90,0.12) 0px, rgba(180,140,90,0.12) 1px, transparent 1px, transparent 26px)",
          backgroundColor: "rgba(245, 232, 198, 0.08)",
        }}
      />

      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            position: "relative",
            width: PANEL_W,
            backgroundColor: "#f6efde",
            boxShadow: PAPER_SHADOW,
            transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scaleY(${bounce})`,
            padding: 22,
          }}
        >
          <div style={{ width: PANEL_W - 44, height: IMAGE_H, overflow: "hidden", backgroundColor: "#0a0a0a" }}>
            {isVideo ? (
              <OffthreadVideo src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            )}
          </div>
          {locationLabel && (
            <div
              style={{
                marginTop: 14,
                color: "#2a1c10",
                fontFamily: "Space Grotesk, sans-serif",
                fontWeight: 600,
                fontSize: 28,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                textAlign: "center",
              }}
            >
              {locationLabel}
            </div>
          )}

          {/* Pin — head + needle. Sits at the top centre, piercing the panel. */}
          <div
            style={{
              position: "absolute",
              top: -36,
              left: "50%",
              marginLeft: -22,
              transform: `translateY(${pinY}px) scale(${pinScale})`,
              transformOrigin: "center bottom",
            }}
          >
            {/* Needle */}
            <div
              style={{
                position: "absolute",
                top: 16,
                left: 20,
                width: 4,
                height: 38,
                background: "linear-gradient(180deg, #555 0%, #222 100%)",
                transform: "rotate(2deg)",
              }}
            />
            {/* Head */}
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 22,
                background:
                  "radial-gradient(circle at 35% 32%, #ff5a4a 0%, #b3201a 60%, #6e120e 100%)",
                boxShadow: "0 4px 10px rgba(0,0,0,0.5)",
              }}
            />
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}
