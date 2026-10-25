import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import EditNoteIcon from "@mui/icons-material/EditNote";
import SendIcon from "@mui/icons-material/Send";
import type { SvgIconComponent } from "@mui/icons-material";
import type { Priority, TaskStatus, VersionStatus } from "../api/types";
import { PRIORITY_META, TASK_STATUS_META, VERSION_STATUS_LABEL } from "../domain/status";

/** 状態は「色 + アイコン + 文字」(色を消しても区別できる)。 */
export function StatusLabel({ status }: { status: TaskStatus }) {
  const { label, Icon } = TASK_STATUS_META[status];
  return (
    <span className={`status status--${status}`}>
      <Icon fontSize="small" aria-hidden />
      {label}
    </span>
  );
}

export function PriorityLabel({ priority }: { priority: Priority }) {
  const { label, Icon } = PRIORITY_META[priority];
  return (
    <span className="status muted" title={`優先度: ${label}`}>
      <Icon fontSize="small" aria-hidden />
      <span className="visually-hidden">優先度: </span>
      {label}
    </span>
  );
}

const VERSION_META: Record<VersionStatus, { Icon: SvgIconComponent; cls: string }> = {
  draft: { Icon: EditNoteIcon, cls: "todo" },
  submitted: { Icon: SendIcon, cls: "review" },
  approved: { Icon: CheckCircleIcon, cls: "approved" },
  rejected: { Icon: CancelIcon, cls: "rejected" },
};

export function VersionStatusLabel({ status }: { status: VersionStatus }) {
  const { Icon, cls } = VERSION_META[status];
  return (
    <span className={`status status--${cls}`}>
      <Icon fontSize="small" aria-hidden />
      {VERSION_STATUS_LABEL[status]}
    </span>
  );
}
