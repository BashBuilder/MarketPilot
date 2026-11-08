import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import NewCampaignPage from "./page";

const { push } = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  push.mockClear();
});
afterAll(() => server.close());

async function submitIdea() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Campaign idea"), "A hair-care campaign");
  await user.click(screen.getByRole("button", { name: "Create campaign" }));
}

describe("NewCampaignPage", () => {
  it("creates a campaign and routes to its run", async () => {
    server.use(
      http.post("*/api/v1/campaigns", () =>
        HttpResponse.json({ campaign_id: "campaign-1", run_id: "run-1" }, { status: 201 }),
      ),
    );

    render(<NewCampaignPage />);
    await submitIdea();

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith("/campaigns/campaign-1/run/run-1");
    });
  });

  it("shows the API error without navigating", async () => {
    server.use(
      http.post("*/api/v1/campaigns", () =>
        HttpResponse.json(
          {
            error: {
              code: "rate_limited",
              message: "Too many runs are active. Try again shortly.",
            },
          },
          { status: 429 },
        ),
      ),
    );

    render(<NewCampaignPage />);
    await submitIdea();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Too many runs are active. Try again shortly.",
    );
    expect(push).not.toHaveBeenCalled();
  });
});
