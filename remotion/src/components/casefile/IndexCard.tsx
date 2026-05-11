import React from "react";
import { TitleCard } from "./TitleCard";

// "Index card" — was a typed manila card. Now: bold Netflix-doc title card
// on pure black. The text IS the fact, no decorative paper around it.

interface IndexCardProps {
  text: string;
}

export function IndexCard({ text }: IndexCardProps) {
  // Auto-size: 4 lines @ 88pt feels right up to ~16 words; longer beats
  // drop to 72pt so they fit without overflow.
  const wordCount = text.split(/\s+/).filter(Boolean).length;
  const size = wordCount > 16 ? 72 : 88;
  return <TitleCard text={text} size={size} />;
}
