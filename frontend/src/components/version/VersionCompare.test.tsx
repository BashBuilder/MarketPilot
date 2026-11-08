import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import type { VersionSummary } from "@/lib/schemas";
import { VersionCompare } from "./VersionCompare";

const server = setupServer();
const campaignId = "00000000-0000-4000-8000-000000000001";

const versions: VersionSummary[] = [
  {
    version: 2,
    parent_version_id: `${campaignId}-v1`,
    score: 88,
    created_at: "2026-01-02T10:05:00Z",
  },
  { version: 1, parent_version_id: null, score: 84, created_at: "2026-01-01T10:05:00Z" },
];

function useDiff(changes: unknown[]) {
  server.use(
    http.get("*/api/v1/campaigns/:id/versions/:from/diff/:to", () =>
      HttpResponse.json({ from: 1, to: 2, changes }),
    ),
  );
}

async function compare() {
  const user = userEvent.setup();
  render(<VersionCompare campaignId={campaignId} versions={versions} />);
  await user.click(screen.getByRole("button", { name: "Compare" }));
}

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("VersionCompare", () => {
  it("shows a copy change grouped by section with before and after", async () => {
    useDiff([
      {
        path: "copy.variants[0].headline",
        before: "Shine, without the fuss",
        after: "All-day shine, one drop",
      },
    ]);

    await compare();

    const copy = await screen.findByRole("region", { name: "Copy" });
    expect(within(copy).getByText("copy.variants[0].headline")).toBeInTheDocument();
    expect(within(copy).getByText("Before")).toBeInTheDocument();
    expect(within(copy).getByText("Shine, without the fuss")).toBeInTheDocument();
    expect(within(copy).getByText("After")).toBeInTheDocument();
    expect(within(copy).getByText("All-day shine, one drop")).toBeInTheDocument();
    expect(within(copy).getByText("Changed")).toBeInTheDocument();
  });

  it("shows an asset change grouped under assets", async () => {
    useDiff([{ path: "assets.assets[0].seed", before: 42, after: 99 }]);

    await compare();

    const assets = await screen.findByRole("region", { name: "Assets" });
    expect(within(assets).getByText("assets.assets[0].seed")).toBeInTheDocument();
    expect(within(assets).getByText("42")).toBeInTheDocument();
    expect(within(assets).getByText("99")).toBeInTheDocument();
  });

  it("says when there are no changes", async () => {
    useDiff([]);

    await compare();

    expect(
      await screen.findByText("No changes between versions 1 and 2."),
    ).toBeInTheDocument();
  });

  it("shows an error state when the diff request fails", async () => {
    server.use(
      http.get("*/api/v1/campaigns/:id/versions/:from/diff/:to", () =>
        HttpResponse.json(
          { error: { code: "server_error", message: "The diff is unavailable." } },
          { status: 500 },
        ),
      ),
    );

    await compare();

    expect(await screen.findByRole("alert")).toHaveTextContent("The diff is unavailable.");
  });
});
