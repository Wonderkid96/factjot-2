import brandKit from "../../../brand/brand_kit.json";
import { loadFont as loadArchivoBlack } from "@remotion/google-fonts/ArchivoBlack";
import { loadFont as loadInstrumentSerif } from "@remotion/google-fonts/InstrumentSerif";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";

// Load brand fonts at module level. Remotion blocks render via delayRender
// internally until the font files are fetched and applied.
loadArchivoBlack();
loadInstrumentSerif();
loadInstrumentSerif("italic", { weights: ["400"] });
loadSpaceGrotesk("normal", { weights: ["500", "600", "700"] });

export const palette = {
  paper: brandKit.colors.paper,
  ink: brandKit.colors.ink,
  near_black: brandKit.colors.near_black,
  muted: brandKit.colors.muted,
  off_white: brandKit.colors.off_white,
  accent: brandKit.colors.accent,
  lime: brandKit.colors.lime,
  lilac: brandKit.colors.lilac,
  white: brandKit.colors.white,
} as const;

export const dimensions = {
  reelW: 1080,
  reelH: 1920,
  carouselW: brandKit.layout.canvas_width,
  carouselH: brandKit.layout.canvas_height,
} as const;

export const fonts = {
  serif: "Instrument Serif",
  serifItalic: "Instrument Serif",
  caption: "Archivo Black",
  subtitle: "Archivo",
  label: "Space Grotesk",
  labelLegacy: "JetBrains Mono",
} as const;

export const typography = {
  headlineSizeMax: brandKit.typography.headline_size_max,
  headlineSizeMin: brandKit.typography.headline_size_min,
  headlineLineHeight: brandKit.typography.headline_line_height,
  headlineLetterSpacingEm: brandKit.typography.headline_letter_spacing_em,
  labelLetterSpacingEm: brandKit.typography.label_letter_spacing_em,
  captionLetterSpacingEm: brandKit.typography.caption_letter_spacing_em,
} as const;

export const wordmark = {
  text: brandKit.wordmark.text,
  italicPart: brandKit.wordmark.italic_part,
  accentDot: brandKit.wordmark.accent_dot,
  color: palette[brandKit.wordmark.color as keyof typeof palette],
} as const;

export type Palette = typeof palette;
