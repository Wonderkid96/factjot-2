import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

// "Redacted doc" — bold typed paragraph on pure black. Selected words get an
// inverter-matte redaction block that sweeps in left-to-right: a WHITE block
// with `mix-blend-mode: difference` inverts the colours inside it, so the
// surrounding black bg becomes white AND the white text becomes black. Net
// visual: the redacted word flips to black-on-white, reads exactly like a
// classic redaction stamp.
//
// The block only covers the bounds of each redacted word individually, so the
// surrounding text stays white-on-black untouched.

interface RedactedDocProps {
  text: string;
  /** Word indices to redact. Defaults to every 3rd word > 2 chars. */
  redactIndices?: number[];
  /** Frames to take typing the full text. */
  typeDurationFrames?: number;
  /** Frames after typing before the bars sweep in. */
  redactDelayFrames?: number;
}

export function RedactedDoc({
  text,
  redactIndices,
  typeDurationFrames = 36,
  redactDelayFrames = 12,
}: RedactedDocProps) {
  const frame = useCurrentFrame();

  const words = text.split(/\s+/).filter(Boolean);
  const redactSet = new Set(
    redactIndices ?? words.map((_, i) => i).filter((i) => i % 3 === 2 && words[i].length > 2),
  );

  const typeProgress = interpolate(frame, [0, typeDurationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });
  const wordsToShow = Math.floor(typeProgress * words.length);

  const sweepStart = typeDurationFrames + redactDelayFrames;
  const sweepProgress = interpolate(frame, [sweepStart, sweepStart + 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{
      backgroundColor: "#000000",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "0 90px",
    }}>
      <p style={{
        color: "#FFFFFF",
        fontFamily: "IBM Plex Mono, Courier New, monospace",
        fontSize: 56,
        lineHeight: 1.45,
        margin: 0,
        textAlign: "left",
        maxWidth: 900,
      }}>
        {words.map((w, i) => {
          const visible = i < wordsToShow;
          const isRedacted = redactSet.has(i);
          const localSweep = isRedacted ? sweepProgress : 0;
          return (
            <span
              key={`w-${i}`}
              style={{
                position: "relative",
                display: "inline-block",
                marginRight: "0.35em",
                opacity: visible ? 1 : 0,
              }}
            >
              {w}
              {isRedacted && (
                <span
                  aria-hidden
                  style={{
                    position: "absolute",
                    top: -2,
                    left: -4,
                    bottom: -2,
                    right: -4,
                    backgroundColor: "#FFFFFF",
                    // Inverter matte: `difference` with white flips the colours
                    // inside the rectangle. Black bg → white panel, white text
                    // → black text. Result: a redaction block with the word
                    // appearing as black-on-white, exactly like real censorship.
                    mixBlendMode: "difference",
                    transformOrigin: "left center",
                    transform: `scaleX(${localSweep})`,
                  }}
                />
              )}
            </span>
          );
        })}
      </p>
    </AbsoluteFill>
  );
}
