import { Alert, Button, Paper, Stack, TextField } from "@mui/material";
import { useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../context/Auth";

export default function LoginPage() {
  const { status, login } = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/projects";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  if (status === "authed") return <Navigate to={from} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(undefined);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "ログインに失敗しました。");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack alignItems="center" justifyContent="center" sx={{ minHeight: "100vh", p: 2 }}>
      <Paper component="form" onSubmit={submit} variant="outlined" sx={{ p: 3, width: "100%", maxWidth: 360 }}>
        <Stack spacing={2}>
          <h1 style={{ margin: 0, fontSize: "1.25rem" }}>ProductionTracker</h1>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <TextField label="ユーザー名" autoComplete="username" required autoFocus value={username} onChange={(e) => setUsername(e.target.value)} />
          <TextField label="パスワード" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button type="submit" variant="contained" disabled={busy}>ログイン</Button>
        </Stack>
      </Paper>
    </Stack>
  );
}
