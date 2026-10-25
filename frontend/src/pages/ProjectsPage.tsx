import AddIcon from "@mui/icons-material/Add";
import { Button, Stack } from "@mui/material";
import { useMemo, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { projects } from "../api/endpoints";
import type { Project } from "../api/types";
import { ProjectFormDialog } from "../components/Dialogs";
import { EmptyState, ErrorNotice, RowSkeletons } from "../components/Feedback";
import { FilterChip } from "../components/FilterChip";
import { formatDate, formatPercent, symbolOf } from "../domain/format";
import { useResource } from "../hooks/useResource";

type SortKey = "due" | "name" | "progress";
const SORTS: { key: SortKey; label: string }[] = [
  { key: "due", label: "期日順" },
  { key: "name", label: "名前順" },
  { key: "progress", label: "進捗順" },
];

function sortProjects(items: Project[], key: SortKey): Project[] {
  const copy = [...items];
  if (key === "name") copy.sort((a, b) => a.name.localeCompare(b.name, "ja"));
  if (key === "progress") copy.sort((a, b) => b.progress - a.progress);
  if (key === "due") copy.sort((a, b) => (a.due ?? "9999-12-31").localeCompare(b.due ?? "9999-12-31"));
  return copy;
}

export default function ProjectsPage() {
  const res = useResource(() => projects.list(), []);
  const [sort, setSort] = useState<SortKey>("due");
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  const items = useMemo(() => sortProjects(res.data?.items ?? [], sort), [res.data, sort]);

  return (
    <div>
      <Stack direction="row" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
        <h1 style={{ margin: 0, fontSize: "1.4rem" }}>プロジェクト</h1>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreating(true)}>新規作成</Button>
      </Stack>
      <Stack direction="row" gap={1} sx={{ mb: 2 }} role="group" aria-label="並べ替え">
        {SORTS.map((s) => (
          <FilterChip key={s.key} size="medium" label={s.label} pressed={sort === s.key} onClick={() => setSort(s.key)} />
        ))}
      </Stack>
      {res.error ? <ErrorNotice error={res.error} onRetry={res.reload} /> : null}
      {res.loading && !res.data ? <RowSkeletons /> : null}
      {res.data && items.length === 0 ? <EmptyState message="プロジェクトはありません" actionLabel="プロジェクトを作成" onAction={() => setCreating(true)} /> : null}
      {items.length > 0 ? (
        <div className="panel" style={{ padding: 0 }}>
          {items.map((p) => (
            <RouterLink key={p.id} to={`/projects/${p.code}`} className="row">
              <span className="symbol" aria-hidden>{symbolOf(p.code)}</span>
              <div className="row__main">
                <div className="row__title">{p.name}</div>
                <div className="row__sub"><span className="num">{p.code}</span> · 期日 <span className="num">{formatDate(p.due)}</span></div>
              </div>
              <div className="row__end">
                <span className="muted num" title={`完了 ${p.task_counts.done} / 全 ${p.task_counts.total}`}>{p.task_counts.done}/{p.task_counts.total}</span>
                <strong className="num" style={{ minWidth: 40, textAlign: "right" }}>{formatPercent(p.progress)}</strong>
              </div>
            </RouterLink>
          ))}
        </div>
      ) : null}
      <ProjectFormDialog open={creating} onClose={() => setCreating(false)} onCreated={(p) => navigate(`/projects/${p.code}`)} />
    </div>
  );
}
