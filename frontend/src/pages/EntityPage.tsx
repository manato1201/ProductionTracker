import AddIcon from "@mui/icons-material/Add";
import { Button, Stack, Tab, Tabs } from "@mui/material";
import { useState } from "react";
import { Link as RouterLink, useParams, useSearchParams } from "react-router-dom";
import { entities, steps, tasks, versions } from "../api/endpoints";
import { TaskFormDialog } from "../components/Dialogs";
import { EmptyState, ErrorNotice, RowSkeletons } from "../components/Feedback";
import { EntityQualityPanel, VisualPanel } from "../components/IntegrationPanels";
import { NotesPanel } from "../components/NotesPanel";
import { TaskDrawer } from "../components/TaskDrawer";
import { TaskRow } from "../components/TaskRow";
import { VersionsList } from "../components/VersionsList";
import { useResource } from "../hooks/useResource";
import { useTaskParam } from "../hooks/useTaskParam";
import { useProject } from "./ProjectLayout";

const TABS = [
  { key: "tasks", label: "タスク" },
  { key: "versions", label: "版" },
  { key: "notes", label: "ノート" },
  { key: "quality", label: "品質" },
  { key: "visual", label: "画面差分" },
] as const;
type TabKey = (typeof TABS)[number]["key"];

export default function EntityPage() {
  const { project, members, reloadProject } = useProject();
  const id = Number(useParams().id);
  const [params, setParams] = useSearchParams();
  const tab = (TABS.find((t) => t.key === params.get("tab"))?.key ?? "tasks") as TabKey;
  const [taskId, setTaskId] = useTaskParam();
  const [adding, setAdding] = useState(false);

  const entity = useResource(() => entities.get(id), [id]);
  const taskList = useResource(() => tasks.list({ entity: id, ordering: "status" }), [id]);
  const versionList = useResource(() => versions.list({ entity: id }), [id]);
  const stepList = useResource(() => steps.list(), []);

  if (entity.error) return <ErrorNotice error={entity.error} onRetry={entity.reload} />;
  if (!entity.data) return <RowSkeletons count={3} />;
  const e = entity.data;
  const reloadAll = () => { void taskList.reload(); void versionList.reload(); void reloadProject(); };

  return (
    <div className="panel" style={{ padding: 0 }}>
      <div style={{ padding: 16 }}>
        <RouterLink to={`/projects/${project.code}`}>← {project.name}</RouterLink>
        <h2 style={{ margin: "8px 0 0", overflowWrap: "anywhere" }}>{e.name}</h2>
        <div className="muted num" style={{ overflowWrap: "anywhere" }}>{e.path || "パス未設定"}</div>
      </div>
      <Tabs value={tab} onChange={(_, v: TabKey) => setParams((p) => { const n = new URLSearchParams(p); n.set("tab", v); n.delete("task"); return n; })} variant="scrollable" scrollButtons="auto" sx={{ borderBottom: 1, borderColor: "divider" }}>
        {TABS.map((t) => <Tab key={t.key} value={t.key} label={t.label} />)}
      </Tabs>
      <div style={{ padding: 16 }}>
        {tab === "tasks" ? (
          <>
            {project.can_write ? (
              <Stack direction="row" justifyContent="flex-end" sx={{ mb: 1 }}>
                <Button size="small" startIcon={<AddIcon />} onClick={() => setAdding(true)}>タスクを追加</Button>
              </Stack>
            ) : null}
            {taskList.error ? <ErrorNotice error={taskList.error} onRetry={taskList.reload} /> : null}
            {taskList.loading && !taskList.data ? <RowSkeletons /> : null}
            {taskList.data && taskList.data.items.length === 0 ? <EmptyState message="タスクはありません" actionLabel={project.can_write ? "タスクを追加" : undefined} onAction={() => setAdding(true)} /> : null}
            {taskList.data?.items.map((t) => <TaskRow key={t.id} task={t} onOpen={(x) => setTaskId(x.id)} />)}
          </>
        ) : null}
        {tab === "versions" ? (
          versionList.error ? <ErrorNotice error={versionList.error} onRetry={versionList.reload} /> :
          !versionList.data ? <RowSkeletons /> :
          <VersionsList items={versionList.data.items} project={project} showTask onChanged={reloadAll} />
        ) : null}
        {tab === "notes" ? <NotesPanel targetType="entity" targetId={e.id} canWrite={project.can_write} /> : null}
        {tab === "quality" ? <EntityQualityPanel entityId={e.id} /> : null}
        {tab === "visual" ? <VisualPanel entityId={e.id} /> : null}
      </div>
      <TaskDrawer taskId={taskId} project={project} onClose={() => setTaskId(null)} onChanged={reloadAll} />
      <TaskFormDialog
        open={adding}
        entities={[e]}
        defaultEntityId={e.id}
        usedStepIds={() => (taskList.data?.items ?? []).map((t) => t.step)}
        steps={stepList.data?.results ?? []}
        members={members.filter((m) => m.role !== "viewer")}
        onClose={() => setAdding(false)}
        onCreated={reloadAll}
      />
    </div>
  );
}
