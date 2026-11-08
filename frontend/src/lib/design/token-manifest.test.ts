import { describe, expect, it } from "vitest";
import { SPACING_SCALE } from "./token-manifest";

describe("SPACING_SCALE", () => {
  it("stays out of Tailwind's --spacing-* namespace", () => {
    // Tailwind resolves named max-w-* sizes through theme keys such as 3xl.
    // A --spacing-3xl token would silently make max-w-3xl 6rem wide.
    for (const token of SPACING_SCALE) {
      expect(token.variable).toMatch(/^--space-/);
      expect(token.variable).not.toMatch(/^--spacing-/);
    }
  });
});
