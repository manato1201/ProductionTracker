import { render, screen } from "@testing-library/react";
import { StackedBar } from "./StackedBar";

it("状態ごとの件数を文字でも出す(色だけに頼らない)", () => {
  render(<StackedBar counts={{ todo: 1, in_progress: 2, review: 0, done: 3, total: 6 }} />);
  expect(screen.getByRole("img")).toHaveAccessibleName("未着手 1件、進行中 2件、レビュー待ち 0件、完了 3件");
  expect(screen.getByText("レビュー待ち")).toBeInTheDocument();
  expect(screen.getByText("3")).toBeInTheDocument();
});

it("タスクが 0 件でも壊れない", () => {
  render(<StackedBar counts={{ todo: 0, in_progress: 0, review: 0, done: 0, total: 0 }} />);
  expect(screen.getByRole("img")).toBeInTheDocument();
});
