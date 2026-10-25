import { Button, Stack, TextField } from "@mui/material";
import { useState } from "react";
import { notes } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { NoteTarget } from "../api/types";
import { useToast } from "../context/Toast";
import { formatDateTime } from "../domain/format";
import { useResource } from "../hooks/useResource";
import { EmptyState, ErrorNotice, RowSkeletons } from "./Feedback";

export function NotesPanel({ targetType, targetId, canWrite }: { targetType: NoteTarget; targetId: number; canWrite: boolean }) {
  const { notify } = useToast();
  const res = useResource(() => notes.list(targetType, targetId), [targetType, targetId]);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    setBusy(true);
    try {
      await notes.create(targetType, targetId, body);
      setBody("");
      await res.reload();
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "ノートを送信できませんでした。", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      {canWrite ? (
        <Stack spacing={1} sx={{ mb: 2 }}>
          <TextField label="ノートを書く" multiline minRows={2} value={body} onChange={(e) => setBody(e.target.value)} inputProps={{ maxLength: 5000 }} />
          <Button variant="contained" onClick={send} disabled={busy || !body.trim()} sx={{ alignSelf: "flex-end" }}>
            送信
          </Button>
        </Stack>
      ) : null}
      {res.error ? <ErrorNotice error={res.error} onRetry={res.reload} /> : null}
      {res.loading && !res.data ? <RowSkeletons count={2} /> : null}
      {res.data && res.data.results.length === 0 ? <EmptyState message="ノートはまだありません" /> : null}
      {res.data?.results.map((n) => (
        <div key={n.id} className="row" style={{ alignItems: "flex-start" }}>
          <div className="row__main" style={{ whiteSpace: "normal" }}>
            <div className="row__sub">
              {n.author_name || "—"} · <span className="num">{formatDateTime(n.created_at)}</span>
            </div>
            <div style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{n.body}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
