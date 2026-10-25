import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Task, TaskStatus } from "../api/types";
import { Board } from "./Board";

function task(id: number, status: TaskStatus, over: Partial<Task> = {}): Task {
  const next: Record<TaskStatus, TaskStatus[]> = { todo: ["in_progress"], in_progress: ["review"], review: ["in_progress", "done"], done: ["in_progress"] };
  return {
    id, entity: 1, entity_name: "木箱", project: 1, project_code: "DEMO", step: id, step_name: `工程${id}`,
    status, status_label: "", priority: "normal", priority_label: "中", assignee: null, assignee_name: "",
    due: null, estimate_h: null, is_overdue: false, version_count: 0, next_statuses: next[status], updated_at: "2026-10-25T00:00:00Z",
    ...over,
  };
}

const base = { loading: false, intro: false, onOpen: vi.fn(), onMove: vi.fn() };

describe("Board", () => {
  beforeEach(() => vi.clearAllMocks());

  it("状態ごとの列に分け、件数と空の列の案内を出す", () => {
    render(<Board {...base} canWrite tasks={[task(1, "todo"), task(2, "todo"), task(3, "done")]} />);
    const todo = screen.getByRole("region", { name: "未着手の列" });
    expect(within(todo).getAllByRole("article")).toHaveLength(2);
    expect(within(todo).getByLabelText("2件")).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "進行中の列" })).getByText("タスクはありません")).toBeInTheDocument();
  });

  it("カードに題名・副題(アセット名)・優先度・期日が出る", () => {
    render(<Board {...base} canWrite tasks={[task(1, "todo", { due: "2026-10-01", is_overdue: true, priority: "urgent", assignee_name: "alice" })]} />);
    const card = screen.getByRole("article");
    expect(within(card).getByText("工程1")).toBeInTheDocument();
    expect(within(card).getByText("木箱")).toBeInTheDocument();
    expect(within(card).getByText("緊急")).toBeInTheDocument();
    expect(within(card).getByText(/期限切れ/)).toBeInTheDocument();
    expect(within(card).getByText("alice")).toBeInTheDocument();
  });

  it("Shift + 右矢印で隣の列へ(キーボードの代替操作)", async () => {
    const user = userEvent.setup();
    const t = task(1, "in_progress");
    render(<Board {...base} canWrite tasks={[t]} />);
    screen.getByRole("article").focus();
    await user.keyboard("{Shift>}{ArrowRight}{/Shift}");
    expect(base.onMove).toHaveBeenCalledWith(t, "review");
    await user.keyboard("{Shift>}{ArrowLeft}{/Shift}");
    expect(base.onMove).toHaveBeenCalledWith(t, "todo"); // 列の並びで隣へ。可否の判断はサーバー(409)
  });

  it("「状態を変更」メニューから移動できる", async () => {
    const user = userEvent.setup();
    const t = task(1, "review");
    render(<Board {...base} canWrite tasks={[t]} />);
    await user.click(screen.getByRole("button", { name: /状態を変更/ }));
    expect(screen.getByRole("menuitem", { name: /進行中にする/ })).toBeInTheDocument();
    await user.click(screen.getByRole("menuitem", { name: /完了にする/ }));
    expect(base.onMove).toHaveBeenCalledWith(t, "done");
  });

  it("書き込み権限が無いと、メニューもショートカットも出ない", async () => {
    const user = userEvent.setup();
    render(<Board {...base} canWrite={false} tasks={[task(1, "todo")]} />);
    expect(screen.queryByRole("button", { name: /状態を変更/ })).not.toBeInTheDocument();
    screen.getByRole("article").focus();
    await user.keyboard("{Shift>}{ArrowRight}{/Shift}");
    expect(base.onMove).not.toHaveBeenCalled();
  });

  it("Enter で詳細を開く", async () => {
    const user = userEvent.setup();
    const t = task(1, "todo");
    render(<Board {...base} canWrite tasks={[t]} />);
    screen.getByRole("article").focus();
    await user.keyboard("{Enter}");
    expect(base.onOpen).toHaveBeenCalledWith(t);
  });

  it("読み込み中はスケルトンを出す", () => {
    render(<Board {...base} canWrite loading tasks={[]} />);
    expect(screen.getAllByLabelText("読み込み中").length).toBeGreaterThan(0);
  });
});
