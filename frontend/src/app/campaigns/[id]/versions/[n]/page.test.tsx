import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import {
  CampaignPackageSchema,
  ComplianceSchema,
  type CampaignPackage,
} from "@/lib/schemas";
import { demoCampaign, demoVersions } from "@/mocks/fixtures/campaigns";
import { hairCarePackage } from "@/mocks/fixtures/hair-care";
import VersionReviewPage from "./page";

const server = setupServer();

const baseCompliance = ComplianceSchema.parse(hairCarePackage.compliance);
const packageWithFailure = CampaignPackageSchema.parse({
  ...hairCarePackage,
  compliance: {
    items: [
      ...baseCompliance.items,
      {
        check: "No unverifiable claims",
        passed: false,
        reason: "The headline promises a result the copy cannot support.",
      },
    ],
  },
});

function usePackage(pkg: CampaignPackage) {
  server.use(
    http.get("*/api/v1/campaigns/:id", () => HttpResponse.json(demoCampaign)),
    http.get("*/api/v1/campaigns/:id/versions", () => HttpResponse.json(demoVersions)),
    http.get("*/api/v1/campaigns/:id/versions/:version", () => HttpResponse.json(pkg)),
  );
}

async function renderPage(version = "1") {
  const page = await VersionReviewPage({
    params: Promise.resolve({ id: demoCampaign.id, n: version }),
  });
  render(page);
}

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("VersionReviewPage", () => {
  it("renders the package and a failed compliance item", async () => {
    usePackage(packageWithFailure);

    await renderPage();

    expect(screen.getByRole("heading", { level: 1, name: "Version 1" })).toBeInTheDocument();
    expect(screen.getByText(/Lumen & Co\. hair-care serum/)).toBeInTheDocument();
    expect(screen.getByText("Busy professionals")).toBeInTheDocument();
    expect(screen.getByText("Shine, without the fuss")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /matte serum bottle/i })).toBeInTheDocument();
    expect(screen.getByText("Fail")).toBeInTheDocument();
    expect(
      screen.getByText("The headline promises a result the copy cannot support."),
    ).toBeInTheDocument();
    expect(screen.getByText("84")).toBeInTheDocument();
  });

  it("renders an empty state for every missing section", async () => {
    usePackage(CampaignPackageSchema.parse({}));

    await renderPage();

    expect(screen.getByText("Brief not produced")).toBeInTheDocument();
    expect(screen.getByText("Research not produced")).toBeInTheDocument();
    expect(screen.getByText("Copy not produced")).toBeInTheDocument();
    expect(screen.getByText("No images produced")).toBeInTheDocument();
    expect(screen.getByText("Compliance not produced")).toBeInTheDocument();
    expect(screen.getByText("Score not produced")).toBeInTheDocument();
  });

  it("rejects an invalid version number without calling the API", async () => {
    await renderPage("not-a-number");

    expect(screen.getByRole("alert")).toHaveTextContent("Version not found");
  });

  it("shows an error state when the API fails", async () => {
    server.use(
      http.get("*/api/v1/campaigns/:id", () => HttpResponse.json(demoCampaign)),
      http.get("*/api/v1/campaigns/:id/versions", () => HttpResponse.json(demoVersions)),
      http.get("*/api/v1/campaigns/:id/versions/:version", () =>
        HttpResponse.json(
          {
            error: {
              code: "server_error",
              message: "The version is temporarily unavailable.",
            },
          },
          { status: 500 },
        ),
      ),
    );

    await renderPage();

    expect(screen.getByRole("alert")).toHaveTextContent(
      "The version is temporarily unavailable.",
    );
  });
});
