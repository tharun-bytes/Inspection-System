import { labelFor } from "../components/SeverityBadge";
import SeverityBadge from "../components/SeverityBadge";
import { render, screen } from "@testing-library/react";

describe("SeverityBadge", () => {
  it.each([
    ["minor", "Minor"],
    ["major", "Major"],
    ["critical", "Critical"],
    ["passed", "Passed"],
    ["failed", "Failed"],
    ["review", "Needs review"],
    ["pending", "Pending"],
  ])("labels %s as %s", (value, expected) => {
    expect(labelFor(value)).toBe(expected);
    render(<SeverityBadge value={value} />);
    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  it("shows Unscored when there is no value", () => {
    expect(labelFor(null)).toBe("Unscored");
    render(<SeverityBadge value={null} />);
    expect(screen.getByText("Unscored")).toBeInTheDocument();
  });

  it("falls back to the raw value for unknown input", () => {
    expect(labelFor("weird")).toBe("weird");
  });
});
