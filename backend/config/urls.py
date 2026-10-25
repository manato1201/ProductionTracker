from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from tracker import health, views, views_auth, views_ingest

router = SimpleRouter()
router.register("projects", views.ProjectViewSet, basename="project")
router.register("steps", views.StepViewSet, basename="step")
router.register("entities", views.EntityViewSet, basename="entity")
router.register("tasks", views.TaskViewSet, basename="task")
router.register("versions", views.VersionViewSet, basename="version")
router.register("notes", views.NoteViewSet, basename="note")
router.register("quality-reports", views.QualityReportViewSet, basename="quality-report")
router.register("visual-results", views.VisualResultViewSet, basename="visual-result")

api_patterns = [
    path("auth/csrf/", views_auth.CsrfView.as_view()),
    path("auth/login/", views_auth.LoginView.as_view()),
    path("auth/logout/", views_auth.LogoutView.as_view()),
    path("me/", views_auth.MeView.as_view()),
    path("ingest/quality/", views_ingest.QualityIngestView.as_view()),
    path("ingest/visual/", views_ingest.VisualIngestView.as_view()),
    path("healthz", health.healthz),
    path("_debug/sentry/", health.SentryDebugView.as_view()),
    path("", include(router.urls)),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", health.healthz),  # ToolOrchestrationHub の死活監視用(認証なし)
    path("api/v1/", include(api_patterns)),
]


def _json_error(status, code, detail):
    def view(request, *args, **kwargs):
        if request.path.startswith("/api/"):
            return JsonResponse({"code": code, "detail": detail}, status=status)
        from django.http import HttpResponse

        return HttpResponse(detail, status=status, content_type="text/plain; charset=utf-8")

    return view


handler404 = _json_error(404, "not_found", "見つかりません。")
handler500 = _json_error(500, "server_error", "サーバーでエラーが発生しました。")
