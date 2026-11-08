import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ComplianceSchema } from "@/lib/schemas";
import { hairCarePackage } from "@/mocks/fixtures/hair-care";
import { ComplianceReport } from "./ComplianceReport";

const compliance = ComplianceSchema.parse(hairCarePackage.compliance);

describe("ComplianceReport", () => {
  it("renders every check with a pass label and reason", () => {
    render(<ComplianceReport compliance={compliance} />);

    expect(screen.getAllByText("Pass")).toHaveLength(3);
    expect(screen.queryByText("Fail")).not.toBeInTheDocument();
    expect(screen.getByText("Copy avoids treatment language.")).toBeInTheDocument();
  });

  it("marks a failed check with a word, an icon and the reason", () => {
    const { container } = render(
      <ComplianceReport
        compliance={{
          items: [
            ...compliance.items,
            {
              check: "No unverifiable claims",
              passed: false,
              reason: "The headline promises a result the copy cannot support.",
            },
          ],
        }}
      />,
    );

    expect(screen.getByText("Fail")).toBeInTheDocument();
    expect(
      screen.getByText("The headline promises a result the copy cannot support."),
    ).toBeInTheDocument();
    expect(container.querySelector(".lucide-circle-x")).toBeInTheDocument();
  });

  it("shows an empty state when compliance was not produced", () => {
    render(<ComplianceReport compliance={null} />);

    expect(screen.getByText("Compliance not produced")).toBeInTheDocument();
  });
});
