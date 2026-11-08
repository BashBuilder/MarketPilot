import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it } from "vitest";
import { approveRun, createCampaign, getCampaign, getVersion, getVersionDiff, listVersions, reviseRun } from "@/lib/api";
import { DEMO_CAMPAIGN_ID, DEMO_RUN_ID } from "./fixtures/campaigns";
import { handlers } from "./handlers";
import { resetMockStore } from "./store";

const server = setupServer(...handlers);

beforeAll(() => server.listen());
beforeEach(() => resetMockStore());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("mock campaign actions", () => {
  it("creates a campaign that is immediately awaiting approval", async () => {
    const created = await createCampaign("A new hair-care idea");
    const campaign = await getCampaign(created.campaign_id);

    expect(campaign.idea).toBe("A new hair-care idea");
    expect(campaign.status).toBe("awaiting_approval");
    expect(campaign.active_run_id).toBe(created.run_id);
  });

  it("rejects an empty idea with the error envelope", async () => {
    await expect(createCampaign("   ")).rejects.toThrow();
  });
});

describe("mock approval", () => {
  it("completes the campaign on approve", async () => {
    const result = await approveRun(DEMO_RUN_ID, "Ship it");
    expect(result).toEqual({ status: "completed", version: 1 });

    const campaign = await getCampaign(DEMO_CAMPAIGN_ID);
    expect(campaign.status).toBe("completed");
    expect(campaign.active_run_id).toBeNull();
  });

  it("returns 409 when the run is not awaiting approval", async () => {
    await approveRun(DEMO_RUN_ID);
    await expect(approveRun(DEMO_RUN_ID)).rejects.toMatchObject({ status: 409 });
  });
});

describe("mock revision", () => {
  it("creates version 2 with a parent, a new run and a diff", async () => {
    const revised = await reviseRun(DEMO_RUN_ID, {
      comment: "Sharper headline",
      target_node: "copywriter",
    });
    expect(revised.version).toBe(2);
    expect(revised.run_id).not.toBe(DEMO_RUN_ID);

    const versions = await listVersions(DEMO_CAMPAIGN_ID);
    expect(versions.map((item) => item.version)).toEqual([1, 2]);
    expect(versions[1]?.parent_version_id).not.toBeNull();

    const pkg = await getVersion(DEMO_CAMPAIGN_ID, 2);
    expect(pkg.copy?.variants[0]?.headline).toBe("All-day shine, one drop");

    const diff = await getVersionDiff(DEMO_CAMPAIGN_ID, 1, 2);
    expect(diff.changes.map((change) => change.path)).toContain("copy.variants");

    const campaign = await getCampaign(DEMO_CAMPAIGN_ID);
    expect(campaign.latest_version).toBe(2);
    expect(campaign.active_run_id).toBe(revised.run_id);
  });
});
