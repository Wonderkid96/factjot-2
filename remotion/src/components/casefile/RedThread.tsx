import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, useCurrentFrame, interpolate, Easing } from "remotion";
import { useSettleSpring, useImpactBounce, PAPER_SHADOW } from "./primitives";

// RedThread: shows the CURRENT beat's asset on one side, the PRIOR beat's
// asset on the other, with a red string drawn between them. Used for the
// "connection" moment in a story. Subtle — one thread, two pinned photos,
// no full corkboard chaos.

interface RedThreadProps {
  src: string;
  isVideo?: boolean;
  /** The prior beat's asset, drawn as the connected photo. */
  priorSrc: string | null;
  priorIsVideo?: boolean;
}

export function RedThread({ src, isVideo = false, priorSrc, priorIsVideo = false }: RedThreadProps) {
  const frame = useCurrentFrame();
  const settle = useSettleSpring(0);
  const bounce = useImpactBounce(0);

  // Thread draws after both photos are visible
  const threadProgress = interpolate(frame, [22, 38], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Photo positions — left and right of frame, with the thread connecting them
  const LEFT_X = 90;
  const RIGHT_X = 1080 - 90 - 380;
  const PHOTO_TOP = 540;
  const PHOTO_W = 380;
  const PHOTO_H = 480;

  const photoStyle = (offsetX: number, finalRot: number, delay = 0): React.CSSProperties => ({
    position: "absolute",
    left: offsetX,
    top: PHOTO_TOP,
    width: PHOTO_W,
    height: PHOTO_H,
    backgroundColor: "#fdfaf2",
    padding: 18,
    boxShadow: PAPER_SHADOW,
    transform: `rotate(${finalRot}deg) scaleY(${bounce})`,
    transformOrigin: "center top",
  });

  // Anchor coordinates for the SVG thread
  const leftAnchor = { x: LEFT_X + PHOTO_W / 2, y: PHOTO_TOP - 6 };
  const rightAnchor = { x: RIGHT_X + PHOTO_W / 2, y: PHOTO_TOP - 6 };

  // Sagging mid-point — the thread droops slightly
  const midX = (leftAnchor.x + rightAnchor.x) / 2;
  const midY = Math.min(leftAnchor.y, rightAnchor.y) + 70;

  return (
    <AbsoluteFill>
      {/* Pinned photo — prior beat (left) */}
      {priorSrc && (
        <div style={photoStyle(LEFT_X, -3)}>
          <div style={{ position: "relative", width: PHOTO_W - 36, height: PHOTO_H - 60, overflow: "hidden", backgroundColor: "#0a0a0a" }}>
            {priorIsVideo ? (
              <OffthreadVideo src={priorSrc} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              <Img src={priorSrc} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(0.4)" }} />
            )}
          </div>
          {/* Push-pin head at top centre */}
          <div
            style={{
              position: "absolute",
              top: -4,
              left: "50%",
              marginLeft: -10,
              width: 20,
              height: 20,
              borderRadius: 10,
              background: "radial-gradient(circle at 35% 32%, #ff5a4a 0%, #b3201a 60%, #6e120e 100%)",
              boxShadow: "0 2px 4px rgba(0,0,0,0.5)",
            }}
          />
        </div>
      )}

      {/* Pinned photo — current beat (right) */}
      <div style={photoStyle(RIGHT_X, 3)}>
        <div style={{ position: "relative", width: PHOTO_W - 36, height: PHOTO_H - 60, overflow: "hidden", backgroundColor: "#0a0a0a" }}>
          {isVideo ? (
            <OffthreadVideo src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(0.2)" }} />
          )}
        </div>
        <div
          style={{
            position: "absolute",
            top: -4,
            left: "50%",
            marginLeft: -10,
            width: 20,
            height: 20,
            borderRadius: 10,
            background: "radial-gradient(circle at 35% 32%, #ff5a4a 0%, #b3201a 60%, #6e120e 100%)",
            boxShadow: "0 2px 4px rgba(0,0,0,0.5)",
          }}
        />
      </div>

      {/* SVG thread, drawn with stroke-dasharray for the "drawing in" effect */}
      <svg
        width="1080"
        height="1920"
        style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      >
        <defs>
          <filter id="thread-shadow">
            <feGaussianBlur stdDeviation="2" />
          </filter>
        </defs>
        <path
          d={`M ${leftAnchor.x} ${leftAnchor.y} Q ${midX} ${midY}, ${rightAnchor.x} ${rightAnchor.y}`}
          stroke="#b3201a"
          strokeWidth={4}
          fill="none"
          strokeLinecap="round"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - threadProgress}
        />
      </svg>
    </AbsoluteFill>
  );
}
