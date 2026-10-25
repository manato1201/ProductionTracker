import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { auth } from "../api/endpoints";
import { ApiError, setUnauthorizedHandler } from "../api/client";
import type { User } from "../api/types";

type Status = "loading" | "authed" | "anon";
interface Ctx {
  status: Status;
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}
const AuthContext = createContext<Ctx | null>(null);

export function useAuth(): Ctx {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("AuthProvider が必要です");
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
      setStatus("anon");
    });
    (async () => {
      try {
        await auth.csrf(); // CSRF クッキーを受け取る
        setUser(await auth.me());
        setStatus("authed");
      } catch (e) {
        if (!(e instanceof ApiError) || e.status !== 401) console.error(e);
        setStatus("anon");
      }
    })();
    return () => setUnauthorizedHandler(null);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    await auth.csrf();
    setUser(await auth.login(username, password));
    setStatus("authed");
  }, []);

  const logout = useCallback(async () => {
    await auth.logout();
    setUser(null);
    setStatus("anon");
  }, []);

  const value = useMemo(() => ({ status, user, login, logout }), [status, user, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
