import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CopySchema } from "@/lib/schemas";
import { hairCarePackage } from "@/mocks/fixtures/hair-care";
import { CopyCard } from "./CopyCard";

const copy = CopySchema.parse(hairCarePackage.copy);

function groupFor(channel: string): HTMLElement {
  const heading = screen.getByRole("heading", { level: 3, name: channel });
  const group = heading.closest("div");
  if (!group) throw new Error(`No group container for ${channel}`);
  return group as HTMLElement;
}

describe("CopyCard", () => {
  it("groups variants by channel", () => {
    const withSecondInstagram = CopySchema.parse({
      variants: [
        ...copy.variants,
        {
          channel: "instagram",
          headline: "Second Instagram headline",
          description: "Another variation for the same channel.",
          cta: "See more",
        },
      ],
    });

    render(<CopyCard copy={withSecondInstagram} />);

    expect(within(groupFor("instagram")).getAllByRole("listitem")).toHaveLength(2);
    expect(within(groupFor("email")).getAllByRole("listitem")).toHaveLength(1);
    expect(screen.getByText("Second Instagram headline")).toBeInTheDocument();
    expect(screen.getByText("Claim your sample")).toBeInTheDocument();
  });

  it("shows an empty state when copy was not produced", () => {
    render(<CopyCard copy={null} />);

    expect(screen.getByText("Copy not produced")).toBeInTheDocument();
  });

  it("shows an empty state for an empty variant list", () => {
    render(<CopyCard copy={{ variants: [] }} />);

    expect(screen.getByText("No copy variants")).toBeInTheDocument();
  });
});
