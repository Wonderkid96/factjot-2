import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

// "Redacted doc" — was typewritten paper page with sweeping black bars.
// Netflix-doc rebuild: still a text-on-black moment (so it reads as a quoted
// document), but now without the manila page; just bold mono text on pure
// black with the same redaction-bar sweep over selected words. Reads as a
// stylised quote-card, not a literal scan.

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
                <span style={{
                  position: "absolute",
                  top: -4,
                  left: -4,
                  bottom: -4,
                  right: -4,
                  backgroundColor: "#FFFFFF",
                  transformOrigin: "left center",
                  transform: `scaleX(${localSweep})`,
                }} />
              )}
            </span>
          );
        })}
      </p>
    </AbsoluteFill>
  );
}
