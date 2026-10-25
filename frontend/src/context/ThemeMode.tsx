import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { CssBaseline, ThemeProvider, useMediaQuery } from "@mui/material";
import { buildTheme } from "../theme";

export type ThemeModeSetting = "system" | "light" | "dark";
const KEY = "pt-theme";

function load(): ThemeModeSetting {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : "system";
  } catch {
    return "system"; // プライベートウィンドウ等で使えなくても動く
  }
}

interface Ctx {
  setting: ThemeModeSetting;
  effective: "light" | "dark";
  cycle: () => void;
}
const ThemeModeContext = createContext<Ctx>({ setting: "system", effective: "light", cycle: () => {} });
export const useThemeMode = () => useContext(ThemeModeContext);

const ORDER: ThemeModeSetting[] = ["system", "light", "dark"];

export function ThemeModeProvider({ children }: { children: ReactNode }) {
  const [setting, setSetting] = useState<ThemeModeSetting>(load);
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  const effective = setting === "system" ? (prefersDark ? "dark" : "light") : setting;

  useEffect(() => {
    const root = document.documentElement;
    if (setting === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", setting);
    try {
      localStorage.setItem(KEY, setting);
    } catch {
      /* 保存できなくても続行 */
    }
  }, [setting]);

  const theme = useMemo(() => buildTheme(effective), [effective]);
  const value = useMemo<Ctx>(
    () => ({ setting, effective, cycle: () => setSetting((s) => ORDER[(ORDER.indexOf(s) + 1) % ORDER.length]) }),
    [setting, effective],
  );
  return (
    <ThemeModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline enableColorScheme />
        {children}
      </ThemeProvider>
    </ThemeModeContext.Provider>
  );
}
