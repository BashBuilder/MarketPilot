import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ErrorState } from "./error-state";

describe("ErrorState", () => {
  it("announces the error as an alert", () => {
    render(<ErrorState message="The run failed to start." />);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Something went wrong");
    expect(alert).toHaveTextContent("The run failed to start.");
  });

  it("accepts a custom title, heading level and action", () => {
    render(
      <ErrorState
        title="Invalid version"
        message="Version 7 does not exist."
        headingLevel={3}
        action={<a href="/campaigns">Back to campaigns</a>}
      />,
    );

    expect(
      screen.getByRole("heading", { level: 3, name: "Invalid version" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Back to campaigns" }),
    ).toBeInTheDocument();
  });
});
