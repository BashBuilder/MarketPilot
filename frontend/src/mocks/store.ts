import type { CampaignPackage, CampaignSummary, VersionDiff, VersionSummary } from "@/lib/schemas";
import {
  DEMO_CAMPAIGN_ID,
  DEMO_RUN_ID,
  demoCampaign,
  demoVersions,
  type MockRun,
} from "./fixtures/campaigns";
import { hairCarePackage } from "./fixtures/hair-care";

interface MockState {
  campaigns: CampaignSummary[];
  versions: Map<string, VersionSummary[]>;
  packages: Map<string, CampaignPackage>;
  diffs: Map<string, VersionDiff>;
  runs: Map<string, MockRun>;
}

function packageKey(campaignId: string, version: number): string {
  return `${campaignId}:${version}`;
}

function seed(): MockState {
  return {
    campaigns: [{ ...demoCampaign }],
    versions: new Map([[DEMO_CAMPAIGN_ID, demoVersions.map((item) => ({ ...item }))]]),
    packages: new Map([[packageKey(DEMO_CAMPAIGN_ID, 1), hairCarePackage]]),
    diffs: new Map(),
    runs: new Map([
      [DEMO_RUN_ID, { id: DEMO_RUN_ID, campaignId: DEMO_CAMPAIGN_ID, status: "awaiting_approval", version: 1 }],
    ]),
  };
}

let state: MockState = seed();

export function resetMockStore(): void {
  state = seed();
}

export const mockStore = {
  listCampaigns(): CampaignSummary[] {
    return state.campaigns.map((campaign) => ({ ...campaign }));
  },
  getCampaign(id: string): CampaignSummary | null {
    const campaign = state.campaigns.find((item) => item.id === id);
    return campaign ? { ...campaign } : null;
  },
  addCampaign(campaign: CampaignSummary): void {
    state.campaigns.unshift(campaign);
  },
  updateCampaign(id: string, patch: Partial<CampaignSummary>): CampaignSummary | null {
    const campaign = state.campaigns.find((item) => item.id === id);
    if (!campaign) return null;
    Object.assign(campaign, patch, { updated_at: new Date().toISOString() });
    return { ...campaign };
  },
  listVersions(campaignId: string): VersionSummary[] {
    return (state.versions.get(campaignId) ?? []).map((version) => ({ ...version }));
  },
  getPackage(campaignId: string, version: number): CampaignPackage | null {
    return state.packages.get(packageKey(campaignId, version)) ?? null;
  },
  addVersion(campaignId: string, version: VersionSummary, pkg: CampaignPackage): void {
    const versions = state.versions.get(campaignId) ?? [];
    state.versions.set(campaignId, [...versions, version]);
    state.packages.set(packageKey(campaignId, version.version), pkg);
  },
  getDiff(campaignId: string, from: number, to: number): VersionDiff | null {
    return state.diffs.get(`${campaignId}:${from}:${to}`) ?? null;
  },
  setDiff(campaignId: string, diff: VersionDiff): void {
    state.diffs.set(`${campaignId}:${diff.from}:${diff.to}`, diff);
  },
  getRun(id: string): MockRun | null {
    return state.runs.get(id) ?? null;
  },
  setRun(run: MockRun): void {
    state.runs.set(run.id, run);
  },
};
