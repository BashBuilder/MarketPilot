import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SkeletonBlock } from "./skeleton-block";

describe("SkeletonBlock", () => {
  it("exposes a status label for assistive technology", () => {
    render(<SkeletonBlock label="Loading campaign" />);

    expect(
      screen.getByRole("status", { name: "Loading campaign" }),
    ).toBeInTheDocument();
  });

  it("renders the requested number of lines", () => {
    const { container } = render(<SkeletonBlock lines={3} />);

    expect(container.querySelectorAll("[aria-hidden='true']")).toHaveLength(3);
  });
});
