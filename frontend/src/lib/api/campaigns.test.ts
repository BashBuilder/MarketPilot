import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import {
  createCampaign,
  getCampaign,
  getVersion,
  getVersionDiff,
  listCampaigns,
  listVersions,
} from "./campaigns";

const server = setupServer();
const campaign = {
  id: "00000000-0000-4000-8000-000000000001",
  idea: "Hair-care campaign",
  status: "awaiting_approval",
  latest_version: 1,
  latest_score: 78,
  active_run_id: "run-1",
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-01T10:05:00Z",
};

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("campaign endpoints", () => {
  it("lists campaigns", async () => {
    server.use(http.get("*/api/v1/campaigns", () => HttpResponse.json([campaign])));

    await expect(listCampaigns()).resolves.toEqual([campaign]);
  });

  it("fetches one campaign", async () => {
    server.use(http.get(`*/api/v1/campaigns/${campaign.id}`, () => HttpResponse.json(campaign)));

    await expect(getCampaign(campaign.id)).resolves.toEqual(campaign);
  });

  it("creates a campaign with a validated idea", async () => {
    let received: unknown;
    server.use(
      http.post("*/api/v1/campaigns", async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ campaign_id: campaign.id, run_id: "run-1" }, { status: 201 });
      }),
    );

    await expect(createCampaign("  A hair-care brief  ")).resolves.toEqual({
      campaign_id: campaign.id,
      run_id: "run-1",
    });
    expect(received).toEqual({ idea: "A hair-care brief" });
  });

  it("rejects an over-long idea before calling the API", async () => {
    await expect(createCampaign("x".repeat(2001))).rejects.toThrow();
  });

  it("lists versions", async () => {
    server.use(
      http.get(`*/api/v1/campaigns/${campaign.id}/versions`, () =>
        HttpResponse.json([
          { version: 1, parent_version_id: null, score: 78, created_at: "2026-01-01T10:05:00Z" },
        ]),
      ),
    );

    const versions = await listVersions(campaign.id);
    expect(versions[0]?.version).toBe(1);
  });

  it("fetches a package and fills omitted sections with null", async () => {
    server.use(
      http.get(`*/api/v1/campaigns/${campaign.id}/versions/1`, () => HttpResponse.json({})),
    );

    const pkg = await getVersion(campaign.id, 1);
    expect(pkg.brief).toBeNull();
    expect(pkg.score).toBeNull();
  });

  it("fetches a version diff", async () => {
    const diff = { from: 1, to: 2, changes: [{ path: "copy.variants", before: 1, after: 2 }] };
    server.use(
      http.get(`*/api/v1/campaigns/${campaign.id}/versions/1/diff/2`, () =>
        HttpResponse.json(diff),
      ),
    );

    await expect(getVersionDiff(campaign.id, 1, 2)).resolves.toEqual(diff);
  });
});
