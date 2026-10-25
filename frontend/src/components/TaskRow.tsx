import { Link as RouterLink } from "react-router-dom";
import type { Task } from "../api/types";
import { DueText } from "./DueText";
import { PriorityLabel, StatusLabel } from "./StatusLabel";

/** 一覧の行: 題名 + 副題(アセット名)+ 状態 + 優先度 + 期日。 */
export function TaskRow({ task, onOpen, showProject }: { task: Task; onOpen: (t: Task) => void; showProject?: boolean }) {
  return (
    <button type="button" className="row row--task" onClick={() => onOpen(task)}>
      <div className="row__main">
        <div className="row__title">{task.step_name}</div>
        <div className="row__sub">
          {showProject ? <>{task.project_code} / </> : null}
          {task.entity_name} · {task.assignee_name || "未割当"}
        </div>
      </div>
      <div className="row__end">
        <PriorityLabel priority={task.priority} />
        <StatusLabel status={task.status} />
        <DueText due={task.due} overdue={task.is_overdue} />
      </div>
    </button>
  );
}

export function EntityLink({ task }: { task: Task }) {
  return (
    <RouterLink to={`/projects/${task.project_code}/entities/${task.entity}`} onClick={(e) => e.stopPropagation()}>
      {task.entity_name}
    </RouterLink>
  );
}
