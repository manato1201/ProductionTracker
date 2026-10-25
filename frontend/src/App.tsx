import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { Sentry } from "./sentry";
import { AppLayout } from "./components/AppLayout";
import { RowSkeletons } from "./components/Feedback";
import { useAuth } from "./context/Auth";
import BoardPage from "./pages/BoardPage";
import DebugSentryPage from "./pages/DebugSentryPage";
import EntityPage from "./pages/EntityPage";
import LoginPage from "./pages/LoginPage";
import MyTasksPage from "./pages/MyTasksPage";
import OverviewPage from "./pages/OverviewPage";
import ProjectLayout from "./pages/ProjectLayout";
import ProjectsPage from "./pages/ProjectsPage";

function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();
  if (status === "loading") return <div style={{ padding: 24 }}><RowSkeletons count={3} /></div>;
  if (status === "anon") return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return <Outlet />;
}

function NotFound() {
  return <p>ページが見つかりません。<a href="/projects">プロジェクト一覧へ</a></p>;
}

export default function App() {
  return (
    <Sentry.ErrorBoundary fallback={<p style={{ padding: 24 }}>エラーが発生しました。ページを再読み込みしてください。</p>}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/projects" replace />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/:code" element={<ProjectLayout />}>
              <Route index element={<OverviewPage />} />
              <Route path="board" element={<BoardPage />} />
              <Route path="entities/:id" element={<EntityPage />} />
            </Route>
            <Route path="/me/tasks" element={<MyTasksPage />} />
            {import.meta.env.VITE_SENTRY_DEBUG === "1" ? <Route path="/debug/sentry" element={<DebugSentryPage />} /> : null}
            <Route path="*" element={<NotFound />} />
          </Route>
        </Route>
      </Routes>
    </Sentry.ErrorBoundary>
  );
}
