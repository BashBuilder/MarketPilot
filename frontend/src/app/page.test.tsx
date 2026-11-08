import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("Home", () => {
  it("renders the hero, pipeline and primary action", () => {
    render(<Home />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "From idea to campaign package, reviewed by you.",
      }),
    ).toBeInTheDocument();

    expect(screen.getByRole("link", { name: "Start a campaign" })).toHaveAttribute(
      "href",
      "/campaigns/new",
    );
    expect(screen.getByRole("link", { name: "Design system" })).toHaveAttribute(
      "href",
      "/style",
    );

    const pipeline = screen.getByRole("region", { name: "The pipeline" });
    expect(within(pipeline).getAllByRole("listitem")).toHaveLength(8);
    expect(within(pipeline).getByText("Brief")).toBeInTheDocument();
    expect(within(pipeline).getByText("Supervisor")).toBeInTheDocument();
  });
});
