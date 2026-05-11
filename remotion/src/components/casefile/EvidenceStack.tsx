import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, useCurrentFrame, spring, useVideoConfig, interpolate } from "remotion";
import { PAPER_SHADOW } from "./primitives";

// EvidenceStack: corner-pinned accumulator. Renders ALL prior beats' assets
// as small "filed" photos stacked in the bottom-right, slightly rotated and
// fanned. Each enters with a spring as the playhead crosses its start frame.
// Used as a CONSTANT overlay across the CaseFileReel — not a per-beat scene.
//
// The current beat is highlighted ("most recent on top"). Prior beats sit
// behind it with reduced opacity. This is what creates the "evidence is
// stacking up" sensation as the reel progresses.

interface StackItem {
  src: string;
  isVideo: boolean;
  startFrame: number;
}

interface EvidenceStackProps {
  items: StackItem[];
  /** Disable the stack (e.g. during outro). */
  hide?: boolean;
}

export function EvidenceStack({ items, hide = false }: EvidenceStackProps) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (hide || items.length === 0) {
    return null;
  }

  // Stack anchored to bottom-right. Each item offset by 22px diagonal so
  // they form a small overlapping fan. Slight rotation alternation for life.
  const BASE_X = 1080 - 220;
  const BASE_Y = 1920 - 320;
  const ITEM_W = 200;
  const ITEM_H = 250;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {items.map((it, i) => {
        const enter = spring({
          frame: Math.max(0, frame - it.startFrame),
          fps,
          config: { damping: 12, stiffness: 130 },
        });
        if (enter <= 0.001) {
          return null;
        }
        // Determine if this item is the CURRENTLY-displayed beat. If so, skip
        // rendering it in the stack — the scene component already shows it
        // at full size. The stack should only show what's been "filed away".
        const isCurrent = i === items.length - 1
          ? frame >= it.startFrame
          : (items[i + 1] ? frame < items[i + 1].startFrame : false);
        if (isCurrent) {
          return null;
        }

        const rotation = i % 2 === 0 ? -6 : 5;
        const offsetX = -i * 18;
        const offsetY = -i * 14;
        const opacity = 0.78;
        const lift = interpolate(enter, [0, 1], [40, 0]);

        return (
          <div
            key={`stack-${i}`}
            style={{
              position: "absolute",
              left: BASE_X + offsetX,
              top: BASE_Y + offsetY + lift,
              width: ITEM_W,
              height: ITEM_H,
              backgroundColor: "#fdfaf2",
              padding: 10,
              boxShadow: PAPER_SHADOW,
              transform: `rotate(${rotation}deg) scale(${interpolate(enter, [0, 1], [0.6, 1])})`,
              transformOrigin: "center center",
              opacity: enter * opacity,
              zIndex: i + 1,
            }}
          >
            <div style={{ width: ITEM_W - 20, height: ITEM_H - 38, overflow: "hidden", backgroundColor: "#0a0a0a" }}>
              {it.isVideo ? (
                <OffthreadVideo
                  src={it.src}
                  style={{ width: "100%", height: "100%", objectFit: "cover", filter: isCurrent ? undefined : "grayscale(0.6)" }}
                />
              ) : (
                <Img
                  src={it.src}
                  style={{ width: "100%", height: "100%", objectFit: "cover", filter: isCurrent ? undefined : "grayscale(0.6)" }}
                />
              )}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
}
