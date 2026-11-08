import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "./empty-state";

describe("EmptyState", () => {
  it("renders the title, description and action", () => {
    render(
      <EmptyState
        title="No campaigns yet"
        description="Create one to start the pipeline."
        action={<button type="button">Create campaign</button>}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "No campaigns yet" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Create one to start the pipeline."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create campaign" }),
    ).toBeInTheDocument();
  });

  it("uses the requested heading level", () => {
    render(<EmptyState title="Nothing here" headingLevel={3} />);

    expect(screen.getByRole("heading", { level: 3 })).toHaveTextContent(
      "Nothing here",
    );
  });
});
