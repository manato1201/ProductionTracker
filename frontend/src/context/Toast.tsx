import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { Alert, Snackbar } from "@mui/material";

type Severity = "success" | "error" | "info" | "warning";
interface ToastItem {
  key: number;
  message: string;
  severity: Severity;
}
interface Ctx {
  notify: (message: string, severity?: Severity) => void;
}
const ToastContext = createContext<Ctx>({ notify: () => {} });
export const useToast = () => useContext(ToastContext);

/** トースト(08)。状態遷移の成功と、拒否されたときの理由を出す。 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [current, setCurrent] = useState<ToastItem | null>(null);

  const notify = useCallback((message: string, severity: Severity = "info") => {
    setCurrent({ key: Date.now() + Math.random(), message, severity });
  }, []);
  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <Snackbar
        key={current?.key}
        open={current !== null}
        autoHideDuration={current?.severity === "error" ? 8000 : 4000}
        onClose={(_, reason) => reason !== "clickaway" && setCurrent(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        {current ? (
          <Alert severity={current.severity} variant="filled" onClose={() => setCurrent(null)} sx={{ width: "100%" }} role="status">
            {current.message}
          </Alert>
        ) : undefined}
      </Snackbar>
    </ToastContext.Provider>
  );
}
