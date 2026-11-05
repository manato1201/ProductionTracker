import InboxOutlinedIcon from "@mui/icons-material/InboxOutlined";
import { Alert, Button, Skeleton, Stack } from "@mui/material";
import type { ReactNode } from "react";
import type { ApiError } from "../api/client";
import { explainError } from "../domain/errorGuide";

/** エンプティステート(24): 理由 + 次の操作(ボタン `actionLabel`、置けないときは説明 `hint`)。 */
export function EmptyState({
  message, hint, actionLabel, onAction, motif,
}: {
  message: string;
  /** 押せるボタンを置けないときの、次の一手の説明(1 文)。 */
  hint?: string;
  actionLabel?: string; onAction?: () => void;
  /** 飾り(ASCII モチーフなど)。指定すると既定のアイコンの代わりに出す */
  motif?: ReactNode;
}) {
  return (
    <Stack alignItems="center" spacing={1.5} sx={{ py: 4, color: "text.secondary", textAlign: "center" }}>
      {motif ?? <InboxOutlinedIcon aria-hidden />}
      <div>{message}</div>
      {hint ? <div style={{ fontSize: "0.8125rem" }}>{hint}</div> : null}
      {actionLabel && onAction ? (
        <Button size="small" variant="outlined" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </Stack>
  );
}

/** エラーの表示。「何が起きた / なぜ / 次にどうする」の 3 行(domain/errorGuide.ts)。 */
export function ErrorNotice({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  const guide = explainError(error);
  return (
    <Alert
      severity="error"
      action={onRetry ? <Button color="inherit" size="small" onClick={onRetry}>再読み込み</Button> : undefined}
    >
      <strong>{guide.what}</strong>
      {guide.why && guide.why !== guide.what ? <div>{guide.why}</div> : null}
      <div>{guide.next}</div>
    </Alert>
  );
}

/** スケルトン(21): 本物のカード/行と同じ形の灰色の枠。 */
export function CardSkeletons({ count = 3 }: { count?: number }) {
  return (
    <Stack spacing={1} aria-busy="true" aria-label="読み込み中">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} variant="rounded" height={84} animation="wave" />
      ))}
    </Stack>
  );
}

export function RowSkeletons({ count = 4 }: { count?: number }) {
  return (
    <Stack spacing={0.5} aria-busy="true" aria-label="読み込み中">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} variant="rounded" height={56} animation="wave" />
      ))}
    </Stack>
  );
}

export function Section({ title, actions, children }: { title: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section className="panel" aria-label={title}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1, gap: 1, flexWrap: "wrap" }}>
        <h2 style={{ margin: 0, fontSize: "1rem" }}>{title}</h2>
        {actions}
      </Stack>
      {children}
    </section>
  );
}
