import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import type { CampaignSummary, VersionSummary } from "@/lib/schemas";
import VersionsPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

const server = setupServer();
const campaignId = "00000000-0000-4000-8000-000000000001";

const campaign: CampaignSummary = {
  id: campaignId,
  idea: "Create a hair-care campaign for busy professionals.",
  status: "awaiting_approval",
  latest_version: 2,
  latest_score: 88,
  active_run_id: "11111111-1111-4111-8111-111111111111",
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-02T10:00:00Z",
};

const versions: VersionSummary[] = [
  {
    version: 1,
    parent_version_id: null,
    score: 84,
    created_at: "2026-01-01T10:05:00Z",
  },
  {
    version: 2,
    parent_version_id: `${campaignId}-v1`,
    score: 88,
    created_at: "2026-01-02T10:05:00Z",
  },
];

function useVersions(list: VersionSummary[] = versions) {
  server.use(
    http.get("*/api/v1/campaigns/:id", () => HttpResponse.json(campaign)),
    http.get("*/api/v1/campaigns/:id/versions", () => HttpResponse.json(list)),
  );
}

async function renderPage() {
  render(await VersionsPage({ params: Promise.resolve({ id: campaignId }) }));
}

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("VersionsPage", () => {
  it("lists versions newest first with status and review links", async () => {
    useVersions();

    await renderPage();

    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("Version 2");
    expect(items[1]).toHaveTextContent("Version 1");
    expect(items[0]).toHaveTextContent("Awaiting approval");
    expect(items[0]).toHaveTextContent("Revision");
    expect(items[1]).toHaveTextContent("Superseded");
    expect(screen.getByRole("link", { name: /Version 2/ })).toHaveAttribute(
      "href",
      `/campaigns/${campaignId}/versions/2`,
    );
  });

  it("renders an empty state when there are no versions", async () => {
    useVersions([]);

    await renderPage();

    expect(screen.getByText("No versions yet")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Compare versions" })).not.toBeInTheDocument();
  });

  it("renders an error state with a retry when versions fail to load", async () => {
    server.use(
      http.get("*/api/v1/campaigns/:id", () => HttpResponse.json(campaign)),
      http.get("*/api/v1/campaigns/:id/versions", () =>
        HttpResponse.json(
          { error: { code: "server_error", message: "Version history is unavailable." } },
          { status: 500 },
        ),
      ),
    );

    await renderPage();

    expect(screen.getByRole("alert")).toHaveTextContent("Version history is unavailable.");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });
});
