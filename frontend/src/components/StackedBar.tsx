import type { TaskCounts, TaskStatus } from "../api/types";
import { TASK_STATUS_META, TASK_STATUSES } from "../domain/status";
import { StatusLabel } from "./StatusLabel";

/** 状態の積み上げバー + 凡例(色だけにせず、アイコン・文字・件数を併記)。 */
export function StackedBar({ counts }: { counts: TaskCounts }) {
  const total = counts.total;
  return (
    <div>
      <div
        className="stack-bar"
        role="img"
        aria-label={TASK_STATUSES.map((s) => `${TASK_STATUS_META[s].label} ${counts[s]}件`).join("、")}
      >
        {TASK_STATUSES.map((s: TaskStatus) =>
          counts[s] > 0 ? <div key={s} className={`stack-bar__seg stack-bar__seg--${s}`} style={{ width: `${(counts[s] / total) * 100}%` }} /> : null,
        )}
      </div>
      <ul style={{ listStyle: "none", padding: 0, margin: "12px 0 0", display: "grid", gap: 6 }}>
        {TASK_STATUSES.map((s) => (
          <li key={s} style={{ display: "flex", justifyContent: "space-between" }}>
            <StatusLabel status={s} />
            <span className="num">{counts[s]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
