import { Alert } from "@mui/material";
import { useMemo } from "react";
import { quality, visual } from "../api/endpoints";
import type { Entity, QualityReport } from "../api/types";
import { formatDateTime, formatDiffRatio } from "../domain/format";
import { useResource } from "../hooks/useResource";
import { EmptyState, ErrorNotice, RowSkeletons } from "./Feedback";

interface Run {
  id: number;
  scannedAt: string;
  ingestedAt: string;
  total: number;
  rows: QualityReport[];
}

export function groupRuns(reports: QualityReport[]): Run[] {
  const map = new Map<number, Run>();
  for (const r of reports) {
    const run = map.get(r.scan_run_id) ?? { id: r.scan_run_id, scannedAt: r.scanned_at, ingestedAt: r.ingested_at, total: 0, rows: [] };
    run.total += r.defects;
    run.rows.push(r);
    map.set(r.scan_run_id, run);
  }
  return [...map.values()].sort((a, b) => b.scannedAt.localeCompare(a.scannedAt));
}

/** 品質(AssetDataInsightSuite)。取得日時を固定表示する(P9)。 */
export function QualityView({ reports, entityNames }: { reports: QualityReport[]; entityNames?: Map<number, string> }) {
  const runs = useMemo(() => groupRuns(reports), [reports]);
  if (runs.length === 0) return <EmptyState message="品質スキャンの結果はまだありません" />;
  const [latest, ...older] = runs;
  return (
    <div>
      <Alert severity="info" icon={false} sx={{ mb: 2 }}>
        スキャン実行 <span className="num">#{latest.id}</span> · 取得日時 <span className="num">{formatDateTime(latest.scannedAt)}</span>
        (取り込み <span className="num">{formatDateTime(latest.ingestedAt)}</span>)· 欠陥 <span className="num">{latest.total}</span> 件
      </Alert>
      {latest.rows.map((r) => (
        <div key={r.id} className="row">
          <div className="row__main">
            <div className="row__title num">{r.asset_path}</div>
            <div className="row__sub">
              {r.entity === null ? "対応するアセットなし(パスが一致しません)" : entityNames?.get(r.entity) ?? ""}
            </div>
          </div>
          <div className="row__end"><span className="num">{r.defects}</span>件</div>
        </div>
      ))}
      {older.length > 0 ? (
        <>
          <h3 style={{ fontSize: "0.9rem" }}>過去のスキャン</h3>
          {older.map((run) => (
            <div key={run.id} className="row">
              <div className="row__main"><span className="num">#{run.id}</span> · <span className="num">{formatDateTime(run.scannedAt)}</span></div>
              <div className="row__end"><span className="num">{run.total}</span>件</div>
            </div>
          ))}
        </>
      ) : null}
    </div>
  );
}

export function EntityQualityPanel({ entityId }: { entityId: number }) {
  const res = useResource(() => quality.list({ entity: entityId }), [entityId]);
  if (res.error) return <ErrorNotice error={res.error} onRetry={res.reload} />;
  if (!res.data) return <RowSkeletons count={3} />;
  return <QualityView reports={res.data.items} />;
}

export function ProjectQualityPanel({ projectCode, entities }: { projectCode: string; entities: Entity[] }) {
  const res = useResource(() => quality.list({ project: projectCode }), [projectCode]);
  const names = useMemo(() => new Map(entities.map((e) => [e.id, e.name])), [entities]);
  if (res.error) return <ErrorNotice error={res.error} onRetry={res.reload} />;
  if (!res.data) return <RowSkeletons count={3} />;
  return <QualityView reports={res.data.items} entityNames={names} />;
}

/** 画面差分(VisualRegressionQATool)。撮影条件と取得日時を固定表示する。 */
export function VisualPanel({ entityId }: { entityId: number }) {
  const res = useResource(() => visual.list({ entity: entityId }), [entityId]);
  if (res.error) return <ErrorNotice error={res.error} onRetry={res.reload} />;
  if (!res.data) return <RowSkeletons count={3} />;
  if (res.data.items.length === 0) return <EmptyState message="画面差分の結果はまだありません" />;
  return (
    <div>
      {res.data.items.map((r) => (
        <div key={r.id} className="row" style={{ alignItems: "flex-start" }}>
          <div className="row__main" style={{ whiteSpace: "normal" }}>
            <div>
              <strong className="num">v{String(r.version_number).padStart(3, "0")}</strong> ·{" "}
              <span className={`status status--${r.verdict === "pass" ? "done" : "rejected"}`}>{r.verdict_label}</span> · 差分率{" "}
              <span className="num">{formatDiffRatio(r.diff_ratio)}</span>
            </div>
            <div className="row__sub" style={{ whiteSpace: "normal" }}>
              取得日時 <span className="num">{formatDateTime(r.captured_at)}</span> · 実行 <span className="num">{r.run_id}</span>
            </div>
            <div className="row__sub num" style={{ whiteSpace: "normal", overflowWrap: "anywhere" }}>
              撮影条件: {Object.keys(r.conditions).length ? Object.entries(r.conditions).map(([k, v]) => `${k}=${String(v)}`).join(" / ") : "記録なし"}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
