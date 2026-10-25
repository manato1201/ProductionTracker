import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack } from "@mui/material";
import { useState, type FormEvent, type ReactNode } from "react";
import { ApiError } from "../api/client";

interface Props {
  open: boolean;
  title: string;
  submitLabel?: string;
  onClose: () => void;
  /** 失敗(ApiError)を投げるとダイアログ内に理由を出して開いたままにする。 */
  onSubmit: () => Promise<void>;
  children: ReactNode;
}

/** モーダル(01)の共通部品。送信中の二重送信防止とエラー表示を持つ。 */
export function FormDialog({ open, title, submitLabel = "保存", onClose, onSubmit, children }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(undefined);
    try {
      await onSubmit();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "保存に失敗しました。");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="sm" component="form" onSubmit={submit}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          {children}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={busy}>
          キャンセル
        </Button>
        <Button type="submit" variant="contained" disabled={busy}>
          {submitLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
