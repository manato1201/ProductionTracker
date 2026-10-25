import { createTheme } from "@mui/material/styles";
import tokens from "./styles/tokens.module.scss";

/** MUI のテーマ。色は Sass のデザイントークン(tokens.module.scss の :export)から取る。 */
export function buildTheme(mode: "light" | "dark") {
  const dark = mode === "dark";
  return createTheme({
    palette: {
      mode,
      primary: { main: dark ? tokens.darkPrimary : tokens.lightPrimary },
      error: { main: dark ? tokens.darkDanger : tokens.lightDanger },
      background: {
        default: dark ? tokens.darkBg : tokens.lightBg,
        paper: dark ? tokens.darkSurface : tokens.lightSurface,
      },
      text: {
        primary: dark ? tokens.darkText : tokens.lightText,
        secondary: dark ? tokens.darkTextMuted : tokens.lightTextMuted,
      },
      divider: dark ? tokens.darkBorder : tokens.lightBorder,
    },
    shape: { borderRadius: 8 },
    typography: { fontFamily: tokens.fontSans, button: { textTransform: "none", fontWeight: 600 } },
    components: {
      MuiButton: { defaultProps: { disableElevation: true } },
      MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    },
  });
}
