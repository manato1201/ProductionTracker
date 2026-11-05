import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { Alert, Button, Snackbar } from "@mui/material";

type Severity = "success" | "error" | "info" | "warning";
/** 取り消しなどの「次の一手」。トーストの右に、押せるボタンとして出す。 */
export interface ToastAction {
  label: string;
  onClick: () => void;
}
interface ToastItem {
  key: number;
  lines: string[];
  severity: Severity;
  action?: ToastAction;
}
interface Ctx {
  /** `message` は 1 行の文字列、または行の配列(「何が / なぜ / 次に」など)。 */
  notify: (message: string | string[], severity?: Severity, action?: ToastAction) => void;
}
const ToastContext = createContext<Ctx>({ notify: () => {} });
export const useToast = () => useContext(ToastContext);

/** トースト(08)。状態遷移の成功と、拒否されたときの理由を出す。 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [current, setCurrent] = useState<ToastItem | null>(null);

  const notify = useCallback((message: string | string[], severity: Severity = "info", action?: ToastAction) => {
    setCurrent({ key: Date.now() + Math.random(), lines: Array.isArray(message) ? message : [message], severity, action });
  }, []);
  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <Snackbar
        key={current?.key}
        open={current !== null}
        autoHideDuration={current?.severity === "error" ? 10000 : current?.action ? 8000 : 4000}
        onClose={(_, reason) => reason !== "clickaway" && setCurrent(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        {current ? (
          <Alert
            severity={current.severity}
            variant="filled"
            onClose={() => setCurrent(null)}
            sx={{ width: "100%" }}
            role="status"
            action={
              current.action ? (
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => {
                    const act = current.action;
                    setCurrent(null);
                    act?.onClick();
                  }}
                >
                  {current.action.label}
                </Button>
              ) : undefined
            }
          >
            {current.lines.map((line, i) => (
              <div key={i}>{line}</div>
            ))}
          </Alert>
        ) : undefined}
      </Snackbar>
    </ToastContext.Provider>
  );
}
