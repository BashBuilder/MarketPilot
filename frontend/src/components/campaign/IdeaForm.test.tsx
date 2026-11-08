import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MAX_IDEA_LENGTH } from "@/lib/schemas";
import { EXAMPLE_PROMPTS } from "./example-prompts";
import { IdeaForm } from "./IdeaForm";

const HAIR_CARE = EXAMPLE_PROMPTS[0]?.idea ?? "";

describe("IdeaForm", () => {
  it("shows a clear validation error for an empty idea", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<IdeaForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: "Create campaign" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Enter a campaign idea");
    expect(screen.getByLabelText("Campaign idea")).toHaveAttribute("aria-invalid", "true");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejects an idea longer than the limit", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<IdeaForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Campaign idea"), {
      target: { value: "x".repeat(MAX_IDEA_LENGTH + 1) },
    });
    await user.click(screen.getByRole("button", { name: "Create campaign" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      `${MAX_IDEA_LENGTH} characters or fewer`,
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("fills the textarea from a clickable example prompt", async () => {
    const user = userEvent.setup();
    render(<IdeaForm onSubmit={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Hair care" }));

    expect(screen.getByLabelText("Campaign idea")).toHaveValue(HAIR_CARE);
  });

  it("disables submission while the request is in flight", async () => {
    let resolveSubmit: () => void = () => undefined;
    const onSubmit = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveSubmit = resolve;
        }),
    );
    const user = userEvent.setup();
    render(<IdeaForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Campaign idea"), "A hair-care campaign");
    const button = screen.getByRole("button", { name: "Create campaign" });
    await user.click(button);

    expect(onSubmit).toHaveBeenCalledWith("A hair-care campaign");
    expect(button).toBeDisabled();
    expect(screen.getByRole("button", { name: "Creating campaign…" })).toBeDisabled();

    await act(async () => {
      resolveSubmit();
    });
    expect(button).toBeEnabled();
  });
});
