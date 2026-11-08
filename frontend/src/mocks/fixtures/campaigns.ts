import type { CampaignSummary, VersionSummary } from "@/lib/schemas";

export const DEMO_CAMPAIGN_ID = "00000000-0000-4000-8000-000000000001";
export const DEMO_RUN_ID = "11111111-1111-4111-8111-111111111111";

export const demoCampaign: CampaignSummary = {
  id: DEMO_CAMPAIGN_ID,
  idea: "Create an advertising campaign for a fictional hair-care product targeting adults aged 25 to 40.",
  status: "awaiting_approval",
  latest_version: 1,
  latest_score: 84,
  active_run_id: DEMO_RUN_ID,
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-01T10:05:00Z",
};

export const demoVersions: VersionSummary[] = [
  {
    version: 1,
    parent_version_id: null,
    score: 84,
    created_at: "2026-01-01T10:05:00Z",
  },
];

export interface MockRun {
  id: string;
  campaignId: string;
  status: "running" | "awaiting_approval" | "completed" | "failed";
  version: number | null;
}
