import { render, screen } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "vitest";
import { ScoreSchema } from "@/lib/schemas";
import { hairCarePackage } from "@/mocks/fixtures/hair-care";
import { ScoreBreakdown } from "./ScoreBreakdown";

const score = ScoreSchema.parse(hairCarePackage.score);

beforeAll(() => {
  // Recharts' ResponsiveContainer needs ResizeObserver, which jsdom does not ship.
  if (typeof globalThis.ResizeObserver === "undefined") {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    } as unknown as typeof ResizeObserver;
  }
});

describe("ScoreBreakdown", () => {
  it("shows the weighted total and every dimension justification", () => {
    render(<ScoreBreakdown score={score} />);

    expect(screen.getByText("84")).toBeInTheDocument();
    expect(screen.getByText("/ 100 weighted total")).toBeInTheDocument();
    expect(screen.getByText("Brief alignment")).toBeInTheDocument();
    expect(screen.getByText("Compliance risk")).toBeInTheDocument();
    expect(
      screen.getByText("Strong fit for the brief and the target audience."),
    ).toBeInTheDocument();
    expect(screen.getByText("No regulated claims in copy or imagery.")).toBeInTheDocument();
  });

  it("provides a text alternative for the chart", () => {
    render(<ScoreBreakdown score={score} />);

    expect(
      screen.getByRole("img", {
        name: /Brief alignment: 9 out of 10.*Weighted total 84 out of 100/,
      }),
    ).toBeInTheDocument();
  });

  it("shows an empty state when no score exists yet", () => {
    render(<ScoreBreakdown score={null} />);

    expect(screen.getByText("Score not produced")).toBeInTheDocument();
  });
});
