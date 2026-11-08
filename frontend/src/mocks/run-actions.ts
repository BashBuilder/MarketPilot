import type { ApproveResponse, CampaignSummary, ReviseRequest, ReviseResponse } from "@/lib/schemas";
import type { MockRun } from "./fixtures/campaigns";
import { hairCarePackage, hairCareRevision } from "./fixtures/hair-care";
import { mockStore } from "./store";

const SCORE_V1 = 84;
const SCORE_V2 = 88;

function versionId(campaignId: string, version: number): string {
  return `${campaignId}-v${version}`;
}

function now(): string {
  return new Date().toISOString();
}

/** New campaigns start at version 1 with a run parked at the human gate. */
export function createMockCampaign(
  idea: string,
  ids: { campaignId?: string; runId?: string } = {},
): { campaign_id: string; run_id: string } {
  const campaignId = ids.campaignId ?? crypto.randomUUID();
  const runId = ids.runId ?? crypto.randomUUID();
  const createdAt = now();

  const campaign: CampaignSummary = {
    id: campaignId,
    idea,
    status: "awaiting_approval",
    latest_version: 1,
    latest_score: SCORE_V1,
    active_run_id: runId,
    created_at: createdAt,
    updated_at: createdAt,
  };
  mockStore.addCampaign(campaign);
  mockStore.addVersion(
    campaignId,
    { version: 1, parent_version_id: null, score: SCORE_V1, created_at: createdAt },
    hairCarePackage,
  );
  mockStore.setRun({ id: runId, campaignId, status: "awaiting_approval", version: 1 });

  return { campaign_id: campaignId, run_id: runId };
}

export function approveMockRun(runId: string, comment?: string): ApproveResponse | null {
  const run = mockStore.getRun(runId);
  const campaign = run ? mockStore.getCampaign(run.campaignId) : null;
  if (!run || !campaign || run.version === null) return null;
  void comment;

  const version = run.version;
  mockStore.setRun({ ...run, status: "completed" });
  mockStore.updateCampaign(campaign.id, {
    status: "completed",
    latest_version: version,
    latest_score: campaign.latest_version === 1 ? SCORE_V1 : SCORE_V2,
    active_run_id: null,
  });
  return { status: "completed", version };
}

export function reviseMockRun(runId: string, input: ReviseRequest): ReviseResponse | null {
  const run = mockStore.getRun(runId);
  const campaign = run ? mockStore.getCampaign(run.campaignId) : null;
  if (!run || !campaign) return null;

  const previous = campaign.latest_version ?? 1;
  const version = previous + 1;
  const continuation: MockRun = {
    id: crypto.randomUUID(),
    campaignId: campaign.id,
    status: "awaiting_approval",
    version,
  };
  const createdAt = now();

  mockStore.setRun({ ...run, status: "completed" });
  mockStore.addVersion(
    campaign.id,
    {
      version,
      parent_version_id: versionId(campaign.id, previous),
      score: SCORE_V2,
      created_at: createdAt,
    },
    hairCareRevision,
  );
  mockStore.setRun(continuation);
  mockStore.updateCampaign(campaign.id, {
    status: "awaiting_approval",
    latest_version: version,
    latest_score: SCORE_V2,
    active_run_id: continuation.id,
  });
  mockStore.setDiff(campaign.id, {
    from: previous,
    to: version,
    changes: [
      { path: "copy.variants", before: hairCarePackage.copy, after: hairCareRevision.copy },
      { path: "score.copy_quality", before: 8, after: 9 },
      { path: "score.total", before: SCORE_V1, after: SCORE_V2 },
    ],
  });
  void input.target_node;

  return { run_id: continuation.id, version };
}
