import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it } from "vitest";
import { ApiError, checkHealth, getCampaign, getVersion, getVersionDiff, listCampaigns, listVersions } from "@/lib/api";
import { DEMO_CAMPAIGN_ID } from "./fixtures/campaigns";
import { handlers } from "./handlers";
import { resetMockStore } from "./store";

const server = setupServer(...handlers);

beforeAll(() => server.listen());
beforeEach(() => resetMockStore());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("mock handlers", () => {
  it("serves the seeded campaign and its version", async () => {
    const campaigns = await listCampaigns();
    expect(campaigns).toHaveLength(1);
    expect(campaigns[0]?.id).toBe(DEMO_CAMPAIGN_ID);

    const pkg = await getVersion(DEMO_CAMPAIGN_ID, 1);
    expect(pkg.brief?.product).toContain("hair-care");
    expect(pkg.compliance?.items).toHaveLength(3);
    expect(pkg.assets?.assets).toHaveLength(1);
    expect(pkg.score?.total).toBe(84);
  });

  it("lists versions oldest first", async () => {
    const versions = await listVersions(DEMO_CAMPAIGN_ID);
    expect(versions.map((item) => item.version)).toEqual([1]);
    expect(versions[0]?.parent_version_id).toBeNull();
  });

  it("returns the error envelope for an unknown campaign", async () => {
    const error = (await getCampaign("nope").catch((cause: unknown) => cause)) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(404);
    expect(error.code).toBe("not_found");
  });

  it("returns the error envelope for an unknown version", async () => {
    await expect(getVersion(DEMO_CAMPAIGN_ID, 9)).rejects.toMatchObject({ status: 404 });
  });

  it("has no diff before a revision", async () => {
    await expect(getVersionDiff(DEMO_CAMPAIGN_ID, 1, 2)).rejects.toMatchObject({ status: 404 });
  });

  it("answers the health check", async () => {
    await expect(checkHealth()).resolves.toBeUndefined();
  });
});
