import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiError } from "../api/client";
import type { Task, TaskStatus } from "../api/types";
import { ToastProvider } from "../context/Toast";
import { useTaskTransition } from "./useTaskTransition";

const transition = vi.fn();
vi.mock("../api/endpoints", () => ({ tasks: { transition: (...args: unknown[]) => transition(...args) } }));

const NEXT: Record<TaskStatus, TaskStatus[]> = { todo: ["in_progress"], in_progress: ["review"], review: ["in_progress", "done"], done: ["in_progress"] };
function task(status: TaskStatus): Task {
  return {
    id: 1, entity: 1, entity_name: "木箱", project: 1, project_code: "DEMO", step: 1, step_name: "モデリング", status, status_label: "",
    priority: "normal", priority_label: "中", assignee: null, assignee_name: "", due: null, estimate_h: null, is_overdue: false,
    version_count: 1, next_statuses: NEXT[status], updated_at: "2026-11-04T00:00:00Z",
  };
}

const onApply = vi.fn();
const onRevert = vi.fn();
const onSuccess = vi.fn();

function Harness({ from, to }: { from: TaskStatus; to: TaskStatus }) {
  const { request, dialog } = useTaskTransition({ onApply, onRevert, onSuccess });
  return (
    <>
      <button onClick={() => request(task(from), to)}>移動</button>
      {dialog}
    </>
  );
}

const setup = (from: TaskStatus, to: TaskStatus) =>
  render(
    <ToastProvider>
      <Harness from={from} to={to} />
    </ToastProvider>,
  );

describe("useTaskTransition", () => {
  beforeEach(() => vi.clearAllMocks());

  it("戻り道が遷移表にある移動は、トーストの「元に戻す」で取り消せる", async () => {
    const user = userEvent.setup();
    transition.mockResolvedValueOnce(task("review"));
    setup("in_progress", "review");
    await user.click(screen.getByText("移動"));
    expect(await screen.findByText(/「木箱 \/ モデリング」を「.+」にしました/)).toBeInTheDocument();
    expect(transition).toHaveBeenLastCalledWith(1, "review");

    transition.mockResolvedValueOnce(task("in_progress"));
    await user.click(screen.getByRole("button", { name: "元に戻す" }));
    expect(transition).toHaveBeenLastCalledWith(1, "in_progress"); // 元の状態へ
    expect(await screen.findByText(/に戻しました/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "元に戻す" })).not.toBeInTheDocument(); // 取り消しの取り消しは出さない
    expect(onApply).toHaveBeenLastCalledWith(expect.objectContaining({ status: "review" }), "in_progress");
  });

  it("遷移表が戻り道を許さない移動(未着手 → 進行中)には、ボタンを出さない", async () => {
    const user = userEvent.setup();
    transition.mockResolvedValueOnce(task("in_progress"));
    setup("todo", "in_progress");
    await user.click(screen.getByText("移動"));
    expect(await screen.findByText(/にしました/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "元に戻す" })).not.toBeInTheDocument();
  });

  it("拒否されたら元の列へ戻し、「何が / なぜ / 次に」の 3 行を出す", async () => {
    const user = userEvent.setup();
    transition.mockRejectedValueOnce(new ApiError(409, "invalid_transition", "「未着手」から「完了」へは変更できません。"));
    setup("todo", "review");
    await user.click(screen.getByText("移動"));
    expect(await screen.findByText("状態を変更できませんでした。")).toBeInTheDocument();
    expect(screen.getByText("「未着手」から「完了」へは変更できません。")).toBeInTheDocument();
    expect(screen.getByText(/「状態を変更」のメニューで/)).toBeInTheDocument();
    expect(onRevert).toHaveBeenCalledTimes(1);
  });
});
