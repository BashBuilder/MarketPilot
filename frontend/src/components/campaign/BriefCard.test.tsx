import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BriefSchema } from "@/lib/schemas";
import { hairCarePackage } from "@/mocks/fixtures/hair-care";
import { BriefCard } from "./BriefCard";

const brief = BriefSchema.parse(hairCarePackage.brief);

describe("BriefCard", () => {
  it("renders every brief field from the package", () => {
    render(<BriefCard brief={brief} />);

    expect(screen.getByRole("heading", { level: 2, name: "Brief" })).toBeInTheDocument();
    expect(screen.getByText(brief.product)).toBeInTheDocument();
    expect(screen.getByText(brief.goal)).toBeInTheDocument();
    expect(screen.getByText(brief.audience)).toBeInTheDocument();
    expect(screen.getByText(brief.tone)).toBeInTheDocument();
    expect(screen.getByText("instagram")).toBeInTheDocument();
    expect(screen.getByText("No medical or treatment claims")).toBeInTheDocument();
  });

  it("shows an empty state when the brief was not produced", () => {
    render(<BriefCard brief={null} />);

    expect(screen.getByText("Brief not produced")).toBeInTheDocument();
  });

  it("handles empty channel and constraint lists", () => {
    render(<BriefCard brief={{ ...brief, channels: [], constraints: [] }} />);

    expect(screen.getByText("No channels listed.")).toBeInTheDocument();
    expect(screen.getByText("No constraints listed.")).toBeInTheDocument();
  });
});
