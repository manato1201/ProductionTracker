import { DndContext, DragOverlay, MouseSensor, TouchSensor, useDraggable, useDroppable, useSensor, useSensors, type DragEndEvent, type DragStartEvent } from "@dnd-kit/core";
import { Badge } from "@mui/material";
import { useState, type KeyboardEvent } from "react";
import type { Task, TaskStatus } from "../api/types";
import { adjacentStatus, TASK_STATUS_META, TASK_STATUSES } from "../domain/status";
import { DueText } from "./DueText";
import { CardSkeletons, EmptyState } from "./Feedback";
import { PriorityLabel } from "./StatusLabel";
import { StatusMenu } from "./StatusMenu";

interface BoardProps {
  tasks: Task[];
  loading: boolean;
  canWrite: boolean;
  /** 初回表示のスタッガーを出すか(1 回だけ) */
  intro: boolean;
  onOpen: (task: Task) => void;
  onMove: (task: Task, to: TaskStatus) => void;
  onAddTask?: () => void;
}

/**
 * かんばん。ドラッグ&ドロップは @dnd-kit/core(ポインタ + タッチ。キーボードは下記の代替操作)。
 * 遷移ルールは判断せず、ドロップ時は常に onMove(サーバーが 409/403 を返したら呼び出し側が戻す)。
 */
export function Board({ tasks, loading, canWrite, intro, onOpen, onMove, onAddTask }: BoardProps) {
  const [activeId, setActiveId] = useState<number | null>(null);
  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 6 } }), // クリックとドラッグを区別
    useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 8 } }), // 長押しでドラッグ(スクロールを妨げない)
  );
  const active = tasks.find((t) => t.id === activeId) ?? null;

  function dragEnd(e: DragEndEvent) {
    setActiveId(null);
    const task = tasks.find((t) => t.id === e.active.id);
    const to = e.over?.id as TaskStatus | undefined;
    if (task && to && TASK_STATUSES.includes(to)) onMove(task, to);
  }

  return (
    <DndContext sensors={sensors} onDragStart={(e: DragStartEvent) => setActiveId(Number(e.active.id))} onDragEnd={dragEnd} onDragCancel={() => setActiveId(null)}>
      <div className="board">
        {TASK_STATUSES.map((status) => (
          <Column key={status} status={status} tasks={tasks.filter((t) => t.status === status)} loading={loading} canWrite={canWrite} intro={intro} activeId={activeId} onOpen={onOpen} onMove={onMove} onAddTask={onAddTask} />
        ))}
      </div>
      <DragOverlay>{active ? <CardBody task={active} dragging /> : null}</DragOverlay>
    </DndContext>
  );
}

function Column({ status, tasks, loading, canWrite, intro, activeId, onOpen, onMove, onAddTask }: { status: TaskStatus; tasks: Task[]; loading: boolean; canWrite: boolean; intro: boolean; activeId: number | null; onOpen: BoardProps["onOpen"]; onMove: BoardProps["onMove"]; onAddTask?: () => void }) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const { label, Icon } = TASK_STATUS_META[status];
  return (
    <section ref={setNodeRef} className={`column${isOver ? " column--over" : ""}`} aria-label={`${label}の列`}>
      <header className="column__head">
        {/* 丸の色 + アイコン + 文字 + 件数(色だけにしない) */}
        <span className={`status status--${status}`}>
          <span aria-hidden style={{ width: 10, height: 10, borderRadius: "50%", background: "currentColor", display: "inline-block" }} />
          <Icon fontSize="small" aria-hidden />
          {label}
        </span>
        <span className="column__count">
          <Badge badgeContent={tasks.length} showZero color="default" max={999} sx={{ "& .MuiBadge-badge": { position: "static", transform: "none", fontFamily: "ui-monospace, monospace" } }} aria-label={`${tasks.length}件`} />
        </span>
      </header>
      <div className="column__cards">
        {loading && tasks.length === 0 ? <CardSkeletons count={2} /> : null}
        {!loading && tasks.length === 0 ? (
          <EmptyState message="タスクはありません" actionLabel={status === "todo" && canWrite && onAddTask ? "タスクを追加" : undefined} onAction={onAddTask} />
        ) : null}
        {tasks.map((task, i) => (
          <DraggableCard key={task.id} task={task} index={i} canWrite={canWrite} intro={intro} ghost={activeId === task.id} onOpen={onOpen} onMove={onMove} />
        ))}
      </div>
    </section>
  );
}

function DraggableCard({ task, index, canWrite, intro, ghost, onOpen, onMove }: { task: Task; index: number; canWrite: boolean; intro: boolean; ghost: boolean; onOpen: BoardProps["onOpen"]; onMove: BoardProps["onMove"] }) {
  const { setNodeRef, listeners } = useDraggable({ id: task.id, disabled: !canWrite });

  // キーボードの代替操作: Enter で詳細、Shift + ←/→ で隣の列へ(ドラッグに頼らない)
  function onKeyDown(e: KeyboardEvent<HTMLElement>) {
    if (e.target !== e.currentTarget) return;
    if (e.key === "Enter") onOpen(task);
    if (canWrite && e.shiftKey && (e.key === "ArrowRight" || e.key === "ArrowLeft")) {
      e.preventDefault();
      const to = adjacentStatus(task.status, e.key === "ArrowRight" ? 1 : -1);
      if (to) onMove(task, to);
    }
  }

  return (
    <article
      ref={setNodeRef}
      {...listeners}
      className={`card${ghost ? " card--ghost" : ""}${intro ? " card--stagger" : ""}`}
      style={intro ? ({ "--i": index } as React.CSSProperties) : undefined}
      tabIndex={0}
      aria-label={`${task.entity_name} / ${task.step_name}。Enter で詳細、Shift と左右の矢印キーで状態を変更`}
      onClick={() => onOpen(task)}
      onKeyDown={onKeyDown}
    >
      <CardBody task={task} />
      {canWrite ? (
        <span className="card__menu">
          <StatusMenu task={task} variant="icon" onSelect={(to) => onMove(task, to)} />
        </span>
      ) : null}
    </article>
  );
}

/** カードの中身。ドラッグ中のオーバーレイにも同じものを使う。 */
function CardBody({ task, dragging }: { task: Task; dragging?: boolean }) {
  return (
    <div className={dragging ? "card card--dragging" : undefined} style={dragging ? { width: "100%" } : undefined}>
      <div className="card__title">{task.step_name}</div>
      <div className="card__sub">{task.entity_name}</div>
      <div className="card__meta">
        <PriorityLabel priority={task.priority} />
        <span title="担当者">{task.assignee_name || "未割当"}</span>
        <DueText due={task.due} overdue={task.is_overdue} />
      </div>
    </div>
  );
}
