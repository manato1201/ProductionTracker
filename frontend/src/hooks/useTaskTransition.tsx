import { useCallback, useState } from "react";
import { tasks } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { Task, TaskStatus } from "../api/types";
import { ConfirmDoneDialog } from "../components/Dialogs";
import { useToast } from "../context/Toast";
import { TASK_STATUS_META } from "../domain/status";

interface Options {
  /** 送信前に画面を先に動かす(かんばん用)。失敗したら onRevert で戻す。 */
  onApply?: (task: Task, to: TaskStatus) => void;
  onRevert?: (task: Task) => void;
  onSuccess: (updated: Task) => void;
}

/**
 * 状態変更の共通処理。遷移ルールはサーバーが判断し、ここは結果(成功/拒否の理由)を
 * トーストで表示するだけ。「完了」にする前は確認モーダルを挟む。
 */
export function useTaskTransition({ onApply, onRevert, onSuccess }: Options) {
  const { notify } = useToast();
  const [pending, setPending] = useState<Task | null>(null);

  const run = useCallback(
    async (task: Task, to: TaskStatus) => {
      onApply?.(task, to);
      try {
        const updated = await tasks.transition(task.id, to);
        onSuccess(updated);
        notify(`「${task.entity_name} / ${task.step_name}」を「${TASK_STATUS_META[to].label}」にしました。`, "success");
      } catch (e) {
        onRevert?.(task);
        notify(e instanceof ApiError ? e.detail : "状態を変更できませんでした。", "error");
      }
    },
    [notify, onApply, onRevert, onSuccess],
  );

  const request = useCallback(
    (task: Task, to: TaskStatus) => {
      if (task.status === to) return;
      if (to === "done") setPending(task);
      else void run(task, to);
    },
    [run],
  );

  const dialog = (
    <ConfirmDoneDialog
      task={pending}
      onCancel={() => setPending(null)}
      onConfirm={() => {
        const task = pending;
        setPending(null);
        if (task) void run(task, "done");
      }}
    />
  );

  return { request, dialog };
}
