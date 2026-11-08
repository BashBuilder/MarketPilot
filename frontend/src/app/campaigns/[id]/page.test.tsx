import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import type { CampaignSummary } from "@/lib/schemas";
import CampaignOverviewPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

const server = setupServer();
const campaignId = "00000000-0000-4000-8000-000000000001";
const runId = "11111111-1111-4111-8111-111111111111";

const campaign: CampaignSummary = {
  id: campaignId,
  idea: "Create a hair-care campaign for busy professionals.",
  status: "awaiting_approval",
  latest_version: 2,
  latest_score: 88,
  active_run_id: runId,
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-02T10:00:00Z",
};

function useCampaign(value: CampaignSummary) {
  server.use(http.get("*/api/v1/campaigns/:id", () => HttpResponse.json(value)));
}

async function renderPage() {
  render(await CampaignOverviewPage({ params: Promise.resolve({ id: campaignId }) }));
}

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("CampaignOverviewPage", () => {
  it("shows the campaign, latest version summary and an active-run link", async () => {
    useCampaign(campaign);

    await renderPage();

    expect(screen.getByText(campaign.idea)).toBeInTheDocument();
    expect(screen.getByText("Awaiting approval")).toBeInTheDocument();
    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review latest version" })).toHaveAttribute(
      "href",
      `/campaigns/${campaignId}/versions/2`,
    );
    expect(screen.getByRole("link", { name: "Version history" })).toHaveAttribute(
      "href",
      `/campaigns/${campaignId}/versions`,
    );
    expect(screen.getByRole("link", { name: "Watch the live run" })).toHaveAttribute(
      "href",
      `/campaigns/${campaignId}/run/${runId}`,
    );
  });

  it("hides the live-run notice when no run is active", async () => {
    useCampaign({
      ...campaign,
      status: "completed",
      active_run_id: null,
    });

    await renderPage();

    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Watch the live run" })).not.toBeInTheDocument();
  });

  it("renders the not-found state for an unknown campaign", async () => {
    server.use(
      http.get("*/api/v1/campaigns/:id", () =>
        HttpResponse.json(
          { error: { code: "not_found", message: "Campaign not found" } },
          { status: 404 },
        ),
      ),
    );

    await renderPage();

    expect(screen.getByRole("alert")).toHaveTextContent("Campaign not found");
    expect(screen.getByRole("link", { name: "All campaigns" })).toHaveAttribute("href", "/");
  });
});
