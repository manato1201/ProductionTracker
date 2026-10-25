import AddIcon from "@mui/icons-material/Add";
import SearchIcon from "@mui/icons-material/Search";
import { Button, InputAdornment, Stack, Tab, Tabs, TextField } from "@mui/material";
import { useMemo, useState } from "react";
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";
import { entities, tasks, versions } from "../api/endpoints";
import type { Task, TaskStatus } from "../api/types";
import { EntityFormDialog } from "../components/Dialogs";
import { EmptyState, ErrorNotice, RowSkeletons, Section } from "../components/Feedback";
import { FilterChip } from "../components/FilterChip";
import { ProjectQualityPanel } from "../components/IntegrationPanels";
import { StackedBar } from "../components/StackedBar";
import { TaskDrawer } from "../components/TaskDrawer";
import { TaskRow } from "../components/TaskRow";
import { VersionsList } from "../components/VersionsList";
import { formatDate, formatPercent } from "../domain/format";
import { TASK_STATUS_META, TASK_STATUSES } from "../domain/status";
import { useResource } from "../hooks/useResource";
import { useTaskParam } from "../hooks/useTaskParam";
import { useProject } from "./ProjectLayout";

type Tab = "overview" | "tasks" | "versions" | "quality";
const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "概要" },
  { key: "tasks", label: "タスク" },
  { key: "versions", label: "版" },
  { key: "quality", label: "品質" },
];

export default function OverviewPage() {
  const { project, members, reloadProject } = useProject();
  const [params, setParams] = useSearchParams();
  const tab = (TABS.find((t) => t.key === params.get("tab"))?.key ?? "overview") as Tab;
  const [taskId, setTaskId] = useTaskParam();
  const navigate = useNavigate();
  const ents = useResource(() => entities.list(project.id), [project.id]);
  const [assetQuery, setAssetQuery] = useState("");
  const [adding, setAdding] = useState(false);
  // ドロワーでタスクが変わったら、タスク一覧(タブ)も読み直す。件数の変化だけを見ていると、状態の変更を取りこぼす。
  const [tasksRevision, setTasksRevision] = useState(0);

  const visibleEntities = useMemo(
    () => (ents.data?.items ?? []).filter((e) => e.name.toLowerCase().includes(assetQuery.toLowerCase())),
    [ents.data, assetQuery],
  );

  return (
    <div className="workspace">
      {/* 左: アセット一覧 */}
      <Section
        title="アセット"
        actions={project.can_write ? <Button size="small" startIcon={<AddIcon />} onClick={() => setAdding(true)}>追加</Button> : undefined}
      >
        <TextField
          size="small" fullWidth placeholder="アセットを検索" value={assetQuery} onChange={(e) => setAssetQuery(e.target.value)}
          inputProps={{ "aria-label": "アセットを検索" }}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> }}
        />
        {ents.error ? <ErrorNotice error={ents.error} onRetry={ents.reload} /> : null}
        {ents.loading && !ents.data ? <RowSkeletons count={3} /> : null}
        {ents.data && ents.data.items.length === 0 ? <EmptyState message="アセットはまだありません" actionLabel={project.can_write ? "アセットを追加" : undefined} onAction={() => setAdding(true)} /> : null}
        {ents.data && ents.data.items.length > 0 && visibleEntities.length === 0 ? <EmptyState message="該当するアセットはありません" /> : null}
        <div style={{ marginTop: 8 }}>
          {visibleEntities.map((e) => (
            <RouterLink key={e.id} to={`/projects/${project.code}/entities/${e.id}`} className="row">
              <div className="row__main">
                <div className="row__title">{e.name}</div>
                <div className="row__sub num">{e.path || "パス未設定"}</div>
              </div>
              <div className="row__end"><span className="num muted">{e.done_count}/{e.task_count}</span></div>
            </RouterLink>
          ))}
        </div>
      </Section>

      {/* 中央: タブ */}
      <div className="panel" style={{ padding: 0 }}>
        <Tabs value={tab} onChange={(_, v: Tab) => setParams((p) => { const n = new URLSearchParams(p); n.set("tab", v); n.delete("task"); return n; })} variant="scrollable" scrollButtons="auto" sx={{ borderBottom: 1, borderColor: "divider" }}>
          {TABS.map((t) => <Tab key={t.key} value={t.key} label={t.label} />)}
        </Tabs>
        <div style={{ padding: 16 }}>
          {tab === "overview" ? (
            <Stack spacing={2}>
              <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "6px 16px", margin: 0 }}>
                <dt className="muted">コード</dt><dd style={{ margin: 0 }} className="num">{project.code}</dd>
                <dt className="muted">開始日</dt><dd style={{ margin: 0 }} className="num">{formatDate(project.start)}</dd>
                <dt className="muted">期日</dt><dd style={{ margin: 0 }} className="num">{formatDate(project.due)}</dd>
                <dt className="muted">あなたの役割</dt><dd style={{ margin: 0 }}>{members.find((m) => m.role === project.my_role)?.role_label ?? (project.my_role ? project.my_role : "管理者")}</dd>
              </dl>
              <div>
                <h3 style={{ fontSize: "0.95rem", margin: "0 0 4px" }}>メンバー</h3>
                {members.map((m) => (
                  <div key={m.user} className="row"><div className="row__main"><div className="row__title">{m.display_name}</div></div><div className="row__end muted">{m.role_label}</div></div>
                ))}
                <div className="muted" style={{ fontSize: "0.8125rem" }}>メンバーの追加・変更は管理画面(/admin/)から行います。</div>
              </div>
            </Stack>
          ) : null}
          {tab === "tasks" ? <ProjectTasks code={project.code} onOpen={(t) => setTaskId(t.id)} refreshKey={tasksRevision} /> : null}
          {tab === "versions" ? <ProjectVersions /> : null}
          {tab === "quality" ? <ProjectQualityPanel projectCode={project.code} entities={ents.data?.items ?? []} /> : null}
        </div>
      </div>

      {/* 右: サマリ */}
      <Section title="サマリ">
        <div style={{ marginBottom: 12 }}>
          進捗 <strong className="num">{formatPercent(project.progress)}</strong>
          <span className="muted"> (完了 <span className="num">{project.task_counts.done}</span> / 全 <span className="num">{project.task_counts.total}</span>)</span>
        </div>
        <StackedBar counts={project.task_counts} />
      </Section>

      <TaskDrawer taskId={taskId} project={project} onClose={() => setTaskId(null)} onChanged={() => { void reloadProject(); setTasksRevision((n) => n + 1); }} />
      <EntityFormDialog open={adding} project={project} onClose={() => setAdding(false)} onCreated={(e) => { void ents.reload(); navigate(`/projects/${project.code}/entities/${e.id}`); }} />
    </div>
  );
}

const ORDERINGS = [
  { key: "due", label: "期限順" },
  { key: "-updated_at", label: "更新順" },
  { key: "status", label: "状態順" },
] as const;

function ProjectTasks({ code, onOpen, refreshKey }: { code: string; onOpen: (t: Task) => void; refreshKey: number }) {
  const [statuses, setStatuses] = useState<TaskStatus[]>([]);
  const [mine, setMine] = useState(false);
  const [overdue, setOverdue] = useState(false);
  const [q, setQ] = useState("");
  const [ordering, setOrdering] = useState<string>("due");
  const res = useResource(
    () => tasks.list({ project: code, status: statuses.join(","), assignee: mine ? "me" : undefined, overdue, q, ordering }),
    [code, statuses.join(","), mine, overdue, q, ordering, refreshKey],
  );
  const anyFilter = statuses.length > 0 || mine || overdue || q !== "";
  const toggle = (s: TaskStatus) => setStatuses((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]));

  return (
    <div>
      <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mb: 1 }} role="group" aria-label="絞り込み">
        {TASK_STATUSES.map((s) => (
          <FilterChip key={s} label={TASK_STATUS_META[s].label} pressed={statuses.includes(s)} onClick={() => toggle(s)} />
        ))}
        <FilterChip label="自分" pressed={mine} onClick={() => setMine(!mine)} />
        <FilterChip label="期限切れ" pressed={overdue} onClick={() => setOverdue(!overdue)} />
        {anyFilter ? <FilterChip label="条件をリセット" pressed={false} onClick={() => { setStatuses([]); setMine(false); setOverdue(false); setQ(""); }} /> : null}
      </Stack>
      <Stack direction="row" gap={1} flexWrap="wrap" alignItems="center" sx={{ mb: 1 }}>
        <TextField size="small" placeholder="タスクを検索" value={q} onChange={(e) => setQ(e.target.value)} inputProps={{ "aria-label": "タスクを検索" }} />
        <Stack direction="row" gap={0.5} role="group" aria-label="並べ替え">
          {ORDERINGS.map((o) => (
            <FilterChip key={o.key} label={o.label} pressed={ordering === o.key} onClick={() => setOrdering(o.key)} />
          ))}
        </Stack>
      </Stack>
      {res.error ? <ErrorNotice error={res.error} onRetry={res.reload} /> : null}
      {res.loading && !res.data ? <RowSkeletons /> : null}
      {res.data ? <div className="muted" style={{ fontSize: "0.8125rem", margin: "4px 0" }} aria-live="polite"><span className="num">{res.data.count}</span> 件</div> : null}
      {res.data && res.data.items.length === 0 ? <EmptyState message={anyFilter ? "条件に合うタスクはありません" : "タスクはありません"} /> : null}
      {res.data?.items.map((t) => <TaskRow key={t.id} task={t} onOpen={onOpen} />)}
    </div>
  );
}

function ProjectVersions() {
  const { project, reloadProject } = useProject();
  const res = useResource(() => versions.list({ project: project.code }), [project.code]);
  if (res.error) return <ErrorNotice error={res.error} onRetry={res.reload} />;
  if (!res.data) return <RowSkeletons />;
  return <VersionsList items={res.data.items} project={project} showTask onChanged={() => { void res.reload(); void reloadProject(); }} />;
}
