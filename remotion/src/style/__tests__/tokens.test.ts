import { describe, expect, test } from "vitest";
import { palette, dimensions, wordmark } from "../tokens";

describe("brand tokens", () => {
  test("palette has canonical colours", () => {
    expect(palette.paper).toBe("#F4F1E9");
    expect(palette.ink).toBe("#0A0A0A");
    expect(palette.accent).toBe("#E6352A");
  });
  test("reel dimensions are 1080x1920", () => {
    expect(dimensions.reelW).toBe(1080);
    expect(dimensions.reelH).toBe(1920);
  });
  test("wordmark is factjot/jot", () => {
    expect(wordmark.text).toBe("factjot");
    expect(wordmark.italicPart).toBe("jot");
  });
});
