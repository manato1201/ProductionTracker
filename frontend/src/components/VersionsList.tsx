import { Button, Stack } from "@mui/material";
import { versions } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { Project, Version, VersionStatus } from "../api/types";
import { useToast } from "../context/Toast";
import { formatDateTime } from "../domain/format";
import { EmptyState } from "./Feedback";
import { VersionStatusLabel } from "./StatusLabel";

function isShowableImage(url: string) {
  return /^https?:\/\//.test(url) || url.startsWith("/");
}

export function VersionsList({
  items, project, onChanged, showTask = false, onAdd,
}: {
  items: Version[]; project: Project | undefined; onChanged: () => void; showTask?: boolean; onAdd?: () => void;
}) {
  const { notify } = useToast();

  async function move(v: Version, to: VersionStatus) {
    try {
      await versions.transition(v.id, to);
      onChanged();
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "版の状態を変更できませんでした。", "error");
    }
  }

  if (items.length === 0) {
    return <EmptyState message="版はまだありません" actionLabel={onAdd ? "版を登録" : undefined} onAction={onAdd} />;
  }
  return (
    <div>
      {items.map((v) => (
        <div key={v.id} className="row" style={{ alignItems: "flex-start" }}>
          {v.thumbnail && isShowableImage(v.thumbnail) ? (
            <img src={v.thumbnail} alt={`v${String(v.number).padStart(3, "0")} のサムネイル`} width={72} height={48} loading="lazy" referrerPolicy="no-referrer" style={{ objectFit: "cover", borderRadius: 6 }} />
          ) : null}
          <div className="row__main" style={{ whiteSpace: "normal" }}>
            <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" useFlexGap>
              <strong className="num">v{String(v.number).padStart(3, "0")}</strong>
              <VersionStatusLabel status={v.status} />
              {showTask ? <span className="muted">{v.entity_name} / {v.task_name}</span> : null}
            </Stack>
            <div className="row__sub num" style={{ whiteSpace: "normal", overflowWrap: "anywhere" }}>{v.file_ref}</div>
            {v.comment ? <div style={{ overflowWrap: "anywhere" }}>{v.comment}</div> : null}
            <div className="row__sub">
              {v.created_by_name || "—"} · <span className="num">{formatDateTime(v.created_at)}</span>
            </div>
            {project?.can_write ? (
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                {v.status === "draft" ? <Button size="small" variant="outlined" onClick={() => move(v, "submitted")}>提出する</Button> : null}
                {v.status === "rejected" ? <Button size="small" variant="outlined" onClick={() => move(v, "draft")}>作り直す</Button> : null}
                {v.status === "submitted" && project.can_review ? (
                  <>
                    <Button size="small" variant="contained" onClick={() => move(v, "approved")}>承認</Button>
                    <Button size="small" variant="outlined" color="error" onClick={() => move(v, "rejected")}>却下</Button>
                  </>
                ) : null}
              </Stack>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
