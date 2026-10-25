import { Alert, Button, Stack } from "@mui/material";
import { useState } from "react";
import { debug } from "../api/endpoints";
import { Sentry } from "../sentry";

function Bomb(): never {
  throw new Error("Sentry 疎通確認のための意図的な描画エラー(React)");
}

/** Sentry の疎通確認用(VITE_SENTRY_DEBUG=1 のときだけ表示)。 */
export default function DebugSentryPage() {
  const [explode, setExplode] = useState(false);
  const [message, setMessage] = useState("");
  if (explode) return <Bomb />;
  return (
    <Stack spacing={2} sx={{ maxWidth: 560 }}>
      <h1 style={{ margin: 0, fontSize: "1.4rem" }}>Sentry 疎通確認</h1>
      <Alert severity="info">DSN が設定されている場合のみ、Sentry にイベントが届きます。</Alert>
      <Button variant="outlined" onClick={() => { Sentry.captureException(new Error("Sentry 疎通確認のための意図的な例外(React)")); setMessage("React から例外を送信しました。"); }}>
        React: 例外を送る
      </Button>
      <Button variant="outlined" color="error" onClick={() => setExplode(true)}>React: 描画エラーを起こす(ErrorBoundary)</Button>
      <Button variant="outlined" onClick={() => debug.sentry().catch(() => setMessage("Django: 500 を受け取りました(Sentry へ送信されます)。管理者でログインし SENTRY_DEBUG_ENDPOINT_ENABLED=1 が必要です。"))}>
        Django: 例外を起こす(管理者のみ)
      </Button>
      {message ? <Alert severity="success" role="status">{message}</Alert> : null}
    </Stack>
  );
}
