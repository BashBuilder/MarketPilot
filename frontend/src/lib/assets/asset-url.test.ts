import { describe, expect, it } from "vitest";
import { resolveAssetUrl } from "./asset-url";

describe("resolveAssetUrl", () => {
  it("keeps hosted https URLs", () => {
    expect(
      resolveAssetUrl("https://res.cloudinary.com/demo/image/upload/sample.png"),
    ).toBe("https://res.cloudinary.com/demo/image/upload/sample.png");
  });

  it("routes relative backend file names through the asset proxy", () => {
    expect(resolveAssetUrl("hair-care-serum-01.png")).toBe(
      "/api/assets/hair-care-serum-01.png",
    );
    expect(resolveAssetUrl("nested/folder/image one.png")).toBe(
      "/api/assets/nested/folder/image%20one.png",
    );
  });

  it("rejects unsafe schemes and empty values", () => {
    expect(resolveAssetUrl("javascript:alert(1)")).toBeNull();
    expect(resolveAssetUrl("data:image/png;base64,AAAA")).toBeNull();
    expect(resolveAssetUrl("   ")).toBeNull();
  });
});
