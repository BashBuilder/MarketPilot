import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { delay, http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VersionApproval } from "./VersionApproval";

const { push, refresh } = vi.hoisted(() => ({ push: vi.fn(), refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
}));

const server = setupServer();
const runId = "11111111-1111-4111-8111-111111111111";
const campaignId = "00000000-0000-4000-8000-000000000001";

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  push.mockClear();
  refresh.mockClear();
});
afterAll(() => server.close());

function renderPanel() {
  render(<VersionApproval campaignId={campaignId} version={1} runId={runId} />);
}

describe("VersionApproval", () => {
  it("approves a version once and shows the approved state", async () => {
    let calls = 0;
    server.use(
      http.post(`*/api/v1/runs/${runId}/approve`, () => {
        calls += 1;
        return HttpResponse.json({ status: "completed", version: 1 });
      }),
    );
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: "Approve version" }));
    await user.click(screen.getByRole("button", { name: "Confirm approval" }));

    expect(await screen.findByText("Version 1 approved")).toBeInTheDocument();
    expect(calls).toBe(1);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(push).not.toHaveBeenCalled();
  });

  it("requests a revision and follows the continuation run", async () => {
    let received: unknown;
    server.use(
      http.post(`*/api/v1/runs/${runId}/revise`, async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ run_id: "run-2", version: 2 });
      }),
    );
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: "Request revision" }));
    await user.type(screen.getByLabelText("What should change?"), "Sharper headline");
    await user.selectOptions(screen.getByLabelText("Target agent (optional)"), "copywriter");
    await user.click(screen.getByRole("button", { name: "Confirm revision" }));

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith(`/campaigns/${campaignId}/run/run-2`);
    });
    expect(received).toEqual({ comment: "Sharper headline", target_node: "copywriter" });
    expect(refresh).not.toHaveBeenCalled();
  });

  it("shows an HTTP error and stays on the review page", async () => {
    server.use(
      http.post(`*/api/v1/runs/${runId}/approve`, () =>
        HttpResponse.json(
          {
            error: {
              code: "run_not_awaiting_approval",
              message: "This run is no longer awaiting approval.",
            },
          },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: "Approve version" }));
    await user.click(screen.getByRole("button", { name: "Confirm approval" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This run is no longer awaiting approval.",
    );
    expect(refresh).not.toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });

  it("sends one request when confirm is double clicked", async () => {
    let calls = 0;
    server.use(
      http.post(`*/api/v1/runs/${runId}/approve`, async () => {
        calls += 1;
        await delay(20);
        return HttpResponse.json({ status: "completed", version: 1 });
      }),
    );
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: "Approve version" }));
    const confirm = screen.getByRole("button", { name: "Confirm approval" });

    fireEvent.click(confirm);
    fireEvent.click(confirm);

    expect(await screen.findByText("Version 1 approved")).toBeInTheDocument();
    expect(calls).toBe(1);
  });
});
