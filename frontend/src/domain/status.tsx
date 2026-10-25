import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import HourglassTopIcon from "@mui/icons-material/HourglassTop";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import KeyboardDoubleArrowUpIcon from "@mui/icons-material/KeyboardDoubleArrowUp";
import PlayCircleOutlineIcon from "@mui/icons-material/PlayCircleOutline";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import RemoveIcon from "@mui/icons-material/Remove";
import type { SvgIconComponent } from "@mui/icons-material";
import type { Priority, TaskStatus, VersionStatus } from "../api/types";

// アイコンは @mui/icons-material の 1 セットに統一(決めごと P1)。
export const TASK_STATUS_META: Record<TaskStatus, { label: string; Icon: SvgIconComponent }> = {
  todo: { label: "未着手", Icon: RadioButtonUncheckedIcon },
  in_progress: { label: "進行中", Icon: PlayCircleOutlineIcon },
  review: { label: "レビュー待ち", Icon: HourglassTopIcon },
  done: { label: "完了", Icon: CheckCircleIcon },
};

/**
 * 状態の一覧。並び順 = かんばんの列順 = Shift+←/→ で動く隣。
 * META(Record<TaskStatus, ...>)から導くので、状態を足して META を書き忘れると型エラーになり、
 * 一覧への足し忘れは起きない。並び順は META の定義順。
 */
export const TASK_STATUSES = Object.keys(TASK_STATUS_META) as TaskStatus[];

export const PRIORITIES: Priority[] = ["urgent", "high", "normal", "low"];

export const PRIORITY_META: Record<Priority, { label: string; Icon: SvgIconComponent }> = {
  urgent: { label: "緊急", Icon: KeyboardDoubleArrowUpIcon },
  high: { label: "高", Icon: KeyboardArrowUpIcon },
  normal: { label: "中", Icon: RemoveIcon },
  low: { label: "低", Icon: KeyboardArrowDownIcon },
};

export const VERSION_STATUS_LABEL: Record<VersionStatus, string> = {
  draft: "作成中",
  submitted: "提出済み",
  approved: "承認",
  rejected: "却下",
};

/** 列を左右に動かすショートカット用: 隣の状態(列の並び順)。 */
export function adjacentStatus(status: TaskStatus, direction: 1 | -1): TaskStatus | null {
  const next = TASK_STATUSES[TASK_STATUSES.indexOf(status) + direction];
  return next ?? null;
}
