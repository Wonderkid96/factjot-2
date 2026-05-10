import React from "react";
import { fonts, palette, wordmark } from "../style/tokens";

interface Props {
  size?: number;
  colour?: string;
}

export const Wordmark: React.FC<Props> = ({ size = 48, colour }) => {
  const baseColour = colour || wordmark.color;
  const stem = wordmark.text.replace(wordmark.italicPart, "");
  return (
    <span style={{
      fontFamily: fonts.serif,
      fontSize: size,
      color: baseColour,
      letterSpacing: -0.02 * size,
      fontWeight: 400,
    }}>
      {stem}
      <span style={{ fontStyle: "italic", color: baseColour }}>{wordmark.italicPart}</span>
      {wordmark.accentDot && <span style={{ color: palette.accent }}>.</span>}
    </span>
  );
};
