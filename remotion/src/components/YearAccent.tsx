import React from "react";
import { palette } from "../style/tokens";

const YEAR_RE = /\b(1[1-9]\d{2}|20\d{2})\b/g;

interface Props {
  text: string;
  yearColour?: string;
}

export const YearAccent: React.FC<Props> = ({ text, yearColour = palette.accent }) => {
  // Use matchAll-style split to keep the year tokens in the output
  const parts: Array<{ text: string; isYear: boolean }> = [];
  let lastIndex = 0;
  for (const match of text.matchAll(YEAR_RE)) {
    if (match.index === undefined) continue;
    if (match.index > lastIndex) {
      parts.push({ text: text.slice(lastIndex, match.index), isYear: false });
    }
    parts.push({ text: match[0], isYear: true });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push({ text: text.slice(lastIndex), isYear: false });
  }
  return (
    <>
      {parts.map((p, i) =>
        p.isYear ? (
          <span key={i} style={{ color: yearColour }}>{p.text}</span>
        ) : (
          <React.Fragment key={i}>{p.text}</React.Fragment>
        )
      )}
    </>
  );
};
