import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
import { PAPER_SHADOW } from "./primitives";

// RedactedDoc: typewriter-effect paragraph on a page, then sweeping black
// redaction bars cover ~30% of the words to reveal "CLASSIFIED". The text
// shown is the BEAT's text — so the spoken narration is mirrored on screen
// for emphasis, with the editorialised redactions hinting at concealment.

interface RedactedDocProps {
  text: string;
  /** Which words to redact (0-indexed). If not provided, redacts every 3rd word
      starting at index 2 — a sensible default that looks deliberate. */
  redactIndices?: number[];
  /** Frames to take typing the full text. Default ~1.2s. */
  typeDurationFrames?: number;
  /** Frames after typing finishes before the bars sweep in. */
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

  // Typewriter progress 0..1
  const typeProgress = interpolate(frame, [0, typeDurationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });
  const wordsToShow = Math.floor(typeProgress * words.length);

  // Bar sweep progress 0..1 (starts after typing+delay)
  const sweepStart = typeDurationFrames + redactDelayFrames;
  const sweepDur = 14;
  const sweepProgress = interpolate(frame, [sweepStart, sweepStart + sweepDur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          width: 880,
          minHeight: 1100,
          padding: "120px 110px",
          backgroundColor: "#f5edd6",
          boxShadow: PAPER_SHADOW,
          transform: "rotate(-1.5deg)",
          position: "relative",
          // Page texture — subtle horizontal lines like ruled paper
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(120,80,40,0.04) 0px, rgba(120,80,40,0.04) 1px, transparent 1px, transparent 56px)",
        }}
      >
        {/* Document header */}
        <div
          style={{
            position: "absolute",
            top: 44,
            left: 110,
            right: 110,
            display: "flex",
            justifyContent: "space-between",
            color: "#3a2818",
            fontFamily: "Space Grotesk, sans-serif",
            fontSize: 18,
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            borderBottom: "1.5px solid #3a2818",
            paddingBottom: 12,
          }}
        >
          <span>Case file</span>
          <span>Restricted</span>
        </div>

        {/* Typewriter paragraph */}
        <p
          style={{
            color: "#2a1c10",
            fontFamily: "IBM Plex Mono, Courier New, monospace",
            fontSize: 44,
            lineHeight: 1.55,
            margin: 0,
            marginTop: 60,
          }}
        >
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
                    style={{
                      position: "absolute",
                      top: -4,
                      left: -4,
                      bottom: -4,
                      right: -4,
                      backgroundColor: "#0a0a0a",
                      transformOrigin: "left center",
                      transform: `scaleX(${localSweep})`,
                    }}
                  />
                )}
              </span>
            );
          })}
        </p>

        {/* Footer stamp */}
        <div
          style={{
            position: "absolute",
            bottom: 60,
            right: 100,
            color: "#b3201a",
            fontFamily: "Archivo Black, sans-serif",
            fontSize: 38,
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            border: "4px solid #b3201a",
            padding: "10px 22px",
            transform: "rotate(-8deg)",
            opacity: interpolate(frame, [sweepStart + 6, sweepStart + 18], [0, 0.92], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          Classified
        </div>
      </div>
    </AbsoluteFill>
  );
}
