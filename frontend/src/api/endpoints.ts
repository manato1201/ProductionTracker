import { get, getAll, patch, post } from "./client";
import type {
  Entity,
  Member,
  Note,
  NoteTarget,
  Page,
  Priority,
  Project,
  QualityReport,
  Step,
  Task,
  TaskStatus,
  User,
  Version,
  VersionStatus,
  VisualResult,
} from "./types";

export const auth = {
  csrf: () => get<{ csrf: string }>("/auth/csrf/"),
  me: () => get<User>("/me/"),
  login: (username: string, password: string) => post<User>("/auth/login/", { username, password }),
  logout: () => post<void>("/auth/logout/"),
};

export const projects = {
  list: () => getAll<Project>("/projects/", { ordering: "-updated_at" }),
  get: (code: string) => get<Project>(`/projects/${encodeURIComponent(code)}/`),
  create: (data: { code: string; name: string; start?: string | null; due?: string | null }) =>
    post<Project>("/projects/", data),
  members: (id: number) => get<Page<Member>>(`/projects/${id}/members/`, { page_size: 200 }),
};

export const steps = { list: () => get<Page<Step>>("/steps/", { page_size: 200 }) };

export const entities = {
  list: (project: number | string) => getAll<Entity>("/entities/", { project, ordering: "name" }),
  get: (id: number) => get<Entity>(`/entities/${id}/`),
  create: (data: { project: number; name: string; path?: string }) => post<Entity>("/entities/", data),
};

export interface TaskQuery {
  project?: number | string;
  entity?: number;
  assignee?: "me" | number;
  status?: string;
  overdue?: boolean;
  q?: string;
  ordering?: string;
}

export const tasks = {
  list: (query: TaskQuery) => getAll<Task>("/tasks/", { ...query, overdue: query.overdue ? 1 : undefined }),
  get: (id: number) => get<Task>(`/tasks/${id}/`),
  create: (data: {
    entity: number;
    step: number;
    assignee?: number | null;
    due?: string | null;
    priority?: Priority;
    estimate_h?: number | null;
  }) => post<Task>("/tasks/", data),
  update: (id: number, data: Partial<{ assignee: number | null; due: string | null; priority: Priority; estimate_h: number | null }>) =>
    patch<Task>(`/tasks/${id}/`, data),
  transition: (id: number, to: TaskStatus) => post<Task>(`/tasks/${id}/transition/`, { to }),
};

export const versions = {
  list: (query: { task?: number; entity?: number; project?: string }) =>
    getAll<Version>("/versions/", { ...query, ordering: "-created_at" }),
  create: (data: { task: number; file_ref: string; comment?: string; thumbnail?: string; status?: VersionStatus }) =>
    post<Version>("/versions/", data),
  transition: (id: number, to: VersionStatus) => post<Version>(`/versions/${id}/transition/`, { to }),
};

export const notes = {
  list: (target_type: NoteTarget, target_id: number) => get<Page<Note>>("/notes/", { target_type, target_id, page_size: 200 }),
  create: (target_type: NoteTarget, target_id: number, body: string) => post<Note>("/notes/", { target_type, target_id, body }),
};

export const quality = {
  list: (query: { entity?: number; project?: string }) => getAll<QualityReport>("/quality-reports/", query),
};

export const visual = {
  list: (query: { entity?: number; version?: number }) => getAll<VisualResult>("/visual-results/", query),
};

export const debug = { sentry: () => get<void>("/_debug/sentry/") };
