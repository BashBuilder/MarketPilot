import { describe, expect, it } from "vitest";
import { CampaignPackageSchema } from "./package";

const dimension = { score: 8, justification: "Clear and on-brief for the audience." };

const validPackage = {
  brief: {
    product: "Fictional hair-care serum",
    goal: "Drive trial sign-ups",
    audience: "Adults aged 25 to 40",
    tone: "Warm and confident",
    channels: ["instagram", "email"],
    constraints: ["No medical claims"],
  },
  research: {
    segments: [{ name: "Busy professionals", description: "Low-maintenance routines" }],
    pain_points: ["Frizz in humidity"],
    messaging_angles: ["Effortless shine"],
    sources: [{ title: "Category report", url: "https://example.com/report" }],
  },
  copy: {
    variants: [
      {
        channel: "instagram",
        headline: "Shine, without the fuss",
        description: "A lightweight serum for everyday gloss.",
        cta: "Try it today",
      },
    ],
  },
  direction: {
    style_guide: "Editorial, warm light, soft shadows",
    composition: "Centered bottle on stone, generous negative space",
    image_prompts: ["A serum bottle on warm stone"],
    video_prompts: [],
    negative_prompts: ["text overlays", "harsh flash"],
  },
  assets: {
    assets: [
      {
        uri: "hair-care-01.png",
        checksum: "a".repeat(64),
        model: "fake-image-v1",
        seed: 9223372036854775807,
        prompt: "A serum bottle on warm stone",
      },
    ],
  },
  compliance: {
    items: [
      { check: "No medical claims", passed: true, reason: "Copy avoids treatment language." },
      { check: "No unverifiable claims", passed: true, reason: "Only sensory claims." },
      { check: "No competitor references", passed: true, reason: "No brands named." },
    ],
  },
  score: {
    brief_alignment: dimension,
    audience_fit: dimension,
    copy_quality: dimension,
    visual_quality: dimension,
    compliance_risk: dimension,
    total: 80,
  },
};

describe("CampaignPackageSchema", () => {
  it("accepts a full package", () => {
    const parsed = CampaignPackageSchema.parse(validPackage);
    expect(parsed).toEqual(validPackage);
  });

  it("defaults omitted sections to null and keeps explicit nulls", () => {
    const parsed = CampaignPackageSchema.parse({ brief: validPackage.brief });
    expect(parsed.research).toBeNull();
    expect(parsed.score).toBeNull();

    const explicit = CampaignPackageSchema.parse({ ...validPackage, score: null });
    expect(explicit.score).toBeNull();
  });

  it("rejects a malformed asset checksum", () => {
    expect(() =>
      CampaignPackageSchema.parse({
        assets: { assets: [{ ...validPackage.assets.assets[0], checksum: "nothex" }] },
      }),
    ).toThrow();
  });

  it("rejects a negative seed and an out-of-range total", () => {
    expect(() =>
      CampaignPackageSchema.parse({
        assets: { assets: [{ ...validPackage.assets.assets[0], seed: -1 }] },
      }),
    ).toThrow();
    expect(() =>
      CampaignPackageSchema.parse({ score: { ...validPackage.score, total: 120 } }),
    ).toThrow();
  });
});
