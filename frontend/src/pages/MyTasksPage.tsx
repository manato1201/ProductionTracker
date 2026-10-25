import { Stack } from "@mui/material";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { projects, tasks } from "../api/endpoints";
import type { Task } from "../api/types";
import { EmptyState, ErrorNotice, RowSkeletons } from "../components/Feedback";
import { FilterChip } from "../components/FilterChip";
import { TaskDrawer } from "../components/TaskDrawer";
import { TaskRow } from "../components/TaskRow";
import { useResource } from "../hooks/useResource";
import { useTaskParam } from "../hooks/useTaskParam";

const VIEWS = {
  default: { title: "自分のタスク", query: { assignee: "me" as const, status: "todo,in_progress,review", ordering: "due" } },
  overdue: { title: "期限切れ(自分)", query: { assignee: "me" as const, overdue: true, ordering: "due" } },
  review: { title: "レビュー待ち", query: { status: "review", ordering: "due" } },
};

/** 期日順。期限切れは記号 + 文字でも示す。 */
export default function MyTasksPage() {
  const [params] = useSearchParams();
  const viewKey = (params.get("view") as keyof typeof VIEWS) in VIEWS ? (params.get("view") as keyof typeof VIEWS) : "default";
  const view = VIEWS[viewKey];
  const [withDone, setWithDone] = useState(false);
  const query = viewKey === "default" && withDone ? { assignee: "me" as const, ordering: "due" } : view.query;
  const res = useResource(() => tasks.list(query), [viewKey, withDone]);
  const [taskId, setTaskId] = useTaskParam();
  const [selected, setSelected] = useState<Task | null>(null);
  const projectCode = res.data?.items.find((t) => t.id === taskId)?.project_code ?? selected?.project_code;
  const project = useResource(async () => (projectCode ? projects.get(projectCode) : undefined), [projectCode]);

  return (
    <div>
      <h1 style={{ margin: "0 0 16px", fontSize: "1.4rem" }}>{view.title}</h1>
      {viewKey === "default" ? (
        <Stack direction="row" gap={1} sx={{ mb: 2 }}>
          <FilterChip label="完了も表示" pressed={withDone} onClick={() => setWithDone(!withDone)} />
        </Stack>
      ) : null}
      {res.error ? <ErrorNotice error={res.error} onRetry={res.reload} /> : null}
      {res.loading && !res.data ? <RowSkeletons /> : null}
      {res.data && res.data.items.length === 0 ? <EmptyState message={viewKey === "overdue" ? "期限切れのタスクはありません" : "タスクはありません"} /> : null}
      {res.data && res.data.items.length > 0 ? (
        <div className="panel" style={{ padding: 0 }}>
          <div className="muted" style={{ fontSize: "0.8125rem", padding: "8px 12px" }} aria-live="polite"><span className="num">{res.data.count}</span> 件</div>
          {res.data.items.map((t) => <TaskRow key={t.id} task={t} showProject onOpen={(x) => { setSelected(x); setTaskId(x.id); }} />)}
        </div>
      ) : null}
      <TaskDrawer taskId={taskId} project={project.data} onClose={() => setTaskId(null)} onChanged={() => void res.reload()} />
    </div>
  );
}
