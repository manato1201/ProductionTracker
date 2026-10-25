import ViewKanbanOutlinedIcon from "@mui/icons-material/ViewKanbanOutlined";
import { Breadcrumbs, Button, Stack } from "@mui/material";
import { Link as RouterLink, Outlet, useOutletContext, useParams } from "react-router-dom";
import { projects } from "../api/endpoints";
import type { Member, Project } from "../api/types";
import { ErrorNotice, RowSkeletons } from "../components/Feedback";
import { useResource } from "../hooks/useResource";

export interface ProjectContext {
  project: Project;
  members: Member[];
  reloadProject: () => Promise<void>;
}
export const useProject = () => useOutletContext<ProjectContext>();

/** `/projects/:code` 以下で共有するプロジェクトとメンバーを読み込む。 */
export default function ProjectLayout() {
  const { code = "" } = useParams();
  const project = useResource(() => projects.get(code), [code]);
  const members = useResource(async () => (project.data ? (await projects.members(project.data.id)).results : []), [project.data?.id]);

  if (project.error) return <ErrorNotice error={project.error} onRetry={project.reload} />;
  if (!project.data) return <RowSkeletons count={3} />;
  const p = project.data;

  return (
    <div>
      <Stack direction="row" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
        <div style={{ minWidth: 0 }}>
          <Breadcrumbs aria-label="現在地">
            <RouterLink to="/projects">プロジェクト</RouterLink>
            <RouterLink to={`/projects/${p.code}`}>{p.code}</RouterLink>
          </Breadcrumbs>
          <h1 style={{ margin: "4px 0 0", fontSize: "1.4rem", overflowWrap: "anywhere" }}>{p.name}</h1>
        </div>
        <Button component={RouterLink} to={`/projects/${p.code}/board`} variant="outlined" startIcon={<ViewKanbanOutlinedIcon />}>
          タスクボード
        </Button>
      </Stack>
      <Outlet context={{ project: p, members: members.data ?? [], reloadProject: project.reload } satisfies ProjectContext} />
    </div>
  );
}
