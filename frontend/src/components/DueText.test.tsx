import { render, screen } from "@testing-library/react";
import { DueText } from "./DueText";

it("期限切れは文字でも示す", () => {
  render(<DueText due="2026-10-01" overdue />);
  expect(screen.getByText(/期限切れ/)).toBeInTheDocument();
  expect(screen.getByText("2026-10-01")).toHaveClass("num");
});

it("期日なし", () => {
  render(<DueText due={null} overdue={false} />);
  expect(screen.getByText("期日なし")).toBeInTheDocument();
});
