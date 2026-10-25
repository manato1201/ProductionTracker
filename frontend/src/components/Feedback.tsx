import InboxOutlinedIcon from "@mui/icons-material/InboxOutlined";
import { Alert, Button, Skeleton, Stack } from "@mui/material";
import type { ReactNode } from "react";
import type { ApiError } from "../api/client";

/** エンプティステート(24): 理由 + 次の操作。 */
export function EmptyState({ message, actionLabel, onAction }: { message: string; actionLabel?: string; onAction?: () => void }) {
  return (
    <Stack alignItems="center" spacing={1.5} sx={{ py: 4, color: "text.secondary", textAlign: "center" }}>
      <InboxOutlinedIcon aria-hidden />
      <div>{message}</div>
      {actionLabel && onAction ? (
        <Button size="small" variant="outlined" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </Stack>
  );
}

export function ErrorNotice({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  return (
    <Alert
      severity="error"
      action={onRetry ? <Button color="inherit" size="small" onClick={onRetry}>再読み込み</Button> : undefined}
    >
      {error.detail}
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
