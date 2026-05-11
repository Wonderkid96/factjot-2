import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

// Netflix-doc title card: bold white text on pure black, slow fade in,
// optional second line in lighter weight. Used by treatments that lean on
// the spoken word more than the visual (index_card, redacted_doc, quote
// moments) — replaces the manila/typewriter paper cards from the case-file
// kit. Clean. Quiet. Lets the audio breathe.

interface TitleCardProps {
  text: string;
  /** Optional smaller line below (caption / source / attribution). */
  subtitle?: string;
  /** Font size for the main line. Default 88 (works for ~10 word lines). */
  size?: number;
}

export function TitleCard({ text, subtitle, size = 88 }: TitleCardProps) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  // Tiny scale-in for a touch of weight.
  const scale = interpolate(frame, [0, 26], [0.96, 1.0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{
      backgroundColor: "#000000",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "0 90px",
      opacity,
    }}>
      <h2 style={{
        color: "#FFFFFF",
        fontFamily: "Archivo Black",
        fontSize: size,
        lineHeight: 1.08,
        letterSpacing: "-0.01em",
        textAlign: "center",
        textTransform: "lowercase",
        margin: 0,
        transform: `scale(${scale})`,
      }}>
        {text}
      </h2>
      {subtitle && (
        <p style={{
          color: "rgba(255,255,255,0.66)",
          fontFamily: "Space Grotesk",
          fontWeight: 500,
          fontSize: 28,
          letterSpacing: "0.16em",
          textTransform: "uppercase",
          margin: "32px 0 0",
          textAlign: "center",
        }}>
          {subtitle}
        </p>
      )}
    </AbsoluteFill>
  );
}
