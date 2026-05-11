import React from "react";
import { Polaroid } from "./Polaroid";
import { EvidenceSlide } from "./EvidenceSlide";
import { RedactedDoc } from "./RedactedDoc";
import { StampReveal } from "./StampReveal";
import { IndexCard } from "./IndexCard";
import { NewsprintClip } from "./NewsprintClip";
import { ArchiveFilm } from "./ArchiveFilm";
import { MapPin } from "./MapPin";
import { RedThread } from "./RedThread";
import { KenBurns } from "./KenBurns";

// Dispatcher: picks the right scene component for a beat based on its
// scene_treatment string. Each treatment receives a normalised set of props
// derived from the beat spec — the asset URL, whether it's video, the beat
// duration in frames, and a few treatment-specific overrides (priorSrc for
// red_thread, stamp text for stamp_reveal, etc.).

export type SceneTreatment =
  | "polaroid"
  | "evidence_slide"
  | "redacted_doc"
  | "stamp_reveal"
  | "index_card"
  | "newsprint_clip"
  | "archive_film"
  | "map_pin"
  | "red_thread"
  | "ken_burns";

interface SceneRendererProps {
  treatment: SceneTreatment;
  src: string | null;
  isVideo: boolean;
  beatText: string;
  durationFrames: number;
  /** Prior beat's asset — needed for red_thread. */
  priorSrc?: string | null;
  priorIsVideo?: boolean;
  /** Stamp text override. Derived by parent (often a year or short verdict). */
  stampText?: string;
  /** Map pin label override. Usually the location name. */
  locationLabel?: string;
}

export function SceneRenderer({
  treatment,
  src,
  isVideo,
  beatText,
  durationFrames,
  priorSrc,
  priorIsVideo,
  stampText,
  locationLabel,
}: SceneRendererProps) {
  // Treatments that NEED an asset fall back to ken_burns / index_card when
  // src is null. red_thread also degrades to polaroid if there's no prior.
  if (!src) {
    return <IndexCard text={beatText} />;
  }

  switch (treatment) {
    case "polaroid":
      return <Polaroid src={src} isVideo={isVideo} />;
    case "evidence_slide":
      return <EvidenceSlide src={src} isVideo={isVideo} />;
    case "redacted_doc":
      return <RedactedDoc text={beatText} />;
    case "stamp_reveal":
      return (
        <StampReveal
          src={src}
          isVideo={isVideo}
          text={stampText ?? deriveStampText(beatText)}
        />
      );
    case "index_card":
      return <IndexCard text={beatText} />;
    case "newsprint_clip":
      return <NewsprintClip src={src} isVideo={isVideo} headline={deriveHeadline(beatText)} />;
    case "archive_film":
      return <ArchiveFilm src={src} isVideo={isVideo} />;
    case "map_pin":
      return (
        <MapPin
          src={src}
          isVideo={isVideo}
          locationLabel={locationLabel ?? deriveLocationLabel(beatText)}
        />
      );
    case "red_thread":
      if (!priorSrc) {
        return <Polaroid src={src} isVideo={isVideo} />;
      }
      return (
        <RedThread
          src={src}
          isVideo={isVideo}
          priorSrc={priorSrc}
          priorIsVideo={priorIsVideo ?? false}
        />
      );
    case "ken_burns":
    default:
      return <KenBurns src={src} isVideo={isVideo} durationFrames={durationFrames} />;
  }
}

// Pull a 4-digit year out of the beat text, or fall back to a short verdict.
function deriveStampText(beatText: string): string {
  const yearMatch = beatText.match(/\b(1[6-9]\d{2}|20\d{2})\b/);
  if (yearMatch) {
    return yearMatch[1];
  }
  const verdicts = ["FILED", "CONFIRMED", "ON RECORD", "VERIFIED"];
  return verdicts[beatText.length % verdicts.length];
}

// Try to detect a place-name from the beat. We look for capitalised tokens
// after "in" / "at" / "from" / "to" — the simplest heuristic that catches
// "in Hiroshima", "to Nagasaki", "at Versailles". Falls back to "On Record".
function deriveLocationLabel(beatText: string): string {
  const m = beatText.match(/\b(?:in|at|from|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)/);
  if (m && m[1].length >= 3 && m[1].length <= 30) {
    return m[1];
  }
  return "On Record";
}

// Pull a short masthead-style headline from the beat. Used as the newspaper
// banner. Keeps it short — the first 2-3 significant words.
function deriveHeadline(beatText: string): string {
  // Strip punctuation and articles; take first 2 significant tokens.
  const words = beatText
    .replace(/[^A-Za-z0-9\s]/g, "")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !["the", "and", "for", "from", "into", "with"].includes(w.toLowerCase()));
  if (words.length === 0) {
    return "Bulletin";
  }
  return words.slice(0, 2).map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
}
