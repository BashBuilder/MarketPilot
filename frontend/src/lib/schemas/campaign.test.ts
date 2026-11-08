import { describe, expect, it } from "vitest";
import { CampaignSummarySchema, CreateCampaignRequestSchema } from "./campaign";

const validCampaign = {
  id: "00000000-0000-4000-8000-000000000001",
  idea: "Create an advertising campaign for a fictional hair-care product.",
  status: "awaiting_approval",
  latest_version: 1,
  latest_score: 78,
  active_run_id: "11111111-1111-4111-8111-111111111111",
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-01T10:05:00Z",
};

describe("CampaignSummarySchema", () => {
  it("accepts a valid campaign summary", () => {
    expect(CampaignSummarySchema.parse(validCampaign)).toEqual(validCampaign);
  });

  it("accepts null version, score and run", () => {
    const parsed = CampaignSummarySchema.parse({
      ...validCampaign,
      latest_version: null,
      latest_score: null,
      active_run_id: null,
      status: "draft",
    });
    expect(parsed.latest_version).toBeNull();
  });

  it("rejects an unknown status", () => {
    expect(() =>
      CampaignSummarySchema.parse({ ...validCampaign, status: "paused" }),
    ).toThrow();
  });

  it("rejects a summary missing the idea", () => {
    const withoutIdea: Partial<typeof validCampaign> = { ...validCampaign };
    delete withoutIdea.idea;
    expect(() => CampaignSummarySchema.parse(withoutIdea)).toThrow();
  });
});

describe("CreateCampaignRequestSchema", () => {
  it("accepts an idea within the limit", () => {
    const parsed = CreateCampaignRequestSchema.parse({ idea: "  A hair-care brief  " });
    expect(parsed.idea).toBe("A hair-care brief");
  });

  it("rejects an empty or over-long idea", () => {
    expect(() => CreateCampaignRequestSchema.parse({ idea: "   " })).toThrow();
    expect(() => CreateCampaignRequestSchema.parse({ idea: "x".repeat(2001) })).toThrow();
  });
});
