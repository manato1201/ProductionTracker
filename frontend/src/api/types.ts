export type TaskStatus = "todo" | "in_progress" | "review" | "done";
export type Priority = "low" | "normal" | "high" | "urgent";
export type VersionStatus = "draft" | "submitted" | "approved" | "rejected";
export type Role = "reviewer" | "artist" | "viewer";

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface User {
  id: number;
  username: string;
  display_name: string;
  is_staff: boolean;
}

export interface TaskCounts {
  todo: number;
  in_progress: number;
  review: number;
  done: number;
  total: number;
}

export interface Project {
  id: number;
  code: string;
  name: string;
  start: string | null;
  due: string | null;
  task_counts: TaskCounts;
  progress: number;
  my_role: Role | null;
  can_write: boolean;
  can_review: boolean;
  created_at: string;
  updated_at: string;
}

export interface Member {
  user: number;
  username: string;
  display_name: string;
  role: Role;
  role_label: string;
}

export interface Entity {
  id: number;
  project: number;
  project_code: string;
  name: string;
  kind: "asset" | "shot";
  status: "active" | "on_hold" | "final";
  path: string;
  task_count: number;
  done_count: number;
}

export interface Step {
  id: number;
  code: string;
  name: string;
  order: number;
}

export interface Task {
  id: number;
  entity: number;
  entity_name: string;
  project: number;
  project_code: string;
  step: number;
  step_name: string;
  status: TaskStatus;
  status_label: string;
  priority: Priority;
  priority_label: string;
  assignee: number | null;
  assignee_name: string;
  due: string | null;
  estimate_h: number | null;
  is_overdue: boolean;
  version_count: number;
  next_statuses: TaskStatus[];
  updated_at: string;
}

export interface Version {
  id: number;
  task: number;
  task_name: string;
  entity: number;
  entity_name: string;
  project_code: string;
  number: number;
  status: VersionStatus;
  status_label: string;
  file_ref: string;
  thumbnail: string;
  comment: string;
  dcc: Record<string, unknown>;
  created_by_name: string;
  created_at: string;
}

export type NoteTarget = "entity" | "task" | "version";

export interface Note {
  id: number;
  target_type: NoteTarget;
  target_id: number;
  body: string;
  author_name: string;
  created_at: string;
}

export interface QualityReport {
  id: number;
  project_code: string;
  entity: number | null;
  scan_run_id: number;
  asset_path: string;
  defects: number;
  scanned_at: string;
  ingested_at: string;
}

export interface VisualResult {
  id: number;
  version: number;
  version_number: number;
  run_id: string;
  verdict: "pass" | "fail";
  verdict_label: string;
  diff_ratio: number;
  captured_at: string;
  conditions: Record<string, unknown>;
  ingested_at: string;
}
