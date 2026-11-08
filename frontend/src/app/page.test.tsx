import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import type { CampaignSummary } from "@/lib/schemas";
import Home from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

const server = setupServer();

const newer: CampaignSummary = {
  id: "campaign-newer",
  idea: "A newer campaign idea",
  status: "awaiting_approval",
  latest_version: 2,
  latest_score: 88,
  active_run_id: "run-2",
  created_at: "2026-01-03T10:00:00Z",
  updated_at: "2026-01-04T10:00:00Z",
};

const older: CampaignSummary = {
  id: "campaign-older",
  idea: "An older campaign idea",
  status: "completed",
  latest_version: 1,
  latest_score: 84,
  active_run_id: null,
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-02T10:00:00Z",
};

function useCampaigns(campaigns: CampaignSummary[]) {
  server.use(http.get("*/api/v1/campaigns", () => HttpResponse.json(campaigns)));
}

async function renderPage() {
  render(await Home());
}

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("Home campaign list", () => {
  it("renders a populated campaign with status, score and overview link", async () => {
    useCampaigns([newer]);

    await renderPage();

    expect(screen.getByText("A newer campaign idea")).toBeInTheDocument();
    expect(screen.getByText("Awaiting approval")).toBeInTheDocument();
    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /A newer campaign idea/ })).toHaveAttribute(
      "href",
      "/campaigns/campaign-newer",
    );
  });

  it("orders campaigns newest first", async () => {
    useCampaigns([older, newer]);

    await renderPage();

    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("A newer campaign idea");
    expect(items[1]).toHaveTextContent("An older campaign idea");
  });

  it("renders an empty state linking to the new campaign form", async () => {
    useCampaigns([]);

    await renderPage();

    expect(screen.getByText("No campaigns yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create a campaign" })).toHaveAttribute(
      "href",
      "/campaigns/new",
    );
  });

  it("renders a retry error state when the list fails", async () => {
    server.use(
      http.get("*/api/v1/campaigns", () =>
        HttpResponse.json(
          { error: { code: "server_error", message: "Campaigns are unavailable." } },
          { status: 500 },
        ),
      ),
    );

    await renderPage();

    expect(screen.getByRole("alert")).toHaveTextContent("Campaigns are unavailable.");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });
});
