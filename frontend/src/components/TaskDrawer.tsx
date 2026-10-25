import CloseIcon from "@mui/icons-material/Close";
import { Drawer, IconButton, Stack, Tab, Tabs } from "@mui/material";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import { tasks, versions } from "../api/endpoints";
import type { Project, Task } from "../api/types";
import { useTaskTransition } from "../hooks/useTaskTransition";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../domain/format";
import { VersionFormDialog } from "./Dialogs";
import { DueText } from "./DueText";
import { CardSkeletons, ErrorNotice } from "./Feedback";
import { EntityQualityPanel } from "./IntegrationPanels";
import { NotesPanel } from "./NotesPanel";
import { PriorityLabel, StatusLabel } from "./StatusLabel";
import { StatusMenu } from "./StatusMenu";
import { VersionsList } from "./VersionsList";

interface Props {
  taskId: number | null;
  project: Project | undefined;
  onClose: () => void;
  /** タスクが変わったとき(一覧の再読込用) */
  onChanged: () => void;
}

/** ドロワー(02): カードをクリックすると右からタスクの詳細(版・ノート・品質)。 */
export function TaskDrawer({ taskId, project, onClose, onChanged }: Props) {
  return (
    <Drawer anchor="right" open={taskId !== null} onClose={onClose} slotProps={{ paper: { sx: { width: "min(520px, 100vw)" } } }} sx={{ zIndex: (t) => t.zIndex.modal }}>
      {taskId !== null ? <DrawerBody key={taskId} taskId={taskId} project={project} onClose={onClose} onChanged={onChanged} /> : null}
    </Drawer>
  );
}

function DrawerBody({ taskId, project, onClose, onChanged }: Omit<Props, "taskId"> & { taskId: number }) {
  const task = useResource(() => tasks.get(taskId), [taskId]);
  const vers = useResource(() => versions.list({ task: taskId }), [taskId]);
  const [tab, setTab] = useState<"versions" | "notes" | "quality">("versions");
  const [adding, setAdding] = useState(false);

  const transition = useTaskTransition({
    onSuccess: (updated) => {
      task.setData(() => updated);
      onChanged();
    },
  });

  const t: Task | undefined = task.data;
  return (
    <Stack sx={{ p: 2, minWidth: 0 }} spacing={2}>
      <Stack direction="row" alignItems="flex-start" justifyContent="space-between" gap={1}>
        <div style={{ minWidth: 0 }}>
          <h2 style={{ margin: 0, fontSize: "1.15rem", overflowWrap: "anywhere" }}>{t ? t.step_name : "タスク"}</h2>
          {t ? (
            <div className="muted">
              <RouterLink to={`/projects/${t.project_code}/entities/${t.entity}`}>{t.entity_name}</RouterLink> · {t.project_code}
            </div>
          ) : null}
        </div>
        <IconButton aria-label="閉じる" onClick={onClose}><CloseIcon /></IconButton>
      </Stack>

      {task.error ? <ErrorNotice error={task.error} onRetry={task.reload} /> : null}
      {!t && task.loading ? <CardSkeletons count={2} /> : null}
      {t ? (
        <>
          <Stack direction="row" gap={2} alignItems="center" flexWrap="wrap">
            <StatusLabel status={t.status} />
            <PriorityLabel priority={t.priority} />
            <DueText due={t.due} overdue={t.is_overdue} />
            {project?.can_write ? <StatusMenu task={t} variant="button" onSelect={(to) => transition.request(t, to)} /> : null}
          </Stack>
          <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 16px", margin: 0 }}>
            <dt className="muted">担当者</dt><dd style={{ margin: 0 }}>{t.assignee_name || "未割当"}</dd>
            <dt className="muted">見積</dt><dd style={{ margin: 0 }} className="num">{t.estimate_h ?? "—"} 時間</dd>
            <dt className="muted">更新</dt><dd style={{ margin: 0 }} className="num">{formatDate(t.updated_at)}</dd>
          </dl>

          <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
            <Tab value="versions" label={`版 (${t.version_count})`} />
            <Tab value="notes" label="ノート" />
            <Tab value="quality" label="品質" />
          </Tabs>
          {tab === "versions" ? (
            vers.error ? <ErrorNotice error={vers.error} onRetry={vers.reload} /> : (
              <VersionsList
                items={vers.data?.items ?? []}
                project={project}
                onChanged={() => { void vers.reload(); void task.reload(); onChanged(); }}
                onAdd={project?.can_write ? () => setAdding(true) : undefined}
              />
            )
          ) : null}
          {tab === "versions" && project?.can_write && (vers.data?.items.length ?? 0) > 0 ? (
            <button type="button" className="row" style={{ justifyContent: "center", border: "1px dashed var(--pt-border)", borderRadius: 8 }} onClick={() => setAdding(true)}>
              ＋ 版を登録
            </button>
          ) : null}
          {tab === "notes" ? <NotesPanel targetType="task" targetId={t.id} canWrite={!!project?.can_write} /> : null}
          {tab === "quality" ? <EntityQualityPanel entityId={t.entity} /> : null}
          <VersionFormDialog
            open={adding}
            task={t}
            onClose={() => setAdding(false)}
            onCreated={() => { void vers.reload(); void task.reload(); onChanged(); }}
          />
        </>
      ) : null}
      {transition.dialog}
    </Stack>
  );
}
