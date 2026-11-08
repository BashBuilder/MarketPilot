import { describe, expect, it } from "vitest";
import {
  contrastRatio,
  formatRatio,
  oklchToLinearRgb,
  relativeLuminance,
} from "./contrast";
import {
  CONTRAST_PAIRS,
  THEME_COLORS,
  type ThemeName,
} from "./token-manifest";

const THEMES: ThemeName[] = ["light", "dark"];

describe("design token contrast", () => {
  for (const theme of THEMES) {
    describe(`${theme} theme`, () => {
      for (const pair of CONTRAST_PAIRS) {
        it(`${pair.label} meets ${pair.minimum}:1`, () => {
          const ratio = contrastRatio(
            THEME_COLORS[theme][pair.foreground],
            THEME_COLORS[theme][pair.background],
          );
          expect(
            ratio,
            `${theme}: ${pair.foreground} on ${pair.background} = ${formatRatio(ratio)}`,
          ).toBeGreaterThanOrEqual(pair.minimum);
        });
      }
    });
  }

  it("reads OKLCH values and rejects unsupported colours", () => {
    expect(relativeLuminance("oklch(1 0 0)")).toBeCloseTo(1, 3);
    expect(relativeLuminance("oklch(0 0 0)")).toBeCloseTo(0, 3);
    expect(() => oklchToLinearRgb("#ffffff")).toThrow();
  });

  it("reports the maximum 21:1 ratio for black on white", () => {
    expect(contrastRatio("oklch(0 0 0)", "oklch(1 0 0)")).toBeCloseTo(21, 1);
  });
});
