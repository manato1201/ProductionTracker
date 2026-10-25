import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./context/Auth";
import { ThemeModeProvider } from "./context/ThemeMode";
import { ToastProvider } from "./context/Toast";
import { initSentry } from "./sentry";
import "./styles/global.scss";

initSentry();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeModeProvider>
      <ToastProvider>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </ToastProvider>
    </ThemeModeProvider>
  </StrictMode>,
);
