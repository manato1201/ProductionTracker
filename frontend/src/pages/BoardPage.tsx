import AddIcon from "@mui/icons-material/Add";
import SearchIcon from "@mui/icons-material/Search";
import { Button, Chip, InputAdornment, Stack, TextField } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { entities, steps, tasks } from "../api/endpoints";
import type { Priority, Task } from "../api/types";
import { Board } from "../components/Board";
import { TaskFormDialog } from "../components/Dialogs";
import { ErrorNotice } from "../components/Feedback";
import { TaskDrawer } from "../components/TaskDrawer";
import { useAuth } from "../context/Auth";
import { PRIORITIES, PRIORITY_META } from "../domain/status";
import { useResource } from "../hooks/useResource";
import { useTaskParam } from "../hooks/useTaskParam";
import { useTaskTransition } from "../hooks/useTaskTransition";
import { useProject } from "./ProjectLayout";

type Assignee = "all" | "me" | "none";

export default function BoardPage() {
  const { project, members, reloadProject } = useProject();
  const { user } = useAuth();
  const [taskId, setTaskId] = useTaskParam();
  const res = useResource(() => tasks.list({ project: project.code }), [project.code]);
  const [assignee, setAssignee] = useState<Assignee>("all");
  const [priorities, setPriorities] = useState<Priority[]>([]);
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [q, setQ] = useState("");
  const [adding, setAdding] = useState(false);

  // 初回表示のスタッガーは 1 回だけ
  const [intro, setIntro] = useState(true);
  const introTimer = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (res.data && introTimer.current === undefined) introTimer.current = window.setTimeout(() => setIntro(false), 800);
  }, [res.data]);
  useEffect(() => () => window.clearTimeout(introTimer.current), []);

  const patchTask = useCallback(
    (id: number, patch: Partial<Task> | ((t: Task) => Task)) =>
      res.setData((d) => d && { ...d, items: d.items.map((t) => (t.id === id ? (typeof patch === "function" ? patch(t) : { ...t, ...patch }) : t)) }),
    [res.setData], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const transition = useTaskTransition({
    onApply: (task, to) => patchTask(task.id, { status: to }), // 先に動かす
    onRevert: (task) => patchTask(task.id, { status: task.status }), // 拒否されたら元の列へ戻す
    onSuccess: (updated) => {
      patchTask(updated.id, () => updated);
      void reloadProject();
    },
  });

  const all = res.data?.items ?? [];
  const filtered = useMemo(
    () =>
      all.filter((t) => {
        if (assignee === "me" && t.assignee !== user?.id) return false;
        if (assignee === "none" && t.assignee !== null) return false;
        if (priorities.length && !priorities.includes(t.priority)) return false;
        if (overdueOnly && !t.is_overdue) return false;
        if (q && !`${t.entity_name} ${t.step_name}`.toLowerCase().includes(q.toLowerCase())) return false;
        return true;
      }),
    [all, assignee, priorities, overdueOnly, q, user?.id],
  );
  const anyFilter = assignee !== "all" || priorities.length > 0 || overdueOnly || q !== "";

  // タスク追加(アセットはダイアログ内で選ぶ)
  const ents = useResource(() => entities.list(project.id), [project.id]);
  const stepList = useResource(() => steps.list(), []);

  return (
    <div>
      <Stack direction="row" gap={1} flexWrap="wrap" alignItems="center" sx={{ mb: 1 }}>
        <TextField size="small" placeholder="タスクを検索" value={q} onChange={(e) => setQ(e.target.value)} inputProps={{ "aria-label": "タスクを検索" }} InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> }} />
        {project.can_write ? <Button size="small" variant="contained" startIcon={<AddIcon />} onClick={() => setAdding(true)} disabled={!ents.data?.items.length}>タスクを追加</Button> : null}
      </Stack>
      <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mb: 2 }} role="group" aria-label="絞り込み">
        {(["all", "me", "none"] as const).map((a) => (
          <Chip key={a} size="small" clickable label={{ all: "担当: すべて", me: "担当: 自分", none: "担当: 未割当" }[a]} aria-pressed={assignee === a} color={assignee === a ? "primary" : "default"} variant={assignee === a ? "filled" : "outlined"} onClick={() => setAssignee(a)} />
        ))}
        {PRIORITIES.map((p) => (
          <Chip key={p} size="small" clickable label={`優先度: ${PRIORITY_META[p].label}`} aria-pressed={priorities.includes(p)} color={priorities.includes(p) ? "primary" : "default"} variant={priorities.includes(p) ? "filled" : "outlined"} onClick={() => setPriorities((cur) => (cur.includes(p) ? cur.filter((x) => x !== p) : [...cur, p]))} />
        ))}
        <Chip size="small" clickable label="期限切れ" aria-pressed={overdueOnly} color={overdueOnly ? "primary" : "default"} variant={overdueOnly ? "filled" : "outlined"} onClick={() => setOverdueOnly(!overdueOnly)} />
        {anyFilter ? <Chip size="small" label="条件をリセット" onClick={() => { setAssignee("all"); setPriorities([]); setOverdueOnly(false); setQ(""); }} /> : null}
      </Stack>
      <div className="muted" style={{ fontSize: "0.8125rem", marginBottom: 8 }} aria-live="polite">
        <span className="num">{filtered.length}</span> 件{anyFilter ? <> (全 <span className="num">{res.data?.count ?? 0}</span> 件中)</> : null}
        {res.data && res.data.count > all.length ? <> · 先頭の <span className="num">{all.length}</span> 件のみ表示</> : null}
      </div>
      {res.error ? <ErrorNotice error={res.error} onRetry={res.reload} /> : null}
      <Board
        tasks={filtered}
        loading={res.loading && !res.data}
        canWrite={project.can_write}
        intro={intro}
        onOpen={(t) => setTaskId(t.id)}
        onMove={transition.request}
        onAddTask={ents.data?.items.length ? () => setAdding(true) : undefined}
      />
      <TaskDrawer taskId={taskId} project={project} onClose={() => setTaskId(null)} onChanged={() => void res.reload()} />
      {transition.dialog}
      <TaskFormDialog
        open={adding}
        entities={ents.data?.items ?? []}
        usedStepIds={(entityId) => all.filter((t) => t.entity === entityId).map((t) => t.step)}
        steps={stepList.data?.results ?? []}
        members={members.filter((m) => m.role !== "viewer")}
        onClose={() => setAdding(false)}
        onCreated={() => { void res.reload(); void reloadProject(); }}
      />
    </div>
  );
}
