import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResearchSchema } from "@/lib/schemas";
import { hairCarePackage } from "@/mocks/fixtures/hair-care";
import { ResearchCard } from "./ResearchCard";

const research = ResearchSchema.parse(hairCarePackage.research);

describe("ResearchCard", () => {
  it("renders segments, pain points, angles and safe source links", () => {
    render(<ResearchCard research={research} />);

    expect(screen.getByText("Busy professionals")).toBeInTheDocument();
    expect(screen.getByText("Humidity sufferers")).toBeInTheDocument();
    expect(screen.getByText("Frizz returns by midday")).toBeInTheDocument();
    expect(screen.getByText("Effortless shine")).toBeInTheDocument();

    const link = screen.getByRole("link", { name: "Hair-care category report" });
    expect(link).toHaveAttribute("href", "https://example.com/hair-care-report");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders non-http sources as text, never as a link", () => {
    render(
      <ResearchCard
        research={{
          ...research,
          sources: [{ title: "Unsafe source", url: "javascript:alert(1)" }],
        }}
      />,
    );

    expect(screen.getByText(/Unsafe source/)).toBeInTheDocument();
    expect(screen.getByText(/javascript:alert\(1\)/)).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("shows an empty state when research was not produced", () => {
    render(<ResearchCard research={null} />);

    expect(screen.getByText("Research not produced")).toBeInTheDocument();
  });
});
